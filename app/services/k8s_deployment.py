from kubernetes_asyncio.client import (
    V1Deployment, V1DeploymentSpec, V1PodTemplateSpec, V1ObjectMeta,
    V1PodSpec, V1Container, V1ContainerPort, V1EnvVar, V1LabelSelector,
    V1Service, V1ServiceSpec, V1ServicePort,
    ApiException
)
from typing import Optional, List, Dict
import logging
from app.services.k8s_client import k8s_client

logger = logging.getLogger(__name__)

class DeploymentService:
    """Service for managing Kubernetes deployments"""
    
    async def create_deployment(
        self,
        namespace: str,
        name: str,
        image: str,
        replicas: int = 1,
        port: Optional[int] = None,
        image_pull_policy: str = "IfNotPresent",
        service_type: str = "ClusterIP",
        env_vars: Optional[Dict[str, str]] = None,
        labels: Optional[Dict[str, str]] = None
    ) -> V1Deployment:
        """
        Create a Kubernetes deployment and optional service
        """
        try:
            apps_v1 = k8s_client.get_apps_v1_api()
            core_v1 = k8s_client.get_core_v1_api()
            
            # Default labels
            if labels is None:
                labels = {}
            labels.update({
                "app": name,
                "managed-by": "mini-openshift"
            })
            
            # Build container spec
            container_ports = []
            if port:
                container_ports.append(V1ContainerPort(container_port=port))
            
            # Build environment variables
            env = []
            if env_vars:
                env = [V1EnvVar(name=k, value=v) for k, v in env_vars.items()]
            
            container = V1Container(
                name=name,
                image=image,
                image_pull_policy=image_pull_policy,
                ports=container_ports if container_ports else None,
                env=env if env else None
            )
            
            # Build pod template
            pod_template = V1PodTemplateSpec(
                metadata=V1ObjectMeta(labels=labels),
                spec=V1PodSpec(containers=[container])
            )
            
            # Build deployment spec
            deployment_spec = V1DeploymentSpec(
                replicas=replicas,
                selector=V1LabelSelector(match_labels={"app": name}),
                template=pod_template
            )
            
            # Build deployment
            deployment = V1Deployment(
                api_version="apps/v1",
                kind="Deployment",
                metadata=V1ObjectMeta(
                    name=name,
                    namespace=namespace,
                    labels=labels
                ),
                spec=deployment_spec
            )
            
            # Create deployment
            result = await apps_v1.create_namespaced_deployment(
                namespace=namespace,
                body=deployment
            )
            logger.info(f"Created deployment {name} in namespace {namespace}")
            
            # Create Service if port is specified
            if port:
                try:
                    service_spec = V1ServiceSpec(
                        selector={"app": name},
                        ports=[V1ServicePort(port=port, target_port=port)],
                        type=service_type
                    )
                    
                    service = V1Service(
                        metadata=V1ObjectMeta(
                            name=name,
                            namespace=namespace,
                            labels=labels
                        ),
                        spec=service_spec
                    )
                    
                    await core_v1.create_namespaced_service(
                        namespace=namespace,
                        body=service
                    )
                    logger.info(f"Created service {name} in namespace {namespace}")
                except ApiException as e:
                    if e.status != 409: # Ignore if already exists
                        logger.error(f"Failed to create service {name}: {e}")
                        # We don't raise here to allow deployment creation to succeed even if service fails
            
            return result
            
        except ApiException as e:
            logger.error(f"Failed to create deployment {name}: {e}")
            raise
    
    async def get_deployment(self, namespace: str, name: str) -> Optional[V1Deployment]:
        """
        Get a Kubernetes deployment
        
        Args:
            namespace: Namespace of the deployment
            name: Deployment name
        
        Returns:
            V1Deployment object if found, None otherwise
        """
        try:
            apps_v1 = k8s_client.get_apps_v1_api()
            deployment = await apps_v1.read_namespaced_deployment(
                name=name,
                namespace=namespace
            )
            return deployment
            
        except ApiException as e:
            if e.status == 404:
                return None
            logger.error(f"Failed to get deployment {name}: {e}")
            raise
    
    async def list_deployments(self, namespace: str) -> List[V1Deployment]:
        """
        List all deployments in a namespace
        
        Args:
            namespace: Namespace to list deployments from
        
        Returns:
            List of V1Deployment objects
        """
        try:
            apps_v1 = k8s_client.get_apps_v1_api()
            result = await apps_v1.list_namespaced_deployment(namespace=namespace)
            return result.items
            
        except ApiException as e:
            logger.error(f"Failed to list deployments in {namespace}: {e}")
            raise
    
    async def delete_deployment(self, namespace: str, name: str) -> bool:
        """
        Delete a Kubernetes deployment
        
        Args:
            namespace: Namespace of the deployment
            name: Deployment name
        
        Returns:
            True if deleted successfully, False if not found
        
        Raises:
            ApiException: If K8s API call fails
        """
        try:
            apps_v1 = k8s_client.get_apps_v1_api()
            await apps_v1.delete_namespaced_deployment(
                name=name,
                namespace=namespace
            )
            logger.info(f"Deleted deployment {name} from namespace {namespace}")
            return True
            
        except ApiException as e:
            if e.status == 404:
                logger.warning(f"Deployment {name} not found in {namespace}")
                return False
            logger.error(f"Failed to delete deployment {name}: {e}")
            raise
    
    async def scale_deployment(
        self,
        namespace: str,
        name: str,
        replicas: int
    ) -> V1Deployment:
        """
        Scale a deployment to a specific number of replicas
        
        Args:
            namespace: Namespace of the deployment
            name: Deployment name
            replicas: Desired number of replicas
        
        Returns:
            Updated V1Deployment object
        
        Raises:
            ApiException: If K8s API call fails
        """
        try:
            apps_v1 = k8s_client.get_apps_v1_api()
            
            # Get current deployment
            deployment = await apps_v1.read_namespaced_deployment(
                name=name,
                namespace=namespace
            )
            
            # Update replicas
            deployment.spec.replicas = replicas
            
            # Patch deployment
            result = await apps_v1.patch_namespaced_deployment(
                name=name,
                namespace=namespace,
                body=deployment
            )
            logger.info(f"Scaled deployment {name} to {replicas} replicas")
            return result
            
        except ApiException as e:
            logger.error(f"Failed to scale deployment {name}: {e}")
            raise
    
    async def get_deployment_status(self, namespace: str, name: str) -> Dict:
        """
        Get deployment status information
        
        Args:
            namespace: Namespace of the deployment
            name: Deployment name
        
        Returns:
            Dict with status information
        """
        try:
            deployment = await self.get_deployment(namespace, name)
            if not deployment:
                return None
            
            status = deployment.status
            return {
                "name": deployment.metadata.name,
                "namespace": deployment.metadata.namespace,
                "replicas": deployment.spec.replicas,
                "ready_replicas": status.ready_replicas or 0,
                "available_replicas": status.available_replicas or 0,
                "unavailable_replicas": status.unavailable_replicas or 0,
                "updated_replicas": status.updated_replicas or 0,
                "image": deployment.spec.template.spec.containers[0].image,
                "created_at": deployment.metadata.creation_timestamp,
                "labels": deployment.metadata.labels
            }
            
        except ApiException as e:
            logger.error(f"Failed to get deployment status {name}: {e}")
            raise

deployment_service = DeploymentService()
