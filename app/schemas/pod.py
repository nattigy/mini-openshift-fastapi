from typing import Optional, List, Dict, Any
from pydantic import BaseModel, Field
from datetime import datetime

# Container status schema
class ContainerStatus(BaseModel):
    name: str
    ready: bool
    restart_count: int
    image: str
    state: Optional[str] = None
    started_at: Optional[datetime] = None
    reason: Optional[str] = None
    exit_code: Optional[int] = None

# Pod condition schema
class PodCondition(BaseModel):
    type: str
    status: str
    reason: Optional[str] = None

# Pod response schema
class Pod(BaseModel):
    name: str
    namespace: str
    phase: str
    pod_ip: Optional[str] = None
    host_ip: Optional[str] = None
    node_name: Optional[str] = None
    created_at: Optional[datetime] = None
    labels: Optional[Dict[str, str]] = None
    containers: List[ContainerStatus]
    conditions: List[PodCondition]

    class Config:
        from_attributes = True

# Pod list response
class PodList(BaseModel):
    pods: List[Pod]
    total: int

# Pod logs request
class PodLogsRequest(BaseModel):
    container: Optional[str] = Field(None, description="Container name (optional)")
    tail_lines: Optional[int] = Field(None, ge=1, le=10000, description="Number of lines to show")
    since_seconds: Optional[int] = Field(None, ge=1, description="Show logs from last N seconds")

# Pod logs response
class PodLogs(BaseModel):
    pod_name: str
    container: str
    logs: str
    lines: int
