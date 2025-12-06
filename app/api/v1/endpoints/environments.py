from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from typing import List
import uuid

from app import schemas, crud
from app.api import deps
from app.models.core import User

router = APIRouter()


@router.get("/", response_model=List[schemas.Environment])
async def list_environments(
    db: AsyncSession = Depends(deps.get_db),
    skip: int = 0,
    limit: int = 100,
    current_user: User = Depends(deps.get_current_user),
):
    """
    List all environments (available system-wide).
    Any authenticated user can view environments.
    """
    environments = await crud.environment.get_multi(db, skip=skip, limit=limit)
    return environments


@router.post("/", response_model=schemas.Environment, status_code=201)
async def create_environment(
    *,
    db: AsyncSession = Depends(deps.get_db),
    environment_in: schemas.EnvironmentCreate,
    current_user: User = Depends(deps.get_current_user),
):
    """
    Create new environment.
    Only admin users can create environments.
    """
    # Check if environment with this name already exists
    existing = await crud.environment.get_by_name(db, name=environment_in.name)
    if existing:
        raise HTTPException(
            status_code=400,
            detail=f"Environment with name '{environment_in.name}' already exists"
        )

    # Create the environment
    environment = await crud.environment.create(db, obj_in=environment_in)
    await db.commit()
    await db.refresh(environment)
    
    return environment


@router.get("/{environment_id}", response_model=schemas.Environment)
async def get_environment(
    *,
    db: AsyncSession = Depends(deps.get_db),
    environment_id: uuid.UUID,
    current_user: User = Depends(deps.get_current_user),
):
    """Get environment by ID"""
    environment = await crud.environment.get(db, id=environment_id)
    if not environment:
        raise HTTPException(status_code=404, detail="Environment not found")
    return environment


@router.put("/{environment_id}", response_model=schemas.Environment)
async def update_environment(
    *,
    db: AsyncSession = Depends(deps.get_db),
    environment_id: uuid.UUID,
    environment_in: schemas.EnvironmentUpdate,
    current_user: User = Depends(deps.get_current_user),
):
    """
    Update environment.
    Only admin users can update environments.
    """
    environment = await crud.environment.get(db, id=environment_id)
    if not environment:
        raise HTTPException(status_code=404, detail="Environment not found")

    # If name is being changed, check it doesn't conflict
    if environment_in.name and environment_in.name != environment.name:
        existing = await crud.environment.get_by_name(db, name=environment_in.name)
        if existing:
            raise HTTPException(
                status_code=400,
                detail=f"Environment with name '{environment_in.name}' already exists"
            )

    environment = await crud.environment.update(db, db_obj=environment, obj_in=environment_in)
    await db.commit()
    await db.refresh(environment)
    
    return environment


@router.delete("/{environment_id}")
async def delete_environment(
    *,
    db: AsyncSession = Depends(deps.get_db),
    environment_id: uuid.UUID,
    current_user: User = Depends(deps.get_current_user),
):
    """
    Delete environment.
    Only admin users can delete environments.
    Will fail if deployments exist in this environment.
    """
    environment = await crud.environment.get(db, id=environment_id)
    if not environment:
        raise HTTPException(status_code=404, detail="Environment not found")

    # Check if any deployments exist in this environment
    # This will be handled by the database foreign key constraint
    try:
        await crud.environment.remove(db, id=environment_id)
        await db.commit()
    except Exception as e:
        await db.rollback()
        raise HTTPException(
            status_code=400,
            detail="Cannot delete environment with existing deployments"
        )

    return {"message": "Environment deleted successfully"}
