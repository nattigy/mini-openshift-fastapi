"""
Kubernetes Ingress management service.
Handles domain routing with automatic HTTPS via cert-manager.
"""
from kubernetes_asyncio import client
from kubernetes_asyncio.client.rest import ApiException
from typing import Optional
import logging

from app.services.k8s_client import k8s_client

logger = logging.getLogger(__name__)


class IngressService:
    """Service for managing Kubernetes Ingress resources"""

    async def create_ingress(
        self,
        namespace: str,
        name: str,
        host: str,
        service_name: str,
        service_port: int,
    ) -> None:
        """
        Create a Kubernetes Ingress resource with automatic HTTPS.
        
        Args:
            namespace: Kubernetes namespace
            name: Deployment name (used for ingress name)
            host: Full domain name (e.g., admin.clienta.com or clienta.com)
            service_name: Name of the Kubernetes service to route to
            service_port: Port of the service
            
        The Ingress will:
        - Route traffic from the domain to the service
        - Request automatic SSL certificate from Let's Encrypt via cert-manager
        - Redirect HTTP to HTTPS
        """
        try:
            ingress_name = f"{name}-ingress"
            
            # Create Ingress manifest
            ingress = client.V1Ingress(
                api_version="networking.k8s.io/v1",
                kind="Ingress",
                metadata=client.V1ObjectMeta(
                    name=ingress_name,
                    namespace=namespace,
                    annotations={
                        # cert-manager will automatically create SSL certificate
                        "cert-manager.io/cluster-issuer": "letsencrypt-prod",
                        # Redirect HTTP to HTTPS
                        "nginx.ingress.kubernetes.io/ssl-redirect": "true",
                        # Force SSL
                        "nginx.ingress.kubernetes.io/force-ssl-redirect": "true",
                    },
                    labels={
                        "app": name,
                        "managed-by": "mini-openshift",
                    }
                ),
                spec=client.V1IngressSpec(
                    ingress_class_name="nginx",
                    tls=[
                        client.V1IngressTLS(
                            hosts=[host],
                            secret_name=f"{name}-tls"  # cert-manager will create this secret
                        )
                    ],
                    rules=[
                        client.V1IngressRule(
                            host=host,
                            http=client.V1HTTPIngressRuleValue(
                                paths=[
                                    client.V1HTTPIngressPath(
                                        path="/",
                                        path_type="Prefix",
                                        backend=client.V1IngressBackend(
                                            service=client.V1IngressServiceBackend(
                                                name=service_name,
                                                port=client.V1ServiceBackendPort(
                                                    number=service_port
                                                )
                                            )
                                        )
                                    )
                                ]
                            )
                        )
                    ]
                )
            )

            # Create the Ingress
            networking_api = client.NetworkingV1Api(k8s_client._api_client)
            await networking_api.create_namespaced_ingress(
                namespace=namespace,
                body=ingress
            )
            
            logger.info(f"Created Ingress '{ingress_name}' for host '{host}' in namespace '{namespace}'")
            
        except ApiException as e:
            logger.error(f"Failed to create Ingress: {e}")
            raise Exception(f"Failed to create Ingress for {host}: {e.reason}")
        except Exception as e:
            logger.error(f"Unexpected error creating Ingress: {e}")
            raise

    async def delete_ingress(
        self,
        namespace: str,
        name: str,
    ) -> None:
        """
        Delete a Kubernetes Ingress resource.
        
        Args:
            namespace: Kubernetes namespace
            name: Deployment name (ingress name is derived from this)
        """
        try:
            ingress_name = f"{name}-ingress"
            
            networking_api = client.NetworkingV1Api(k8s_client._api_client)
            await networking_api.delete_namespaced_ingress(
                name=ingress_name,
                namespace=namespace,
                body=client.V1DeleteOptions(
                    propagation_policy='Foreground'
                )
            )
            
            logger.info(f"Deleted Ingress '{ingress_name}' from namespace '{namespace}'")
            
        except ApiException as e:
            if e.status == 404:
                logger.warning(f"Ingress '{name}-ingress' not found in namespace '{namespace}'")
            else:
                logger.error(f"Failed to delete Ingress: {e}")
                raise Exception(f"Failed to delete Ingress: {e.reason}")
        except Exception as e:
            logger.error(f"Unexpected error deleting Ingress: {e}")
            raise

    async def get_ingress(
        self,
        namespace: str,
        name: str,
    ) -> Optional[client.V1Ingress]:
        """
        Get a Kubernetes Ingress resource.
        
        Args:
            namespace: Kubernetes namespace
            name: Deployment name (ingress name is derived from this)
            
        Returns:
            V1Ingress object or None if not found
        """
        try:
            ingress_name = f"{name}-ingress"
            
            networking_api = client.NetworkingV1Api(k8s_client._api_client)
            ingress = await networking_api.read_namespaced_ingress(
                name=ingress_name,
                namespace=namespace
            )
            
            return ingress
            
        except ApiException as e:
            if e.status == 404:
                logger.debug(f"Ingress '{name}-ingress' not found in namespace '{namespace}'")
                return None
            else:
                logger.error(f"Failed to get Ingress: {e}")
                raise Exception(f"Failed to get Ingress: {e.reason}")
        except Exception as e:
            logger.error(f"Unexpected error getting Ingress: {e}")
            raise

    async def list_ingresses(
        self,
        namespace: str,
        label_selector: Optional[str] = None
    ) -> list:
        """
        List all Ingress resources in a namespace.
        
        Args:
            namespace: Kubernetes namespace
            label_selector: Optional label selector (e.g., "app=myapp")
            
        Returns:
            List of V1Ingress objects
        """
        try:
            networking_api = client.NetworkingV1Api(k8s_client._api_client)
            ingresses = await networking_api.list_namespaced_ingress(
                namespace=namespace,
                label_selector=label_selector
            )
            
            return ingresses.items
            
        except ApiException as e:
            logger.error(f"Failed to list Ingresses: {e}")
            raise Exception(f"Failed to list Ingresses: {e.reason}")
        except Exception as e:
            logger.error(f"Unexpected error listing Ingresses: {e}")
            raise


# Singleton instance
ingress_service = IngressService()
