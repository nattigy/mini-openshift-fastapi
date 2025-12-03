from typing import Optional
from pydantic import BaseModel, field_validator
from uuid import UUID
from datetime import datetime
import re

# Shared properties
class ProjectBase(BaseModel):
    name: Optional[str] = None
    description: Optional[str] = None

# Properties to receive via API on creation
class ProjectCreate(ProjectBase):
    name: str
    
    @field_validator('name')
    @classmethod
    def validate_k8s_name(cls, v: str) -> str:
        """Validate that project name is Kubernetes-compatible"""
        if not v:
            raise ValueError('Project name cannot be empty')
        
        # K8s namespace naming rules:
        # - lowercase alphanumeric characters or '-'
        # - must start and end with alphanumeric
        # - max 63 characters
        if len(v) > 63:
            raise ValueError('Project name must be 63 characters or less')
        
        pattern = r'^[a-z0-9]([-a-z0-9]*[a-z0-9])?$'
        if not re.match(pattern, v):
            raise ValueError(
                'Project name must be lowercase alphanumeric with hyphens, '
                'starting and ending with alphanumeric characters'
            )
        
        return v

# Properties to receive via API on update
class ProjectUpdate(ProjectBase):
    pass

class ProjectInDBBase(ProjectBase):
    id: Optional[UUID] = None
    owner_id: Optional[UUID] = None
    created_at: Optional[datetime] = None

    class Config:
        from_attributes = True

# Additional properties to return via API
class Project(ProjectInDBBase):
    pass
