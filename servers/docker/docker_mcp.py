"""
Docker MCP Server

This server implements the Model Context Protocol (MCP) to provide tools for
interacting with Docker. It enables management of containers, images,
networks, and volumes through a standardized interface.
"""

import json
import os
import logging
from typing import Any, Dict, List, Optional, Tuple, Union
import docker
from mcp.server.fastmcp import FastMCP, Context

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("docker-mcp")

# Initialize FastMCP server
mcp = FastMCP("docker")

# Create Docker client
try:
    docker_client = docker.from_env()
    logger.info("Successfully connected to Docker daemon")
except Exception as e:
    logger.error(f"Failed to connect to Docker daemon: {e}")
    raise

#
# Container Tools
#

@mcp.tool()
async def list_containers(show_all: bool = False) -> str:
    """List all containers or only running ones.
    
    Args:
        show_all: If True, show all containers including stopped ones. Default: False.
    
    Returns:
        String representation of containers list.
    """
    try:
        containers = docker_client.containers.list(all=show_all)
        container_list = []
        
        for container in containers:
            container_list.append({
                "id": container.short_id,
                "name": container.name,
                "image": container.image.tags[0] if container.image.tags else container.image.id,
                "status": container.status,
                "created": container.attrs["Created"],
                "ports": container.ports
            })
        
        return json.dumps(container_list, indent=2)
    except Exception as e:
        logger.error(f"Error listing containers: {e}")
        return f"Error listing containers: {str(e)}"

@mcp.tool()
async def create_container(
    image: str,
    name: Optional[str] = None,
    command: Optional[str] = None,
    ports: Optional[Dict[str, str]] = None,
    environment: Optional[Dict[str, str]] = None,
    volumes: Optional[Dict[str, str]] = None,
    detach: bool = True
) -> str:
    """Create a new container without starting it.
    
    Args:
        image: Docker image name to use.
        name: Optional name for the container.
        command: Optional command to run in the container.
        ports: Dictionary mapping container ports to host ports (e.g., {"8080/tcp": "80"}).
        environment: Dictionary of environment variables.
        volumes: Dictionary mapping host volumes to container volumes.
        detach: Run container in background. Default: True.
    
    Returns:
        Container ID or error message.
    """
    try:
        # Prepare port bindings in Docker SDK format
        port_bindings = {}
        if ports:
            for container_port, host_port in ports.items():
                port_bindings[container_port] = host_port
        
        # Prepare volume bindings in Docker SDK format
        volume_bindings = {}
        if volumes:
            for host_vol, container_vol in volumes.items():
                volume_bindings[host_vol] = {"bind": container_vol, "mode": "rw"}
        
        container = docker_client.containers.create(
            image=image,
            name=name,
            command=command,
            ports=port_bindings,
            environment=environment,
            volumes=volume_bindings,
            detach=detach
        )
        
        return f"Container created successfully with ID: {container.short_id}"
    except Exception as e:
        logger.error(f"Error creating container: {e}")
        return f"Error creating container: {str(e)}"

@mcp.tool()
async def run_container(
    image: str,
    name: Optional[str] = None,
    command: Optional[str] = None,
    ports: Optional[Dict[str, str]] = None,
    environment: Optional[Dict[str, str]] = None,
    volumes: Optional[Dict[str, str]] = None,
    detach: bool = True
) -> str:
    """Create and start a container.
    
    Args:
        image: Docker image name to use.
        name: Optional name for the container.
        command: Optional command to run in the container.
        ports: Dictionary mapping container ports to host ports (e.g., {"8080/tcp": "80"}).
        environment: Dictionary of environment variables.
        volumes: Dictionary mapping host volumes to container volumes.
        detach: Run container in background. Default: True.
    
    Returns:
        Container ID or error message.
    """
    try:
        # Prepare port bindings in Docker SDK format
        port_bindings = {}
        if ports:
            for container_port, host_port in ports.items():
                port_bindings[container_port] = host_port
        
        # Prepare volume bindings in Docker SDK format
        volume_bindings = {}
        if volumes:
            for host_vol, container_vol in volumes.items():
                volume_bindings[host_vol] = {"bind": container_vol, "mode": "rw"}
        
        container = docker_client.containers.run(
            image=image,
            name=name,
            command=command,
            ports=port_bindings,
            environment=environment,
            volumes=volume_bindings,
            detach=detach
        )
        
        return f"Container started successfully with ID: {container.short_id}"
    except Exception as e:
        logger.error(f"Error running container: {e}")
        return f"Error running container: {str(e)}"

@mcp.tool()
async def recreate_container(container_id: str, start: bool = True) -> str:
    """Recreate a container with the same settings.
    
    Args:
        container_id: ID or name of the container to recreate.
        start: Whether to start the new container after creation. Default: True.
    
    Returns:
        New container ID or error message.
    """
    try:
        # Get the container
        container = docker_client.containers.get(container_id)
        
        # Get container configuration
        config = container.attrs
        
        # Extract key configuration elements
        image = config["Config"]["Image"]
        name = config["Name"].lstrip("/")  # Remove leading slash
        command = config["Config"]["Cmd"]
        env = config["Config"]["Env"]
        
        # Convert environment variables to dictionary
        environment = {}
        if env:
            for env_var in env:
                if "=" in env_var:
                    key, value = env_var.split("=", 1)
                    environment[key] = value
        
        # Extract ports mapping
        ports = {}
        if config["HostConfig"]["PortBindings"]:
            for container_port, host_bindings in config["HostConfig"]["PortBindings"].items():
                if host_bindings:
                    # Use the first binding
                    ports[container_port] = host_bindings[0]["HostPort"]
        
        # Extract volume mappings
        volumes = {}
        if config["HostConfig"]["Binds"]:
            for binding in config["HostConfig"]["Binds"]:
                host_path, container_path = binding.split(":", 1)
                volumes[host_path] = container_path
        
        # Remove the old container
        container.remove(force=True)
        
        # Create a new container with the same configuration
        new_container = docker_client.containers.create(
            image=image,
            name=name,
            command=command,
            environment=environment,
            ports=ports,
            volumes=volumes
        )
        
        # Start the container if requested
        if start:
            new_container.start()
            status = "started"
        else:
            status = "created"
        
        return f"Container recreated and {status} with ID: {new_container.short_id}"
    except Exception as e:
        logger.error(f"Error recreating container: {e}")
        return f"Error recreating container: {str(e)}"

@mcp.tool()
async def start_container(container_id: str) -> str:
    """Start a stopped container.
    
    Args:
        container_id: ID or name of the container to start.
    
    Returns:
        Success message or error message.
    """
    try:
        container = docker_client.containers.get(container_id)
        container.start()
        return f"Container {container_id} started successfully"
    except Exception as e:
        logger.error(f"Error starting container: {e}")
        return f"Error starting container: {str(e)}"

@mcp.tool()
async def fetch_container_logs(container_id: str, tail: int = 100) -> str:
    """Fetch logs from a container.
    
    Args:
        container_id: ID or name of the container to fetch logs from.
        tail: Number of lines to fetch from the end of the logs. Default: 100.
    
    Returns:
        Container logs or error message.
    """
    try:
        container = docker_client.containers.get(container_id)
        logs = container.logs(tail=tail).decode('utf-8')
        return logs if logs else "No logs available"
    except Exception as e:
        logger.error(f"Error fetching container logs: {e}")
        return f"Error fetching container logs: {str(e)}"

@mcp.tool()
async def stop_container(container_id: str, timeout: int = 10) -> str:
    """Stop a running container.
    
    Args:
        container_id: ID or name of the container to stop.
        timeout: Timeout in seconds to wait before killing the container. Default: 10.
    
    Returns:
        Success message or error message.
    """
    try:
        container = docker_client.containers.get(container_id)
        container.stop(timeout=timeout)
        return f"Container {container_id} stopped successfully"
    except Exception as e:
        logger.error(f"Error stopping container: {e}")
        return f"Error stopping container: {str(e)}"

@mcp.tool()
async def remove_container(container_id: str, force: bool = False) -> str:
    """Remove a container.
    
    Args:
        container_id: ID or name of the container to remove.
        force: Force removal of running container. Default: False.
    
    Returns:
        Success message or error message.
    """
    try:
        container = docker_client.containers.get(container_id)
        container.remove(force=force)
        return f"Container {container_id} removed successfully"
    except Exception as e:
        logger.error(f"Error removing container: {e}")
        return f"Error removing container: {str(e)}"

#
# Image Tools
#

@mcp.tool()
async def list_images() -> str:
    """List all available Docker images.
    
    Returns:
        String representation of images list.
    """
    try:
        images = docker_client.images.list()
        image_list = []
        
        for image in images:
            tags = image.tags if image.tags else ["<none>"]
            image_list.append({
                "id": image.short_id,
                "tags": tags,
                "size": f"{image.attrs['Size'] / 1000000:.2f} MB",
                "created": image.attrs["Created"]
            })
        
        return json.dumps(image_list, indent=2)
    except Exception as e:
        logger.error(f"Error listing images: {e}")
        return f"Error listing images: {str(e)}"

@mcp.tool()
async def pull_image(image_name: str, tag: str = "latest") -> str:
    """Pull a Docker image from a registry.
    
    Args:
        image_name: Name of the image to pull.
        tag: Tag of the image to pull. Default: "latest".
    
    Returns:
        Success message or error message.
    """
    try:
        full_name = f"{image_name}:{tag}"
        docker_client.images.pull(image_name, tag=tag)
        return f"Image {full_name} pulled successfully"
    except Exception as e:
        logger.error(f"Error pulling image: {e}")
        return f"Error pulling image: {str(e)}"

@mcp.tool()
async def push_image(image_name: str, tag: str = "latest") -> str:
    """Push a Docker image to a registry.
    
    Args:
        image_name: Name of the image to push.
        tag: Tag of the image to push. Default: "latest".
    
    Returns:
        Success message or error message.
    """
    try:
        full_name = f"{image_name}:{tag}"
        auth_config = {}  # Add auth configuration if needed
        
        # This returns a generator that produces push progress
        for line in docker_client.images.push(image_name, tag=tag, stream=True, decode=True, auth_config=auth_config):
            # We could process the stream but for now we'll just ignore it
            pass
            
        return f"Image {full_name} pushed successfully"
    except Exception as e:
        logger.error(f"Error pushing image: {e}")
        return f"Error pushing image: {str(e)}"

@mcp.tool()
async def build_image(
    path: str,
    tag: str,
    dockerfile: str = "Dockerfile",
    rm: bool = True,
    nocache: bool = False
) -> str:
    """Build a Docker image from a Dockerfile.
    
    Args:
        path: Path to the directory containing the Dockerfile.
        tag: Tag to apply to the built image.
        dockerfile: Name of the Dockerfile. Default: "Dockerfile".
        rm: Remove intermediate containers. Default: True.
        nocache: Do not use cache when building the image. Default: False.
    
    Returns:
        Success message or error message.
    """
    try:
        # Check if path exists
        if not os.path.exists(path):
            return f"Error: Path {path} does not exist"
        
        # Build the image
        image, logs = docker_client.images.build(
            path=path,
            tag=tag,
            dockerfile=dockerfile,
            rm=rm,
            nocache=nocache
        )
        
        return f"Image built successfully with ID: {image.short_id}"
    except Exception as e:
        logger.error(f"Error building image: {e}")
        return f"Error building image: {str(e)}"

@mcp.tool()
async def remove_image(image_id: str, force: bool = False) -> str:
    """Remove a Docker image.
    
    Args:
        image_id: ID or name of the image to remove.
        force: Force removal of the image. Default: False.
    
    Returns:
        Success message or error message.
    """
    try:
        docker_client.images.remove(image_id, force=force)
        return f"Image {image_id} removed successfully"
    except Exception as e:
        logger.error(f"Error removing image: {e}")
        return f"Error removing image: {str(e)}"

#
# Network Tools
#

@mcp.tool()
async def list_networks() -> str:
    """List all Docker networks.
    
    Returns:
        String representation of networks list.
    """
    try:
        networks = docker_client.networks.list()
        network_list = []
        
        for network in networks:
            network_list.append({
                "id": network.short_id,
                "name": network.name,
                "driver": network.attrs["Driver"],
                "scope": network.attrs["Scope"],
                "containers": list(network.attrs["Containers"].keys()) if "Containers" in network.attrs else []
            })
        
        return json.dumps(network_list, indent=2)
    except Exception as e:
        logger.error(f"Error listing networks: {e}")
        return f"Error listing networks: {str(e)}"

@mcp.tool()
async def create_network(
    name: str,
    driver: str = "bridge",
    internal: bool = False,
    labels: Optional[Dict[str, str]] = None
) -> str:
    """Create a Docker network.
    
    Args:
        name: Name of the network to create.
        driver: Network driver to use. Default: "bridge".
        internal: Restrict external access to the network. Default: False.
        labels: Map of labels to set on the network.
    
    Returns:
        Success message or error message.
    """
    try:
        network = docker_client.networks.create(
            name=name,
            driver=driver,
            internal=internal,
            labels=labels
        )
        return f"Network created successfully with ID: {network.short_id}"
    except Exception as e:
        logger.error(f"Error creating network: {e}")
        return f"Error creating network: {str(e)}"

@mcp.tool()
async def remove_network(network_id: str) -> str:
    """Remove a Docker network.
    
    Args:
        network_id: ID or name of the network to remove.
    
    Returns:
        Success message or error message.
    """
    try:
        network = docker_client.networks.get(network_id)
        network.remove()
        return f"Network {network_id} removed successfully"
    except Exception as e:
        logger.error(f"Error removing network: {e}")
        return f"Error removing network: {str(e)}"

#
# Volume Tools
#

@mcp.tool()
async def list_volumes() -> str:
    """List all Docker volumes.
    
    Returns:
        String representation of volumes list.
    """
    try:
        volumes = docker_client.volumes.list()
        volume_list = []
        
        for volume in volumes:
            volume_list.append({
                "name": volume.name,
                "driver": volume.attrs["Driver"],
                "mountpoint": volume.attrs["Mountpoint"],
                "created": volume.attrs["CreatedAt"]
            })
        
        return json.dumps(volume_list, indent=2)
    except Exception as e:
        logger.error(f"Error listing volumes: {e}")
        return f"Error listing volumes: {str(e)}"

@mcp.tool()
async def create_volume(
    name: str,
    driver: str = "local",
    labels: Optional[Dict[str, str]] = None
) -> str:
    """Create a Docker volume.
    
    Args:
        name: Name of the volume to create.
        driver: Volume driver to use. Default: "local".
        labels: Map of labels to set on the volume.
    
    Returns:
        Success message or error message.
    """
    try:
        volume = docker_client.volumes.create(
            name=name,
            driver=driver,
            labels=labels
        )
        
        return f"Volume created successfully"
    except Exception as e:
        logger.error(f"Error creating volume: {e}")
        return f"Error creating volume: {str(e)}"

@mcp.tool()
async def remove_volume(volume_name: str, force: bool = False) -> str:
    """Remove a Docker volume.
    
    Args:
        volume_name: Name of the volume to remove.
        force: Force removal of the volume. Default: False.
    
    Returns:
        Success message or error message.
    """
    try:
        volume = docker_client.volumes.get(volume_name)
        volume.remove(force=force)
        return f"Volume {volume_name} removed successfully"
    except Exception as e:
        logger.error(f"Error removing volume: {e}")
        return f"Error removing volume: {str(e)}"

if __name__ == "__main__":
    # Run the server
    mcp.run()