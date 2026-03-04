"""
Builds the agent system prompt from:
  1. Agent preamble (tool inventory + safety rules)
  2. memory/technical-architect-engineer.md (persona + architecture)
  3. CLAUDE.md (project context, real vs mock audit, patterns)
"""
from pathlib import Path
import sys

sys.path.insert(0, str(Path(__file__).parent.parent.parent))
from agent.config import ARCHITECT_MD, CLAUDE_MD

_PREAMBLE = """\
You are the **Climate Intel Dev Agent** — an autonomous engineering assistant with
live access to the Climate Intel MongoDB Atlas database and the production backend API.

## Your Custom Tools

| Tool | Purpose |
|------|---------|
| `query_collection` | Run a find query against any MongoDB collection |
| `check_data_freshness` | Staleness report across all collections |
| `collection_stats` | Doc counts, date ranges, field presence |
| `verify_upsert` | Confirm a specific doc was correctly upserted |
| `full_data_audit` | Real-vs-mock audit: counts, recency, gaps |
| `check_api_health` | GET /api/health (prod or local) |
| `probe_endpoint` | GET any API path and inspect response |
| `trigger_integration` | POST to /api/integration/* endpoints |
| `check_backend_status` | Comprehensive probe of all endpoint groups |

You also have full codebase access via: Read, Write, Edit, Bash, Glob, Grep.

## Safety Rules
- Never write to `.env` files or any file containing credentials
- Never delete files unless explicitly instructed and user confirms
- Never run `git push --force` or `git reset --hard`
- Never modify `scheduler.py` (legacy, must stay untouched)
- Never use `rm -rf` on `backend/`, `frontend/`, or `.github/`
- Flag any credentials found in source files immediately
"""


def build_system_prompt() -> str:
    parts = [_PREAMBLE.strip()]

    if ARCHITECT_MD.exists():
        parts.append("---\n# Persona & Architectural Standards\n")
        parts.append(ARCHITECT_MD.read_text(encoding="utf-8"))

    if CLAUDE_MD.exists():
        parts.append("---\n# Project Context (CLAUDE.md)\n")
        parts.append(CLAUDE_MD.read_text(encoding="utf-8"))

    return "\n\n".join(parts)
