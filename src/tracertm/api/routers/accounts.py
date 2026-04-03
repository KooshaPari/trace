"""Accounts API endpoints for TraceRTM.

Provides:
- Account listing
- Account creation
- Account switching
"""

from typing import Annotated, Any, cast

from fastapi import APIRouter, Depends, HTTPException, Request
from pydantic import BaseModel
from sqlalchemy.ext.asyncio import AsyncSession

from tracertm.api.config.rate_limiting import enforce_rate_limit
from tracertm.api.deps import auth_guard, get_db

router = APIRouter(prefix="/api/v1/accounts", tags=["accounts"])


class AccountCreate(BaseModel):
    """Schema for creating an account."""

    name: str
    email: str
    plan: str | None = "free"


def ensure_project_access(project_id: str | None, claims: dict[str, Any] | None) -> None:
    """Check project access; system admins bypass."""
    from tracertm.api.main import ensure_project_access as _epa

    _epa(project_id, claims)


@router.get("")
async def list_accounts(
    request: Request,
    claims: Annotated[dict[str, Any], Depends(auth_guard)],
    db: Annotated[AsyncSession, Depends(get_db)],
    skip: int = 0,
    limit: int = 100,
) -> dict[str, Any]:
    """List accounts for the current user."""
    enforce_rate_limit(request, claims)

    from sqlalchemy import func, select

    from tracertm.models.account import Account

    user_id = claims.get("sub")
    if not user_id:
        raise HTTPException(status_code=401, detail="User ID not found in token")

    query = (
        select(Account)
        .where(Account.owner_id == cast("str", user_id))
        .offset(skip)
        .limit(limit)
    )
    result = await db.execute(query)
    accounts = result.scalars().all()

    count_query = (
        select(func.count())
        .select_from(Account)
        .where(Account.owner_id == cast("str", user_id))
    )
    count_result = await db.execute(count_query)
    total = count_result.scalar() or 0

    return {
        "accounts": [
            {
                "id": str(a.id),
                "name": a.name,
                "email": a.email,
                "plan": getattr(a, "plan", "free"),
                "created_at": a.created_at.isoformat() if hasattr(a, "created_at") and a.created_at else None,
            }
            for a in accounts
        ],
        "total": total,
        "skip": skip,
        "limit": limit,
    }


@router.post("")
async def create_account(
    request: Request,
    payload: AccountCreate,
    claims: Annotated[dict[str, Any], Depends(auth_guard)],
    db: Annotated[AsyncSession, Depends(get_db)],
) -> dict[str, Any]:
    """Create a new account."""
    enforce_rate_limit(request, claims)

    from tracertm.models.account import Account

    user_id = claims.get("sub")
    if not user_id:
        raise HTTPException(status_code=401, detail="User ID not found in token")

    account = Account(
        name=payload.name,
        email=payload.email,
        plan=payload.plan or "free",
        owner_id=cast("str", user_id),
    )
    db.add(account)
    await db.commit()
    await db.refresh(account)

    return {
        "id": str(account.id),
        "name": account.name,
        "email": account.email,
        "plan": account.plan,
        "created": True,
    }


@router.post("/{account_id}/switch")
async def switch_account(
    account_id: str,
    claims: Annotated[dict[str, Any], Depends(auth_guard)],
    db: Annotated[AsyncSession, Depends(get_db)],
) -> dict[str, Any]:
    """Switch to a different account."""
    from sqlalchemy import select

    from tracertm.models.account import Account

    user_id = claims.get("sub")
    if not user_id:
        raise HTTPException(status_code=401, detail="User ID not found in token")

    query = select(Account).where(
        Account.id == account_id,
        Account.owner_id == cast("str", user_id),
    )
    result = await db.execute(query)
    account = result.scalar_one_or_none()

    if not account:
        raise HTTPException(status_code=404, detail="Account not found")

    return {
        "account_id": str(account.id),
        "name": account.name,
        "switched": True,
    }
