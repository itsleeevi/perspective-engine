"""
Checkpointer factory for the pipeline graph.

Phase 1 offers two options:
- MemorySaver  — used in tests; state is lost when the process exits.
- SqliteSaver  — used for interactive demos; state persists across processes.

Phase 3+ will replace SqliteSaver with the Neon/Postgres checkpointer.
The graph build function accepts the checkpointer as a parameter so call
sites (tests, CLI, API) can inject the appropriate one without touching
graph internals.
"""

from __future__ import annotations

from pathlib import Path

from langgraph.checkpoint.memory import MemorySaver
from langgraph.checkpoint.sqlite.aio import AsyncSqliteSaver


def make_memory_checkpointer() -> MemorySaver:
    """Return an in-memory checkpointer (no persistence across processes)."""
    return MemorySaver()


async def make_sqlite_checkpointer(db_path: str = "pipeline.sqlite") -> AsyncSqliteSaver:
    """
    Return an async SQLite checkpointer backed by ``db_path``.

    The file is created if it does not exist.  Relative paths are resolved
    relative to the current working directory.
    """
    path = Path(db_path)
    path.parent.mkdir(parents=True, exist_ok=True)
    return AsyncSqliteSaver.from_conn_string(str(path))
