from app.api.v1.schemas.policy import PolicyWithRules


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
