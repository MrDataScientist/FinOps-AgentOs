"""No arbitrary infrastructure or GitHub writes are exposed by the MVP."""


class HumanApprovalRequired(PermissionError):
    pass


def require_approval(*, approved_by_human: bool) -> None:
    """Stub gate for future action workflows, not a complete approval protocol."""
    if not approved_by_human:
        raise HumanApprovalRequired("Human approval required for consequential actions")
