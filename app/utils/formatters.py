from app.api.v1.schemas.policy import PolicyWithRules
from app.db.models import Message


def format_policies_and_rules_into_text(policies: list[PolicyWithRules]) -> str:
    formatted_policies = []

    for policy in policies:
        policy_info = [
            f"Policy Type: {policy.policy_type}",
            f"Policy Name: {policy.name}",
            f"Description: {policy.description}",
            "Rules:"
        ]

        for rule in policy.rules:
            policy_info.extend([
                f"  - Rule Type: {rule.rule_type}",
                f"  - Severity: {rule.severity}",
                f"  - Description: {rule.description}",
            ])

        formatted_policies.append("\n".join(policy_info))

    return "\n\n---\n\n".join(formatted_policies)


def format_messages_history(messages: list[Message]) -> str:
    formatted_messages = []
    for message in messages:
            formatted_messages.append(f"({message.created_at}){message.author}: {message.content}")
    return "\n".join(formatted_messages)


def print_model(model, label="Model"):
    print(f"\n--- {label} ---")
    for c in model.__table__.columns:
        print(f"{c.name}: {getattr(model, c.name)}")
    print("-" * (len(label) + 8))

