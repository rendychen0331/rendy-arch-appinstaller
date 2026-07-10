"""Logging setup: daily file + error view + task journal, all carrying a trace id."""
import contextvars
import glob
import itertools
import json
import logging
import os
import sys
import time
from contextlib import contextmanager
from datetime import datetime

APP_NAME = "rendy-arch-appinstaller"
PREFIX = "appinstaller"

RUN_ID = f"{datetime.now():%H%M%S}-{os.getpid()}"
_seq = itertools.count(1)
_trace = contextvars.ContextVar("trace_id", default="-")


def default_log_dir() -> str:
    """Logs sit next to the entry file when writable, else under XDG_STATE_HOME."""
    entry_dir = os.path.dirname(os.path.abspath(__file__))
    if os.access(entry_dir, os.W_OK):
        return os.path.join(entry_dir, "logs")
    state = os.environ.get("XDG_STATE_HOME") or os.path.expanduser("~/.local/state")
    return os.path.join(state, APP_NAME, "logs")


class TraceFilter(logging.Filter):
    def filter(self, record: logging.LogRecord) -> bool:
        record.trace_id = _trace.get()
        return True


class DailyFileHandler(logging.FileHandler):
    """Append-mode handler with the date in the filename; re-opens when the day changes."""

    def __init__(self, log_dir: str, prefix: str, suffix: str = ".log") -> None:
        self._dir, self._prefix, self._suffix = log_dir, prefix, suffix
        self._day = f"{datetime.now():%Y%m%d}"
        super().__init__(self._path(), mode="a", encoding="utf-8", delay=True)

    def _path(self) -> str:
        return os.path.join(self._dir, f"{self._prefix}_{self._day}{self._suffix}")

    def emit(self, record: logging.LogRecord) -> None:
        day = f"{datetime.now():%Y%m%d}"
        if day != self._day:
            self._day = day
            self.close()
            self.baseFilename = os.path.abspath(self._path())
        super().emit(record)


def _cleanup_old_logs(log_dir: str, prefix: str, keep_days: int = 30) -> None:
    cutoff = time.time() - keep_days * 86400
    for path in glob.glob(os.path.join(log_dir, f"{prefix}_*")):
        try:
            if os.path.getmtime(path) < cutoff:
                os.remove(path)
        except OSError as exc:
            logging.warning("log cleanup skipped %s: %s", path, exc)


def setup_logging(log_dir: str | None = None, log_level: int = logging.INFO) -> None:
    root = logging.getLogger()
    if root.handlers:  # idempotent: a second call must not duplicate handlers
        return
    log_dir = log_dir or default_log_dir()
    os.makedirs(log_dir, exist_ok=True)
    root.setLevel(log_level)
    fmt = logging.Formatter("%(asctime)s | %(levelname)s | %(trace_id)s | %(message)s")

    def _add(handler: logging.Handler, level: int | None = None) -> None:
        handler.setFormatter(fmt)
        handler.addFilter(TraceFilter())
        if level:
            handler.setLevel(level)
        root.addHandler(handler)

    _add(DailyFileHandler(log_dir, PREFIX))
    _add(DailyFileHandler(log_dir, PREFIX, ".err.log"), logging.WARNING)
    _add(logging.StreamHandler(sys.stdout))

    journal = logging.getLogger("task_journal")
    journal.propagate = False
    journal_handler = DailyFileHandler(log_dir, PREFIX, ".task.jsonl")
    journal_handler.setFormatter(logging.Formatter("%(message)s"))
    journal.addHandler(journal_handler)

    _cleanup_old_logs(log_dir, PREFIX)


@contextmanager
def task_scope(biz_key: str = ""):
    """Wrap one unit of work (an install / uninstall / upgrade run)."""
    task_id = f"{RUN_ID}.{next(_seq):04d}"
    token = _trace.set(task_id)
    started = time.monotonic()
    logging.info("task start | %s", biz_key)
    status, err = "ok", ""
    try:
        yield task_id
    except Exception as exc:
        status, err = "fail", f"{type(exc).__name__}: {exc}"
        logging.exception("task failed")
        raise
    finally:
        _trace.reset(token)
        logging.getLogger("task_journal").info(json.dumps({
            "time": datetime.now().isoformat(timespec="seconds"),
            "task_id": task_id,
            "biz_key": biz_key,
            "status": status,
            "duration_ms": round((time.monotonic() - started) * 1000),
            "error": err,
        }, ensure_ascii=False))
