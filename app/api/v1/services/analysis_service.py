import os

from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select

from app.analysers.document_processor import DocumentProcessor
from app.api.v1.services.policy_service import get_active_policies_by_company
from app.core.ai.document_analysis import upload_file, initial_analysis, chat_with_document as ask_the_document
from app.db.models import Document, AnalysisResult
from app.utils.formatters import format_policies_and_rules_into_text


async def upload_document_to_gemini(db: AsyncSession, document_id: int) -> Document:
    result = await db.execute(select(Document).filter(Document.id == document_id))
    document = result.scalar_one_or_none()

    if not document:
        raise Exception("Document not found")

    if document.gemini_name:
        assert isinstance(document, Document)
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
    assert isinstance(document, Document)

    return document


async def analyze_document(db: AsyncSession, document: Document):
    print("Getting policies and rules")
    policies_and_rules = await get_active_policies_by_company(db, company_id=document.company_id)
    print("got policies_and_rules")
    print(policies_and_rules)
    pr_text = format_policies_and_rules_into_text(policies_and_rules)
    analysis_data = initial_analysis(document.gemini_name, pr_text)

    analysis_result_db = AnalysisResult(
        document_id=document.id,
        company_name=analysis_data.company_name,
        conflicts=[conflict.model_dump() for conflict in analysis_data.conflicts] if analysis_data.conflicts else [],
        risks=[risk.model_dump() for risk in analysis_data.risks] if analysis_data.risks else [],
        missing_clauses=[clause.model_dump() for clause in
                         analysis_data.missing_clauses] if analysis_data.missing_clauses else [],
        suggestions=[suggestion.model_dump() for suggestion in
                     analysis_data.suggestions] if analysis_data.suggestions else [],
    )

    db.add(analysis_result_db)
    document.is_processed = True
    await db.commit()
    await db.refresh(analysis_result_db)
    return analysis_result_db


async def chat_with_document(db:AsyncSession, document_id: int, message: str):
    result = await db.execute(select(Document).filter(Document.id == document_id))
    document = result.scalar_one_or_none()

    print(f"Chat with document {document_id}")

    if not document:
        raise Exception("Document not found")
    if not document.is_processed or document.gemini_name is None:
        raise Exception("Document is not processed yet")

    return await ask_the_document(text=message, gemini_file_name=document.gemini_name, db=db)
