import time
from typing import Type

from sqlalchemy.orm import Session

from app.api.v1.schemas.policy import PolicyInDB
from app.api.v1.schemas.rule import RuleInDB
from app.core.ai.embeddings import get_embedding_gemini
from app.db.models.embedding import Embedding
from app.db.models.policy import Policy
from app.db.models.policy_rule import PolicyRule
from app.db.session import SessionLocal


def embed_existing_data():
    db: Session = SessionLocal()

    requests_made = 0
    RATE_LIMIT = 10
    SLEEP_INTERVAL = 60 / RATE_LIMIT

    policies = db.query(Policy).all()
    policy: Type[PolicyInDB]
    for policy in policies:
        if policy.description:
            embedding = Embedding(
                content_type='policy',
                content_id=policy.id,
                embedding=get_embedding_gemini(f"{policy.name} - {policy.description}")
            )
            db.add(embedding)

            requests_made += 1
            time.sleep(SLEEP_INTERVAL)

    rules = db.query(PolicyRule).all()
    rule: Type[RuleInDB]
    for rule in rules:
        rule_text = rule.description or " ".join(rule.keywords)
        embedding = Embedding(
            content_type='rule',
            content_id=rule.id,
            embedding=get_embedding_gemini(f"{rule.rule_type} \n\n {rule_text}")
        )
        db.add(embedding)

        requests_made += 1
        time.sleep(SLEEP_INTERVAL)

    db.commit()
    db.close()


if __name__ == "__main__":
    embed_existing_data()