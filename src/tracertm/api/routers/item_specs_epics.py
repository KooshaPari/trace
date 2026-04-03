"""Epic specification endpoints.

Provides REST endpoints for EpicSpec operations.
"""

from typing import Annotated

from fastapi import APIRouter, Body, Depends, HTTPException, Path, Query, status
from sqlalchemy.ext.asyncio import AsyncSession

from tracertm.api.deps import auth_guard, get_db
from tracertm.api.routers.item_specs_schemas import (
    EpicSpecCreate,
    EpicSpecListResponse,
    EpicSpecResponse,
    EpicSpecUpdate,
)

router = APIRouter(
    prefix="/epics",
    tags=["Epic Specifications"],
)


@router.post(
    "",
    response_model=EpicSpecResponse,
    status_code=status.HTTP_201_CREATED,
)
async def create_epic_spec(
    _project_id: Annotated[str, Path(description="Project ID")],
    data: Annotated[EpicSpecCreate | None, Body()] = None,
    _claims: dict[str, object] = Depends(auth_guard),
    _db: AsyncSession = Depends(get_db),
) -> None:
    if not data:
        raise HTTPException(status_code=400, detail="Request body required")
    try:
        raise HTTPException(status_code=501, detail="Service implementation pending")
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e)) from e
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e)) from e


@router.get(
    "/{spec_id}",
    response_model=EpicSpecResponse,
)
async def get_epic_spec(
    _project_id: Annotated[str, Path(description="Project ID")],
    _spec_id: Annotated[str, Path(description="Epic spec ID")],
    _claims: Annotated[dict[str, object], Depends(auth_guard)],
    _db: Annotated[AsyncSession, Depends(get_db)],
) -> None:
    try:
        raise HTTPException(status_code=501, detail="Service implementation pending")
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e)) from e


@router.get(
    "",
    response_model=EpicSpecListResponse,
)
async def list_epic_specs(
    _project_id: Annotated[str, Path(description="Project ID")],
    _business_value: Annotated[str | None, Query(description="Filter by business value")] = None,
    _limit: Annotated[int, Query(ge=1, le=500, description="Result limit")] = 100,
    _offset: Annotated[int, Query(ge=0, description="Result offset")] = 0,
    _claims: dict[str, object] = Depends(auth_guard),
    _db: AsyncSession = Depends(get_db),
) -> None:
    try:
        raise HTTPException(status_code=501, detail="Service implementation pending")
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e)) from e


@router.patch(
    "/{spec_id}",
    response_model=EpicSpecResponse,
)
async def update_epic_spec(
    _project_id: Annotated[str, Path(description="Project ID")],
    _spec_id: Annotated[str, Path(description="Epic spec ID")],
    data: Annotated[EpicSpecUpdate | None, Body()] = None,
    _claims: dict[str, object] = Depends(auth_guard),
    _db: AsyncSession = Depends(get_db),
) -> None:
    if not data:
        raise HTTPException(status_code=400, detail="Request body required")
    try:
        raise HTTPException(status_code=501, detail="Service implementation pending")
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e)) from e
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e)) from e


@router.delete(
    "/{spec_id}",
    status_code=status.HTTP_204_NO_CONTENT,
)
async def delete_epic_spec(
    _project_id: Annotated[str, Path(description="Project ID")],
    _spec_id: Annotated[str, Path(description="Epic spec ID")],
    _claims: Annotated[dict[str, object], Depends(auth_guard)],
    _db: Annotated[AsyncSession, Depends(get_db)],
) -> None:
    try:
        raise HTTPException(status_code=501, detail="Service implementation pending")
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e)) from e
