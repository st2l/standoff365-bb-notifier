"""Command-line entry point for the watcher."""

from __future__ import annotations

import argparse
import logging
import sys
from pathlib import Path

from s365watch.client import Standoff365Client
from s365watch.config import Config, ConfigError
from s365watch.monitor import Monitor, run_loop
from s365watch.state import StateStore
from s365watch.telegram import TelegramNotifier

logger = logging.getLogger("s365watch")


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="s365watch",
        description="Notify a Telegram chat when new Standoff 365 bug bounty "
        "programs are published.",
    )
    parser.add_argument(
        "--once",
        action="store_true",
        help="Run a single poll cycle and exit (for cron). Default: loop.",
    )
    parser.add_argument(
        "--log-level",
        default="INFO",
        choices=["DEBUG", "INFO", "WARNING", "ERROR"],
        help="Logging verbosity (default: INFO).",
    )
    return parser


def main(argv: list[str] | None = None) -> int:
    """Parse arguments, build dependencies, and run the watcher.

    Returns:
        Process exit code (0 on success, 1 on configuration error).
    """
    args = build_parser().parse_args(argv)
    logging.basicConfig(
        level=args.log_level,
        format="%(asctime)s %(levelname)s %(name)s: %(message)s",
    )

    try:
        config = Config.from_env()
    except ConfigError as exc:
        logger.error("configuration error: %s", exc)
        return 1

    store = StateStore(Path(config.state_path))
    store.load()

    with (
        Standoff365Client.create(timeout=config.request_timeout) as client,
        TelegramNotifier.create(
            config.bot_token,
            config.chat_id,
            timeout=config.request_timeout,
            proxy=config.telegram_proxy,
        ) as notifier,
    ):
        monitor = Monitor(
            client,
            notifier,
            store,
            notify_first_run=config.notify_existing_on_first_run,
        )
        if args.once:
            monitor.run_once()
        else:
            run_loop(monitor, config.poll_interval)
    return 0


if __name__ == "__main__":
    sys.exit(main())
