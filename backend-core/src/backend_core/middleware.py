from collections.abc import Callable

from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request
from starlette.responses import Response

from shared_core.schemas.tenant import TenantContext


class TenantMiddleware(BaseHTTPMiddleware):
    """Phase 1: attach tenant from TENANT_ID env. Phase 2: JWT/headers."""

    def __init__(self, app, tenant_id: str) -> None:
        super().__init__(app)
        self.tenant_id = tenant_id

    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        request.state.tenant = TenantContext(tenant_id=self.tenant_id)
        return await call_next(request)
