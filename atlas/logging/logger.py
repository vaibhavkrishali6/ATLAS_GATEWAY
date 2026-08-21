"""JSON file logging for Atlas application events."""

import json
import logging
from datetime import datetime, timezone
from logging.handlers import RotatingFileHandler
from pathlib import Path

LOG_FILE = Path(__file__).resolve().parents[2] / "logs" / "atlas.log"
MAX_LOG_BYTES = 10 * 1024 * 1024
BACKUP_COUNT = 5
_HANDLER_NAME = "atlas_json_file"


class JsonFormatter(logging.Formatter):
    """Render selected, non-sensitive Atlas request fields as JSON."""

    def format(self, record: logging.LogRecord) -> str:
        payload = {
            "timestamp": datetime.now(timezone.utc)
            .isoformat(timespec="milliseconds")
            .replace("+00:00", "Z"),
            "level": record.levelname,
            "logger": record.name,
            "event": getattr(record, "event", record.getMessage()),
        }
        for field in (
            "request_id",
            "method",
            "path",
            "service",
            "status_code",
            "duration_ms",
        ):
            value = getattr(record, field, None)
            if value is not None:
                payload[field] = value
        return json.dumps(payload, separators=(",", ":"))


def get_logger() -> logging.Logger:
    """Return the Atlas JSON logger without adding duplicate file handlers."""
    logger = logging.getLogger("atlas")
    logger.setLevel(logging.INFO)
    logger.propagate = False

    if not any(handler.name == _HANDLER_NAME for handler in logger.handlers):
        LOG_FILE.parent.mkdir(parents=True, exist_ok=True)
        
        handler = RotatingFileHandler(
            LOG_FILE,
            maxBytes=MAX_LOG_BYTES,
            backupCount=BACKUP_COUNT,
            encoding="utf-8",
        )
        handler.name = _HANDLER_NAME
        handler.setFormatter(JsonFormatter())
        logger.addHandler(handler)
    return logger


def log_gateway_request(
    *,
    event: str,
    level: int,
    request_id: str,
    method: str,
    path: str,
    service: str | None,
    status_code: int,
    duration_ms: int,) -> None:
    """Write one structured request event without inspecting request headers/body."""
    get_logger().log(
        level,
        event,
        extra={
            "event": event,
            "request_id": request_id,
            "method": method,
            "path": path,
            "service": service,
            "status_code": status_code,
            "duration_ms": duration_ms,
        },
    )
