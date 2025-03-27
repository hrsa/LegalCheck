from typing import Dict

from pgvector.sqlalchemy import Vector
from sqlalchemy import func, cast
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select

from app.api.v1.schemas.policy import PolicyWithRulesForSemanticSearch
from app.api.v1.schemas.rule import RuleWithSimilarity
from app.core.ai.embeddings import get_embedding_gemini
from app.db.models import Embedding, PolicyRule, Policy


async def semantic_search(db: AsyncSession, text: str, top_k: int = 10) -> list:

    embedding_vector = get_embedding_gemini(text)

    stmt = (
        select(
            Embedding,
            func.cosine_distance(Embedding.embedding, cast(embedding_vector, Vector)).label("distance")
        )
        .order_by("distance")
        .limit(top_k)
    )

    result = await db.execute(stmt)
    matches = result.all()

    policies: Dict[int, PolicyWithRulesForSemanticSearch] = {}

    for embedding, distance in matches:
        similarity = 1 - distance

        if embedding.content_type == "rule":
            rule_result = await db.execute(
                select(PolicyRule).filter(PolicyRule.id == embedding.content_id)
            )
            rule_db = rule_result.scalars().first()

            if not rule_db:
                continue  # Safety check explicitly done

            rule_with_similarity = RuleWithSimilarity(
                id=rule_db.id,
                policy_id=rule_db.policy_id,
                rule_type=rule_db.rule_type,
                description=rule_db.description,
                severity=rule_db.severity,
                keywords=rule_db.keywords,
                created_at=rule_db.created_at,
                updated_at=rule_db.updated_at,
                similarity=similarity
            )

            policy_entry = policies.get(rule_db.policy_id)

            if not policy_entry:
                policy_result = await db.execute(
                    select(Policy).filter(Policy.id == rule_db.policy_id)
                )
                policy_db = policy_result.scalars().first()

                if not policy_db:
                    continue  # Explicit safety check

                policies[rule_db.policy_id] = PolicyWithRulesForSemanticSearch(
                    id=policy_db.id,
                    name=policy_db.name,
                    description=policy_db.description,
                    policy_type=policy_db.policy_type,
                    source_url=policy_db.source_url,
                    is_active=policy_db.is_active,
                    company_id=policy_db.company_id,
                    created_at=policy_db.created_at,
                    updated_at=policy_db.updated_at,
                    rules=[rule_with_similarity],
                    similarity=similarity
                )
            else:
                policy_entry.rules.append(rule_with_similarity)
                if similarity > policy_entry.similarity:
                    policy_entry.similarity = similarity

        elif embedding.content_type == "policy":
            policy_result = await db.execute(
                select(Policy).filter(Policy.id == embedding.content_id)
            )
            policy_db = policy_result.scalars().first()

            if not policy_db:
                continue  # Explicit and clear safety check

            policy_entry = policies.get(policy_db.id)

            if not policy_entry:
                policies[policy_db.id] = PolicyWithRulesForSemanticSearch(
                    id=policy_db.id,
                    name=policy_db.name,
                    description=policy_db.description,
                    policy_type=policy_db.policy_type,
                    source_url=policy_db.source_url,
                    is_active=policy_db.is_active,
                    company_id=policy_db.company_id,
                    created_at=policy_db.created_at,
                    updated_at=policy_db.updated_at,
                    rules=[],
                    similarity=similarity
                )
            else:
                if similarity > policy_entry.similarity:
                    policy_entry.similarity = similarity

    # Explicit sort by similarity in descending order
    return sorted(policies.values(), key=lambda p: p.similarity, reverse=True)


