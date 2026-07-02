"""
Local-filesystem asset store for Phase 1.

Nodes store asset URLs (not binaries) in state.  In Phase 1, assets are
written to a local directory and referenced via file:// URLs.

Phase 3+ will replace this with Cloudflare R2 behind the same interface:
swap the body of ``save_asset`` and ``local_asset_url`` without changing
any call sites.
"""

from __future__ import annotations

import os
from pathlib import Path

from graph.config import LOCAL_ASSETS_DIR


def _assets_root() -> Path:
    """Return the absolute path to the local assets directory, creating it if needed."""
    root = Path(os.environ.get("ASSETS_DIR", LOCAL_ASSETS_DIR))
    if not root.is_absolute():
        # Resolve relative to the project root (two levels up from this file).
        root = Path(__file__).parent.parent / root
    root.mkdir(parents=True, exist_ok=True)
    return root


def local_asset_url(relative_path: str) -> str:
    """
    Return a ``file://`` URL for the given relative asset path.

    The file is not created; this just computes the canonical URL that would
    be stored in state.  Use ``save_asset`` to actually write bytes.
    """
    full_path = _assets_root() / relative_path
    full_path.parent.mkdir(parents=True, exist_ok=True)
    return full_path.as_uri()


def save_asset(relative_path: str, content: bytes) -> str:
    """
    Write ``content`` to the local asset store and return the file:// URL.

    Phase 3+ will replace this with an R2 upload returning an https:// URL.
    """
    full_path = _assets_root() / relative_path
    full_path.parent.mkdir(parents=True, exist_ok=True)
    full_path.write_bytes(content)
    return full_path.as_uri()
