from kubernetes_asyncio.client import V1Namespace, V1ObjectMeta, ApiException
from typing import Optional, List
import logging
from app.services.k8s_client import k8s_client

logger = logging.getLogger(__name__)

class NamespaceService:
    """Service for managing Kubernetes namespaces"""
    
    async def create_namespace(self, name: str) -> bool:
        """
        Create a Kubernetes namespace
        
        Args:
            name: Namespace name (must be DNS-compatible)
        
        Returns:
            True if created successfully, False otherwise
        
        Raises:
            ApiException: If K8s API call fails
        """
        try:
            core_v1 = k8s_client.get_core_v1_api()
            
            # Check if namespace already exists
            try:
                await core_v1.read_namespace(name=name)
                logger.warning(f"Namespace {name} already exists")
                return True  # Already exists, consider it success
            except ApiException as e:
                if e.status != 404:
                    raise
            
            # Create namespace
            namespace = V1Namespace(
                metadata=V1ObjectMeta(
                    name=name,
                    labels={
                        "managed-by": "mini-openshift",
                        "app": "mini-openshift"
                    }
                )
            )
            
            await core_v1.create_namespace(body=namespace)
            logger.info(f"Created namespace: {name}")
            return True
            
        except ApiException as e:
            logger.error(f"Failed to create namespace {name}: {e}")
            raise
    
    async def delete_namespace(self, name: str) -> bool:
        """
        Delete a Kubernetes namespace
        
        Args:
            name: Namespace name
        
        Returns:
            True if deleted successfully, False if not found
        
        Raises:
            ApiException: If K8s API call fails
        """
        try:
            core_v1 = k8s_client.get_core_v1_api()
            await core_v1.delete_namespace(name=name)
            logger.info(f"Deleted namespace: {name}")
            return True
            
        except ApiException as e:
            if e.status == 404:
                logger.warning(f"Namespace {name} not found")
                return False
            logger.error(f"Failed to delete namespace {name}: {e}")
            raise
    
    async def get_namespace(self, name: str) -> Optional[V1Namespace]:
        """
        Get a Kubernetes namespace
        
        Args:
            name: Namespace name
        
        Returns:
            V1Namespace object if found, None otherwise
        """
        try:
            core_v1 = k8s_client.get_core_v1_api()
            namespace = await core_v1.read_namespace(name=name)
            return namespace
            
        except ApiException as e:
            if e.status == 404:
                return None
            logger.error(f"Failed to get namespace {name}: {e}")
            raise
    
    async def list_namespaces(self) -> List[str]:
        """
        List all Kubernetes namespaces managed by mini-openshift
        
        Returns:
            List of namespace names
        """
        try:
            core_v1 = k8s_client.get_core_v1_api()
            namespaces = await core_v1.list_namespace(
                label_selector="managed-by=mini-openshift"
            )
            return [ns.metadata.name for ns in namespaces.items]
            
        except ApiException as e:
            logger.error(f"Failed to list namespaces: {e}")
            raise

namespace_service = NamespaceService()
