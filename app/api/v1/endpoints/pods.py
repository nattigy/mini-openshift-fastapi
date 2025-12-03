from typing import Any, List, Optional
from fastapi import APIRouter, Depends, HTTPException, Path, Query
from sqlalchemy.ext.asyncio import AsyncSession
from kubernetes_asyncio.client import ApiException

from app import crud, schemas
from app.api import deps
from app.models.core import User
from app.services import pod_service

router = APIRouter()

@router.get("/", response_model=schemas.PodList)
async def list_pods(
    *,
    db: AsyncSession = Depends(deps.get_db),
    project_id: str = Path(..., description="Project ID"),
    label_selector: Optional[str] = Query(None, description="Label selector (e.g., app=nginx)"),
    current_user: User = Depends(deps.get_current_active_user),
) -> Any:
    """
    List all pods in a project's namespace.
    """
    # Get project to verify it exists and get namespace
    project = await crud.project.get(db, id=project_id)
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")
    
    # List pods from K8s
    try:
        pods = await pod_service.list_pods(
            namespace=project.name,
            label_selector=label_selector
        )
        
        # Convert to response format
        pod_list = []
        for pod in pods:
            status = await pod_service.get_pod_status(
                namespace=project.name,
                name=pod.metadata.name
            )
            if status:
                pod_list.append(status)
        
        return {
            "pods": pod_list,
            "total": len(pod_list)
        }
        
    except ApiException as e:
        raise HTTPException(
            status_code=500,
            detail=f"Failed to list pods: {e.reason}"
        )

@router.get("/{pod_name}", response_model=schemas.Pod)
async def get_pod(
    *,
    db: AsyncSession = Depends(deps.get_db),
    project_id: str = Path(..., description="Project ID"),
    pod_name: str = Path(..., description="Pod name"),
    current_user: User = Depends(deps.get_current_active_user),
) -> Any:
    """
    Get details of a specific pod.
    """
    # Get project
    project = await crud.project.get(db, id=project_id)
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")
    
    # Get pod from K8s
    try:
        status = await pod_service.get_pod_status(
            namespace=project.name,
            name=pod_name
        )
        
        if not status:
            raise HTTPException(status_code=404, detail="Pod not found")
        
        return status
        
    except ApiException as e:
        raise HTTPException(
            status_code=500,
            detail=f"Failed to get pod: {e.reason}"
        )

@router.delete("/{pod_name}")
async def delete_pod(
    *,
    db: AsyncSession = Depends(deps.get_db),
    project_id: str = Path(..., description="Project ID"),
    pod_name: str = Path(..., description="Pod name"),
    current_user: User = Depends(deps.get_current_active_user),
) -> Any:
    """
    Delete a pod from a project's namespace.
    """
    # Get project
    project = await crud.project.get(db, id=project_id)
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")
    
    # Delete pod from K8s
    try:
        success = await pod_service.delete_pod(
            namespace=project.name,
            name=pod_name
        )
        
        if not success:
            raise HTTPException(status_code=404, detail="Pod not found")
        
        return {"message": f"Pod '{pod_name}' deleted successfully"}
        
    except ApiException as e:
        raise HTTPException(
            status_code=500,
            detail=f"Failed to delete pod: {e.reason}"
        )

@router.get("/{pod_name}/logs", response_model=schemas.PodLogs)
async def get_pod_logs(
    *,
    db: AsyncSession = Depends(deps.get_db),
    project_id: str = Path(..., description="Project ID"),
    pod_name: str = Path(..., description="Pod name"),
    container: Optional[str] = Query(None, description="Container name"),
    tail_lines: Optional[int] = Query(100, ge=1, le=10000, description="Number of lines"),
    since_seconds: Optional[int] = Query(None, ge=1, description="Logs from last N seconds"),
    current_user: User = Depends(deps.get_current_active_user),
) -> Any:
    """
    Get logs from a pod.
    """
    # Get project
    project = await crud.project.get(db, id=project_id)
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")
    
    # Get logs from K8s
    try:
        logs = await pod_service.get_pod_logs(
            namespace=project.name,
            name=pod_name,
            container=container,
            tail_lines=tail_lines,
            since_seconds=since_seconds
        )
        
        # Get container name if not specified
        if not container:
            pod = await pod_service.get_pod(project.name, pod_name)
            if pod and pod.spec.containers:
                container = pod.spec.containers[0].name
        
        return {
            "pod_name": pod_name,
            "container": container or "unknown",
            "logs": logs,
            "lines": len(logs.split('\n')) if logs else 0
        }
        
    except ApiException as e:
        if e.status == 404:
            raise HTTPException(status_code=404, detail="Pod not found")
        raise HTTPException(
            status_code=500,
            detail=f"Failed to get pod logs: {e.reason}"
        )
