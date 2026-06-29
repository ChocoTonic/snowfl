"""Backwards-compatible re-export.

The canonical exception definitions now live in :mod:`snowfl.core` so they can be
inlined into the single-file qBittorrent plugin. Importing them from here (or from
``snowfl``) continues to work unchanged.
"""

from ..core import ApiError, FetchError

__all__ = ["ApiError", "FetchError"]
