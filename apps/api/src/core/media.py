"""DI provider for the media storage adapter, mirroring the
`get_embedding_adapter`/`get_routing_adapter` pattern used elsewhere for
swappable adapters (src/core/embedding.py, src/core/location.py)."""

from __future__ import annotations

from functools import lru_cache

from src.adapters.media_storage import LocalFilesystemMediaStorage, MediaStorageAdapter
from src.core.config import Settings, get_settings


@lru_cache
def _build_adapter(
    upload_dir: str, public_base_url: str, api_public_base_url: str
) -> LocalFilesystemMediaStorage:
    return LocalFilesystemMediaStorage(upload_dir, public_base_url, api_public_base_url)


def get_media_storage_adapter() -> MediaStorageAdapter:
    settings: Settings = get_settings()
    return _build_adapter(
        settings.media_upload_dir, settings.media_public_base_url, settings.api_public_base_url
    )


__all__ = ["get_media_storage_adapter"]
