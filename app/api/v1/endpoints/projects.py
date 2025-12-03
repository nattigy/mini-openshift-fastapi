from typing import Any, List, Optional
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.ext.asyncio import AsyncSession

from app import crud, schemas
from app.api import deps
from app.services import namespace_service
from app.models.core import User

router = APIRouter()

@router.get("/", response_model=List[schemas.Project])
async def read_projects(
    db: AsyncSession = Depends(deps.get_db),
    skip: int = 0,
    limit: int = 100,
    q: Optional[str] = Query(None, description="Search query"),
    current_user: User = Depends(deps.get_current_active_user),
) -> Any:
    """
    Retrieve projects.
    """
    if q:
        projects = await crud.project.search(db, query=q, skip=skip, limit=limit)
    else:
        projects = await crud.project.get_multi(db, skip=skip, limit=limit)
    return projects

@router.post("/", response_model=schemas.Project)
async def create_project(
    *,
    db: AsyncSession = Depends(deps.get_db),
    project_in: schemas.ProjectCreate,
    current_user: User = Depends(deps.get_current_active_user),
) -> Any:
    """
    Create new project.
    """
    # Check if project exists in DB
    project = await crud.project.get_by_name(db, name=project_in.name)
    if project:
        raise HTTPException(
            status_code=400,
            detail="The project with this name already exists.",
        )
    
    # Create K8s namespace first
    try:
        namespace_service.create_namespace(project_in.name)
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Failed to create Kubernetes namespace: {str(e)}"
        )
    
    # Create project in DB
    try:
        project = await crud.project.create_with_owner(
            db=db, obj_in=project_in, owner_id=current_user.id
        )
        return project
    except Exception as e:
        # Rollback: delete namespace if DB creation fails
        try:
            namespace_service.delete_namespace(project_in.name)
        except:
            pass
        raise HTTPException(
            status_code=500,
            detail=f"Failed to create project in database: {str(e)}"
        )

@router.get("/{project_id}", response_model=schemas.Project)
async def read_project(
    *,
    db: AsyncSession = Depends(deps.get_db),
    project_id: str,
    current_user: User = Depends(deps.get_current_active_user),
) -> Any:
    """
    Get project by ID.
    """
    project = await crud.project.get(db, id=project_id)
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")
    return project

@router.put("/{project_id}", response_model=schemas.Project)
async def update_project(
    *,
    db: AsyncSession = Depends(deps.get_db),
    project_id: str,
    project_in: schemas.ProjectUpdate,
    current_user: User = Depends(deps.get_current_active_user),
) -> Any:
    """
    Update project.
    """
    project = await crud.project.get(db, id=project_id)
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")
    
    # Only owner can update (or admin)
    if str(project.owner_id) != str(current_user.id) and current_user.role != "admin":
        raise HTTPException(status_code=403, detail="Not enough permissions")
    
    # Cannot change name (K8s namespace is immutable)
    if project_in.name and project_in.name != project.name:
        raise HTTPException(
            status_code=400,
            detail="Cannot change project name (namespace is immutable)"
        )
    
    project = await crud.project.update(db, db_obj=project, obj_in=project_in)
    return project

@router.delete("/{project_id}", response_model=schemas.Project)
async def delete_project(
    *,
    db: AsyncSession = Depends(deps.get_db),
    project_id: str,
    current_user: User = Depends(deps.get_current_active_user),
) -> Any:
    """
    Delete a project and its associated Kubernetes namespace.
    """
    project = await crud.project.get(db, id=project_id)
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")
        
    # Only owner can delete (or admin)
    if str(project.owner_id) != str(current_user.id) and current_user.role != "admin":
        raise HTTPException(status_code=403, detail="Not enough permissions")
    
    # Delete K8s namespace
    try:
        namespace_service.delete_namespace(project.name)
    except Exception as e:
        # Log error but continue to delete from DB
        print(f"Failed to delete namespace {project.name}: {e}")
        
    # Delete from DB
    project = await crud.project.remove(db, id=project_id)
    return project
