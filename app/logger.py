import json
import logging
import os
from datetime import datetime, timezone
from pathlib import Path


LOG_DIR = Path("logs")
LOG_FILE = LOG_DIR / "chat.jsonl"

LOG_DIR.mkdir(parents=True, exist_ok=True)


logger = logging.getLogger("local_slm")

logger.setLevel(logging.INFO)

if not logger.handlers:

    handler = logging.FileHandler(
        LOG_FILE,
        encoding="utf-8"
    )

    handler.setFormatter(
        logging.Formatter("%(message)s")
    )

    logger.addHandler(handler)


def log_event(event: dict) -> None:

    event = {
        "timestamp": datetime.now(
            timezone.utc
        ).isoformat(),
        **event
    }

    logger.info(
        json.dumps(
            event,
            ensure_ascii=False
        )
    )


def get_logs(limit: int = 100) -> list[dict]:

    if not LOG_FILE.exists():
        return []

    lines = LOG_FILE.read_text(
        encoding="utf-8"
    ).splitlines()

    lines = lines[-limit:]

    logs = []

    for line in lines:

        try:
            logs.append(
                json.loads(line)
            )

        except json.JSONDecodeError:
            continue

    return logs