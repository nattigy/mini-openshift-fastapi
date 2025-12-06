from typing import Optional, Dict, List
from pydantic import BaseModel, Field, ConfigDict
from datetime import datetime
import uuid

# Deployment creation schema
class DeploymentCreate(BaseModel):
    name: str = Field(..., min_length=1, max_length=63, pattern=r'^[a-z0-9]([-a-z0-9]*[a-z0-9])?$')
    subdomain: str = Field(default="", description="Subdomain (leave empty for root domain)")
    environment_id: uuid.UUID = Field(..., description="Environment ID")
    image: str = Field(..., min_length=1, description="Container image (e.g., nginx:latest)")
    replicas: int = Field(default=1, ge=1, le=100, description="Number of replicas")
    image_pull_policy: str = Field("IfNotPresent", description="Image pull policy (Always, IfNotPresent, Never)")
    env_vars: Optional[Dict[str, str]] = Field(None, description="Environment variables")
    labels: Optional[Dict[str, str]] = Field(None, description="Additional labels")

# Deployment update schema
class DeploymentUpdate(BaseModel):
    replicas: Optional[int] = Field(None, ge=1, le=100)
    image: Optional[str] = None

# Deployment scale schema
class DeploymentScale(BaseModel):
    replicas: int = Field(..., ge=0, le=100, description="Desired number of replicas")

# Deployment response schema (from Kubernetes)
class Deployment(BaseModel):
    name: str
    namespace: str
    image: str
    replicas: int
    ready_replicas: int
    available_replicas: int
    unavailable_replicas: int
    updated_replicas: int
    created_at: Optional[datetime] = None
    labels: Optional[Dict[str, str]] = None

    model_config = ConfigDict(from_attributes=True)

# Deployment DB response schema (from database)
class DeploymentDB(BaseModel):
    id: uuid.UUID
    name: str
    subdomain: str
    environment_id: uuid.UUID
    project_id: uuid.UUID
    image: str
    replicas: int
    image_pull_policy: str
    created_at: datetime
    updated_at: datetime
    
    # Computed field for full domain
    full_domain: Optional[str] = None
    
    model_config = ConfigDict(from_attributes=True)

# Deployment list response
class DeploymentList(BaseModel):
    deployments: List[Deployment]
    total: int
