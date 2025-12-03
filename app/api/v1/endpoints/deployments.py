from typing import Any, List
from fastapi import APIRouter, Depends, HTTPException, Path
from sqlalchemy.ext.asyncio import AsyncSession
from kubernetes_asyncio.client import ApiException

from app import crud, schemas
from app.api import deps
from app.models.core import User
from app.services import deployment_service

router = APIRouter()

@router.post("/", response_model=schemas.Deployment, status_code=201)
async def create_deployment(
    *,
    db: AsyncSession = Depends(deps.get_db),
    project_id: str = Path(..., description="Project ID"),
    deployment_in: schemas.DeploymentCreate,
    current_user: User = Depends(deps.get_current_active_user),
) -> Any:
    """
    Create a new deployment in a project's namespace.
    """
    # Get project to verify it exists and get namespace
    project = await crud.project.get(db, id=project_id)
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")
    
    # Create deployment in K8s
    try:
        k8s_deployment = await deployment_service.create_deployment(
            namespace=project.name,
            name=deployment_in.name,
            image=deployment_in.image,
            replicas=deployment_in.replicas,
            port=deployment_in.port,
            env_vars=deployment_in.env_vars,
            labels=deployment_in.labels
        )
        
        # Get status and return
        status = await deployment_service.get_deployment_status(
            namespace=project.name,
            name=deployment_in.name
        )
        return status
        
    except ApiException as e:
        raise HTTPException(
            status_code=500,
            detail=f"Failed to create deployment: {e.reason}"
        )

@router.get("/", response_model=schemas.DeploymentList)
async def list_deployments(
    *,
    db: AsyncSession = Depends(deps.get_db),
    project_id: str = Path(..., description="Project ID"),
    current_user: User = Depends(deps.get_current_active_user),
) -> Any:
    """
    List all deployments in a project's namespace.
    """
    # Get project
    project = await crud.project.get(db, id=project_id)
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")
    
    # List deployments from K8s
    try:
        deployments = await deployment_service.list_deployments(namespace=project.name)
        
        # Convert to response format
        deployment_list = []
        for dep in deployments:
            status = await deployment_service.get_deployment_status(
                namespace=project.name,
                name=dep.metadata.name
            )
            deployment_list.append(status)
        
        return {
            "deployments": deployment_list,
            "total": len(deployment_list)
        }
        
    except ApiException as e:
        raise HTTPException(
            status_code=500,
            detail=f"Failed to list deployments: {e.reason}"
        )

@router.get("/{deployment_name}", response_model=schemas.Deployment)
async def get_deployment(
    *,
    db: AsyncSession = Depends(deps.get_db),
    project_id: str = Path(..., description="Project ID"),
    deployment_name: str = Path(..., description="Deployment name"),
    current_user: User = Depends(deps.get_current_active_user),
) -> Any:
    """
    Get details of a specific deployment.
    """
    # Get project
    project = await crud.project.get(db, id=project_id)
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")
    
    # Get deployment from K8s
    try:
        status = await deployment_service.get_deployment_status(
            namespace=project.name,
            name=deployment_name
        )
        
        if not status:
            raise HTTPException(status_code=404, detail="Deployment not found")
        
        return status
        
    except ApiException as e:
        raise HTTPException(
            status_code=500,
            detail=f"Failed to get deployment: {e.reason}"
        )

@router.delete("/{deployment_name}")
async def delete_deployment(
    *,
    db: AsyncSession = Depends(deps.get_db),
    project_id: str = Path(..., description="Project ID"),
    deployment_name: str = Path(..., description="Deployment name"),
    current_user: User = Depends(deps.get_current_active_user),
) -> Any:
    """
    Delete a deployment from a project's namespace.
    """
    # Get project
    project = await crud.project.get(db, id=project_id)
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")
    
    # Delete deployment from K8s
    try:
        success = await deployment_service.delete_deployment(
            namespace=project.name,
            name=deployment_name
        )
        
        if not success:
            raise HTTPException(status_code=404, detail="Deployment not found")
        
        return {"message": f"Deployment '{deployment_name}' deleted successfully"}
        
    except ApiException as e:
        raise HTTPException(
            status_code=500,
            detail=f"Failed to delete deployment: {e.reason}"
        )

@router.patch("/{deployment_name}/scale", response_model=schemas.Deployment)
async def scale_deployment(
    *,
    db: AsyncSession = Depends(deps.get_db),
    project_id: str = Path(..., description="Project ID"),
    deployment_name: str = Path(..., description="Deployment name"),
    scale_in: schemas.DeploymentScale,
    current_user: User = Depends(deps.get_current_active_user),
) -> Any:
    """
    Scale a deployment to a specific number of replicas.
    """
    # Get project
    project = await crud.project.get(db, id=project_id)
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")
    
    # Scale deployment in K8s
    try:
        await deployment_service.scale_deployment(
            namespace=project.name,
            name=deployment_name,
            replicas=scale_in.replicas
        )
        
        # Get updated status
        status = await deployment_service.get_deployment_status(
            namespace=project.name,
            name=deployment_name
        )
        
        return status
        
    except ApiException as e:
        raise HTTPException(
            status_code=500,
            detail=f"Failed to scale deployment: {e.reason}"
        )
