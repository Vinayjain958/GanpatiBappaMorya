from __future__ import annotations

from typing import Annotated

from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from src.core.db import get_session
from src.repositories.category_repository import CategoryRepository
from src.schemas.category import CategoryResponse

router = APIRouter(prefix="/categories", tags=["categories"])


@router.get("", response_model=list[CategoryResponse])
async def list_categories(session: Annotated[AsyncSession, Depends(get_session)]) -> list[CategoryResponse]:
    rows = await CategoryRepository(session).list()
    return [CategoryResponse.model_validate(row) for row in rows]
