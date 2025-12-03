from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager
from app.core.config import settings
from app.services import k8s_client

@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup: Initialize K8s client
    await k8s_client.initialize()
    yield
    # Shutdown: Close K8s client
    await k8s_client.close()

app = FastAPI(
    title=settings.PROJECT_NAME,
    openapi_url=f"{settings.API_V1_STR}/openapi.json",
    lifespan=lifespan
)

# Add CORS middleware BEFORE routers
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:3000",
        "http://127.0.0.1:3000",
        "http://localhost:3001",
        "http://127.0.0.1:3001",
        "http://localhost",
        "http://127.0.0.1",
    ],
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "DELETE", "OPTIONS", "PATCH"],
    allow_headers=["*"],
    max_age=3600,
)

@app.get("/")
async def root():
    return {"message": "Welcome to Mini OpenShift API"}

from app.api.v1.api import api_router

app.include_router(api_router, prefix=settings.API_V1_STR)
