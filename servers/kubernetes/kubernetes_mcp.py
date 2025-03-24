#!/usr/bin/env python3
"""
Kubernetes MCP Server

This server implements the Model Context Protocol (MCP) for Kubernetes,
allowing LLMs like Claude to interact with your Kubernetes clusters.
"""

import os
import json
import yaml
import tempfile
import asyncio
import logging
import subprocess
from typing import Dict, List, Optional, Any, Union, Tuple
from kubernetes import client, config, watch
from kubernetes.client.rest import ApiException
from mcp.server.fastmcp import FastMCP, Context

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# Initialize the MCP server
mcp = FastMCP("kubernetes-mcp")

# Load Kubernetes configuration
try:
    config.load_kube_config()
    logger.info("Loaded Kubernetes configuration from kubeconfig")
except Exception:
    try:
        config.load_incluster_config()
        logger.info("Loaded in-cluster Kubernetes configuration")
    except Exception as e:
        logger.error(f"Failed to load Kubernetes config: {e}")
        raise

# Initialize Kubernetes API clients
core_v1_api = client.CoreV1Api()
apps_v1_api = client.AppsV1Api()
batch_v1_api = client.BatchV1Api()
rbac_v1_api = client.RbacAuthorizationV1Api()
storage_v1_api = client.StorageV1Api()
networking_v1_api = client.NetworkingV1Api()
apiextensions_v1_api = client.ApiextensionsV1Api()
custom_objects_api = client.CustomObjectsApi()

# State management
# Using a simple dict for now, could be enhanced with a proper database
state = {
    "current_namespace": "default",
    "port_forwards": {},
}

# Helper functions
def format_resource(resource: Dict[str, Any], kind: str) -> Dict[str, Any]:
    """Format Kubernetes resource into a consistent structure."""
    try:
        metadata = resource.get("metadata", {})
        status = resource.get("status", {})
        
        return {
            "name": metadata.get("name", "unknown"),
            "namespace": metadata.get("namespace", "default"),
            "kind": kind,
            "creationTimestamp": metadata.get("creationTimestamp", "unknown"),
            "status": get_status(resource, kind),
            "labels": metadata.get("labels", {}),
            "annotations": metadata.get("annotations", {}),
        }
    except Exception as e:
        logger.error(f"Error formatting {kind}: {e}")
        return {"name": "error", "error": str(e)}

def get_status(resource: Dict[str, Any], kind: str) -> str:
    """Get the appropriate status based on resource kind."""
    try:
        if kind == "Pod":
            return resource.get("status", {}).get("phase", "Unknown")
        elif kind == "Deployment":
            status = resource.get("status", {})
            ready = status.get("readyReplicas", 0)
            total = status.get("replicas", 0)
            return f"{ready}/{total} ready"
        elif kind == "Service":
            return resource.get("spec", {}).get("type", "ClusterIP")
        elif kind == "Node":
            conditions = resource.get("status", {}).get("conditions", [])
            ready_condition = next((c for c in conditions if c.get("type") == "Ready"), {})
            return "Ready" if ready_condition.get("status") == "True" else "NotReady"
        else:
            return "Available" if resource.get("status") else "Unknown"
    except Exception as e:
        logger.error(f"Error getting status for {kind}: {e}")
        return "Error"

async def run_kubectl(args: str) -> Tuple[str, str]:
    """Run a kubectl command and return stdout, stderr."""
    cmd = f"kubectl {args}"
    logger.info(f"Executing: {cmd}")
    
    process = await asyncio.create_subprocess_shell(
        cmd,
        stdout=asyncio.subprocess.PIPE,
        stderr=asyncio.subprocess.PIPE
    )
    
    stdout, stderr = await process.communicate()
    
    return stdout.decode(), stderr.decode()

async def run_helm(args: str) -> Tuple[str, str]:
    """Run a helm command and return stdout, stderr."""
    cmd = f"helm {args}"
    logger.info(f"Executing: {cmd}")
    
    process = await asyncio.create_subprocess_shell(
        cmd,
        stdout=asyncio.subprocess.PIPE,
        stderr=asyncio.subprocess.PIPE
    )
    
    stdout, stderr = await process.communicate()
    
    return stdout.decode(), stderr.decode()

def dict_to_yaml(data: Dict[str, Any]) -> str:
    """Convert a dictionary to YAML string."""
    return yaml.dump(data, default_flow_style=False)

def yaml_to_dict(data: str) -> Dict[str, Any]:
    """Convert a YAML string to dictionary."""
    return yaml.safe_load(data)

# MCP Tool implementations

@mcp.tool()
async def choose_namespace(namespace: str) -> str:
    """Set the default namespace for subsequent commands.
    
    Args:
        namespace: Name of the namespace to use
    """
    try:
        # Verify the namespace exists
        core_v1_api.read_namespace(namespace)
        state["current_namespace"] = namespace
        return f"Successfully set the current namespace to {namespace}"
    except ApiException as e:
        if e.status == 404:
            return f"Namespace {namespace} not found. Please create it first or check the name."
        return f"Error setting namespace: {str(e)}"
    except Exception as e:
        return f"Unexpected error: {str(e)}"

@mcp.tool()
async def list_namespaces() -> str:
    """List all namespaces in the cluster."""
    try:
        namespaces = core_v1_api.list_namespace()
        
        result = ["NAMESPACE\tSTATUS\tAGE"]
        for ns in namespaces.items:
            metadata = ns.metadata
            status = ns.status.phase
            age = metadata.creation_timestamp.strftime("%Y-%m-%d %H:%M:%S")
            result.append(f"{metadata.name}\t{status}\t{age}")
        
        return "\n".join(result)
    except ApiException as e:
        return f"Error listing namespaces: {str(e)}"
    except Exception as e:
        return f"Unexpected error: {str(e)}"

@mcp.tool()
async def list_pods(namespace: Optional[str] = None, label_selector: Optional[str] = None) -> str:
    """List all pods in a namespace.
    
    Args:
        namespace: Namespace to list pods from (uses current namespace if not specified)
        label_selector: Label selector to filter pods (e.g. "app=nginx")
    """
    try:
        ns = namespace or state["current_namespace"]
        pods = core_v1_api.list_namespaced_pod(
            namespace=ns, 
            label_selector=label_selector
        )
        
        result = ["NAME\tREADY\tSTATUS\tRESTARTS\tAGE\tNODE"]
        for pod in pods.items:
            metadata = pod.metadata
            status = pod.status
            
            ready_containers = 0
            total_containers = 0
            restarts = 0
            
            if status.container_statuses:
                total_containers = len(status.container_statuses)
                ready_containers = sum(1 for c in status.container_statuses if c.ready)
                restarts = sum(c.restart_count for c in status.container_statuses)
                
            age = metadata.creation_timestamp.strftime("%Y-%m-%d %H:%M:%S")
            node = status.host_ip or "N/A"
            
            result.append(
                f"{metadata.name}\t{ready_containers}/{total_containers}\t{status.phase}\t{restarts}\t{age}\t{node}"
            )
        
        if not pods.items:
            return f"No pods found in namespace {ns}"
            
        return "\n".join(result)
    except ApiException as e:
        return f"Error listing pods: {str(e)}"
    except Exception as e:
        return f"Unexpected error: {str(e)}"

@mcp.tool()
async def list_services(namespace: Optional[str] = None) -> str:
    """List all services in a namespace.
    
    Args:
        namespace: Namespace to list services from (uses current namespace if not specified)
    """
    try:
        ns = namespace or state["current_namespace"]
        services = core_v1_api.list_namespaced_service(namespace=ns)
        
        result = ["NAME\tTYPE\tCLUSTER-IP\tEXTERNAL-IP\tPORT(S)\tAGE"]
        for svc in services.items:
            metadata = svc.metadata
            spec = svc.spec
            
            ports = []
            for port in spec.ports:
                port_str = f"{port.port}"
                if port.target_port:
                    port_str += f":{port.target_port}"
                if port.node_port:
                    port_str += f":{port.node_port}"
                port_str += f"/{port.protocol}"
                ports.append(port_str)
                
            age = metadata.creation_timestamp.strftime("%Y-%m-%d %H:%M:%S")
            external_ip = "none" if not spec.external_i_ps else ",".join(spec.external_i_ps)
            
            result.append(
                f"{metadata.name}\t{spec.type}\t{spec.cluster_ip}\t{external_ip}\t{','.join(ports)}\t{age}"
            )
        
        if not services.items:
            return f"No services found in namespace {ns}"
            
        return "\n".join(result)
    except ApiException as e:
        return f"Error listing services: {str(e)}"
    except Exception as e:
        return f"Unexpected error: {str(e)}"

@mcp.tool()
async def list_deployments(namespace: Optional[str] = None) -> str:
    """List all deployments in a namespace.
    
    Args:
        namespace: Namespace to list deployments from (uses current namespace if not specified)
    """
    try:
        ns = namespace or state["current_namespace"]
        deployments = apps_v1_api.list_namespaced_deployment(namespace=ns)
        
        result = ["NAME\tREADY\tUP-TO-DATE\tAVAILABLE\tAGE"]
        for deploy in deployments.items:
            metadata = deploy.metadata
            spec = deploy.spec
            status = deploy.status
            
            ready = f"{status.ready_replicas or 0}/{spec.replicas}"
            up_to_date = status.updated_replicas or 0
            available = status.available_replicas or 0
            age = metadata.creation_timestamp.strftime("%Y-%m-%d %H:%M:%S")
            
            result.append(
                f"{metadata.name}\t{ready}\t{up_to_date}\t{available}\t{age}"
            )
        
        if not deployments.items:
            return f"No deployments found in namespace {ns}"
            
        return "\n".join(result)
    except ApiException as e:
        return f"Error listing deployments: {str(e)}"
    except Exception as e:
        return f"Unexpected error: {str(e)}"

@mcp.tool()
async def list_nodes() -> str:
    """List all nodes in the cluster."""
    try:
        nodes = core_v1_api.list_node()
        
        result = ["NAME\tSTATUS\tROLES\tAGE\tVERSION"]
        for node in nodes.items:
            metadata = node.metadata
            status = node.status
            
            # Determine node status
            conditions = status.conditions
            node_status = "Unknown"
            for condition in conditions:
                if condition.type == "Ready":
                    node_status = "Ready" if condition.status == "True" else "NotReady"
                    break
            
            # Get node roles
            roles = []
            for label, value in metadata.labels.items():
                if label.startswith("node-role.kubernetes.io/"):
                    role = label.split("/")[1]
                    roles.append(role)
            roles_str = ",".join(roles) if roles else "<none>"
            
            age = metadata.creation_timestamp.strftime("%Y-%m-%d %H:%M:%S")
            version = status.node_info.kubelet_version
            
            result.append(
                f"{metadata.name}\t{node_status}\t{roles_str}\t{age}\t{version}"
            )
        
        return "\n".join(result)
    except ApiException as e:
        return f"Error listing nodes: {str(e)}"
    except Exception as e:
        return f"Unexpected error: {str(e)}"

@mcp.tool()
async def create_pod(manifest: str, namespace: Optional[str] = None) -> str:
    """Create a pod from YAML manifest.
    
    Args:
        manifest: YAML manifest defining the pod
        namespace: Namespace to create the pod in (uses current namespace if not specified)
    """
    try:
        ns = namespace or state["current_namespace"]
        
        # Parse the manifest
        pod_dict = yaml.safe_load(manifest)
        
        # Ensure namespace is set
        if not pod_dict.get("metadata"):
            pod_dict["metadata"] = {}
        pod_dict["metadata"]["namespace"] = ns
        
        # Create the pod
        api_version = pod_dict.get("apiVersion", "v1")
        kind = pod_dict.get("kind", "Pod")
        
        if api_version != "v1" or kind != "Pod":
            return f"Expected a Pod resource with apiVersion: v1, but got {api_version}/{kind}"
        
        core_v1_api.create_namespaced_pod(
            namespace=ns,
            body=pod_dict
        )
        
        pod_name = pod_dict["metadata"]["name"]
        return f"Pod {pod_name} created successfully in namespace {ns}"
    except ApiException as e:
        return f"Error creating pod: {str(e)}"
    except yaml.YAMLError as e:
        return f"Error parsing YAML manifest: {str(e)}"
    except Exception as e:
        return f"Unexpected error: {str(e)}"

@mcp.tool()
async def delete_pod(name: str, namespace: Optional[str] = None) -> str:
    """Delete a pod.
    
    Args:
        name: Name of the pod to delete
        namespace: Namespace of the pod (uses current namespace if not specified)
    """
    try:
        ns = namespace or state["current_namespace"]
        core_v1_api.delete_namespaced_pod(name=name, namespace=ns)
        return f"Pod {name} deleted successfully from namespace {ns}"
    except ApiException as e:
        if e.status == 404:
            return f"Pod {name} not found in namespace {ns}"
        return f"Error deleting pod: {str(e)}"
    except Exception as e:
        return f"Unexpected error: {str(e)}"

@mcp.tool()
async def describe_pod(name: str, namespace: Optional[str] = None) -> str:
    """Describe a pod, showing detailed information.
    
    Args:
        name: Name of the pod to describe
        namespace: Namespace of the pod (uses current namespace if not specified)
    """
    try:
        ns = namespace or state["current_namespace"]
        pod = core_v1_api.read_namespaced_pod(name=name, namespace=ns)
        
        # Convert to dict for easier manipulation
        pod_dict = client.ApiClient().sanitize_for_serialization(pod)
        
        # Format the output similar to kubectl describe
        result = []
        result.append(f"Name:         {pod_dict['metadata']['name']}")
        result.append(f"Namespace:    {pod_dict['metadata']['namespace']}")
        
        # Basic metadata
        if 'labels' in pod_dict['metadata']:
            result.append("Labels:       " + ", ".join([f"{k}={v}" for k, v in pod_dict['metadata']['labels'].items()]))
        
        if 'annotations' in pod_dict['metadata']:
            result.append("Annotations:  " + ", ".join([f"{k}={v}" for k, v in pod_dict['metadata']['annotations'].items()]))
        
        result.append(f"Status:       {pod_dict['status']['phase']}")
        
        # IP and node information
        result.append(f"IP:           {pod_dict['status'].get('pod_ip', 'N/A')}")
        result.append(f"Node:         {pod_dict['spec'].get('node_name', 'N/A')}")
        result.append(f"Start Time:   {pod_dict['metadata'].get('creation_timestamp', 'N/A')}")
        
        # Containers
        result.append("\nContainers:")
        for container in pod_dict['spec']['containers']:
            result.append(f"  {container['name']}:")
            result.append(f"    Image:       {container['image']}")
            
            if 'resources' in container:
                resources = container['resources']
                if 'requests' in resources:
                    requests = resources['requests']
                    result.append(f"    Requests:    CPU: {requests.get('cpu', 'N/A')}, Memory: {requests.get('memory', 'N/A')}")
                
                if 'limits' in resources:
                    limits = resources['limits']
                    result.append(f"    Limits:      CPU: {limits.get('cpu', 'N/A')}, Memory: {limits.get('memory', 'N/A')}")
            
            if 'ports' in container:
                for port in container['ports']:
                    result.append(f"    Port:        {port.get('container_port', 'N/A')}/{port.get('protocol', 'TCP')}")
        
        # Container statuses
        if 'container_statuses' in pod_dict['status']:
            result.append("\nContainer Statuses:")
            for status in pod_dict['status']['container_statuses']:
                result.append(f"  {status['name']}:")
                result.append(f"    Ready:       {status['ready']}")
                result.append(f"    Restarts:    {status['restart_count']}")
                
                state = status['state']
                if 'running' in state:
                    result.append(f"    State:       Running")
                    result.append(f"    Started:     {state['running'].get('started_at', 'N/A')}")
                elif 'waiting' in state:
                    result.append(f"    State:       Waiting")
                    result.append(f"    Reason:      {state['waiting'].get('reason', 'N/A')}")
                    result.append(f"    Message:     {state['waiting'].get('message', 'N/A')}")
                elif 'terminated' in state:
                    result.append(f"    State:       Terminated")
                    result.append(f"    Reason:      {state['terminated'].get('reason', 'N/A')}")
                    result.append(f"    Exit Code:   {state['terminated'].get('exit_code', 'N/A')}")
        
        # Events
        result.append("\nEvents:")
        field_selector = f"involvedObject.name={name},involvedObject.namespace={ns}"
        events = core_v1_api.list_namespaced_event(namespace=ns, field_selector=field_selector)
        
        if events.items:
            for event in events.items:
                result.append(f"  {event.last_timestamp}: {event.reason}: {event.message}")
        else:
            result.append("  No events found")
        
        return "\n".join(result)
    except ApiException as e:
        if e.status == 404:
            return f"Pod {name} not found in namespace {ns}"
        return f"Error describing pod: {str(e)}"
    except Exception as e:
        return f"Unexpected error: {str(e)}"

@mcp.tool()
async def get_pod_logs(
    name: str, 
    namespace: Optional[str] = None, 
    container: Optional[str] = None,
    tail_lines: Optional[int] = None,
    previous: bool = False
) -> str:
    """Get logs from a pod.
    
    Args:
        name: Name of the pod, deployment, or job to get logs from
        namespace: Namespace of the resource (uses current namespace if not specified)
        container: Name of the container (if pod has multiple containers)
        tail_lines: Number of lines to show from the end of the logs
        previous: If true, get logs from previous instance of the container
    """
    try:
        ns = namespace or state["current_namespace"]
        
        # Check if this is a pod, deployment, or job by trying to get the resource
        resource_type = None
        resource_name = name
        
        # Try to find the pod directly first
        try:
            core_v1_api.read_namespaced_pod(name=name, namespace=ns)
            resource_type = "pod"
        except ApiException as e:
            if e.status != 404:
                return f"Error accessing pod {name}: {str(e)}"
                
            # Try deployment
            try:
                deployment = apps_v1_api.read_namespaced_deployment(name=name, namespace=ns)
                resource_type = "deployment"
                
                # Get selector from deployment
                selector = deployment.spec.selector.match_labels
                selector_str = ",".join([f"{k}={v}" for k, v in selector.items()])
                
                # Get pods with this selector
                pods = core_v1_api.list_namespaced_pod(namespace=ns, label_selector=selector_str)
                
                if not pods.items:
                    return f"No pods found for deployment {name} in namespace {ns}"
                
                # Use the first pod found
                resource_name = pods.items[0].metadata.name
                
            except ApiException:
                # Try job
                try:
                    job = batch_v1_api.read_namespaced_job(name=name, namespace=ns)
                    resource_type = "job"
                    
                    # Get selector from job
                    selector = job.spec.selector.match_labels
                    selector_str = ",".join([f"{k}={v}" for k, v in selector.items()])
                    
                    # Get pods with this selector
                    pods = core_v1_api.list_namespaced_pod(namespace=ns, label_selector=selector_str)
                    
                    if not pods.items:
                        return f"No pods found for job {name} in namespace {ns}"
                    
                    # Use the first pod found
                    resource_name = pods.items[0].metadata.name
                    
                except ApiException:
                    return f"Resource {name} not found in namespace {ns}"
        
        # Get logs from the pod
        logs = core_v1_api.read_namespaced_pod_log(
            name=resource_name,
            namespace=ns,
            container=container,
            tail_lines=tail_lines,
            previous=previous
        )
        
        if not logs:
            resource_prefix = f"{resource_type} " if resource_type != "pod" else ""
            return f"No logs found for {resource_prefix}{name} in namespace {ns}"
        
        return logs
    except ApiException as e:
        return f"Error getting logs: {str(e)}"
    except Exception as e:
        return f"Unexpected error: {str(e)}"

@mcp.tool()
async def exec_kubectl(command: str, namespace: Optional[str] = None) -> str:
    """Execute a raw kubectl command.
    
    Args:
        command: The kubectl command to execute (without 'kubectl' prefix)
        namespace: Namespace to use (uses current namespace if not specified)
    """
    try:
        ns = namespace or state["current_namespace"]
        
        # Add namespace to command if not specified
        if " -n " not in command and " --namespace " not in command:
            command = f"{command} -n {ns}"
        
        stdout, stderr = await run_kubectl(command)
        
        if stderr and not stdout:
            return f"Error: {stderr}"
        elif stderr:
            return f"Output: {stdout}\nWarnings: {stderr}"
        else:
            return stdout
    except Exception as e:
        return f"Error executing kubectl command: {str(e)}"

@mcp.tool()
async def install_helm_chart(
    release_name: str,
    chart: str,
    namespace: Optional[str] = None,
    repo: Optional[str] = None,
    version: Optional[str] = None,
    values: Optional[str] = None
) -> str:
    """Install a Helm chart.
    
    Args:
        release_name: Name for the release
        chart: Name of the chart to install
        namespace: Namespace to install into (uses current namespace if not specified)
        repo: Repository to use (e.g., "stable" or URL)
        version: Specific version to install
        values: YAML-formatted values to override defaults
    """
    try:
        ns = namespace or state["current_namespace"]
        
        # Build the command
        cmd = f"install {release_name} {chart} --namespace {ns} --create-namespace"
        
        if repo:
            if not repo.startswith(("http://", "https://")):
                # Add the repo if it's not a URL (assuming it's a chart from a repo)
                await run_helm(f"repo add {repo}-repo {repo}")
                chart = f"{repo}-repo/{chart}"
            else:
                # It's a URL, use it directly
                chart = f"{repo}/{chart}"
                cmd = f"install {release_name} {chart} --namespace {ns} --create-namespace"
        
        if version:
            cmd += f" --version {version}"
        
        # Handle values
        if values:
            # Create a temporary file for values
            with tempfile.NamedTemporaryFile(mode='w', suffix='.yaml', delete=False) as temp:
                temp.write(values)
                temp_path = temp.name
            
            cmd += f" -f {temp_path}"
            
            # Execute and then clean up
            stdout, stderr = await run_helm(cmd)
            
            # Remove the temporary file
            os.unlink(temp_path)
        else:
            # Execute without values file
            stdout, stderr = await run_helm(cmd)
        
        if stderr and "Error:" in stderr:
            return f"Error installing chart: {stderr}"
        elif stderr:
            return f"Chart installed with warnings:\n{stdout}\n\nWarnings:\n{stderr}"
        else:
            return stdout
    except Exception as e:
        return f"Error installing Helm chart: {str(e)}"

@mcp.tool()
async def uninstall_helm_release(release_name: str, namespace: Optional[str] = None) -> str:
    """Uninstall a Helm release.
    
    Args:
        release_name: Name of the release to uninstall
        namespace: Namespace of the release (uses current namespace if not specified)
    """
    try:
        ns = namespace or state["current_namespace"]
        
        # Build the command
        cmd = f"uninstall {release_name} --namespace {ns}"
        
        stdout, stderr = await run_helm(cmd)
        
        if stderr and "Error:" in stderr:
            return f"Error uninstalling release: {stderr}"
        elif stderr:
            return f"Release uninstalled with warnings:\n{stdout}\n\nWarnings:\n{stderr}"
        else:
            return stdout
    except Exception as e:
        return f"Error uninstalling Helm release: {str(e)}"

@mcp.tool()
async def list_helm_releases(namespace: Optional[str] = None, all_namespaces: bool = False) -> str:
    """List Helm releases.
    
    Args:
        namespace: Namespace to list releases from (uses current namespace if not specified)
        all_namespaces: If true, list releases across all namespaces
    """
    try:
        cmd = "list"
        
        if all_namespaces:
            cmd += " --all-namespaces"
        else:
            ns = namespace or state["current_namespace"]
            cmd += f" --namespace {ns}"
        
        stdout, stderr = await run_helm(cmd)
        
        if stderr and "Error:" in stderr:
            return f"Error listing releases: {stderr}"
        elif not stdout or "NAME" not in stdout:
            return "No Helm releases found"
        else:
            return stdout
    except Exception as e:
        return f"Error listing Helm releases: {str(e)}"

@mcp.tool()
async def upgrade_helm_release(
    release_name: str,
    chart: str,
    namespace: Optional[str] = None,
    repo: Optional[str] = None,
    version: Optional[str] = None,
    values: Optional[str] = None,
    reset_values: bool = False
) -> str:
    """Upgrade a Helm release.
    
    Args:
        release_name: Name of the release to upgrade
        chart: Chart name or path
        namespace: Namespace of the release (uses current namespace if not specified)
        repo: Repository to use
        version: Version to upgrade to
        values: YAML-formatted values to override
        reset_values: If true, reset values to chart defaults
    """
    try:
        ns = namespace or state["current_namespace"]
        
        # Build the command
        cmd = f"upgrade {release_name} {chart} --namespace {ns}"
        
        if repo:
            if not repo.startswith(("http://", "https://")):
                # Add the repo if it's not a URL
                await run_helm(f"repo add {repo}-repo {repo}")
                chart = f"{repo}-repo/{chart}"
            else:
                # It's a URL, use it directly
                chart = f"{repo}/{chart}"
                cmd = f"upgrade {release_name} {chart} --namespace {ns}"
        
        if version:
            cmd += f" --version {version}"
            
        if reset_values:
            cmd += " --reset-values"
        
        # Handle values
        if values:
            # Create a temporary file for values
            with tempfile.NamedTemporaryFile(mode='w', suffix='.yaml', delete=False) as temp:
                temp.write(values)
                temp_path = temp.name
            
            cmd += f" -f {temp_path}"
            
            # Execute and then clean up
            stdout, stderr = await run_helm(cmd)
            
            # Remove the temporary file
            os.unlink(temp_path)
        else:
            # Execute without values file
            stdout, stderr = await run_helm(cmd)
        
        if stderr and "Error:" in stderr:
            return f"Error upgrading release: {stderr}"
        elif stderr:
            return f"Release upgraded with warnings:\n{stdout}\n\nWarnings:\n{stderr}"
        else:
            return stdout
    except Exception as e:
        return f"Error upgrading Helm release: {str(e)}"

@mcp.tool()
async def port_forward(
    resource: str,
    local_port: int,
    remote_port: int,
    namespace: Optional[str] = None,
    resource_type: str = "pod"
) -> str:
    """Forward a local port to a port on a Kubernetes resource.
    
    Args:
        resource: Name of the Kubernetes resource
        local_port: Local port to forward from
        remote_port: Remote port to forward to
        namespace: Namespace of the resource (uses current namespace if not specified)
        resource_type: Type of resource (pod, service, deployment)
    """
    try:
        ns = namespace or state["current_namespace"]
        
        # Check if there's already a port-forward for this local port
        if local_port in state["port_forwards"]:
            process = state["port_forwards"][local_port]
            if process.poll() is None:  # Process is still running
                return f"Port {local_port} is already forwarded. Stop it first with stop_port_forward."
        
        # Build the resource string based on type
        resource_str = f"{resource_type}/{resource}"
        
        # Create the port forward process
        cmd = f"kubectl port-forward {resource_str} {local_port}:{remote_port} -n {ns}"
        
        process = subprocess.Popen(
            cmd,
            shell=True,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True
        )
        
        # Store the process for later management
        state["port_forwards"][local_port] = process
        
        # Wait a moment to see if the port forward succeeds
        await asyncio.sleep(2)
        
        if process.poll() is not None:
            # Process exited
            _, stderr = process.communicate()
            return f"Port forward failed: {stderr}"
        
        return f"Port forward started: localhost:{local_port} -> {resource_str}:{remote_port} in namespace {ns}"
    except Exception as e:
        return f"Error setting up port forward: {str(e)}"

@mcp.tool()
async def stop_port_forward(local_port: int) -> str:
    """Stop a port forwarding process.
    
    Args:
        local_port: The local port to stop forwarding
    """
    try:
        if local_port not in state["port_forwards"]:
            return f"No port forward found for local port {local_port}"
        
        process = state["port_forwards"][local_port]
        
        if process.poll() is None:  # Process is still running
            process.terminate()
            await asyncio.sleep(1)
            
            if process.poll() is None:  # Still not terminated
                process.kill()
            
            del state["port_forwards"][local_port]
            return f"Port forward to local port {local_port} stopped"
        else:
            del state["port_forwards"][local_port]
            return f"Port forward to local port {local_port} was already stopped"
    except Exception as e:
        return f"Error stopping port forward: {str(e)}"

@mcp.tool()
async def list_port_forwards() -> str:
    """List all active port forwards."""
    try:
        if not state["port_forwards"]:
            return "No active port forwards"
        
        result = ["LOCAL PORT\tSTATUS\tCOMMAND"]
        
        for local_port, process in state["port_forwards"].items():
            status = "Active" if process.poll() is None else "Terminated"
            
            # Get the original command
            cmd = process.args if hasattr(process, 'args') else "Unknown"
            
            result.append(f"{local_port}\t{status}\t{cmd}")
        
        return "\n".join(result)
    except Exception as e:
        return f"Error listing port forwards: {str(e)}"

@mcp.tool()
async def get_events(namespace: Optional[str] = None, field_selector: Optional[str] = None) -> str:
    """Get Kubernetes events from the cluster.
    
    Args:
        namespace: Namespace to get events from (uses current namespace if not specified)
        field_selector: Field selector to filter events (e.g. "involvedObject.name=nginx")
    """
    try:
        ns = namespace or state["current_namespace"]
        
        # Get events
        events = core_v1_api.list_namespaced_event(namespace=ns, field_selector=field_selector)
        
        if not events.items:
            return f"No events found in namespace {ns}" + (f" with selector {field_selector}" if field_selector else "")
        
        # Format events
        result = ["LAST SEEN\tTYPE\tREASON\tOBJECT\tMESSAGE"]
        
        for event in events.items:
            last_seen = event.last_timestamp or event.event_time or event.first_timestamp
            event_type = event.type
            reason = event.reason
            object_ref = f"{event.involved_object.kind}/{event.involved_object.name}"
            message = event.message
            
            result.append(f"{last_seen}\t{event_type}\t{reason}\t{object_ref}\t{message}")
        
        return "\n".join(result)
    except ApiException as e:
        return f"Error getting events: {str(e)}"
    except Exception as e:
        return f"Unexpected error: {str(e)}"

@mcp.tool()
async def kubectl_explain(resource: str) -> str:
    """Get explanation for Kubernetes resource kind.
    
    Args:
        resource: Resource kind to explain (e.g., pod, service, deployment)
    """
    try:
        stdout, stderr = await run_kubectl(f"explain {resource}")
        
        if stderr and not stdout:
            return f"Error explaining resource: {stderr}"
        
        return stdout
    except Exception as e:
        return f"Error running kubectl explain: {str(e)}"

@mcp.tool()
async def kubectl_api_resources(namespaced: bool = True) -> str:
    """List available Kubernetes API resources.
    
    Args:
        namespaced: If true, show only namespaced resources
    """
    try:
        cmd = "api-resources"
        if namespaced:
            cmd += " --namespaced=true"
        
        stdout, stderr = await run_kubectl(cmd)
        
        if stderr and not stdout:
            return f"Error listing API resources: {stderr}"
        
        return stdout
    except Exception as e:
        return f"Error running kubectl api-resources: {str(e)}"

@mcp.tool()
async def list_statefulsets(namespace: Optional[str] = None) -> str:
    """List all StatefulSets in a namespace.
    
    Args:
        namespace: Namespace to list StatefulSets from (uses current namespace if not specified)
    """
    try:
        ns = namespace or state["current_namespace"]
        statefulsets = apps_v1_api.list_namespaced_stateful_set(namespace=ns)
        
        result = ["NAME\tREADY\tAGE"]
        for sts in statefulsets.items:
            metadata = sts.metadata
            spec = sts.spec
            status = sts.status
            
            ready = f"{status.ready_replicas or 0}/{spec.replicas}"
            age = metadata.creation_timestamp.strftime("%Y-%m-%d %H:%M:%S")
            
            result.append(f"{metadata.name}\t{ready}\t{age}")
        
        if not statefulsets.items:
            return f"No StatefulSets found in namespace {ns}"
            
        return "\n".join(result)
    except ApiException as e:
        return f"Error listing StatefulSets: {str(e)}"
    except Exception as e:
        return f"Unexpected error: {str(e)}"

@mcp.tool()
async def list_daemonsets(namespace: Optional[str] = None) -> str:
    """List all DaemonSets in a namespace.
    
    Args:
        namespace: Namespace to list DaemonSets from (uses current namespace if not specified)
    """
    try:
        ns = namespace or state["current_namespace"]
        daemonsets = apps_v1_api.list_namespaced_daemon_set(namespace=ns)
        
        result = ["NAME\tDESIRED\tCURRENT\tREADY\tAGE"]
        for ds in daemonsets.items:
            metadata = ds.metadata
            status = ds.status
            
            desired = status.desired_number_scheduled or 0
            current = status.current_number_scheduled or 0
            ready = status.number_ready or 0
            age = metadata.creation_timestamp.strftime("%Y-%m-%d %H:%M:%S")
            
            result.append(f"{metadata.name}\t{desired}\t{current}\t{ready}\t{age}")
        
        if not daemonsets.items:
            return f"No DaemonSets found in namespace {ns}"
            
        return "\n".join(result)
    except ApiException as e:
        return f"Error listing DaemonSets: {str(e)}"
    except Exception as e:
        return f"Unexpected error: {str(e)}"

@mcp.tool()
async def list_cronjobs(namespace: Optional[str] = None) -> str:
    """List all CronJobs in a namespace.
    
    Args:
        namespace: Namespace to list CronJobs from (uses current namespace if not specified)
    """
    try:
        ns = namespace or state["current_namespace"]
        cronjobs = batch_v1_api.list_namespaced_cron_job(namespace=ns)
        
        result = ["NAME\tSCHEDULE\tSUSPEND\tACTIVE\tLAST SCHEDULE\tAGE"]
        for cj in cronjobs.items:
            metadata = cj.metadata
            spec = cj.spec
            status = cj.status
            
            schedule = spec.schedule
            suspended = "True" if spec.suspend else "False"
            active = len(status.active or [])
            last_schedule = status.last_schedule_time.strftime("%Y-%m-%d %H:%M:%S") if status.last_schedule_time else "N/A"
            age = metadata.creation_timestamp.strftime("%Y-%m-%d %H:%M:%S")
            
            result.append(f"{metadata.name}\t{schedule}\t{suspended}\t{active}\t{last_schedule}\t{age}")
        
        if not cronjobs.items:
            return f"No CronJobs found in namespace {ns}"
            
        return "\n".join(result)
    except ApiException as e:
        return f"Error listing CronJobs: {str(e)}"
    except Exception as e:
        return f"Unexpected error: {str(e)}"

@mcp.tool()
async def update_deployment(
    name: str,
    replicas: Optional[int] = None,
    image: Optional[str] = None,
    namespace: Optional[str] = None
) -> str:
    """Update a deployment with new replicas count or image.
    
    Args:
        name: Name of the deployment to update
        replicas: New number of replicas (optional)
        image: New container image (optional)
        namespace: Namespace of the deployment (uses current namespace if not specified)
    """
    try:
        ns = namespace or state["current_namespace"]
        
        # Get existing deployment
        deployment = apps_v1_api.read_namespaced_deployment(name=name, namespace=ns)
        
        updated = False
        
        # Update replicas if specified
        if replicas is not None:
            deployment.spec.replicas = replicas
            updated = True
        
        # Update image if specified
        if image is not None:
            if not deployment.spec.template.spec.containers:
                return f"Deployment {name} has no containers"
            
            # Update the first container's image
            deployment.spec.template.spec.containers[0].image = image
            updated = True
        
        if not updated:
            return "No updates specified. Please provide either replicas or image."
        
        # Update the deployment
        apps_v1_api.patch_namespaced_deployment(
            name=name,
            namespace=ns,
            body=deployment
        )
        
        return f"Deployment {name} updated successfully in namespace {ns}"
    except ApiException as e:
        if e.status == 404:
            return f"Deployment {name} not found in namespace {ns}"
        return f"Error updating deployment: {str(e)}"
    except Exception as e:
        return f"Unexpected error: {str(e)}"

@mcp.tool()
async def rollback_deployment(name: str, revision: Optional[int] = None, namespace: Optional[str] = None) -> str:
    """Rollback a deployment to a previous revision.
    
    Args:
        name: Name of the deployment to rollback
        revision: Revision to rollback to (optional, defaults to previous revision)
        namespace: Namespace of the deployment (uses current namespace if not specified)
    """
    try:
        ns = namespace or state["current_namespace"]
        
        # Build kubectl command for rollback
        cmd = f"rollout undo deployment/{name} -n {ns}"
        
        if revision:
            cmd += f" --to-revision={revision}"
        
        stdout, stderr = await run_kubectl(cmd)
        
        if stderr and "Error:" in stderr:
            return f"Error rolling back deployment: {stderr}"
        
        return stdout or f"Deployment {name} rolled back successfully"
    except Exception as e:
        return f"Error rolling back deployment: {str(e)}"

@mcp.tool()
async def list_persistent_volumes() -> str:
    """List all PersistentVolumes in the cluster."""
    try:
        pvs = core_v1_api.list_persistent_volume()
        
        result = ["NAME\tCAPACITY\tACCESS MODES\tRECLAIM POLICY\tSTATUS\tCLAIM\tSTORAGECLASS\tAGE"]
        for pv in pvs.items:
            metadata = pv.metadata
            spec = pv.spec
            status = pv.status
            
            name = metadata.name
            capacity = spec.capacity.get("storage", "N/A")
            access_modes = ",".join(spec.access_modes) if spec.access_modes else "N/A"
            reclaim_policy = spec.persistent_volume_reclaim_policy or "N/A"
            pv_status = status.phase or "N/A"
            
            claim = "N/A"
            if spec.claim_ref:
                claim = f"{spec.claim_ref.namespace}/{spec.claim_ref.name}"
            
            storage_class = spec.storage_class_name or "N/A"
            age = metadata.creation_timestamp.strftime("%Y-%m-%d %H:%M:%S")
            
            result.append(f"{name}\t{capacity}\t{access_modes}\t{reclaim_policy}\t{pv_status}\t{claim}\t{storage_class}\t{age}")
        
        if not pvs.items:
            return "No PersistentVolumes found in the cluster"
            
        return "\n".join(result)
    except ApiException as e:
        return f"Error listing PersistentVolumes: {str(e)}"
    except Exception as e:
        return f"Unexpected error: {str(e)}"

@mcp.tool()
async def list_persistent_volume_claims(namespace: Optional[str] = None) -> str:
    """List all PersistentVolumeClaims in a namespace.
    
    Args:
        namespace: Namespace to list PVCs from (uses current namespace if not specified)
    """
    try:
        ns = namespace or state["current_namespace"]
        pvcs = core_v1_api.list_namespaced_persistent_volume_claim(namespace=ns)
        
        result = ["NAME\tSTATUS\tVOLUME\tCAPACITY\tACCESS MODES\tSTORAGECLASS\tAGE"]
        for pvc in pvcs.items:
            metadata = pvc.metadata
            spec = pvc.spec
            status = pvc.status
            
            name = metadata.name
            pvc_status = status.phase or "N/A"
            volume = getattr(status, 'volume_name', None) or "N/A"
            
            # Handle capacity more safely
            capacity = "N/A"
            if hasattr(status, 'capacity') and status.capacity and 'storage' in status.capacity:
                capacity = status.capacity['storage']
            
            access_modes = ",".join(spec.access_modes) if spec.access_modes else "N/A"
            storage_class = spec.storage_class_name or "N/A"
            age = metadata.creation_timestamp.strftime("%Y-%m-%d %H:%M:%S")
            
            result.append(f"{name}\t{pvc_status}\t{volume}\t{capacity}\t{access_modes}\t{storage_class}\t{age}")
        
        if not pvcs.items:
            return f"No PersistentVolumeClaims found in namespace {ns}"
            
        return "\n".join(result)
    except ApiException as e:
        return f"Error listing PersistentVolumeClaims: {str(e)}"
    except Exception as e:
        return f"Unexpected error: {str(e)}"

@mcp.tool()
async def create_persistent_volume_claim(
    name: str,
    storage_class: str,
    size: str,
    access_modes: Optional[List[str]] = None,
    namespace: Optional[str] = None
) -> str:
    """Create a PersistentVolumeClaim.
    
    Args:
        name: Name of the PVC
        storage_class: StorageClass to use
        size: Size of the volume (e.g., "1Gi")
        access_modes: Access modes (default: ["ReadWriteOnce"])
        namespace: Namespace to create the PVC in (uses current namespace if not specified)
    """
    try:
        ns = namespace or state["current_namespace"]
        
        if access_modes is None:
            access_modes = ["ReadWriteOnce"]
        
        # Create PVC object
        pvc = client.V1PersistentVolumeClaim(
            api_version="v1",
            kind="PersistentVolumeClaim",
            metadata=client.V1ObjectMeta(name=name),
            spec=client.V1PersistentVolumeClaimSpec(
                access_modes=access_modes,
                resources=client.V1ResourceRequirements(
                    requests={"storage": size}
                ),
                storage_class_name=storage_class
            )
        )
        
        # Create the PVC
        core_v1_api.create_namespaced_persistent_volume_claim(
            namespace=ns,
            body=pvc
        )
        
        return f"PersistentVolumeClaim {name} created successfully in namespace {ns}"
    except ApiException as e:
        return f"Error creating PersistentVolumeClaim: {str(e)}"
    except Exception as e:
        return f"Unexpected error: {str(e)}"

@mcp.tool()
async def list_configmaps(namespace: Optional[str] = None) -> str:
    """List all ConfigMaps in a namespace.
    
    Args:
        namespace: Namespace to list ConfigMaps from (uses current namespace if not specified)
    """
    try:
        ns = namespace or state["current_namespace"]
        configmaps = core_v1_api.list_namespaced_config_map(namespace=ns)
        
        result = ["NAME\tDATA\tAGE"]
        for cm in configmaps.items:
            metadata = cm.metadata
            
            name = metadata.name
            data_count = len(cm.data or {})
            age = metadata.creation_timestamp.strftime("%Y-%m-%d %H:%M:%S")
            
            result.append(f"{name}\t{data_count}\t{age}")
        
        if not configmaps.items:
            return f"No ConfigMaps found in namespace {ns}"
            
        return "\n".join(result)
    except ApiException as e:
        return f"Error listing ConfigMaps: {str(e)}"
    except Exception as e:
        return f"Unexpected error: {str(e)}"

@mcp.tool()
async def create_configmap(
    name: str,
    data: Dict[str, str],
    namespace: Optional[str] = None
) -> str:
    """Create a ConfigMap.
    
    Args:
        name: Name of the ConfigMap
        data: Dictionary of key-value pairs to store in the ConfigMap
        namespace: Namespace to create the ConfigMap in (uses current namespace if not specified)
    """
    try:
        ns = namespace or state["current_namespace"]
        
        # Create ConfigMap object
        configmap = client.V1ConfigMap(
            api_version="v1",
            kind="ConfigMap",
            metadata=client.V1ObjectMeta(name=name),
            data=data
        )
        
        # Create the ConfigMap
        core_v1_api.create_namespaced_config_map(
            namespace=ns,
            body=configmap
        )
        
        return f"ConfigMap {name} created successfully in namespace {ns}"
    except ApiException as e:
        return f"Error creating ConfigMap: {str(e)}"
    except Exception as e:
        return f"Unexpected error: {str(e)}"

@mcp.tool()
async def list_secrets(namespace: Optional[str] = None) -> str:
    """List all Secrets in a namespace.
    
    Args:
        namespace: Namespace to list Secrets from (uses current namespace if not specified)
    """
    try:
        ns = namespace or state["current_namespace"]
        secrets = core_v1_api.list_namespaced_secret(namespace=ns)
        
        result = ["NAME\tTYPE\tDATA\tAGE"]
        for secret in secrets.items:
            metadata = secret.metadata
            
            name = metadata.name
            secret_type = secret.type
            data_count = len(secret.data or {})
            age = metadata.creation_timestamp.strftime("%Y-%m-%d %H:%M:%S")
            
            result.append(f"{name}\t{secret_type}\t{data_count}\t{age}")
        
        if not secrets.items:
            return f"No Secrets found in namespace {ns}"
            
        return "\n".join(result)
    except ApiException as e:
        return f"Error listing Secrets: {str(e)}"
    except Exception as e:
        return f"Unexpected error: {str(e)}"

@mcp.tool()
async def create_secret(
    name: str,
    data: Dict[str, str],
    secret_type: str = "Opaque",
    namespace: Optional[str] = None
) -> str:
    """Create a Secret.
    
    Args:
        name: Name of the Secret
        data: Dictionary of key-value pairs to store in the Secret
        secret_type: Type of Secret (default: "Opaque")
        namespace: Namespace to create the Secret in (uses current namespace if not specified)
    """
    try:
        ns = namespace or state["current_namespace"]
        
        # Encode the data values to base64
        encoded_data = {}
        for key, value in data.items():
            import base64
            encoded_data[key] = base64.b64encode(value.encode()).decode()
        
        # Create Secret object
        secret = client.V1Secret(
            api_version="v1",
            kind="Secret",
            metadata=client.V1ObjectMeta(name=name),
            type=secret_type,
            data=encoded_data
        )
        
        # Create the Secret
        core_v1_api.create_namespaced_secret(
            namespace=ns,
            body=secret
        )
        
        return f"Secret {name} created successfully in namespace {ns}"
    except ApiException as e:
        return f"Error creating Secret: {str(e)}"
    except Exception as e:
        return f"Unexpected error: {str(e)}"

@mcp.tool()
async def list_roles(namespace: Optional[str] = None) -> str:
    """List all Roles in a namespace.
    
    Args:
        namespace: Namespace to list Roles from (uses current namespace if not specified)
    """
    try:
        ns = namespace or state["current_namespace"]
        roles = rbac_v1_api.list_namespaced_role(namespace=ns)
        
        result = ["NAME\tAGE"]
        for role in roles.items:
            metadata = role.metadata
            
            name = metadata.name
            age = metadata.creation_timestamp.strftime("%Y-%m-%d %H:%M:%S")
            
            result.append(f"{name}\t{age}")
        
        if not roles.items:
            return f"No Roles found in namespace {ns}"
            
        return "\n".join(result)
    except ApiException as e:
        return f"Error listing Roles: {str(e)}"
    except Exception as e:
        return f"Unexpected error: {str(e)}"

@mcp.tool()
async def list_role_bindings(namespace: Optional[str] = None) -> str:
    """List all RoleBindings in a namespace.
    
    Args:
        namespace: Namespace to list RoleBindings from (uses current namespace if not specified)
    """
    try:
        ns = namespace or state["current_namespace"]
        role_bindings = rbac_v1_api.list_namespaced_role_binding(namespace=ns)
        
        result = ["NAME\tROLE\tAGE"]
        for rb in role_bindings.items:
            metadata = rb.metadata
            
            name = metadata.name
            role = rb.role_ref.name
            age = metadata.creation_timestamp.strftime("%Y-%m-%d %H:%M:%S")
            
            result.append(f"{name}\t{role}\t{age}")
        
        if not role_bindings.items:
            return f"No RoleBindings found in namespace {ns}"
            
        return "\n".join(result)
    except ApiException as e:
        return f"Error listing RoleBindings: {str(e)}"
    except Exception as e:
        return f"Unexpected error: {str(e)}"

@mcp.tool()
async def get_cluster_metrics() -> str:
    """Get cluster resource utilization metrics."""
    try:
        # Get nodes
        nodes = core_v1_api.list_node()
        
        if not nodes.items:
            return "No nodes found in the cluster"
        
        # Build metrics information
        cluster_metrics = {
            "cpu": {
                "capacity": 0,
                "allocatable": 0,
                "requests": 0,
                "limits": 0,
            },
            "memory": {
                "capacity": 0,
                "allocatable": 0,
                "requests": 0,
                "limits": 0,
            },
            "pods": {
                "capacity": 0,
                "used": 0,
            },
        }
        
        # Get node metrics
        result = ["CLUSTER METRICS:"]
        
        # Calculate resource totals across nodes
        for node in nodes.items:
            # Node capacity
            capacity = node.status.capacity
            allocatable = node.status.allocatable
            
            # CPU
            cpu_capacity = capacity.get("cpu", "0")
            cpu_allocatable = allocatable.get("cpu", "0")
            
            cluster_metrics["cpu"]["capacity"] += _parse_cpu(cpu_capacity)
            cluster_metrics["cpu"]["allocatable"] += _parse_cpu(cpu_allocatable)
            
            # Memory
            memory_capacity = capacity.get("memory", "0")
            memory_allocatable = allocatable.get("memory", "0")
            
            cluster_metrics["memory"]["capacity"] += _parse_memory(memory_capacity)
            cluster_metrics["memory"]["allocatable"] += _parse_memory(memory_allocatable)
            
            # Pods
            pods_capacity = int(capacity.get("pods", "0"))
            cluster_metrics["pods"]["capacity"] += pods_capacity
        
        # Get pod counts and resource requests
        pods = core_v1_api.list_pod_for_all_namespaces()
        
        cluster_metrics["pods"]["used"] = len(pods.items)
        
        # Calculate resource requests and limits
        for pod in pods.items:
            for container in pod.spec.containers:
                # CPU requests and limits
                requests = container.resources.requests or {}
                limits = container.resources.limits or {}
                
                cpu_request = requests.get("cpu", "0")
                cpu_limit = limits.get("cpu", "0")
                
                cluster_metrics["cpu"]["requests"] += _parse_cpu(cpu_request)
                cluster_metrics["cpu"]["limits"] += _parse_cpu(cpu_limit)
                
                # Memory requests and limits
                memory_request = requests.get("memory", "0")
                memory_limit = limits.get("memory", "0")
                
                cluster_metrics["memory"]["requests"] += _parse_memory(memory_request)
                cluster_metrics["memory"]["limits"] += _parse_memory(memory_limit)
        
        # Format the results
        result.append("\nCPU:")
        result.append(f"  Capacity:    {cluster_metrics['cpu']['capacity']} cores")
        result.append(f"  Allocatable: {cluster_metrics['cpu']['allocatable']} cores")
        result.append(f"  Requests:    {cluster_metrics['cpu']['requests']:.2f} cores ({(cluster_metrics['cpu']['requests'] / cluster_metrics['cpu']['allocatable'] * 100):.2f}% of allocatable)")
        result.append(f"  Limits:      {cluster_metrics['cpu']['limits']:.2f} cores ({(cluster_metrics['cpu']['limits'] / cluster_metrics['cpu']['allocatable'] * 100):.2f}% of allocatable)")
        
        result.append("\nMemory:")
        result.append(f"  Capacity:    {_format_memory(cluster_metrics['memory']['capacity'])}")
        result.append(f"  Allocatable: {_format_memory(cluster_metrics['memory']['allocatable'])}")
        result.append(f"  Requests:    {_format_memory(cluster_metrics['memory']['requests'])} ({(cluster_metrics['memory']['requests'] / cluster_metrics['memory']['allocatable'] * 100):.2f}% of allocatable)")
        result.append(f"  Limits:      {_format_memory(cluster_metrics['memory']['limits'])} ({(cluster_metrics['memory']['limits'] / cluster_metrics['memory']['allocatable'] * 100):.2f}% of allocatable)")
        
        result.append("\nPods:")
        result.append(f"  Capacity:    {cluster_metrics['pods']['capacity']}")
        result.append(f"  Used:        {cluster_metrics['pods']['used']} ({(cluster_metrics['pods']['used'] / cluster_metrics['pods']['capacity'] * 100):.2f}% of capacity)")
        
        # Add node-specific metrics
        result.append("\nNODE METRICS:")
        result.append("NAME\tSTATUS\tCPU USED\tMEM USED")
        
        for node in nodes.items:
            node_name = node.metadata.name
            
            # Get node status
            node_status = "Unknown"
            for condition in node.status.conditions:
                if condition.type == "Ready":
                    node_status = "Ready" if condition.status == "True" else "NotReady"
                    break
            
            # Try to get node metrics
            node_metrics = await _get_node_metrics(node_name)
            
            cpu_used = node_metrics.get("cpu", "N/A")
            memory_used = node_metrics.get("memory", "N/A")
            
            result.append(f"{node_name}\t{node_status}\t{cpu_used}\t{memory_used}")
        
        return "\n".join(result)
    except ApiException as e:
        return f"Error getting cluster metrics: {str(e)}"
    except Exception as e:
        return f"Unexpected error: {str(e)}"

@mcp.tool()
async def list_network_policies(namespace: Optional[str] = None) -> str:
    """List all NetworkPolicies in a namespace.
    
    Args:
        namespace: Namespace to list NetworkPolicies from (uses current namespace if not specified)
    """
    try:
        ns = namespace or state["current_namespace"]
        network_policies = networking_v1_api.list_namespaced_network_policy(namespace=ns)
        
        result = ["NAME\tPOD-SELECTOR\tAGE"]
        for policy in network_policies.items:
            metadata = policy.metadata
            
            name = metadata.name
            selector = ",".join([f"{k}={v}" for k, v in policy.spec.pod_selector.match_labels.items()]) if policy.spec.pod_selector.match_labels else "All"
            age = metadata.creation_timestamp.strftime("%Y-%m-%d %H:%M:%S")
            
            result.append(f"{name}\t{selector}\t{age}")
        
        if not network_policies.items:
            return f"No NetworkPolicies found in namespace {ns}"
            
        return "\n".join(result)
    except ApiException as e:
        return f"Error listing NetworkPolicies: {str(e)}"
    except Exception as e:
        return f"Unexpected error: {str(e)}"

@mcp.tool()
async def list_custom_resource_definitions() -> str:
    """List all CustomResourceDefinitions in the cluster."""
    try:
        crds = apiextensions_v1_api.list_custom_resource_definition()
        
        result = ["NAME\tGROUP\tVERSIONS\tSCOPE\tAGE"]
        for crd in crds.items:
            metadata = crd.metadata
            spec = crd.spec
            
            name = metadata.name
            group = spec.group
            versions = ",".join([v.name for v in spec.versions])
            scope = spec.scope
            age = metadata.creation_timestamp.strftime("%Y-%m-%d %H:%M:%S")
            
            result.append(f"{name}\t{group}\t{versions}\t{scope}\t{age}")
        
        if not crds.items:
            return "No CustomResourceDefinitions found in the cluster"
            
        return "\n".join(result)
    except ApiException as e:
        return f"Error listing CustomResourceDefinitions: {str(e)}"
    except Exception as e:
        return f"Unexpected error: {str(e)}"

@mcp.tool()
async def get_argo_cd_applications(namespace: str = "argocd") -> str:
    """List all ArgoCD Applications.
    
    Args:
        namespace: Namespace where ArgoCD is installed (default: argocd)
    """
    try:
        # Check if ArgoCD CRD exists
        try:
            apiextensions_v1_api.read_custom_resource_definition(name="applications.argoproj.io")
        except ApiException as e:
            if e.status == 404:
                return "ArgoCD CustomResourceDefinition 'applications.argoproj.io' not found. Is ArgoCD installed?"
            raise
        
        # Get all ArgoCD applications
        apps = custom_objects_api.list_namespaced_custom_object(
            group="argoproj.io",
            version="v1alpha1",
            namespace=namespace,
            plural="applications"
        )
        
        if not apps.get("items"):
            return f"No ArgoCD Applications found in namespace {namespace}"
        
        result = ["NAME\tDESTINATION\tSYNC STATUS\tHEALTH STATUS"]
        for app in apps["items"]:
            metadata = app["metadata"]
            spec = app["spec"]
            status = app.get("status", {})
            
            name = metadata["name"]
            destination = f"{spec['destination']['server']}/{spec['destination']['namespace']}"
            sync_status = status.get("sync", {}).get("status", "Unknown")
            health_status = status.get("health", {}).get("status", "Unknown")
            
            result.append(f"{name}\t{destination}\t{sync_status}\t{health_status}")
        
        return "\n".join(result)
    except ApiException as e:
        return f"Error getting ArgoCD Applications: {str(e)}"
    except Exception as e:
        return f"Unexpected error: {str(e)}"

@mcp.tool()
async def get_flux_resources(namespace: str = "flux-system") -> str:
    """List Flux resources like GitRepositories, Kustomizations, etc.
    
    Args:
        namespace: Namespace where Flux is installed (default: flux-system)
    """
    try:
        # Check if Flux CRDs exist
        flux_crds = [
            "gitrepositories.source.toolkit.fluxcd.io",
            "kustomizations.kustomize.toolkit.fluxcd.io",
            "helmreleases.helm.toolkit.fluxcd.io"
        ]
        
        # Check at least one Flux CRD exists
        found_flux = False
        for crd_name in flux_crds:
            try:
                apiextensions_v1_api.read_custom_resource_definition(name=crd_name)
                found_flux = True
                break
            except ApiException as e:
                if e.status != 404:
                    raise
        
        if not found_flux:
            return "Flux CustomResourceDefinitions not found. Is Flux installed?"
        
        # Gather results
        all_results = []
        
        # Get GitRepositories
        try:
            git_repos = custom_objects_api.list_namespaced_custom_object(
                group="source.toolkit.fluxcd.io",
                version="v1",
                namespace=namespace,
                plural="gitrepositories"
            )
            
            if git_repos.get("items"):
                all_results.append("GITREPOSITORIES:")
                all_results.append("NAME\tURL\tREADY\tSTATUS")
                
                for repo in git_repos["items"]:
                    metadata = repo["metadata"]
                    spec = repo["spec"]
                    status = repo.get("status", {})
                    
                    name = metadata["name"]
                    url = spec["url"]
                    ready = "True" if status.get("conditions") and any(c.get("type") == "Ready" and c.get("status") == "True" for c in status["conditions"]) else "False"
                    status_msg = next((c.get("message", "Unknown") for c in status.get("conditions", []) if c.get("type") == "Ready"), "Unknown")
                    
                    all_results.append(f"{name}\t{url}\t{ready}\t{status_msg}")
        except ApiException as e:
            if e.status != 404:
                all_results.append(f"Error listing GitRepositories: {str(e)}")
        
        # Get Kustomizations
        try:
            kustomizations = custom_objects_api.list_namespaced_custom_object(
                group="kustomize.toolkit.fluxcd.io",
                version="v1",
                namespace=namespace,
                plural="kustomizations"
            )
            
            if kustomizations.get("items"):
                if all_results:
                    all_results.append("")
                all_results.append("KUSTOMIZATIONS:")
                all_results.append("NAME\tSOURCE\tREADY\tSTATUS")
                
                for kust in kustomizations["items"]:
                    metadata = kust["metadata"]
                    spec = kust["spec"]
                    status = kust.get("status", {})
                    
                    name = metadata["name"]
                    source = f"{spec['sourceRef']['kind']}/{spec['sourceRef']['name']}"
                    ready = "True" if status.get("conditions") and any(c.get("type") == "Ready" and c.get("status") == "True" for c in status["conditions"]) else "False"
                    status_msg = next((c.get("message", "Unknown") for c in status.get("conditions", []) if c.get("type") == "Ready"), "Unknown")
                    
                    all_results.append(f"{name}\t{source}\t{ready}\t{status_msg}")
        except ApiException as e:
            if e.status != 404:
                all_results.append(f"Error listing Kustomizations: {str(e)}")
        
        # Get HelmReleases
        try:
            helm_releases = custom_objects_api.list_namespaced_custom_object(
                group="helm.toolkit.fluxcd.io",
                version="v2beta1",
                namespace=namespace,
                plural="helmreleases"
            )
            
            if helm_releases.get("items"):
                if all_results:
                    all_results.append("")
                all_results.append("HELMRELEASES:")
                all_results.append("NAME\tCHART\tREADY\tSTATUS")
                
                for release in helm_releases["items"]:
                    metadata = release["metadata"]
                    spec = release["spec"]
                    status = release.get("status", {})
                    
                    name = metadata["name"]
                    chart = f"{spec['chart']['spec']['chart']}"
                    if "sourceRef" in spec["chart"]["spec"]:
                        chart = f"{chart} ({spec['chart']['spec']['sourceRef']['kind']}/{spec['chart']['spec']['sourceRef']['name']})"
                    
                    ready = "True" if status.get("conditions") and any(c.get("type") == "Ready" and c.get("status") == "True" for c in status["conditions"]) else "False"
                    status_msg = next((c.get("message", "Unknown") for c in status.get("conditions", []) if c.get("type") == "Ready"), "Unknown")
                    
                    all_results.append(f"{name}\t{chart}\t{ready}\t{status_msg}")
        except ApiException as e:
            if e.status != 404:
                all_results.append(f"Error listing HelmReleases: {str(e)}")
        
        if not all_results:
            return f"No Flux resources found in namespace {namespace}"
            
        return "\n".join(all_results)
    except ApiException as e:
        return f"Error getting Flux resources: {str(e)}"
    except Exception as e:
        return f"Unexpected error: {str(e)}"

@mcp.tool()
async def open_web_dashboard(browser: bool = True) -> str:
    """Open the Kubernetes Dashboard (if installed) or create a kubectl proxy for it.
    
    Args:
        browser: If true, attempts to open the dashboard in the default browser
    """
    try:
        # Check if Kubernetes Dashboard is installed
        try:
            services = core_v1_api.list_service_for_all_namespaces(
                label_selector="k8s-app=kubernetes-dashboard"
            )
            
            dashboard_found = bool(services.items)
        except:
            dashboard_found = False
        
        if not dashboard_found:
            return """Kubernetes Dashboard not found. You may need to install it:
            
kubectl apply -f https://raw.githubusercontent.com/kubernetes/dashboard/v2.7.0/aio/deploy/recommended.yaml
            
After installation, create a token for login:
            
kubectl create serviceaccount dashboard-admin
kubectl create clusterrolebinding dashboard-admin --clusterrole=cluster-admin --serviceaccount=default:dashboard-admin
kubectl create token dashboard-admin
            
Then access the dashboard at: http://localhost:8001/api/v1/namespaces/kubernetes-dashboard/services/https:kubernetes-dashboard:/proxy/
"""
        
        # Start kubectl proxy
        cmd = "kubectl proxy"
        
        # Start as background process
        proc = subprocess.Popen(
            cmd.split(),
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE
        )
        
        # Store process for later management
        state["dashboard_proxy"] = proc
        
        # Wait a bit to ensure proxy is up
        await asyncio.sleep(2)
        
        if proc.poll() is not None:
            # Process exited
            _, stderr = proc.communicate()
            return f"Failed to start kubectl proxy: {stderr.decode()}"
        
        dashboard_url = "http://localhost:8001/api/v1/namespaces/kubernetes-dashboard/services/https:kubernetes-dashboard:/proxy/"
        
        # Attempt to open in browser if requested
        if browser:
            import webbrowser
            webbrowser.open(dashboard_url)
            return f"Kubernetes Dashboard proxy started and opened in browser at {dashboard_url}"
        else:
            return f"Kubernetes Dashboard proxy started. Access at {dashboard_url}"
    except Exception as e:
        return f"Error opening Kubernetes Dashboard: {str(e)}"

# Helper methods for metric parsing
def _parse_cpu(cpu_str: str) -> float:
    """Parse CPU value from Kubernetes resource notation."""
    try:
        if cpu_str.endswith('m'):
            return float(cpu_str[:-1]) / 1000
        return float(cpu_str)
    except (ValueError, TypeError):
        return 0

def _parse_memory(memory_str: str) -> float:
    """Parse memory value to bytes from Kubernetes resource notation."""
    try:
        if isinstance(memory_str, (int, float)):
            return float(memory_str)
        
        memory_str = memory_str.upper()
        
        if memory_str.endswith('KI') or memory_str.endswith('K'):
            return float(memory_str[:-2] if memory_str.endswith('KI') else memory_str[:-1]) * 1024
        elif memory_str.endswith('MI') or memory_str.endswith('M'):
            return float(memory_str[:-2] if memory_str.endswith('MI') else memory_str[:-1]) * 1024 * 1024
        elif memory_str.endswith('GI') or memory_str.endswith('G'):
            return float(memory_str[:-2] if memory_str.endswith('GI') else memory_str[:-1]) * 1024 * 1024 * 1024
        elif memory_str.endswith('TI') or memory_str.endswith('T'):
            return float(memory_str[:-2] if memory_str.endswith('TI') else memory_str[:-1]) * 1024 * 1024 * 1024 * 1024
        elif memory_str.endswith('PI') or memory_str.endswith('P'):
            return float(memory_str[:-2] if memory_str.endswith('PI') else memory_str[:-1]) * 1024 * 1024 * 1024 * 1024 * 1024
        elif memory_str.endswith('EI') or memory_str.endswith('E'):
            return float(memory_str[:-2] if memory_str.endswith('EI') else memory_str[:-1]) * 1024 * 1024 * 1024 * 1024 * 1024 * 1024
        else:
            return float(memory_str)
    except (ValueError, TypeError, IndexError):
        return 0

def _format_memory(memory_bytes: float) -> str:
    """Format memory bytes to human-readable format."""
    units = ['B', 'KiB', 'MiB', 'GiB', 'TiB', 'PiB', 'EiB']
    unit_index = 0
    value = memory_bytes
    
    while value >= 1024 and unit_index < len(units) - 1:
        value /= 1024
        unit_index += 1
    
    return f"{value:.2f} {units[unit_index]}"

async def _get_node_metrics(node_name: str) -> Dict[str, str]:
    """Get metrics for a specific node."""
    try:
        # Use kubectl top nodes to get metrics
        stdout, stderr = await run_kubectl(f"top node {node_name}")
        
        if stderr and not stdout:
            return {"cpu": "N/A", "memory": "N/A"}
        
        # Parse the output
        lines = stdout.strip().split('\n')
        if len(lines) < 2:
            return {"cpu": "N/A", "memory": "N/A"}
        
        # The second line has the metrics
        metrics_line = lines[1].split()
        if len(metrics_line) < 4:
            return {"cpu": "N/A", "memory": "N/A"}
        
        cpu = metrics_line[2]
        memory = metrics_line[3]
        
        return {"cpu": cpu, "memory": memory}
    except Exception:
        return {"cpu": "N/A", "memory": "N/A"}

# Main function to run the server
if __name__ == "__main__":
    mcp.run(transport='stdio')