"""
Assembles the Claude Agent SDK client for the Climate Intel Dev Agent.

Bundles all 9 custom tools into a single in-process MCP server and returns
ClaudeAgentOptions ready to pass to ClaudeSDKClient.
"""

from pathlib import Path
import sys

from claude_agent_sdk import (
    ClaudeAgentOptions,
    create_sdk_mcp_server,
    HookMatcher,
)

sys.path.insert(0, str(Path(__file__).parent.parent))
from agent.config import PROJECT_ROOT
from agent.prompts.system import build_system_prompt
from agent.tools.mongodb_tools import (
    query_collection,
    check_data_freshness,
    collection_stats,
    verify_upsert,
    full_data_audit,
)
from agent.tools.api_tools import (
    check_api_health,
    probe_endpoint,
    trigger_integration,
    check_backend_status,
)

_ALL_TOOLS = [
    query_collection,
    check_data_freshness,
    collection_stats,
    verify_upsert,
    full_data_audit,
    check_api_health,
    probe_endpoint,
    trigger_integration,
    check_backend_status,
]


def create_mcp_server():
    """Create the in-process MCP server with all 9 custom tools."""
    return create_sdk_mcp_server("climate-intel-tools", tools=_ALL_TOOLS)


def build_options(max_turns: int = 50) -> ClaudeAgentOptions:
    """Return ClaudeAgentOptions wired up with all tools and system prompt."""
    mcp_server = create_mcp_server()
    system_prompt = build_system_prompt()

    # Built-in codebase tools the agent can use
    allowed_tools = [
        "Read",
        "Write",
        "Edit",
        "Bash",
        "Glob",
        "Grep",
    ]

    return ClaudeAgentOptions(
        cwd=str(PROJECT_ROOT),
        system_prompt=system_prompt,
        model="claude-opus-4-6",
        thinking={"type": "adaptive"},
        allowed_tools=allowed_tools,
        mcp_servers={"climate-intel": mcp_server},
        permission_mode="acceptEdits",
        max_turns=max_turns,
    )
