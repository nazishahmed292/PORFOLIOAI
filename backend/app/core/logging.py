"""Logging setup. One consistent format for the whole application."""

import logging
import sys


def setup_logging(level: str = "INFO") -> None:
    root = logging.getLogger()
    root.setLevel(level.upper())

    # Avoid duplicate handlers when the app factory is called more than once (tests).
    if not any(getattr(h, "_portfolioai", False) for h in root.handlers):
        handler = logging.StreamHandler(sys.stdout)
        handler.setFormatter(
            logging.Formatter("%(asctime)s | %(levelname)-8s | %(name)s | %(message)s")
        )
        handler._portfolioai = True  # type: ignore[attr-defined]
        root.addHandler(handler)

    # Keep noisy libraries quiet unless we're debugging.
    logging.getLogger("sqlalchemy.engine").setLevel(
        logging.INFO if level.upper() == "DEBUG" else logging.WARNING
    )
