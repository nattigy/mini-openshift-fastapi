from pydantic import BaseModel, ConfigDict
from typing import Optional
from datetime import datetime
import uuid


class EnvironmentBase(BaseModel):
    """Base schema for Environment"""
    name: str
    subdomain_prefix: str = ""
    description: Optional[str] = None


class EnvironmentCreate(EnvironmentBase):
    """Schema for creating an environment"""
    pass


class EnvironmentUpdate(BaseModel):
    """Schema for updating an environment"""
    name: Optional[str] = None
    subdomain_prefix: Optional[str] = None
    description: Optional[str] = None


class Environment(EnvironmentBase):
    """Schema for environment responses"""
    id: uuid.UUID
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)
