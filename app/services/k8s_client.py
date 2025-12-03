from kubernetes_asyncio import client, config
from kubernetes_asyncio.client import ApiClient
from typing import Optional
import os
from app.core.config import settings

class KubernetesClient:
    """Singleton Kubernetes client wrapper"""
    
    _instance: Optional['KubernetesClient'] = None
    _api_client: Optional[ApiClient] = None
    
    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance
    
    async def initialize(self):
        """Initialize the Kubernetes client"""
        if self._api_client is not None:
            return
        
        try:
            # Try to load in-cluster config first (for when running in K8s)
            config.load_incluster_config()
        except config.ConfigException:
            # Fall back to kubeconfig file
            if settings.KUBE_CONFIG_PATH and os.path.exists(settings.KUBE_CONFIG_PATH):
                await config.load_kube_config(config_file=settings.KUBE_CONFIG_PATH)
            else:
                # Use default ~/.kube/config
                await config.load_kube_config()
        
        self._api_client = ApiClient()
    
    async def close(self):
        """Close the Kubernetes client"""
        if self._api_client:
            await self._api_client.close()
            self._api_client = None
    
    def get_core_v1_api(self) -> client.CoreV1Api:
        """Get CoreV1Api instance for namespace and pod operations"""
        if self._api_client is None:
            raise RuntimeError("Kubernetes client not initialized. Call initialize() first.")
        return client.CoreV1Api(self._api_client)
    
    def get_apps_v1_api(self) -> client.AppsV1Api:
        """Get AppsV1Api instance for deployment operations"""
        if self._api_client is None:
            raise RuntimeError("Kubernetes client not initialized. Call initialize() first.")
        return client.AppsV1Api(self._api_client)

# Singleton instance
k8s_client = KubernetesClient()
