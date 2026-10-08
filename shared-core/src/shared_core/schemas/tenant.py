from pydantic import BaseModel, Field


class TenantContext(BaseModel):
    """Request-scoped tenant identity used by middleware and tools."""

    tenant_id: str = Field(..., min_length=1)
