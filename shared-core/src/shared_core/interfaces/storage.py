from abc import ABC, abstractmethod
from typing import BinaryIO


class StorageService(ABC):
    """Object storage abstraction. Feature code MUST use this, not FS/S3 SDKs."""

    @abstractmethod
    async def upload_file(self, file_obj: BinaryIO, path: str, tenant_id: str) -> str:
        """Upload file; return absolute URI / identifier."""

    @abstractmethod
    async def get_presigned_url(
        self, path: str, tenant_id: str, expires_in: int = 3600
    ) -> str:
        """Direct client read/write URL (local URL or S3 presign)."""
