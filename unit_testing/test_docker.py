import pytest
import json
import asyncio
import docker
import uuid
import time
import os
from typing import Dict, List

# Import the MCP server module
# Note: Adjust the import path as needed based on your project structure
import sys
sys.path.append(".")  # Add the current directory to the path
from mcp.server.fastmcp import FastMCP, Context

# Import the Docker MCP server module
# The following import assumes the provided code is in a file named docker_mcp.py
import servers.docker.docker_mcp as docker_mcp

# Create a test client for Docker
docker_client = docker.from_env()

# Generate unique identifiers for test resources to avoid conflicts
test_id = str(uuid.uuid4())[:8]

# Test image to use
TEST_IMAGE = "alpine:latest"
TEST_NETWORK_NAME = f"test-network-{test_id}"
TEST_VOLUME_NAME = f"test-volume-{test_id}"
TEST_CONTAINER_NAME = f"test-container-{test_id}"

# Fixtures to set up and tear down resources
@pytest.fixture(scope="session", autouse=True)
def setup_test_resources():
    """Set up resources needed for testing and ensure cleanup afterward."""
    # Pull the test image
    docker_client.images.pull(TEST_IMAGE.split(":")[0], tag=TEST_IMAGE.split(":")[1])
    
    yield
    
    # Clean up any test containers
    for container in docker_client.containers.list(all=True):
        if TEST_CONTAINER_NAME in container.name:
            try:
                container.remove(force=True)
            except:
                pass
    
    # Clean up any test networks
    for network in docker_client.networks.list():
        if TEST_NETWORK_NAME in network.name:
            try:
                network.remove()
            except:
                pass
    
    # Clean up any test volumes
    for volume in docker_client.volumes.list():
        if TEST_VOLUME_NAME in volume.name:
            try:
                volume.remove(force=True)
            except:
                pass

# Helper function to run async functions in tests
async def run_tool(tool_func, **kwargs):
    """Helper function to run an async tool function."""
    result = await tool_func(**kwargs)
    return result

def run_async(coroutine):
    """Run an async function and return its result."""
    return asyncio.run(coroutine)

# Container Tests
class TestContainers:
    def test_list_containers(self):
        """Test listing containers."""
        result = run_async(run_tool(docker_mcp.list_containers, show_all=True))
        assert isinstance(result, str)
        
        # Parse the JSON result
        container_list = json.loads(result)
        assert isinstance(container_list, list)
        
        # Check if result contains expected fields
        if container_list:
            assert "id" in container_list[0]
            assert "name" in container_list[0]
            assert "status" in container_list[0]
    
    def test_create_container(self):
        """Test creating a container without starting it."""
        container_name = f"{TEST_CONTAINER_NAME}-create"
        result = run_async(run_tool(
            docker_mcp.create_container,
            image=TEST_IMAGE,
            name=container_name,
            command="echo 'Hello from test container'"
        ))
        
        assert "Container created successfully" in result
        
        # Verify the container exists but is not running
        container = docker_client.containers.get(container_name)
        assert container.status != "running"
        
        # Clean up
        container.remove()
    
    def test_run_container(self):
        """Test creating and running a container."""
        container_name = f"{TEST_CONTAINER_NAME}-run"
        result = run_async(run_tool(
            docker_mcp.run_container,
            image=TEST_IMAGE,
            name=container_name,
            command="sleep 10",
            detach=True
        ))
        
        assert "Container started successfully" in result
        
        # Verify the container is running
        container = docker_client.containers.get(container_name)
        assert container.status == "running"
        
        # Clean up
        container.stop()
        container.remove()
    
    def test_start_and_stop_container(self):
        """Test starting and stopping a container."""
        container_name = f"{TEST_CONTAINER_NAME}-start-stop"
        
        # Create a container first (without starting it)
        result = run_async(run_tool(
            docker_mcp.create_container,
            image=TEST_IMAGE,
            name=container_name,
            command="sleep 30"
        ))
        
        assert "Container created successfully" in result
        
        # Now start the container
        result = run_async(run_tool(docker_mcp.start_container, container_id=container_name))
        assert "started successfully" in result
        
        # Verify the container is running
        container = docker_client.containers.get(container_name)
        assert container.status == "running"
        
        # Now stop the container
        result = run_async(run_tool(docker_mcp.stop_container, container_id=container_name))
        assert "stopped successfully" in result
        
        # Refresh the container status
        container.reload()
        assert container.status != "running"
        
        # Clean up
        container.remove()
    
    def test_fetch_container_logs(self):
        """Test fetching container logs."""
        container_name = f"{TEST_CONTAINER_NAME}-logs"
        test_message = "This is a test log message"
        
        # Create and run a container that outputs a message
        result = run_async(run_tool(
            docker_mcp.run_container,
            image=TEST_IMAGE,
            name=container_name,
            command=f"echo '{test_message}'",
            detach=True
        ))
        
        # Wait a moment for the container to complete its execution
        time.sleep(2)
        
        # Fetch the logs
        result = run_async(run_tool(docker_mcp.fetch_container_logs, container_id=container_name))
        
        # Verify the log contains our test message
        assert test_message in result
        
        # Clean up
        container = docker_client.containers.get(container_name)
        container.remove()
    
    def test_recreate_container(self):
        """Test recreating a container."""
        container_name = f"{TEST_CONTAINER_NAME}-recreate"
        
        # Create and run a container
        result = run_async(run_tool(
            docker_mcp.run_container,
            image=TEST_IMAGE,
            name=container_name,
            command="sleep 10",
            environment={"TEST_VAR": "test_value"},
            detach=True
        ))
        
        assert "Container started successfully" in result
        
        # Get the ID of the original container
        original_container = docker_client.containers.get(container_name)
        original_id = original_container.id
        
        # Now recreate the container
        result = run_async(run_tool(docker_mcp.recreate_container, container_id=container_name, start=True))
        assert "Container recreated and started" in result
        
        # Get the ID of the new container
        new_container = docker_client.containers.get(container_name)
        new_id = new_container.id
        
        # Verify the IDs are different (confirming recreation)
        assert original_id != new_id
        
        # But the environment variables should be the same
        assert "TEST_VAR=test_value" in new_container.attrs["Config"]["Env"]
        
        # Clean up
        new_container.stop()
        new_container.remove()
    
    def test_remove_container(self):
        """Test removing a container."""
        container_name = f"{TEST_CONTAINER_NAME}-remove"
        
        # Create a container
        result = run_async(run_tool(
            docker_mcp.create_container,
            image=TEST_IMAGE,
            name=container_name,
            command="echo 'Test container for removal'"
        ))
        
        assert "Container created successfully" in result
        
        # Now remove the container
        result = run_async(run_tool(docker_mcp.remove_container, container_id=container_name))
        assert "removed successfully" in result
        
        # Verify the container no longer exists
        with pytest.raises(docker.errors.NotFound):
            docker_client.containers.get(container_name)

# Image Tests
class TestImages:
    def test_list_images(self):
        """Test listing images."""
        result = run_async(run_tool(docker_mcp.list_images))
        assert isinstance(result, str)
        
        # Parse the JSON result
        image_list = json.loads(result)
        assert isinstance(image_list, list)
        
        # Check if result contains expected fields
        if image_list:
            assert "id" in image_list[0]
            assert "tags" in image_list[0]
            assert "size" in image_list[0]
    
    def test_pull_image(self):
        """Test pulling an image."""
        # Use a small, commonly available image
        test_image = "hello-world:latest"
        
        # Remove the image first if it exists
        try:
            docker_client.images.remove(test_image)
        except:
            pass
        
        # Pull the image
        result = run_async(run_tool(
            docker_mcp.pull_image,
            image_name="hello-world",
            tag="latest"
        ))
        
        assert "pulled successfully" in result
        
        # Verify the image exists
        images = docker_client.images.list(name="hello-world")
        assert len(images) > 0
    
    # Skipping push_image test as it requires registry credentials
    
    def test_build_image(self, tmp_path):
        """Test building an image from a Dockerfile."""
        # Create a temporary Dockerfile
        dockerfile_content = """
        FROM alpine:latest
        RUN echo "This is a test image" > /test.txt
        CMD ["cat", "/test.txt"]
        """
        
        # Create a temporary directory and Dockerfile
        build_dir = tmp_path / "docker-build"
        build_dir.mkdir()
        dockerfile_path = build_dir / "Dockerfile"
        dockerfile_path.write_text(dockerfile_content)
        
        # Build the image
        test_image_tag = f"test-image-{test_id}"
        result = run_async(run_tool(
            docker_mcp.build_image,
            path=str(build_dir),
            tag=test_image_tag,
            dockerfile="Dockerfile"
        ))
        
        assert "Image built successfully" in result
        
        # Verify the image exists
        images = docker_client.images.list(name=test_image_tag)
        assert len(images) > 0
        
        # Clean up
        docker_client.images.remove(test_image_tag)
    
    def test_remove_image(self):
        """Test removing an image."""
        # Use a small, commonly available image
        test_image = "hello-world:latest"
        
        # Make sure the image exists
        try:
            docker_client.images.pull("hello-world", tag="latest")
        except:
            pass
        
        # Remove the image
        result = run_async(run_tool(
            docker_mcp.remove_image,
            image_id=test_image
        ))
        
        assert "removed successfully" in result
        
        # Verify the image no longer exists
        with pytest.raises(docker.errors.ImageNotFound):
            docker_client.images.get(test_image)

# Network Tests
class TestNetworks:
    def test_list_networks(self):
        """Test listing networks."""
        result = run_async(run_tool(docker_mcp.list_networks))
        assert isinstance(result, str)
        
        # Parse the JSON result
        network_list = json.loads(result)
        assert isinstance(network_list, list)
        
        # Check if result contains expected fields
        if network_list:
            assert "id" in network_list[0]
            assert "name" in network_list[0]
            assert "driver" in network_list[0]
    
    def test_create_and_remove_network(self):
        """Test creating and removing a network."""
        network_name = f"{TEST_NETWORK_NAME}-create-remove"
        
        # Create the network
        result = run_async(run_tool(
            docker_mcp.create_network,
            name=network_name,
            driver="bridge"
        ))
        
        assert "Network created successfully" in result
        
        # Verify the network exists
        networks = docker_client.networks.list(names=[network_name])
        assert len(networks) > 0
        
        # Remove the network
        result = run_async(run_tool(
            docker_mcp.remove_network,
            network_id=network_name
        ))
        
        assert "removed successfully" in result
        
        # Verify the network no longer exists
        networks = docker_client.networks.list(names=[network_name])
        assert len(networks) == 0

# Volume Tests
class TestVolumes:
    def test_list_volumes(self):
        """Test listing volumes."""
        result = run_async(run_tool(docker_mcp.list_volumes))
        assert isinstance(result, str)
        
        # Parse the JSON result
        volume_list = json.loads(result)
        assert isinstance(volume_list, list)
        
        # Check if result contains expected fields
        if volume_list:
            assert "name" in volume_list[0]
            assert "driver" in volume_list[0]
            assert "mountpoint" in volume_list[0]
    
    def test_create_and_remove_volume(self):
        """Test creating and removing a volume."""
        volume_name = f"{TEST_VOLUME_NAME}-create-remove"
        
        # Create the volume
        result = run_async(run_tool(
            docker_mcp.create_volume,
            name=volume_name,
            driver="local"
        ))
        
        assert "Volume created successfully" in result
        
        # Verify the volume exists
        volumes = docker_client.volumes.list(filters={"name": volume_name})
        assert len(volumes.volumes) > 0
        
        # Remove the volume
        result = run_async(run_tool(
            docker_mcp.remove_volume,
            volume_name=volume_name
        ))
        
        assert "removed successfully" in result
        
        # Verify the volume no longer exists
        volumes = docker_client.volumes.list(filters={"name": volume_name})
        assert len(volumes.volumes) == 0

# Integration Tests
class TestIntegration:
    def test_container_with_volume_and_network(self):
        """Test creating a container with a volume and custom network."""
        # Create resources with unique names
        volume_name = f"{TEST_VOLUME_NAME}-integration"
        network_name = f"{TEST_NETWORK_NAME}-integration"
        container_name = f"{TEST_CONTAINER_NAME}-integration"
        
        # Create a volume
        result = run_async(run_tool(
            docker_mcp.create_volume,
            name=volume_name
        ))
        assert "Volume created successfully" in result
        
        # Create a network
        result = run_async(run_tool(
            docker_mcp.create_network,
            name=network_name
        ))
        assert "Network created successfully" in result
        
        # Create and run a container with the volume and on the network
        volumes = {volume_name: "/data"}
        result = run_async(run_tool(
            docker_mcp.run_container,
            image=TEST_IMAGE,
            name=container_name,
            command="sh -c 'echo content > /data/test.txt && sleep 5'",
            volumes=volumes,
            detach=True
        ))
        assert "Container started successfully" in result
        
        # Wait for the container to finish
        time.sleep(7)
        
        # Create another container to verify the data in the volume
        verify_container_name = f"{container_name}-verify"
        result = run_async(run_tool(
            docker_mcp.run_container,
            image=TEST_IMAGE,
            name=verify_container_name,
            command="cat /data/test.txt",
            volumes=volumes,
            detach=True
        ))
        assert "Container started successfully" in result
        
        # Wait for the container to finish
        time.sleep(2)
        
        # Check the logs to verify the data was preserved in the volume
        result = run_async(run_tool(
            docker_mcp.fetch_container_logs,
            container_id=verify_container_name
        ))
        assert "content" in result
        
        # Clean up
        run_async(run_tool(docker_mcp.remove_container, container_id=container_name))
        run_async(run_tool(docker_mcp.remove_container, container_id=verify_container_name))
        run_async(run_tool(docker_mcp.remove_network, network_id=network_name))
        run_async(run_tool(docker_mcp.remove_volume, volume_name=volume_name))