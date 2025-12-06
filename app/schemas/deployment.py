from typing import Optional, Dict, List
from pydantic import BaseModel, Field
from datetime import datetime

# Deployment creation schema
class DeploymentCreate(BaseModel):
    name: str = Field(..., min_length=1, max_length=63, pattern=r'^[a-z0-9]([-a-z0-9]*[a-z0-9])?$')
    image: str = Field(..., min_length=1, description="Container image (e.g., nginx:latest)")
    replicas: int = Field(default=1, ge=1, le=100, description="Number of replicas")
    port: Optional[int] = Field(None, ge=1, le=65535, description="Container port to expose")
    image_pull_policy: str = Field("IfNotPresent", description="Image pull policy (Always, IfNotPresent, Never)")
    service_type: str = Field("ClusterIP", description="Service type (ClusterIP, NodePort, LoadBalancer)")
    env_vars: Optional[Dict[str, str]] = Field(None, description="Environment variables")
    labels: Optional[Dict[str, str]] = Field(None, description="Additional labels")

# Deployment update schema
class DeploymentUpdate(BaseModel):
    replicas: Optional[int] = Field(None, ge=1, le=100)
    image: Optional[str] = None

# Deployment scale schema
class DeploymentScale(BaseModel):
    replicas: int = Field(..., ge=0, le=100, description="Desired number of replicas")

# Deployment response schema
class Deployment(BaseModel):
    name: str
    namespace: str
    image: str
    replicas: int
    ready_replicas: int
    available_replicas: int
    unavailable_replicas: int
    updated_replicas: int
    created_at: Optional[datetime]
    labels: Optional[Dict[str, str]]

    class Config:
        from_attributes = True

# Deployment list response
class DeploymentList(BaseModel):
    deployments: List[Deployment]
    total: int
