from kubernetes_asyncio.client import (
    V1Deployment, V1DeploymentSpec, V1PodTemplateSpec, V1ObjectMeta,
    V1PodSpec, V1Container, V1ContainerPort, V1EnvVar, V1LabelSelector,
    V1Service, V1ServiceSpec, V1ServicePort,
    ApiException
)
from typing import Optional, List, Dict
import logging
from app.services.k8s_client import k8s_client
from app.services.k8s_ingress import ingress_service

logger = logging.getLogger(__name__)

class DeploymentService:
    """Service for managing Kubernetes deployments"""
    
    def _build_domain(
        self, 
        project_domain: str, 
        environment_prefix: str, 
        subdomain: str
    ) -> str:
        """
        Build full domain from components.
        
        Examples:
            _build_domain("clienta.com", "", "admin") → "admin.clienta.com"
            _build_domain("clienta.com", "uat", "admin") → "admin.uat.clienta.com"
            _build_domain("clienta.com", "", "") → "clienta.com"
            _build_domain("clienta.com", "uat", "") → "uat.clienta.com"
        """
        parts = []
        
        if subdomain:
            parts.append(subdomain)
        
        if environment_prefix:
            parts.append(environment_prefix)
        
        parts.append(project_domain)
        
        return ".".join(parts)
    
    async def create_deployment(
        self,
        namespace: str,
        name: str,
        image: str,
        replicas: int = 1,
        # container_port arg is deprecated/ignored, we hardcode to 3000
        container_port: int = 3000, 
        image_pull_policy: str = "IfNotPresent",
        project_domain: Optional[str] = None,
        environment_prefix: str = "",
        subdomain: str = "",
        env_vars: Optional[Dict[str, str]] = None,
        labels: Optional[Dict[str, str]] = None
    ) -> V1Deployment:
        """
        Create a Kubernetes deployment with ClusterIP service and Ingress.
        Service Port: 80 (HTTP) -> Container Port: 3000
        """
        # HARDCODED PORTS per user request
        CONTAINER_PORT = 3000
        SERVICE_PORT = 80

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
            container_ports = [V1ContainerPort(container_port=CONTAINER_PORT)]
            
            # Build environment variables
            env = []
            if env_vars:
                env = [V1EnvVar(name=k, value=v) for k, v in env_vars.items()]
            
            container = V1Container(
                name=name,
                image=image,
                image_pull_policy=image_pull_policy,
                ports=container_ports,
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
            
            # Step 1: Create deployment
            result = await apps_v1.create_namespaced_deployment(
                namespace=namespace,
                body=deployment
            )
            logger.info(f"Created deployment {name} in namespace {namespace}")
            
            # Step 2: Create ClusterIP Service (always)
            try:
                service_spec = V1ServiceSpec(
                    selector={"app": name},
                    ports=[V1ServicePort(port=SERVICE_PORT, target_port=CONTAINER_PORT)],
                    type="ClusterIP"
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
                logger.info(f"Created ClusterIP service {name} in namespace {namespace} (80->3000)")
            except ApiException as e:
                if e.status != 409:  # Ignore if already exists
                    logger.error(f"Failed to create service {name}: {e}")
                    raise
            
            # Step 3: Create Ingress if domain is provided
            if project_domain:
                try:
                    full_domain = self._build_domain(project_domain, environment_prefix, subdomain)
                    
                    await ingress_service.create_ingress(
                        namespace=namespace,
                        name=name,
                        host=full_domain,
                        service_name=name,
                        service_port=SERVICE_PORT
                    )
                    logger.info(f"Created Ingress for {full_domain}")
                except Exception as e:
                    logger.error(f"Failed to create Ingress: {e}")
                    # Don't raise - deployment and service are created successfully
            
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
        Delete a Kubernetes deployment along with its Service and Ingress.
        
        Args:
            namespace: Namespace of the deployment
            name: Deployment name
        
        Returns:
            True if deleted successfully, False if not found
        
        Raises:
            ApiException: If K8s API call fails
        """
        deployment_deleted = False
        
        try:
            # Step 1: Delete Deployment
            apps_v1 = k8s_client.get_apps_v1_api()
            await apps_v1.delete_namespaced_deployment(
                name=name,
                namespace=namespace
            )
            logger.info(f"Deleted deployment {name} from namespace {namespace}")
            deployment_deleted = True
            
        except ApiException as e:
            if e.status == 404:
                logger.warning(f"Deployment {name} not found in {namespace}")
            else:
                logger.error(f"Failed to delete deployment {name}: {e}")
                raise
        
        # Step 2: Delete Service
        try:
            core_v1 = k8s_client.get_core_v1_api()
            await core_v1.delete_namespaced_service(
                name=name,
                namespace=namespace
            )
            logger.info(f"Deleted service {name} from namespace {namespace}")
        except ApiException as e:
            if e.status != 404:
                logger.warning(f"Failed to delete service {name}: {e}")
        
        # Step 3: Delete Ingress
        try:
            await ingress_service.delete_ingress(
                namespace=namespace,
                name=name
            )
            logger.info(f"Deleted ingress for {name}")
        except Exception as e:
            logger.warning(f"Failed to delete ingress for {name}: {e}")
        
        return deployment_deleted
    
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
