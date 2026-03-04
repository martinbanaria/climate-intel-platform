"""
CLI entry point for the Climate Intel Dev Agent.

Usage:
    # Single query
    python -m agent "Check data freshness across all collections"

    # Interactive REPL
    python -m agent --repl
"""

import argparse
import asyncio
import sys
from pathlib import Path

import anyio

sys.path.insert(0, str(Path(__file__).parent.parent))


async def run_query(prompt: str, max_turns: int = 50) -> None:
    from claude_agent_sdk import ClaudeSDKClient, AssistantMessage, TextBlock, ResultMessage

    from agent.client import build_options

    options = build_options(max_turns=max_turns)
    async with ClaudeSDKClient(options=options) as client:
        await client.query(prompt)
        async for message in client.receive_response():
            if isinstance(message, AssistantMessage):
                for block in message.content:
                    if isinstance(block, TextBlock):
                        print(block.text, end="", flush=True)
            elif isinstance(message, ResultMessage):
                # Final result — print a trailing newline if needed
                if message.result:
                    print()


async def repl(max_turns: int = 50) -> None:
    from claude_agent_sdk import ClaudeSDKClient, AssistantMessage, TextBlock, ResultMessage, SystemMessage

    from agent.client import build_options

    print("Climate Intel Dev Agent — REPL mode")
    print("Type your query and press Enter. Ctrl-C or 'exit' to quit.\n")

    options = build_options(max_turns=max_turns)
    session_id = None

    while True:
        try:
            prompt = input("agent> ").strip()
        except (EOFError, KeyboardInterrupt):
            print("\nGoodbye.")
            break

        if not prompt:
            continue
        if prompt.lower() in ("exit", "quit", "q"):
            print("Goodbye.")
            break

        try:
            async with ClaudeSDKClient(options=options) as client:
                await client.query(prompt)
                async for message in client.receive_response():
                    if isinstance(message, SystemMessage) and message.subtype == "init":
                        session_id = message.session_id
                    elif isinstance(message, AssistantMessage):
                        for block in message.content:
                            if isinstance(block, TextBlock):
                                print(block.text, end="", flush=True)
                    elif isinstance(message, ResultMessage):
                        if message.result:
                            print()
            print()  # blank line between turns
        except KeyboardInterrupt:
            print("\n[Interrupted]")
        except Exception as e:
            print(f"\n[Error] {e}")


def main() -> None:
    parser = argparse.ArgumentParser(
        prog="agent",
        description="Climate Intel Dev Agent — Claude Agent SDK powered assistant",
    )
    parser.add_argument(
        "query",
        nargs="?",
        help="Single query to run (omit for --repl mode)",
    )
    parser.add_argument(
        "--repl",
        action="store_true",
        help="Start interactive REPL session",
    )
    parser.add_argument(
        "--max-turns",
        type=int,
        default=50,
        help="Maximum agent turns per query (default: 50)",
    )

    args = parser.parse_args()

    if args.repl or not args.query:
        anyio.run(repl, args.max_turns)
    else:
        anyio.run(run_query, args.query, args.max_turns)


if __name__ == "__main__":
    main()
