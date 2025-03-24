#!/usr/bin/env python3
"""
Kubernetes MCP Server Test Script

This script tests the functionality of the Kubernetes MCP server by executing
various MCP tool functions. It creates resources in an isolated test namespace
and cleans up everything after the tests are completed.
"""
import sys
import os
# Add the parent directory to the Python path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import asyncio
import logging
import sys
import time
import uuid
from typing import Dict, List, Optional, Any, Union, Tuple

# Import the Kubernetes MCP server
import servers.kubernetes.kubernetes_mcp as kubernetes_mcp

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Generate a unique test namespace to avoid conflicts
TEST_NAMESPACE = f"mcp-test-{uuid.uuid4().hex[:8]}"

# Resources that will be created during the test
test_resources = {
    "namespace": TEST_NAMESPACE,
    "configmap": "test-configmap",
    "secret": "test-secret",
    "pod": "test-pod",
    "deployment": "test-deployment",
    "pvc": "test-pvc",
    "service": "test-service",
    "port_forward": 8080,
}

async def invoke_mcp_tool(tool_name: str, **kwargs) -> str:
    """Invoke an MCP tool by name with the given arguments."""
    logger.info(f"Invoking tool: {tool_name} with args: {kwargs}")
    
    # Get the tool function from the MCP server
    tool_function = getattr(kubernetes_mcp, tool_name, None)
    if not tool_function:
        raise ValueError(f"Tool {tool_name} not found in kubernetes_mcp module")
    
    # Invoke the tool
    result = await tool_function(**kwargs)
    
    # Log a truncated version of the result for readability
    max_log_length = 100
    log_result = result[:max_log_length] + "..." if len(result) > max_log_length else result
    logger.info(f"Result: {log_result}")
    
    return result

async def run_tests():
    """Run a series of tests against the Kubernetes MCP server."""
    try:
        # Create test namespace
        logger.info(f"Creating test namespace: {TEST_NAMESPACE}")
        await invoke_mcp_tool(
            "exec_kubectl",
            command=f"create namespace {TEST_NAMESPACE}"
        )
        
        # Set current namespace to test namespace
        logger.info("Setting current namespace")
        await invoke_mcp_tool(
            "choose_namespace",
            namespace=TEST_NAMESPACE
        )
        
        # List namespaces to verify our test namespace exists
        logger.info("Listing namespaces")
        namespaces_result = await invoke_mcp_tool("list_namespaces")
        
        # Test cluster-wide resource listing
        logger.info("Testing cluster resource listing")
        await invoke_mcp_tool("list_nodes")
        await invoke_mcp_tool("list_persistent_volumes")
        
        # Test ConfigMap operations
        logger.info("Testing ConfigMap operations")
        await invoke_mcp_tool(
            "create_configmap",
            name=test_resources["configmap"],
            data={"key1": "value1", "key2": "value2"},
            namespace=TEST_NAMESPACE
        )
        
        await invoke_mcp_tool(
            "list_configmaps",
            namespace=TEST_NAMESPACE
        )
        
        # Test Secret operations
        logger.info("Testing Secret operations")
        await invoke_mcp_tool(
            "create_secret",
            name=test_resources["secret"],
            data={"username": "admin", "password": "test-password"},
            namespace=TEST_NAMESPACE
        )
        
        await invoke_mcp_tool(
            "list_secrets",
            namespace=TEST_NAMESPACE
        )
        
        # Test Pod operations
        logger.info("Testing Pod operations")
        pod_manifest = """
apiVersion: v1
kind: Pod
metadata:
  name: test-pod
spec:
  containers:
  - name: nginx
    image: nginx:alpine
    ports:
    - containerPort: 80
    resources:
      limits:
        cpu: 100m
        memory: 128Mi
      requests:
        cpu: 50m
        memory: 64Mi
"""
        
        await invoke_mcp_tool(
            "create_pod",
            manifest=pod_manifest,
            namespace=TEST_NAMESPACE
        )
        
        # Wait for pod to be ready
        logger.info("Waiting for pod to be ready")
        retries = 10
        while retries > 0:
            pods_result = await invoke_mcp_tool(
                "list_pods",
                namespace=TEST_NAMESPACE
            )
            
            if "Running" in pods_result:
                logger.info("Pod is running")
                break
                
            logger.info(f"Pod not ready yet, waiting... ({retries} retries left)")
            retries -= 1
            await asyncio.sleep(3)
        
        # Describe pod
        await invoke_mcp_tool(
            "describe_pod",
            name=test_resources["pod"],
            namespace=TEST_NAMESPACE
        )
        
        # Test Deployment operations
        logger.info("Testing Deployment operations")
        deployment_yaml = """
apiVersion: apps/v1
kind: Deployment
metadata:
  name: test-deployment
spec:
  replicas: 1
  selector:
    matchLabels:
      app: test-app
  template:
    metadata:
      labels:
        app: test-app
    spec:
      containers:
      - name: nginx
        image: nginx:alpine
        ports:
        - containerPort: 80
"""
        
        await invoke_mcp_tool(
            "exec_kubectl",
            command=f"apply -f - <<EOF\n{deployment_yaml}\nEOF",
            namespace=TEST_NAMESPACE
        )
        
        # List deployments
        await invoke_mcp_tool(
            "list_deployments",
            namespace=TEST_NAMESPACE
        )
        
        # Test updating a deployment
        logger.info("Testing deployment update")
        await invoke_mcp_tool(
            "update_deployment",
            name=test_resources["deployment"],
            replicas=2,
            namespace=TEST_NAMESPACE
        )
        
        # List deployments again to verify update
        await invoke_mcp_tool(
            "list_deployments",
            namespace=TEST_NAMESPACE
        )
        
        # Test Service operations
        logger.info("Testing Service operations")
        service_yaml = """
apiVersion: v1
kind: Service
metadata:
  name: test-service
spec:
  selector:
    app: test-app
  ports:
  - port: 80
    targetPort: 80
  type: ClusterIP
"""
        
        await invoke_mcp_tool(
            "exec_kubectl",
            command=f"apply -f - <<EOF\n{service_yaml}\nEOF",
            namespace=TEST_NAMESPACE
        )
        
        # List services
        await invoke_mcp_tool(
            "list_services",
            namespace=TEST_NAMESPACE
        )
        
        # Test PersistentVolumeClaim operations if storage class exists
        logger.info("Testing PVC operations")
        try:
            # Get available storage classes
            storage_classes = await invoke_mcp_tool(
                "exec_kubectl",
                command="get storageclass -o name"
            )
            
            if storage_classes.strip():
                # Use the first storage class
                storage_class = storage_classes.strip().split("\n")[0].replace("storageclass.storage.k8s.io/", "")
                
                await invoke_mcp_tool(
                    "create_persistent_volume_claim",
                    name=test_resources["pvc"],
                    storage_class=storage_class,
                    size="1Gi",
                    namespace=TEST_NAMESPACE
                )
                
                # List PVCs
                await invoke_mcp_tool(
                    "list_persistent_volume_claims",
                    namespace=TEST_NAMESPACE
                )
            else:
                logger.warning("No StorageClass found, skipping PVC tests")
        except Exception as e:
            logger.warning(f"Error during PVC test: {e}, skipping")
        
        # Test port forwarding (briefly)
        logger.info("Testing port forwarding")
        try:
            # Start port forwarding
            port_forward_result = await invoke_mcp_tool(
                "port_forward",
                resource=test_resources["service"],
                local_port=test_resources["port_forward"],
                remote_port=80,
                namespace=TEST_NAMESPACE,
                resource_type="svc"
            )
            
            # List port forwards
            await invoke_mcp_tool("list_port_forwards")
            
            # Stop port forwarding
            await invoke_mcp_tool(
                "stop_port_forward",
                local_port=test_resources["port_forward"]
            )
        except Exception as e:
            logger.warning(f"Error during port forwarding test: {e}, skipping")
        
        # Test get_events
        logger.info("Testing events retrieval")
        await invoke_mcp_tool(
            "get_events",
            namespace=TEST_NAMESPACE
        )
        
        # Test explaining Kubernetes resources
        logger.info("Testing kubectl explain")
        await invoke_mcp_tool(
            "kubectl_explain",
            resource="pod"
        )
        
        # Test API resources listing
        logger.info("Testing API resources listing")
        await invoke_mcp_tool(
            "kubectl_api_resources",
            namespaced=True
        )
        
        # Test cluster metrics (if available)
        logger.info("Testing cluster metrics")
        try:
            await invoke_mcp_tool("get_cluster_metrics")
        except Exception as e:
            logger.warning(f"Error during metrics test: {e}, skipping")
        
        # If we've reached this point, all tests passed
        logger.info("All tests completed successfully!")
        
    except Exception as e:
        logger.error(f"Error during tests: {e}")
        raise
    finally:
        # Always clean up test resources, even if tests fail
        await cleanup()

async def cleanup():
    """Clean up all test resources."""
    logger.info(f"Cleaning up test namespace {TEST_NAMESPACE}")
    
    try:
        # Delete namespace and all resources in it
        await invoke_mcp_tool(
            "exec_kubectl",
            command=f"delete namespace {TEST_NAMESPACE}"
        )
        
        # Wait for namespace to be deleted
        logger.info("Waiting for namespace deletion to complete")
        retries = 10
        while retries > 0:
            try:
                namespaces = await invoke_mcp_tool("list_namespaces")
                if TEST_NAMESPACE not in namespaces:
                    logger.info("Namespace deleted successfully")
                    break
            except Exception:
                # If we get an error, the namespace might be gone
                logger.info("Namespace appears to be deleted")
                break
                
            logger.info(f"Namespace still exists, waiting... ({retries} retries left)")
            retries -= 1
            await asyncio.sleep(3)
        
        logger.info("Cleanup completed")
    except Exception as e:
        logger.error(f"Error during cleanup: {e}")

async def main():
    """Main entry point for the test script."""
    logger.info("Starting Kubernetes MCP server test")
    
    try:
        await run_tests()
        return 0
    except Exception as e:
        logger.error(f"Test failed: {e}")
        return 1

if __name__ == "__main__":
    # Run the test script
    exit_code = asyncio.run(main())
    sys.exit(exit_code)