"""Utility functions for building manifests for k8s pods."""

from typing import Any, Dict, List

from zenml.constants import ENV_ZENML_ENABLE_REPO_INIT_WARNINGS


def build_base_pod_manifest(
    run_name: str, pipeline_name: str, image_name: str
) -> Dict[str, Any]:
    """Build a basic k8s pod manifest.

    This includes only the data that stays the same for each step manifest.
    To add in the step-specific data, use `update_pod_manifest()` after.

    Args:
        run_name (str): Name of the ZenML run.
        pipeline_name (str): Name of the ZenML pipeline.
        image_name (str): Name of the Docker image.

    Returns:
        Dict[str, Any]: Base pod manifest.
    """
    return {
        "apiVersion": "v1",
        "kind": "Pod",
        "metadata": {
            "name": None,  # to be set in update_pod_manifest
            "labels": {
                "run": run_name,
                "pipeline": pipeline_name,
            },
        },
        "spec": {
            "restartPolicy": "Never",
            "containers": [
                {
                    "name": "main",
                    "image": image_name,
                    "command": None,  # to be set in update_pod_manifest
                    "args": None,  # to be set in update_pod_manifest
                    "env": [
                        {
                            "name": ENV_ZENML_ENABLE_REPO_INIT_WARNINGS,
                            "value": "False",
                        }
                    ],
                }
            ],
        },
    }


def update_pod_manifest(
    base_pod_manifest: Dict[str, Any],
    pod_name: str,
    command: List[str],
    args: List[str],
) -> Dict[str, Any]:
    """Add step-specific arguments to a k8s pod manifest.

    Args:
        base_pod_manifest (Dict[str, Any]): General pod manifest created by
            `build_base_pod_manifest()`.
        pod_name (str): Name of the pod.
        command (List[str]): Command to execute the entrypoint in the pod.
        args (List[str]): Arguments provided to the entrypoint command.

    Returns:
        Dict[str, Any]: Updated pod manifest.
    """
    pod_manifest = base_pod_manifest.copy()
    pod_manifest["metadata"]["name"] = pod_name
    pod_manifest["spec"]["containers"][0]["command"] = command
    pod_manifest["spec"]["containers"][0]["args"] = args
    return pod_manifest


def build_persistent_volume_claim_manifest(
    name: str,
    namespace: str = "default",
    storage_request: str = "10Gi",
) -> Dict[str, Any]:
    """Build a manifest for a persistent volume claim.

    Args:
        name: Name of the persistent volume claim.
        namespace: Kubernetes namespace. Defaults to "default".
        storage_request: Size of the storage to request. Defaults to `"10Gi"`.

    Returns:
        Manifest for a persistent volume claim.
    """
    return {
        "apiVersion": "v1",
        "kind": "PersistentVolumeClaim",
        "metadata": {
            "name": name,
            "namespace": namespace,
        },
        "spec": {
            "storageClassName": "manual",
            "accessModes": ["ReadWriteOnce"],
            "resources": {
                "requests": {
                    "storage": storage_request,
                }
            },
        },
    }


def build_persistent_volume_manifest(
    name: str,
    namespace: str = "default",
    storage_capacity: str = "10Gi",
    path: str = "/mnt/data",
) -> Dict[str, Any]:
    """Build a manifest for a persistent volume.

    Args:
        name: Name of the persistent volume.
        namespace: Kubernetes namespace. Defaults to "default".
        storage_capacity: Storage capacity of the volume. Defaults to `"10Gi"`.
        path: Path where the volume is mounted. Defaults to `"/mnt/data"`.

    Returns:
        Manifest for a persistent volume.
    """
    return {
        "apiVersion": "v1",
        "kind": "PersistentVolume",
        "metadata": {
            "name": name,
            "namespace": namespace,
            "labels": {"type": "local"},
        },
        "spec": {
            "storageClassName": "manual",
            "capacity": {"storage": storage_capacity},
            "accessModes": ["ReadWriteOnce"],
            "hostPath": {"path": path},
        },
    }


def build_mysql_deployment_manifest(
    name: str = "mysql",
    namespace: str = "default",
    port: int = 3306,
    pv_claim_name: str = "mysql-pv-claim",
) -> Dict[str, Any]:
    """Build a manifest for deploying a MySQL database.

    Args:
        name: Name of the deployment. Defaults to "mysql".
        namespace: Kubernetes namespace. Defaults to "default".
        port: Port where MySQL is running. Defaults to 3306.
        pv_claim_name: Name of the required persistent volume claim.
            Defaults to `"mysql-pv-claim"`.

    Returns:
        Manifest for deploying a MySQL database.
    """
    return {
        "apiVersion": "apps/v1",
        "kind": "Deployment",
        "metadata": {"name": name, "namespace": namespace},
        "spec": {
            "selector": {
                "matchLabels": {
                    "app": name,
                },
            },
            "strategy": {
                "type": "Recreate",
            },
            "template": {
                "metadata": {
                    "labels": {"app": name},
                },
                "spec": {
                    "containers": [
                        {
                            "image": "gcr.io/ml-pipeline/mysql:5.6",
                            "name": name,
                            "env": [
                                {
                                    "name": "MYSQL_ALLOW_EMPTY_PASSWORD",
                                    "value": '"true"',
                                }
                            ],
                            "ports": [{"containerPort": port, "name": name}],
                            "volumeMounts": [
                                {
                                    "name": "mysql-persistent-storage",
                                    "mountPath": "/var/lib/mysql",
                                }
                            ],
                        }
                    ],
                    "volumes": [
                        {
                            "name": "mysql-persistent-storage",
                            "persistentVolumeClaim": {
                                "claimName": pv_claim_name
                            },
                        }
                    ],
                },
            },
        },
    }


def build_mysql_service_manifest(
    name: str = "mysql",
    namespace: str = "default",
    port: int = 3306,
) -> Dict[str, Any]:
    """Build a manifest for a service relating to a deployed MySQL database.

    Args:
        name: Name of the service. Defaults to "mysql".
        namespace: Kubernetes namespace. Defaults to "default".
        port: Port where MySQL is running. Defaults to 3306.

    Returns:
        Manifest for the MySQL service.
    """
    return {
        "apiVersion": "v1",
        "kind": "Service",
        "metadata": {
            "name": name,
            "namespace": namespace,
        },
        "spec": {
            "selector": {"app": "mysql"},
            "clusterIP": "None",
            "ports": [{"port": port}],
        },
    }


def build_cluster_role_binding_manifest_for_service_account(
    name: str,
    role_name: str,
    service_account_name: str,
    namespace: str = "default",
) -> Dict[str, Any]:
    """Build a manifest for a cluster role binding of a service account.

    Args:
        name: Name of the cluster role binding.
        role_name: Name of the role.
        service_account_name: Name of the service account.
        namespace: Kubernetes namespace. Defaults to "default".

    Returns:
        Manifest for a cluster role binding of a service account.
    """
    return {
        "apiVersion": "rbac.authorization.k8s.io/v1",
        "kind": "ClusterRoleBinding",
        "metadata": {"name": name},
        "subjects": [
            {
                "kind": "ServiceAccount",
                "name": service_account_name,
                "namespace": namespace,
            }
        ],
        "roleRef": {
            "kind": "ClusterRole",
            "name": role_name,
            "apiGroup": "rbac.authorization.k8s.io",
        },
    }


def build_service_account_manifest(
    name: str, namespace: str = "default"
) -> Dict[str, Any]:
    """Build the manifest for a service account.

    Args:
        name: Name of the service account.
        namespace: Kubernetes namespace. Defaults to "default".

    Returns:
        Manifest for a service account.
    """
    return {
        "apiVersion": "v1",
        "metadata": {
            "name": name,
            "namespace": namespace,
        },
    }


def build_namespace_manifest(namespace: str) -> Dict[str, Any]:
    """Build the manifest for a new namespace.

    Args:
        namespace: Kubernetes namespace.

    Returns:
        Manifest of the new namespace.
    """
    return {
        "apiVersion": "v1",
        "kind": "Namespace",
        "metadata": {
            "name": namespace,
        },
    }
