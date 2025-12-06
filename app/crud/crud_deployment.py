from typing import Optional, List
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from sqlalchemy.orm import selectinload
import uuid

from app.crud.base import CRUDBase
from app.models.core import Deployment
from app.schemas.deployment import DeploymentCreate, DeploymentUpdate


class CRUDDeployment(CRUDBase[Deployment, DeploymentCreate, DeploymentUpdate]):
    """CRUD operations for Deployment"""

    async def get_by_project(
        self, db: AsyncSession, *, project_id: uuid.UUID
    ) -> List[Deployment]:
        """Get all deployments for a project"""
        result = await db.execute(
            select(Deployment).filter(Deployment.project_id == project_id)
        )
        return list(result.scalars().all())

    async def get_by_environment(
        self, db: AsyncSession, *, project_id: uuid.UUID, environment_id: uuid.UUID
    ) -> List[Deployment]:
        """Get deployments filtered by project and environment"""
        result = await db.execute(
            select(Deployment).filter(
                Deployment.project_id == project_id,
                Deployment.environment_id == environment_id
            )
        )
        return list(result.scalars().all())

    async def get_by_name_and_project(
        self, db: AsyncSession, *, name: str, project_id: uuid.UUID
    ) -> Optional[Deployment]:
        """Get deployment by name within a project"""
        result = await db.execute(
            select(Deployment).filter(
                Deployment.name == name,
                Deployment.project_id == project_id
            )
        )
        return result.scalar_one_or_none()

    async def create_with_project(
        self, db: AsyncSession, *, obj_in: DeploymentCreate, project_id: uuid.UUID
    ) -> Deployment:
        """Create deployment with project_id"""
        db_obj = Deployment(
            name=obj_in.name,
            subdomain=obj_in.subdomain,
            environment_id=obj_in.environment_id,
            project_id=project_id,
            image=obj_in.image,
            replicas=obj_in.replicas,
            image_pull_policy=obj_in.image_pull_policy,
        )
        db.add(db_obj)
        await db.flush()
        db.add(db_obj)
        await db.flush()
        
        # Reload with relationships eagerly loaded to avoid "greenlet_spawn" error
        # when accessed by Pydantic response models
        query = select(Deployment).where(Deployment.id == db_obj.id).options(
            selectinload(Deployment.project),
            selectinload(Deployment.environment)
        )
        result = await db.execute(query)
        db_obj = result.scalar_one()
        
        return db_obj


deployment = CRUDDeployment(Deployment)
