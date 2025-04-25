from typing import Optional

from loguru import logger
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.ai.embeddings import get_embedding_gemini
from app.db.models import Embedding, Policy, PolicyRule
from app.db.soft_delete import filtered_select


async def get_embedding(db: AsyncSession, content_type: str, content_id: int):
    query = filtered_select(Embedding).filter(Embedding.content_type == content_type, Embedding.content_id == content_id)
    result = await db.execute(query)
    return result.scalar_one_or_none()

async def delete_embedding(db: AsyncSession, content_type: str, content_id: int):
    embedding = await get_embedding(db, content_type, content_id)
    if embedding:
        await embedding.soft_delete(db=db)
        await db.commit()
        return True
    return False

async def create_embedding(db: AsyncSession, policy: Optional[Policy], rule: Optional[PolicyRule]):
    if not policy and not rule:
        raise ValueError("Either a policy or a rule must be provided to create an embedding.")
    if policy and rule:
        raise ValueError("Provide either a policy or a rule, not both.")

    text_to_embed: str = ""
    content_type: str = ""
    content_id: int = 0

    if policy:
        text_to_embed = f"{policy.name} - {policy.description}"
        content_type = 'policy'
        content_id = policy.id
    elif rule:
        rule_text = rule.description or " ".join(rule.keywords)
        text_to_embed = f"{rule.rule_type} \n\n {rule_text}"
        content_type = 'rule'
        content_id = rule.id

    try:
        embedding_vector = get_embedding_gemini(text_to_embed)

        old_embedding = await get_embedding(db, content_type, content_id)
        if old_embedding:
            await old_embedding.soft_delete(db=db)

        embedding = Embedding(
            content_type=content_type,
            content_id=content_id,
            embedding=embedding_vector
        )

        db.add(embedding)
        await db.commit()
        await db.refresh(embedding)
        return embedding
    except Exception as e:
        logger.error(f"An error occurred during embedding creation: {e}")
        raise
