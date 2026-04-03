"""System endpoints for TraceRTM API.

Provides:
- Health checks (/health, /api/v1/health)
- Prometheus metrics (/metrics)
- Cache management (/api/v1/cache/stats, /api/v1/cache/clear)
- CSRF token (/api/v1/csrf-token)
- MCP config (/api/v1/mcp/config)
"""

from typing import Annotated, Any

from fastapi import APIRouter, Depends, Response
from pydantic import BaseModel

from tracertm.api.deps import auth_guard, get_cache_service
from tracertm.api.handlers.auth import AuthCallbackPayload
from tracertm.services.cache_service import CacheService

router = APIRouter(tags=["system"])


class WorkflowTriggerPayload(BaseModel):
    """Request payload for triggering a workflow by name."""

    workflow_name: str
    input: dict[str, Any] | None = None


@router.get("/health")
async def health_check() -> dict[str, str]:
    """Basic health check endpoint."""
    return {
        "status": "healthy",
        "version": "1.0.0",
        "service": "TraceRTM API",
    }


@router.get("/metrics")
async def metrics() -> Response:
    """Prometheus scrape endpoint for monitoring."""
    from prometheus_client import CONTENT_TYPE_LATEST, REGISTRY, generate_latest

    output = generate_latest(REGISTRY)
    return Response(
        content=output,
        media_type=CONTENT_TYPE_LATEST,
    )


@router.get("/api/v1/csrf-token")
async def get_csrf_token() -> dict[str, Any]:
    """Get CSRF token for client-side requests."""
    import secrets

    token = secrets.token_urlsafe(32)
    return {
        "token": token,
        "valid": True,
    }


@router.get("/api/v1/cache/stats")
async def cache_stats(
    cache: Annotated[CacheService, Depends(get_cache_service)],
) -> dict[str, Any]:
    """Get cache statistics for monitoring."""
    stats = await cache.get_stats()
    healthy = await cache.health_check()
    return {
        "healthy": healthy,
        "hits": stats.hits,
        "misses": stats.misses,
        "hit_rate": round(stats.hit_rate, 2),
        "total_size_bytes": stats.total_size_bytes,
        "evictions": stats.evictions,
    }


@router.post("/api/v1/cache/clear")
async def cache_clear(
    prefix: str | None = None,
    claims: dict[str, Any] = Depends(auth_guard),
    cache: CacheService = Depends(get_cache_service),
) -> dict[str, Any]:
    """Clear cache (admin only). Optionally specify a prefix to clear."""
    from tracertm.api.main import ensure_write_permission

    ensure_write_permission(claims, action="clear_cache")

    if prefix:
        deleted = await cache.clear_prefix(prefix)
        return {"cleared": True, "prefix": prefix, "keys_deleted": deleted}
    await cache.clear()
    return {"cleared": True, "all": True}


@router.get("/api/v1/mcp/config")
async def mcp_config() -> dict[str, Any]:
    """Return MCP configuration for frontend clients."""
    import os

    base_url = os.getenv("TRACERTM_MCP_BASE_URL") or os.getenv("MCP_BASE_URL") or os.getenv("FASTMCP_SERVER_BASE_URL")
    auth_mode = (os.getenv("TRACERTM_MCP_AUTH_MODE") or "oauth").lower().strip()
    return {
        "mcp_base_url": base_url,
        "auth_mode": auth_mode,
        "requires_auth": auth_mode not in {"disabled", "none", "off"},
    }


@router.post("/api/v1/auth/callback")
async def auth_callback(payload: AuthCallbackPayload):
    """Exchange authorization code for user data and tokens (B2B flow)."""
    from tracertm.api.handlers.auth import auth_callback_endpoint

    return await auth_callback_endpoint(payload)
