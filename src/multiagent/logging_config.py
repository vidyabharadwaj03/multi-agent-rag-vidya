import json
import logging
import sys
import time


class StructuredFormatter(logging.Formatter):
    def format(self, record):
        payload = {
            "timestamp": self.formatTime(record, "%Y-%m-%dT%H:%M:%S"),
            "level": record.levelname,
            "event": record.getMessage(),
        }
        extra_fields = getattr(record, "fields", None)
        if extra_fields:
            payload.update(extra_fields)
        return json.dumps(payload)


def configure_logging(level=logging.INFO):
    root = logging.getLogger("multiagent")
    root.setLevel(level)
    root.handlers.clear()

    handler = logging.StreamHandler(sys.stderr)
    handler.setFormatter(StructuredFormatter())
    root.addHandler(handler)
    root.propagate = False
    return root


def get_logger(name):
    return logging.getLogger(f"multiagent.{name}")


def log_event(logger, event, level=logging.INFO, **fields):
    logger.log(level, event, extra={"fields": fields})


class Timer:
    def __enter__(self):
        self.start = time.perf_counter()
        return self

    def __exit__(self, exc_type, exc_value, traceback):
        self.elapsed_seconds = time.perf_counter() - self.start
