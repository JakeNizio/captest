from pathlib import Path
from typing import BinaryIO

from shared_core.interfaces.storage import StorageService


class LocalStorageProvider(StorageService):
    """Phase 1 filesystem storage under LOCAL_STORAGE_PATH/{tenant_id}/..."""

    def __init__(
        self, root_path: str, public_base_url: str = "http://localhost:8080"
    ) -> None:
        self.root_path = Path(root_path)
        self.public_base_url = public_base_url.rstrip("/")

    def _tenant_path(self, tenant_id: str, path: str) -> Path:
        safe_path = Path(path)
        if safe_path.is_absolute() or ".." in safe_path.parts:
            raise ValueError("path must be a relative path without '..'")
        return self.root_path / tenant_id / safe_path

    async def upload_file(self, file_obj: BinaryIO, path: str, tenant_id: str) -> str:
        destination = self._tenant_path(tenant_id, path)
        destination.parent.mkdir(parents=True, exist_ok=True)
        data = file_obj.read()
        destination.write_bytes(data)
        return f"file://{destination.resolve()}"

    async def get_presigned_url(
        self, path: str, tenant_id: str, expires_in: int = 3600
    ) -> str:
        _ = expires_in  # local URLs do not expire
        destination = self._tenant_path(tenant_id, path)
        if not destination.exists():
            raise FileNotFoundError(f"object not found: {tenant_id}/{path}")
        return f"{self.public_base_url}/storage/{tenant_id}/{path}"
