from typing import Any, List, Optional
from fastapi import APIRouter, Depends, HTTPException, Path, Query
from sqlalchemy.ext.asyncio import AsyncSession
from kubernetes_asyncio.client import ApiException
import uuid

from app import crud, schemas
from app.api import deps
from app.models.core import User
from app.services import deployment_service

router = APIRouter()


@router.post("/", response_model=schemas.DeploymentDB, status_code=201)
async def create_deployment(
    *,
    db: AsyncSession = Depends(deps.get_db),
    project_id: uuid.UUID = Path(..., description="Project ID"),
    deployment_in: schemas.DeploymentCreate,
    current_user: User = Depends(deps.get_current_user),
) -> Any:
    """
    Create a new deployment in a project.
    
    This will:
    1. Create Kubernetes Deployment
    2. Create Kubernetes Service (ClusterIP)
    3. Create Kubernetes Ingress (with HTTPS)
    4. Save deployment metadata to database
    """
    # Get project to verify it exists and get domain
    project = await crud.project.get(db, id=project_id)
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")
    
    if not project.domain:
        raise HTTPException(
            status_code=400,
            detail="Project must have a domain configured to create deployments"
        )
    
    # Get environment
    environment = await crud.environment.get(db, id=deployment_in.environment_id)
    if not environment:
        raise HTTPException(status_code=404, detail="Environment not found")
    
    # Check if deployment with same name already exists in this project
    existing = await crud.deployment.get_by_name_and_project(
        db, name=deployment_in.name, project_id=project_id
    )
    if existing:
        raise HTTPException(
            status_code=400,
            detail=f"Deployment '{deployment_in.name}' already exists in this project"
        )
    
    # Create deployment in Kubernetes
    try:
        await deployment_service.create_deployment(
            namespace=project.name,
            name=deployment_in.name,
            image=deployment_in.image,
            replicas=deployment_in.replicas,
            image_pull_policy=deployment_in.image_pull_policy,
            project_domain=project.domain,
            environment_prefix=environment.subdomain_prefix,
            subdomain=deployment_in.subdomain,
            env_vars=deployment_in.env_vars,
            labels=deployment_in.labels
        )
        
    except ApiException as e:
        raise HTTPException(
            status_code=500,
            detail=f"Failed to create deployment in Kubernetes: {e.reason}"
        )
    except Exception as e:
        error_msg = str(e)
        if "connection" in error_msg.lower() or "refused" in error_msg.lower():
            raise HTTPException(
                status_code=503,
                detail="Kubernetes cluster is not available. Please ensure your cluster is running."
            )
        raise HTTPException(
            status_code=500,
            detail=f"Failed to create deployment: {error_msg}"
        )
    
    # Save deployment to database
    try:
        db_deployment = await crud.deployment.create_with_project(
            db, obj_in=deployment_in, project_id=project_id
        )
        await db.commit()
        await db.refresh(db_deployment)
        
        # Build full domain for response
        full_domain = deployment_service._build_domain(
            project.domain,
            environment.subdomain_prefix,
            deployment_in.subdomain
        )
        
        # Convert to response schema
        deployment_response = schemas.DeploymentDB.model_validate(db_deployment)
        deployment_response.full_domain = full_domain
        
        return deployment_response
        
    except Exception as e:
        # Rollback database if saving fails
        await db.rollback()
        # Try to clean up Kubernetes resources
        try:
            await deployment_service.delete_deployment(
                namespace=project.name,
                name=deployment_in.name
            )
        except:
            pass
        raise HTTPException(
            status_code=500,
            detail=f"Failed to save deployment to database: {str(e)}"
        )


@router.get("/", response_model=List[schemas.DeploymentDB])
async def list_deployments(
    *,
    db: AsyncSession = Depends(deps.get_db),
    project_id: uuid.UUID = Path(..., description="Project ID"),
    environment_id: Optional[uuid.UUID] = Query(None, description="Filter by environment ID"),
    current_user: User = Depends(deps.get_current_user),
) -> Any:
    """
    List all deployments in a project.
    Optionally filter by environment.
    """
    # Get project
    project = await crud.project.get(db, id=project_id)
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")
    
    # Get deployments from database (with optional environment filter)
    if environment_id:
        deployments = await crud.deployment.get_by_environment(
            db, project_id=project_id, environment_id=environment_id
        )
    else:
        deployments = await crud.deployment.get_by_project(db, project_id=project_id)
    
    # Build response with full domains
    response = []
    for dep in deployments:
        # Get environment for domain building
        env = await crud.environment.get(db, id=dep.environment_id)
        
        full_domain = deployment_service._build_domain(
            project.domain if project.domain else "",
            env.subdomain_prefix if env else "",
            dep.subdomain
        )
        
        dep_response = schemas.DeploymentDB.model_validate(dep)
        dep_response.full_domain = full_domain
        response.append(dep_response)
    
    return response


@router.get("/{deployment_name}", response_model=schemas.DeploymentDB)
async def get_deployment(
    *,
    db: AsyncSession = Depends(deps.get_db),
    project_id: uuid.UUID = Path(..., description="Project ID"),
    deployment_name: str = Path(..., description="Deployment name"),
    current_user: User = Depends(deps.get_current_user),
) -> Any:
    """
    Get details of a specific deployment.
    """
    # Get project
    project = await crud.project.get(db, id=project_id)
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")
    
    # Get deployment from database
    deployment = await crud.deployment.get_by_name_and_project(
        db, name=deployment_name, project_id=project_id
    )
    
    if not deployment:
        raise HTTPException(status_code=404, detail="Deployment not found")
    
    # Get environment for domain building
    env = await crud.environment.get(db, id=deployment.environment_id)
    
    full_domain = deployment_service._build_domain(
        project.domain if project.domain else "",
        env.subdomain_prefix if env else "",
        deployment.subdomain
    )
    
    dep_response = schemas.DeploymentDB.model_validate(deployment)
    dep_response.full_domain = full_domain
    
    return dep_response


@router.get("/{deployment_name}/status", response_model=schemas.Deployment)
async def get_deployment_kubernetes_status(
    *,
    db: AsyncSession = Depends(deps.get_db),
    project_id: uuid.UUID = Path(..., description="Project ID"),
    deployment_name: str = Path(..., description="Deployment name"),
    current_user: User = Depends(deps.get_current_user),
) -> Any:
    """
    Get live Kubernetes status of a deployment (replicas, health, etc).
    """
    # Get project
    project = await crud.project.get(db, id=project_id)
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")
    
    # Get live status from Kubernetes
    try:
        status = await deployment_service.get_deployment_status(
            namespace=project.name,
            name=deployment_name
        )
        
        if not status:
            raise HTTPException(status_code=404, detail="Deployment not found in Kubernetes")
        
        return status
        
    except ApiException as e:
        raise HTTPException(
            status_code=500,
            detail=f"Failed to get deployment status: {e.reason}"
        )


@router.delete("/{deployment_name}")
async def delete_deployment(
    *,
    db: AsyncSession = Depends(deps.get_db),
    project_id: uuid.UUID = Path(..., description="Project ID"),
    deployment_name: str = Path(..., description="Deployment name"),
    current_user: User = Depends(deps.get_current_user),
) -> Any:
    """
    Delete a deployment.
    This will delete from both Kubernetes and database.
    """
    # Get project
    project = await crud.project.get(db, id=project_id)
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")
    
    # Get deployment from database
    deployment = await crud.deployment.get_by_name_and_project(
        db, name=deployment_name, project_id=project_id
    )
    
    if not deployment:
        raise HTTPException(status_code=404, detail="Deployment not found")
    
    # Delete from Kubernetes (Deployment, Service, Ingress)
    try:
        await deployment_service.delete_deployment(
            namespace=project.name,
            name=deployment_name
        )
    except ApiException as e:
        raise HTTPException(
            status_code=500,
            detail=f"Failed to delete deployment from Kubernetes: {e.reason}"
        )
    
    # Delete from database
    await crud.deployment.remove(db, id=deployment.id)
    await db.commit()
    
    return {"message": f"Deployment '{deployment_name}' deleted successfully"}


@router.patch("/{deployment_name}/scale", response_model=schemas.Deployment)
async def scale_deployment(
    *,
    db: AsyncSession = Depends(deps.get_db),
    project_id: uuid.UUID = Path(..., description="Project ID"),
    deployment_name: str = Path(..., description="Deployment name"),
    scale_in: schemas.DeploymentScale,
    current_user: User = Depends(deps.get_current_user),
) -> Any:
    """
    Scale a deployment to a specific number of replicas.
    """
    # Get project
    project = await crud.project.get(db, id=project_id)
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")
    
    # Get deployment from database
    deployment = await crud.deployment.get_by_name_and_project(
        db, name=deployment_name, project_id=project_id
    )
    
    if not deployment:
        raise HTTPException(status_code=404, detail="Deployment not found")
    
    # Scale in Kubernetes
    try:
        await deployment_service.scale_deployment(
            namespace=project.name,
            name=deployment_name,
            replicas=scale_in.replicas
        )
        
        # Update database
        deployment.replicas = scale_in.replicas
        await db.commit()
        
        # Get updated status from Kubernetes
        status = await deployment_service.get_deployment_status(
            namespace=project.name,
            name=deployment_name
        )
        
        return status
        
    except ApiException as e:
        await db.rollback()
        raise HTTPException(
            status_code=500,
            detail=f"Failed to scale deployment: {e.reason}"
        )


@router.patch("/{deployment_name}/image", response_model=schemas.Deployment)
async def update_deployment_image(
    *,
    db: AsyncSession = Depends(deps.get_db),
    project_id: uuid.UUID = Path(..., description="Project ID"),
    deployment_name: str = Path(..., description="Deployment name"),
    update_in: schemas.DeploymentUpdate,
    current_user: User = Depends(deps.get_current_user),
) -> Any:
    """
    Update the container image of a deployment.
    """
    # Get project
    project = await crud.project.get(db, id=project_id)
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")
    
    # Get deployment from database
    deployment = await crud.deployment.get_by_name_and_project(
        db, name=deployment_name, project_id=project_id
    )
    
    if not deployment:
        raise HTTPException(status_code=404, detail="Deployment not found")
    
    # Update in Kubernetes
    try:
        if update_in.image:
            await deployment_service.update_deployment_image(
                namespace=project.name,
                name=deployment_name,
                image=update_in.image
            )
            deployment.image = update_in.image
        
        if update_in.replicas:
            await deployment_service.scale_deployment(
                namespace=project.name,
                name=deployment_name,
                replicas=update_in.replicas
            )
            deployment.replicas = update_in.replicas
        
        await db.commit()
        
        # Get updated status from Kubernetes
        status = await deployment_service.get_deployment_status(
            namespace=project.name,
            name=deployment_name
        )
        
        return status
        
    except ApiException as e:
        await db.rollback()
        raise HTTPException(
            status_code=500,
            detail=f"Failed to update deployment: {e.reason}"
        )
