import os
from http import HTTPStatus
from typing import Optional

from fastapi import HTTPException
from google.genai.errors import APIError
from loguru import logger
from sqlalchemy import and_
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from sqlalchemy.orm import joinedload, contains_eager

from app.analysers.document_processor import DocumentProcessor
from app.api.v1.schemas.analysis import AnalysisResultInDb
from app.api.v1.schemas.conversation import ConversationCreate, MessageAuthor
from app.api.v1.schemas.policy import PolicyWithRules
from app.api.v1.schemas.rule import RuleInDB
from app.api.v1.services.checklist_service import get_checklist
from app.api.v1.services.conversation_service import get_conversation, create_conversation, add_message, \
    get_recent_messages
from app.api.v1.services.policy_service import get_active_policies_by_company
from app.core.ai.ai_client import gemini_client
from app.core.ai.document_analysis import upload_file, initial_analysis, chat_with_document as ask_the_document
from app.db.models import Document, AnalysisResult, User, Policy, PolicyRule, Checklist
from app.db.soft_delete import filtered_select, filtered_load
from app.utils.formatters import format_policies_and_rules_into_text


async def get_all_analysis_results(db: AsyncSession, user: User):
    if user.is_superuser:
        query = filtered_select(AnalysisResult).order_by(AnalysisResult.id.desc())
    else:
        query = filtered_select(AnalysisResult).join(Document, Document.id == AnalysisResult.document_id).filter(
            Document.company_id == user.company_id)

    results = await db.execute(query.options(joinedload(AnalysisResult.checklist)))
    db_results = results.scalars().all()
    return [
        AnalysisResultInDb.model_validate(item, from_attributes=True).model_copy(
            update={
                "checklist_name": getattr(item.checklist, 'name', None),
                "checklist_id": item.checklist.id if getattr(item.checklist, 'is_deleted', False) else None
            }
        )
        for item in db_results
    ]


async def get_document_analysis_results(db: AsyncSession, user: User, document_id: int):
    result = await db.execute(
        filtered_select(AnalysisResult)
        .filter(AnalysisResult.document_id == document_id)
        .options(joinedload(AnalysisResult.checklist))
    )
    db_results = result.scalars().all()

    return [
        AnalysisResultInDb.model_validate(item, from_attributes=True).model_copy(
            update={
                "checklist_name": getattr(item.checklist, 'name', None),
                "checklist_id": item.checklist.id if getattr(item.checklist, 'is_deleted', False) else None
            }
        )
        for item in db_results
    ]


async def upload_document_to_gemini(db: AsyncSession, document_id: int) -> Document:
    result = await db.execute(filtered_select(Document).filter(Document.id == document_id))
    document = result.scalar_one_or_none()

    if not document:
        raise Exception("Document not found")

    if document.gemini_name and check_document_availability(document):
        return document

    temp_file_created = False
    file_path = document.file_path

    if document.content_type != "text/plain":
        try:
            document_text = document.text_content or DocumentProcessor().process_document(document.file_path)

            file_path = f"/tmp/{document.filename}.txt"
            with open(file_path, "w", encoding="utf-8") as temp_file:
                temp_file.write(document_text)
            temp_file_created = True
        except ValueError as e:
            print(f"Error processing {document_id}: {e}")

    response = upload_file(file_path)

    document.gemini_name = response.name

    if temp_file_created:
        os.remove(file_path)

    await db.commit()
    await db.refresh(document)
    return document


async def get_policies_and_rules_from_checklist(db: AsyncSession, checklist_id: int):
    policies_and_rules = []

    checklist = await get_checklist(db, checklist_id)
    if not checklist:
        raise HTTPException(status_code=404, detail="Checklist not found")

    if checklist.ruleset:
        rule_ids = checklist.ruleset

        rules_query = filtered_select(PolicyRule).filter(PolicyRule.id.in_(rule_ids))
        rules_result = await db.execute(rules_query)
        rules = rules_result.scalars().all()

        policy_ids = set(rule.policy_id for rule in rules)

        policies_query = filtered_select(Policy).filter(Policy.id.in_(policy_ids)).options(
            joinedload(Policy.rules)
        )
        policies_result = await db.execute(policies_query)
        policies = policies_result.unique().scalars().all()

        for policy in policies:
            filtered_rules = [rule for rule in policy.rules if rule.id in rule_ids and rule.is_deleted is False]

            policy_with_rules = PolicyWithRules(
                id=policy.id,
                name=policy.name,
                description=policy.description,
                policy_type=policy.policy_type,
                source_url=policy.source_url,
                is_active=policy.is_active,
                company_id=policy.company_id,
                created_at=policy.created_at,
                updated_at=policy.updated_at,
                rules=[RuleInDB.model_validate(rule) for rule in filtered_rules]
            )

            policies_and_rules.append(policy_with_rules)

    return policies_and_rules


async def analyze_document(db: AsyncSession, document: Document, checklist_id: Optional[int] = None):
    if checklist_id:
        policies_and_rules = await get_policies_and_rules_from_checklist(db, checklist_id)
    else:
        policies_and_rules = await get_active_policies_by_company(db, company_id=document.company_id)

    pr_text = format_policies_and_rules_into_text(policies_and_rules)
    analysis_data = initial_analysis(document.gemini_name, pr_text)

    analysis_result_db = AnalysisResult(
        document_id=document.id,
        checklist_id=checklist_id,
        title=analysis_data.title,
        company_name=analysis_data.company_name,
        conflicts=[conflict.model_dump() for conflict in analysis_data.conflicts] if analysis_data.conflicts else [],
        risks=[risk.model_dump() for risk in analysis_data.risks] if analysis_data.risks else [],
        missing_clauses=[clause.model_dump() for clause in
                         analysis_data.missing_clauses] if analysis_data.missing_clauses else [],
        suggestions=[suggestion.model_dump() for suggestion in
                     analysis_data.suggestions] if analysis_data.suggestions else [],
        payment_terms=[payment_term.model_dump() for payment_term in
                       analysis_data.payment_terms] if analysis_data.payment_terms else [],
    )

    db.add(analysis_result_db)
    document.is_processed = True
    await db.commit()
    await db.refresh(analysis_result_db)
    return analysis_result_db


async def chat_with_document(db: AsyncSession, document_id: int, user: User, message: str):
    result = await db.execute(select(Document).filter(Document.id == document_id))
    document = result.scalar_one_or_none()

    if not document:
        raise HTTPException(HTTPStatus.NOT_FOUND, "Document not found")
    if not document.is_processed or document.gemini_name is None:
        raise HTTPException(HTTPStatus.CONFLICT, "Document is not processed yet")
    if not check_document_availability(document):
        document = await upload_document_to_gemini(db, document.id)

    conversation = await get_conversation(db, document_id=document_id, user_id=user.id)
    if not conversation:
        conversation = await create_conversation(db, ConversationCreate(document_id=document_id, user_id=user.id))

    await add_message(db, conversation.id, message, MessageAuthor.user)

    response = await ask_the_document(text=message, gemini_file_name=document.gemini_name, db=db)

    answer = await add_message(db, conversation.id, response, MessageAuthor.legalcheck)

    return answer


def check_document_availability(document: Document):
    try:
        gemini_client.files.get(name=document.gemini_name)
        return True
    except APIError as e:
        logger.error(f"Error getting document {document.id} from Gemini: {e.code} - {e.message}")
        return False
