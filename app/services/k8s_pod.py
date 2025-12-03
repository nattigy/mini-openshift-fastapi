from kubernetes_asyncio.client import V1Pod, ApiException
from typing import Optional, List, Dict
import logging
from app.services.k8s_client import k8s_client

logger = logging.getLogger(__name__)

class PodService:
    """Service for managing Kubernetes pods"""
    
    async def list_pods(self, namespace: str, label_selector: Optional[str] = None) -> List[V1Pod]:
        """
        List all pods in a namespace
        
        Args:
            namespace: Namespace to list pods from
            label_selector: Optional label selector (e.g., "app=nginx")
        
        Returns:
            List of V1Pod objects
        """
        try:
            core_v1 = k8s_client.get_core_v1_api()
            result = await core_v1.list_namespaced_pod(
                namespace=namespace,
                label_selector=label_selector
            )
            return result.items
            
        except ApiException as e:
            logger.error(f"Failed to list pods in {namespace}: {e}")
            raise
    
    async def get_pod(self, namespace: str, name: str) -> Optional[V1Pod]:
        """
        Get a specific pod
        
        Args:
            namespace: Namespace of the pod
            name: Pod name
        
        Returns:
            V1Pod object if found, None otherwise
        """
        try:
            core_v1 = k8s_client.get_core_v1_api()
            pod = await core_v1.read_namespaced_pod(
                name=name,
                namespace=namespace
            )
            return pod
            
        except ApiException as e:
            if e.status == 404:
                return None
            logger.error(f"Failed to get pod {name}: {e}")
            raise
    
    async def delete_pod(self, namespace: str, name: str) -> bool:
        """
        Delete a pod
        
        Args:
            namespace: Namespace of the pod
            name: Pod name
        
        Returns:
            True if deleted successfully, False if not found
        
        Raises:
            ApiException: If K8s API call fails
        """
        try:
            core_v1 = k8s_client.get_core_v1_api()
            await core_v1.delete_namespaced_pod(
                name=name,
                namespace=namespace
            )
            logger.info(f"Deleted pod {name} from namespace {namespace}")
            return True
            
        except ApiException as e:
            if e.status == 404:
                logger.warning(f"Pod {name} not found in {namespace}")
                return False
            logger.error(f"Failed to delete pod {name}: {e}")
            raise
    
    async def get_pod_logs(
        self,
        namespace: str,
        name: str,
        container: Optional[str] = None,
        tail_lines: Optional[int] = None,
        since_seconds: Optional[int] = None
    ) -> str:
        """
        Get logs from a pod
        
        Args:
            namespace: Namespace of the pod
            name: Pod name
            container: Container name (optional, uses first container if not specified)
            tail_lines: Number of lines from the end of the logs to show
            since_seconds: Return logs newer than a relative duration in seconds
        
        Returns:
            Pod logs as string
        
        Raises:
            ApiException: If K8s API call fails
        """
        try:
            core_v1 = k8s_client.get_core_v1_api()
            
            # If container not specified, get the first container name
            if not container:
                pod = await self.get_pod(namespace, name)
                if pod and pod.spec.containers:
                    container = pod.spec.containers[0].name
            
            logs = await core_v1.read_namespaced_pod_log(
                name=name,
                namespace=namespace,
                container=container,
                tail_lines=tail_lines,
                since_seconds=since_seconds
            )
            return logs
            
        except ApiException as e:
            logger.error(f"Failed to get logs for pod {name}: {e}")
            raise
    
    async def get_pod_status(self, namespace: str, name: str) -> Optional[Dict]:
        """
        Get pod status information
        
        Args:
            namespace: Namespace of the pod
            name: Pod name
        
        Returns:
            Dict with status information
        """
        try:
            pod = await self.get_pod(namespace, name)
            if not pod:
                return None
            
            # Get container statuses
            container_statuses = []
            if pod.status.container_statuses:
                for cs in pod.status.container_statuses:
                    status_info = {
                        "name": cs.name,
                        "ready": cs.ready,
                        "restart_count": cs.restart_count,
                        "image": cs.image
                    }
                    
                    # Get state information
                    if cs.state:
                        if cs.state.running:
                            status_info["state"] = "running"
                            status_info["started_at"] = cs.state.running.started_at
                        elif cs.state.waiting:
                            status_info["state"] = "waiting"
                            status_info["reason"] = cs.state.waiting.reason
                        elif cs.state.terminated:
                            status_info["state"] = "terminated"
                            status_info["reason"] = cs.state.terminated.reason
                            status_info["exit_code"] = cs.state.terminated.exit_code
                    
                    container_statuses.append(status_info)
            
            return {
                "name": pod.metadata.name,
                "namespace": pod.metadata.namespace,
                "phase": pod.status.phase,
                "pod_ip": pod.status.pod_ip,
                "host_ip": pod.status.host_ip,
                "node_name": pod.spec.node_name,
                "created_at": pod.metadata.creation_timestamp,
                "labels": pod.metadata.labels,
                "containers": container_statuses,
                "conditions": [
                    {
                        "type": c.type,
                        "status": c.status,
                        "reason": c.reason if c.reason else None
                    }
                    for c in (pod.status.conditions or [])
                ]
            }
            
        except ApiException as e:
            logger.error(f"Failed to get pod status {name}: {e}")
            raise

pod_service = PodService()
