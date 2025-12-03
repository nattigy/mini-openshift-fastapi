from fastapi import APIRouter
from app.api.v1.endpoints import login, users, projects, deployments, pods

api_router = APIRouter()
api_router.include_router(login.router, tags=["login"])
api_router.include_router(users.router, prefix="/users", tags=["users"])
api_router.include_router(projects.router, prefix="/projects", tags=["projects"])
api_router.include_router(
    deployments.router,
    prefix="/projects/{project_id}/deployments",
    tags=["deployments"]
)
api_router.include_router(
    pods.router,
    prefix="/projects/{project_id}/pods",
    tags=["pods"]
)
