from typing import Optional, List
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
import uuid

from app.crud.base import CRUDBase
from app.models.environment import Environment
from app.schemas.environment import EnvironmentCreate, EnvironmentUpdate


class CRUDEnvironment(CRUDBase[Environment, EnvironmentCreate, EnvironmentUpdate]):
    """CRUD operations for Environment"""

    async def get_by_name(
        self, db: AsyncSession, *, name: str
    ) -> Optional[Environment]:
        """Get environment by name"""
        result = await db.execute(
            select(Environment).filter(Environment.name == name)
        )
        return result.scalar_one_or_none()

    async def get_multi(
        self, db: AsyncSession, *, skip: int = 0, limit: int = 100
    ) -> List[Environment]:
        """Get multiple environments"""
        result = await db.execute(
            select(Environment).offset(skip).limit(limit).order_by(Environment.name)
        )
        return list(result.scalars().all())


environment = CRUDEnvironment(Environment)
