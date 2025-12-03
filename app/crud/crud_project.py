from typing import Optional, List
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from sqlalchemy import or_
from uuid import UUID

from app.crud.base import CRUDBase
from app.models.core import Project
from app.schemas.project import ProjectCreate, ProjectUpdate

class CRUDProject(CRUDBase[Project, ProjectCreate, ProjectUpdate]):
    async def get_by_name(self, db: AsyncSession, *, name: str) -> Optional[Project]:
        """Get project by name"""
        result = await db.execute(select(Project).filter(Project.name == name))
        return result.scalars().first()
    
    async def create_with_owner(
        self, db: AsyncSession, *, obj_in: ProjectCreate, owner_id: UUID
    ) -> Project:
        """Create project with owner"""
        db_obj = Project(
            name=obj_in.name,
            description=obj_in.description,
            owner_id=owner_id
        )
        db.add(db_obj)
        await db.commit()
        await db.refresh(db_obj)
        return db_obj

    async def search(
        self, db: AsyncSession, *, query: str, skip: int = 0, limit: int = 100
    ) -> List[Project]:
        """Search projects by name or description"""
        stmt = (
            select(Project)
            .where(
                or_(
                    Project.name.ilike(f"%{query}%"),
                    Project.description.ilike(f"%{query}%")
                )
            )
            .offset(skip)
            .limit(limit)
        )
        result = await db.execute(stmt)
        return result.scalars().all()

project = CRUDProject(Project)
