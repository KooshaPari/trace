"""Project management API endpoints for TraceRTM.

Provides:
- Project CRUD operations
- Project export/import
"""

from __future__ import annotations

import logging
from typing import TYPE_CHECKING, Annotated, Any, cast

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from sqlalchemy import delete
from sqlalchemy.ext.asyncio import AsyncSession

from tracertm.api.deps import auth_guard, get_cache_service, get_db
from tracertm.models.item import Item
from tracertm.models.project import Project
from tracertm.repositories import item_repository, link_repository, project_repository

if TYPE_CHECKING:
    from tracertm.services.cache_service import CacheService

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/v1/projects", tags=["projects"])


def ensure_project_access(project_id: str | None, claims: dict[str, Any] | None) -> None:
    """Check if user has access to project."""
    from tracertm.api.main import ensure_project_access as _epa

    _epa(project_id, claims)


def ensure_write_permission(claims: dict[str, Any] | None, action: str) -> None:
    """Check if user has write permission."""
    from tracertm.api.main import ensure_write_permission as _ewp

    _ewp(claims, action=action)


async def _maybe_await(result: object) -> object:
    """Await result if awaitable."""
    from tracertm.api.main import _maybe_await as _ma

    return await _ma(result)


class CreateProjectRequest(BaseModel):
    """Request model for create project endpoint."""

    name: str
    description: str | None = None
    metadata: dict[str, Any] | None = None


class UpdateProjectRequest(BaseModel):
    """Request model for update project endpoint."""

    name: str | None = None
    description: str | None = None
    metadata: dict[str, Any] | None = None


class ImportRequest(BaseModel):
    """Request model for import endpoint."""

    format: str
    data: str


async def _ensure_default_account_for_user(db: AsyncSession, user_id: str) -> str:
    """Ensure user has at least one account (for RLS). Create default personal account if none. Returns account id."""
    import hashlib

    from tracertm.models.account_user import AccountRole
    from tracertm.repositories.account_repository import AccountRepository

    account_repo = AccountRepository(db)
    accounts = await account_repo.list_by_user(user_id)
    if accounts:
        return accounts[0].id
    slug = "personal-" + hashlib.md5(user_id.encode(), usedforsecurity=False).hexdigest()[:12]
    account = await account_repo.create(
        name="My Workspace",
        slug=slug,
        account_type="personal",
    )
    await account_repo.add_user(account.id, user_id, AccountRole.OWNER)
    await db.commit()
    return account.id


@router.get("")
async def list_projects(
    skip: int = 0,
    limit: int = 100,
    claims: Annotated[dict[str, Any], Depends(auth_guard)] = Depends(auth_guard),
    db: Annotated[AsyncSession, Depends(get_db)] = Depends(get_db),
    cache: Annotated[CacheService, Depends(get_cache_service)] = Depends(get_cache_service),
) -> dict[str, Any]:
    """List all projects (cached for 10 minutes)."""
    from tracertm.repositories.project_repository import ProjectRepository

    user_id = claims.get("sub") if isinstance(claims, dict) else None
    if user_id and isinstance(user_id, str):
        await _ensure_default_account_for_user(db, user_id)

    cache_key = cache._generate_key("projects", user_id=user_id or "", skip=skip, limit=limit)

    cached = await cache.get(cache_key)
    if cached is not None:
        return cached

    repo = ProjectRepository(db)
    projects = await repo.get_all()

    result = {
        "total": len(projects),
        "projects": [
            {
                "id": str(project.id),
                "name": project.name,
                "description": (
                    project.metadata.get("description") if isinstance(project.metadata, dict) else None
                )
                if hasattr(project, "metadata") and project.metadata
                else None,
                "metadata": project.metadata if hasattr(project, "metadata") else {},
                "created_at": project.created_at.isoformat()
                if hasattr(project, "created_at") and project.created_at
                else None,
            }
            for project in projects[skip : skip + limit]
        ],
    }

    await cache.set(cache_key, result, cache_type="projects")

    return result


@router.get("/{project_id}")
async def get_project(
    project_id: str,
    claims: Annotated[dict[str, Any], Depends(auth_guard)] = Depends(auth_guard),
    db: Annotated[AsyncSession, Depends(get_db)] = Depends(get_db),
    cache: Annotated[CacheService, Depends(get_cache_service)] = Depends(get_cache_service),
) -> dict[str, Any]:
    """Get a specific project (cached for 5 minutes)."""
    ensure_project_access(project_id, claims)

    cache_key = cache._generate_key("project", project_id=project_id)

    cached = await cache.get(cache_key)
    if cached is not None:
        return cached

    from tracertm.repositories.project_repository import ProjectRepository

    repo = ProjectRepository(db)
    project = await repo.get_by_id(project_id)

    if not project:
        raise HTTPException(status_code=404, detail="Project not found")

    project_metadata = getattr(project, "project_metadata", None) or getattr(project, "metadata", None) or {}
    description = getattr(project, "description", None)
    if not description and isinstance(project_metadata, dict):
        description = project_metadata.get("description")

    result = {
        "id": str(project.id),
        "name": project.name,
        "description": description,
        "metadata": project_metadata,
        "created_at": project.created_at.isoformat() if hasattr(project, "created_at") and project.created_at else None,
        "updated_at": project.updated_at.isoformat() if hasattr(project, "updated_at") and project.updated_at else None,
    }

    await cache.set(cache_key, result, cache_type="project")

    return result


@router.post("")
async def create_project(
    request: CreateProjectRequest,
    claims: Annotated[dict[str, Any], Depends(auth_guard)] = Depends(auth_guard),
    db: Annotated[AsyncSession, Depends(get_db)] = Depends(get_db),
    cache: Annotated[CacheService, Depends(get_cache_service)] = Depends(get_cache_service),
) -> dict[str, Any]:
    """Create a new project."""
    ensure_write_permission(claims, action="create_project")
    from tracertm.repositories.project_repository import ProjectRepository

    user_id = claims.get("sub") if isinstance(claims, dict) else None
    account_id = None
    if user_id and isinstance(user_id, str):
        account_id = await _ensure_default_account_for_user(db, user_id)

    repo = ProjectRepository(db)
    try:
        project = await repo.create(
            name=request.name,
            description=request.description,
            metadata=request.metadata,
            account_id=account_id,
        )
        await db.commit()

        await cache.clear_prefix("projects")

        return {
            "id": str(project.id),
            "name": project.name,
            "description": project.description,
            "metadata": project.metadata,
        }
    except Exception as exc:
        await db.rollback()
        logger.exception("Error creating project")
        raise HTTPException(status_code=500, detail=str(exc)) from exc


@router.put("/{project_id}")
async def update_project(
    project_id: str,
    request: UpdateProjectRequest,
    claims: Annotated[dict[str, Any], Depends(auth_guard)] = Depends(auth_guard),
    db: Annotated[AsyncSession, Depends(get_db)] = Depends(get_db),
) -> dict[str, Any]:
    """Update a project."""
    ensure_project_access(project_id, claims)
    ensure_write_permission(claims, action="update_project")
    from tracertm.repositories.project_repository import ProjectRepository

    repo = ProjectRepository(db)
    project = await repo.update(
        project_id=project_id,
        name=request.name,
        description=request.description,
        metadata=request.metadata,
    )

    if not project:
        raise HTTPException(status_code=404, detail="Project not found")

    return {
        "id": str(project.id),
        "name": project.name,
        "description": project.description,
        "metadata": project.metadata,
    }


@router.delete("/{project_id}")
async def delete_project(
    project_id: str,
    claims: Annotated[dict[str, Any], Depends(auth_guard)] = Depends(auth_guard),
    db: Annotated[AsyncSession, Depends(get_db)] = Depends(get_db),
) -> dict[str, Any]:
    """Delete a project."""
    ensure_project_access(project_id, claims)
    ensure_write_permission(claims, action="delete_project")

    repo = project_repository.ProjectRepository(db)
    project = await _maybe_await(repo.get_by_id(project_id))

    if not project:
        raise HTTPException(status_code=404, detail="Project not found")

    link_repo = link_repository.LinkRepository(db)
    item_repo = item_repository.ItemRepository(db)

    links_result = await _maybe_await(link_repo.get_by_project(project_id))
    links = cast("list[Any]", links_result)
    await _maybe_await(item_repo.list_all(project_id))

    for link in links:
        await _maybe_await(link_repo.delete(str(link.id)))

    await _maybe_await(db.execute(delete(Item).where(Item.project_id == project_id)))
    await _maybe_await(db.execute(delete(Project).where(Project.id == project_id)))
    await _maybe_await(db.commit())

    return {"success": True, "message": "Project deleted successfully"}


@router.get("/{project_id}/export")
async def export_project(
    project_id: str,
    format: str = "json",
    claims: Annotated[dict[str, Any], Depends(auth_guard)] = Depends(auth_guard),
    db: Annotated[AsyncSession, Depends(get_db)] = Depends(get_db),
) -> dict[str, Any]:
    """Export project data to various formats. Use format=full for canonical JSON (project+items+links)."""
    ensure_project_access(project_id, claims)

    if format == "full":
        from tracertm.services.export_service import ExportService

        export_service = ExportService(db)
        json_str = await export_service.export_to_json(project_id)
        import json

        return json.loads(json_str)
    from tracertm.services.export_import_service import ExportImportService

    service = ExportImportService(db)
    result: dict[str, Any]
    if format == "json":
        result = await service.export_to_json(project_id)
    elif format == "csv":
        result = await service.export_to_csv(project_id)
    elif format == "markdown":
        result = await service.export_to_markdown(project_id)
    else:
        raise HTTPException(
            status_code=400,
            detail=f"Unsupported format: {format}. Supported formats: json, csv, markdown, full",
        )
    if "error" in result:
        raise HTTPException(status_code=404, detail=result["error"])
    return result


@router.post("/{project_id}/import")
async def import_project(
    project_id: str,
    request: ImportRequest,
    claims: Annotated[dict[str, Any], Depends(auth_guard)] = Depends(auth_guard),
    db: Annotated[AsyncSession, Depends(get_db)] = Depends(get_db),
) -> dict[str, Any]:
    """Import project data into an existing project (items only for json/csv)."""
    ensure_project_access(project_id, claims)
    ensure_write_permission(claims, action="import_project")
    from tracertm.services.export_import_service import ExportImportService

    service = ExportImportService(db)
    if request.format == "json":
        result = await service.import_from_json(project_id, request.data)
    elif request.format == "csv":
        result = await service.import_from_csv(project_id, request.data)
    else:
        raise HTTPException(
            status_code=400,
            detail=f"Unsupported format: {request.format}. Supported formats: json, csv",
        )

    if "error" in result:
        raise HTTPException(status_code=400, detail=result["error"])

    return result


@router.post("")
async def import_full_project(
    body: dict[str, Any],
    claims: Annotated[dict[str, Any], Depends(auth_guard)] = Depends(auth_guard),
    db: Annotated[AsyncSession, Depends(get_db)] = Depends(get_db),
) -> dict[str, Any]:
    """Import a full project from canonical JSON (project + items + links). Creates new project and resolves item ids for links."""
    ensure_write_permission(claims, action="import_project")
    import json

    from tracertm.services.import_service import ImportService

    service = ImportService(db)
    try:
        json_str = json.dumps(body) if isinstance(body, dict) else body
    except TypeError:
        raise HTTPException(status_code=400, detail="Request body must be JSON object (canonical format)")
    result = await service.import_from_json(json_str)
    await db.commit()
    return result
