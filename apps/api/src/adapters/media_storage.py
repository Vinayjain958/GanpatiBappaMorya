"""Media storage abstraction for traveler-uploaded experience photos.

No object-storage/upload infrastructure existed anywhere in this codebase
before this feature (spec §12) — `LocalFilesystemMediaStorage` is a
dev-grade adapter behind the `MediaStorageAdapter` Protocol so a future
production backend (e.g. Supabase Storage — `supabase_url`/keys already
exist unused in `core/config.py`) can be swapped in later without
touching the service layer that calls it. Never store image bytes as a
Base64 blob on the Experience row (spec §12) — the adapter always
returns a servable URL + the object key that produced it.
"""

from __future__ import annotations

import re
from pathlib import Path
from typing import Protocol


class MediaStorageAdapter(Protocol):
    def save(self, data: bytes, key: str, content_type: str) -> str:
        """Persist `data` under `key` and return a URL the frontend can load."""
        ...

    def delete(self, key: str) -> None:
        """Best-effort removal of a previously saved object.

        Called only as cleanup after a failed publish (spec §27) — never
        required to succeed for correctness, since the DB transaction is
        the source of truth for whether the object is actually referenced.
        """
        ...


_SAFE_KEY_RE = re.compile(r"^[a-zA-Z0-9/_.-]+$")


class LocalFilesystemMediaStorage:
    """Writes uploaded images to a local directory, served via StaticFiles.

    `key` is always a server-generated path (see
    `services/media_validation.py`), never derived from a user-supplied
    filename — this rules out path traversal by construction, but the
    class still refuses any key that isn't a clean relative path as
    defense in depth.
    """

    def __init__(self, root_dir: str, public_base_url: str, api_public_base_url: str = "") -> None:
        self._root = Path(root_dir)
        self._root.mkdir(parents=True, exist_ok=True)
        self._public_base_url = public_base_url.rstrip("/")
        # Prepended so the returned URL is absolute (e.g.
        # "http://localhost:8000/media/experiences/<key>.jpg") rather than
        # host-relative — a relative URL resolves against whatever origin
        # renders it, which is wrong whenever the API isn't served from
        # the same origin as the frontend (true in local dev by default).
        self._api_public_base_url = api_public_base_url.rstrip("/")

    def _resolve(self, key: str) -> Path:
        if not _SAFE_KEY_RE.match(key) or ".." in key.split("/"):
            raise ValueError(f"Refusing unsafe media storage key: {key!r}")
        path = (self._root / key).resolve()
        if self._root.resolve() not in path.parents and path != self._root.resolve():
            raise ValueError(f"Refusing media storage key outside root: {key!r}")
        return path

    def save(self, data: bytes, key: str, content_type: str) -> str:
        path = self._resolve(key)
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_bytes(data)
        return f"{self._api_public_base_url}{self._public_base_url}/{key}"

    def delete(self, key: str) -> None:
        try:
            path = self._resolve(key)
        except ValueError:
            return
        path.unlink(missing_ok=True)
