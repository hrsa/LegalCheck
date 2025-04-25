from typing import Dict, Set

from loguru import logger
from pgvector.sqlalchemy import Vector
from sqlalchemy import func, cast
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select

from app.api.v1.schemas.policy import PolicyWithRulesForSemanticSearch
from app.api.v1.schemas.rule import RuleWithSimilarity
from app.core.ai.embeddings import get_embedding_gemini
from app.db.models import Embedding, PolicyRule, Policy
from app.db.soft_delete import filtered_select


async def semantic_search(db: AsyncSession, text: str, top_k: int = 10) -> list:
    embedding_vector = get_embedding_gemini(text)

    stmt = (
        filtered_select(
            Embedding,
            func.cosine_distance(Embedding.embedding, cast(embedding_vector, Vector)).label("distance")
        )
        .order_by("distance")
        .limit(top_k)
    )

    result = await db.execute(stmt)
    matches = result.all()

    if not matches:
        return []

    # 2. Collect IDs and store similarities
    rule_ids_to_fetch: Set[int] = set()
    policy_ids_direct_hit: Set[int] = set()
    # Store similarity keyed by (content_type, content_id)
    similarities: Dict[tuple[str, int], float] = {}

    for embedding, distance in matches:
        similarity = 1.0 - float(distance)  # Ensure float conversion
        key = (embedding.content_type, embedding.content_id)
        # Store the highest similarity found for a specific item
        similarities[key] = max(similarity, similarities.get(key, 0.0))

        if embedding.content_type == "rule":
            rule_ids_to_fetch.add(embedding.content_id)
        elif embedding.content_type == "policy":
            policy_ids_direct_hit.add(embedding.content_id)

    # 3. Fetch all relevant rules in one query
    rules_map: Dict[int, PolicyRule] = {}
    policy_ids_from_rules: Set[int] = set()
    if rule_ids_to_fetch:
        rules_stmt = filtered_select(PolicyRule).filter(PolicyRule.id.in_(rule_ids_to_fetch))
        rules_result = await db.execute(rules_stmt)
        fetched_rules = rules_result.scalars().all()
        for rule_db in fetched_rules:
            rules_map[rule_db.id] = rule_db
            policy_ids_from_rules.add(rule_db.policy_id)

    # 4. Combine policy IDs
    all_policy_ids_to_fetch = policy_ids_direct_hit.union(policy_ids_from_rules)

    # 5. Fetch all relevant policies in one query
    policies_map: Dict[int, Policy] = {}
    if all_policy_ids_to_fetch:
        policies_stmt = filtered_select(Policy).filter(Policy.id.in_(all_policy_ids_to_fetch))
        policies_result = await db.execute(policies_stmt)
        fetched_policies = policies_result.scalars().all()
        for policy_db in fetched_policies:
            policies_map[policy_db.id] = policy_db

    # 6. Process matches using pre-fetched data
    final_policies: Dict[int, PolicyWithRulesForSemanticSearch] = {}

    for (content_type, content_id), similarity in similarities.items():

        if content_type == "rule":
            rule_db = rules_map.get(content_id)
            if not rule_db:
                logger.warning(
                    f"Rule ID {content_id} found in embeddings but not fetched from DB (likely soft-deleted or inconsistency).")
                continue

            policy_db = policies_map.get(rule_db.policy_id)
            if not policy_db:
                logger.warning(
                    f"Policy ID {rule_db.policy_id} for Rule ID {content_id} not fetched from DB (likely soft-deleted or inconsistency).")
                continue

            policy_entry = final_policies.get(policy_db.id)
            if not policy_entry:
                policy_entry = PolicyWithRulesForSemanticSearch(
                    id=policy_db.id,
                    name=policy_db.name,
                    description=policy_db.description,
                    policy_type=policy_db.policy_type,
                    source_url=policy_db.source_url,
                    is_active=policy_db.is_active,
                    company_id=policy_db.company_id,
                    similarity=similarity,
                    rules=[],
                    created_at=policy_db.created_at,
                )
                final_policies[policy_db.id] = policy_entry

            rule_with_similarity = RuleWithSimilarity(
                id=rule_db.id,
                policy_id=rule_db.policy_id,
                rule_type=rule_db.rule_type,
                description=rule_db.description,
                severity=rule_db.severity,
                keywords=rule_db.keywords,
                created_at=rule_db.created_at,
                updated_at=rule_db.updated_at,
                similarity=similarity,
            )
            policy_entry.rules.append(rule_with_similarity)

            policy_entry.similarity = max(policy_entry.similarity, similarity)

        elif content_type == "policy":
            policy_db = policies_map.get(content_id)
            if not policy_db:
                logger.warning(
                    f"Policy ID {content_id} found in embeddings but not fetched from DB (likely soft-deleted or inconsistency).")
                continue

            # Get or create the policy entry
            policy_entry = final_policies.get(policy_db.id)
            if not policy_entry:
                policy_entry = PolicyWithRulesForSemanticSearch(
                    id=policy_db.id,
                    name=policy_db.name,
                    description=policy_db.description,
                    policy_type=policy_db.policy_type,
                    source_url=policy_db.source_url,
                    is_active=policy_db.is_active,
                    company_id=policy_db.company_id,
                    similarity=similarity,
                    rules=[],
                    created_at=policy_db.created_at,
                )
                final_policies[policy_db.id] = policy_entry

            policy_entry.similarity = max(policy_entry.similarity, similarity)

    return sorted(final_policies.values(), key=lambda p: p.similarity, reverse=True)
