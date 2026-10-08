from io import BytesIO

import pytest

from shared_core.providers.local_storage import LocalStorageProvider


@pytest.mark.asyncio
async def test_upload_uses_tenant_prefix(tmp_path):
    storage = LocalStorageProvider(root_path=str(tmp_path))
    uri = await storage.upload_file(
        BytesIO(b"hello"),
        path="docs/a.txt",
        tenant_id="default_tenant",
    )
    assert (tmp_path / "default_tenant" / "docs" / "a.txt").read_bytes() == b"hello"
    assert "default_tenant" in uri
