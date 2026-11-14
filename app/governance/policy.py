"""Allowlisted, resource-specific policy. The LLM cannot change its grants."""

from app.governance.tokens import TokenRejected

MOCK_ISSUES = {
    "DEMO-1": {"key": "DEMO-1", "summary": "Review project acceptance criteria", "status": "Open"},
    "DEMO-2": {"key": "DEMO-2", "summary": "Validate synthetic use case", "status": "Doing"},
}
AGENT_REGISTRY = {
    "agent:triage": frozenset({"jira.issue.read"}),
    "agent:observer": frozenset({"jira.issue.read"}),
}
SUPPORTED_TOOLS = frozenset({"jira.issue.read"})


class PolicyRejected(PermissionError):
    """Request exceeds a trusted delegation or a locally registered agent policy."""


def authorized_grants(
    grants: list[dict], human_claims: dict, actor_claims: dict
) -> list[dict]:
    human = human_claims["sub"]
    agent = actor_claims["sub"]
    if not human.startswith("human:") or agent not in AGENT_REGISTRY:
        raise PolicyRejected("Unknown delegator or agent")
    human_permissions = human_claims.get("permissions")
    actor_permissions = actor_claims.get("permissions")
    if (
        not isinstance(human_permissions, list)
        or not all(isinstance(item, str) for item in human_permissions)
        or not isinstance(actor_permissions, list)
        or not all(isinstance(item, str) for item in actor_permissions)
    ):
        raise TokenRejected("Missing trusted permissions")
    result = []
    for grant in grants:
        tool = grant["tool"]
        resource = grant["resource"]
        if (
            grant["type"] != "mcp_tool"
            or tool not in SUPPORTED_TOOLS
            or resource not in MOCK_ISSUES
            or tool not in human_permissions
            or tool not in actor_permissions
            or tool not in AGENT_REGISTRY[agent]
        ):
            raise PolicyRejected("Requested tool or resource is not authorized")
        if grant not in result:
            result.append(grant)
    return result


def execute_read(tool: str, resource: str, grants: list[dict]) -> dict:
    if (
        tool not in SUPPORTED_TOOLS
        or resource not in MOCK_ISSUES
        or {"type": "mcp_tool", "tool": tool, "resource": resource} not in grants
    ):
        raise PolicyRejected("Tool execution exceeds delegated grant")
    return dict(MOCK_ISSUES[resource])
