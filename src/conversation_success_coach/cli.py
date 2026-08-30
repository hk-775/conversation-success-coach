"""Command-line entry point."""

from __future__ import annotations

import argparse
import sys

from conversation_success_coach.analysis import ConversationAnalyzer
from conversation_success_coach.app import create_app
from conversation_success_coach.config import Settings
from conversation_success_coach.database import Database
from conversation_success_coach.repository import Repository
from conversation_success_coach.seed import seed_demo


def _parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="conversation-success-coach",
        description="Run the local Conversation Success Coach product.",
    )
    subparsers = parser.add_subparsers(dest="command")

    serve = subparsers.add_parser("serve", help="Run the seeded local product")
    serve.add_argument("--host", default=None)
    serve.add_argument("--port", type=int, default=None)
    serve.add_argument("--no-demo-seed", action="store_true")

    reset = subparsers.add_parser("reset-demo", help="Reset fictional demo data")
    reset.add_argument("--database", default=None)

    subparsers.add_parser("show-config", help="Print non-secret runtime configuration")
    return parser


def main(argv: list[str] | None = None) -> None:
    args = _parser().parse_args(argv)
    command = args.command or "serve"
    settings = Settings.from_env()

    if command == "serve":
        import uvicorn

        runtime = Settings(
            database_path=settings.database_path,
            host=args.host or settings.host,
            port=args.port or settings.port,
            demo_seed=not args.no_demo_seed and settings.demo_seed,
            docs_enabled=settings.docs_enabled,
            static_dir=settings.static_dir,
        )
        print(
            "\nConversation Success Coach\n"
            "  Local UI:      "
            f"http://{runtime.host}:{runtime.port}\n"
            "  Dashboard:     "
            f"http://{runtime.host}:{runtime.port}/dashboard\n"
            "  Architecture:  "
            f"http://{runtime.host}:{runtime.port}/architecture\n"
            "  API docs:      "
            f"http://{runtime.host}:{runtime.port}/docs\n"
            "  External calls: disabled\n"
            "  Message sending: not implemented\n"
        )
        uvicorn.run(
            create_app(runtime),
            host=runtime.host,
            port=runtime.port,
            access_log=False,
        )
        return

    if command == "reset-demo":
        database = Database(args.database or settings.database_path)
        try:
            repository = Repository(database)
            seed_demo(repository, ConversationAnalyzer(), reset=True)
            print("Fictional demo data reset.")
        finally:
            database.close()
        return

    if command == "show-config":
        print(
            {
                "database_path": settings.database_path,
                "host": settings.host,
                "port": settings.port,
                "demo_seed": settings.demo_seed,
                "docs_enabled": settings.docs_enabled,
                "external_credentials": False,
            }
        )
        return

    _parser().print_help()
    sys.exit(2)
