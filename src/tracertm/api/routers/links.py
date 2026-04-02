"""Links management API endpoints for TraceRTM.

Provides:
- Link listing with filtering and pagination
- Grouped links by item
- Link CRUD operations
"""

from typing import TYPE_CHECKING, Any

from fastapi import APIRouter, Depends, HTTPException, Request
from sqlalchemy import or_, select
from sqlalchemy.ext.asyncio import AsyncSession

from tracertm.api.config.rate_limiting import enforce_rate_limit
from tracertm.api.deps import auth_guard, get_cache_service, get_db
from tracertm.api.handlers.links import (
    LinkQueryParams,
    build_links_response,
    detect_link_columns,
    execute_links_query,
    parse_exclude_types,
    try_get_links_from_cache,
)
from tracertm.models.item import Item

if TYPE_CHECKING:
    from tracertm.services.cache_service import CacheService

router = APIRouter(prefix="/api/v1/links", tags=["links"])


def ensure_project_access(project_id: str | None, claims: dict[str, Any] | None) -> None:
    """Check project access; system admins bypass."""
    from tracertm.api.main import ensure_project_access as _epa

    _epa(project_id, claims)


@router.get("")
async def list_links(
    request: Request,
    project_id: str | None = None,
    source_id: str | None = None,
    target_id: str | None = None,
    skip: int = 0,
    limit: int = 100,
    exclude_types: str | None = None,
    claims: dict[str, Any] = Depends(auth_guard),
    db: AsyncSession = Depends(get_db),
    cache: "CacheService" = Depends(get_cache_service),
) -> dict[str, Any]:
    """List links, optionally filtered by project, source, or target."""
    if not (request and request.headers.get("X-Bulk-Operation") == "true"):
        enforce_rate_limit(request, claims)

    if project_id:
        ensure_project_access(project_id, claims)

    exclude_types_list = parse_exclude_types(exclude_types)

    params = LinkQueryParams(
        project_id=project_id,
        source_id=source_id,
        target_id=target_id,
        exclude_types=exclude_types_list,
        skip=skip,
        limit=limit,
    )
    cache_key, cached = await try_get_links_from_cache(cache, params)
    if cached is not None:
        return cached

    columns = await detect_link_columns(db)
    total_count, links_result = await execute_links_query(db, params, columns)
    result = build_links_response(links_result, total_count, project_id)

    if cache_key:
        await cache.set(cache_key, result, cache_type="links")

    return result


@router.get("/grouped")
async def list_links_grouped(
    request: Request,
    project_id: str,
    item_id: str,
    claims: dict[str, Any] = Depends(auth_guard),
    db: AsyncSession = Depends(get_db),
) -> dict[str, Any]:
    """Show links for an item grouped as incoming/outgoing."""
    enforce_rate_limit(request, claims)
    ensure_project_access(project_id, claims)

    resolved = await db.execute(
        select(Item.id)
        .where(
            Item.project_id == project_id,
            Item.deleted_at.is_(None),
            or_(Item.id == item_id, Item.external_id.ilike(f"{item_id}%")),
        )
        .limit(1),
    )
    resolved_id = resolved.scalar_one_or_none()
    if not resolved_id:
        raise HTTPException(status_code=404, detail="Item not found")

    item_row = (await db.execute(select(Item).where(Item.id == resolved_id))).scalar_one_or_none()
    if not item_row:
        raise HTTPException(status_code=404, detail="Item not found")

    from tracertm.repositories import link_repository

    repo = link_repository.LinkRepository(db)
    incoming = await repo.get_links_for_target(resolved_id)
    outgoing = await repo.get_links_for_source(resolved_id)

    return {
        "item_id": str(resolved_id),
        "incoming": [_serialize_link(l) for l in incoming],
        "outgoing": [_serialize_link(l) for l in outgoing],
    }


@router.post("")
async def create_link(
    request: Request,
    project_id: str,
    source_id: str,
    target_id: str,
    link_type: str,
    claims: dict[str, Any] = Depends(auth_guard),
    db: AsyncSession = Depends(get_db),
) -> dict[str, Any]:
    """Create a new link between items."""
    enforce_rate_limit(request, claims)
    ensure_project_access(project_id, claims)

    from tracertm.repositories import link_repository

    repo = link_repository.LinkRepository(db)
    link = await repo.create(
        project_id=project_id,
        source_id=source_id,
        target_id=target_id,
        link_type=link_type.upper(),
    )
    await db.commit()
    return {"id": str(link.id), "created": True}


@router.put("/{link_id}")
async def update_link(
    link_id: str,
    request: Request,
    link_type: str | None = None,
    claims: dict[str, Any] = Depends(auth_guard),
    db: AsyncSession = Depends(get_db),
) -> dict[str, Any]:
    """Update an existing link."""
    enforce_rate_limit(request, claims)

    from tracertm.repositories import link_repository

    repo = link_repository.LinkRepository(db)
    link = await repo.get_by_id(link_id)
    if not link:
        raise HTTPException(status_code=404, detail="Link not found")

    ensure_project_access(str(getattr(link, "project_id", "")), claims)

    if link_type:
        link.link_type = link_type.upper()
    await db.commit()
    return {"id": link_id, "updated": True}


@router.delete("/{link_id}")
async def delete_link(
    link_id: str,
    request: Request,
    claims: dict[str, Any] = Depends(auth_guard),
    db: AsyncSession = Depends(get_db),
) -> dict[str, Any]:
    """Delete a link."""
    enforce_rate_limit(request, claims)

    from tracertm.repositories import link_repository

    repo = link_repository.LinkRepository(db)
    link = await repo.get_by_id(link_id)
    if not link:
        raise HTTPException(status_code=404, detail="Link not found")

    ensure_project_access(str(getattr(link, "project_id", "")), claims)
    deleted = await repo.delete(link_id)
    await db.commit()
    return {"deleted": bool(deleted), "id": link_id}


def _serialize_link(link: object) -> dict[str, Any]:
    """Serialize a link object for response."""
    return {
        "id": str(getattr(link, "id", "")),
        "source_id": str(getattr(link, "source_id", "")),
        "target_id": str(getattr(link, "target_id", "")),
        "link_type": getattr(link, "link_type", ""),
        "project_id": str(getattr(link, "project_id", "") or ""),
    }
