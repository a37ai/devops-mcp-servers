Docker MCP Server
==================

The Docker MCP Server is an implementation of the Model Context Protocol (MCP) that provides a standardized interface for interacting with Docker. With this server, you can manage containers, images, networks, and volumes efficiently through a suite of asynchronous tools.

Overview
--------

This server leverages the Docker Python API to enable the following operations:

• Container management – list, create, run, recreate, start, fetch logs, stop, and remove containers  
• Image management – list images, pull, push, build, and remove images  
• Network management – list, create, and remove Docker networks  
• Volume management – list, create, and remove Docker volumes

By providing these endpoints, the server abstracts common Docker operations behind a simple MCP interface, making it easier to integrate Docker management into your workflows.

Features
--------

• Robust Container Tools:  
 – List running or all containers  
 – Create new containers without starting them  
 – Create and immediately run containers  
 – Recreate containers with existing settings  
 – Start or stop containers, fetch logs, and remove containers  

• Comprehensive Image Tools:  
 – List available Docker images  
 – Pull images from any Docker registry  
 – Push local images to a registry  
 – Build images from Dockerfiles  
 – Remove images as needed  

• Flexible Network Tools:  
 – List Docker networks with detailed metadata  
 – Create new networks with customizable drivers and labels  
 – Remove networks seamlessly  

• Versatile Volume Tools:  
 – List volumes including details such as mount point and creation time  
 – Create volumes with specified drivers and labels  
 – Remove volumes, with force option for active volumes  

• Standardized MCP Interface:  
 – All tools are exposed via the MCP protocol using asynchronous functions  
 – Easy integration with other systems that support MCP  

Installation & Prerequisites
----------------------------

1. Docker Environment:  
 Ensure that Docker is installed and the Docker daemon is running on your system.

2. Python Dependencies:  
 • Python 3.7 or higher  
 • Docker Python SDK  
 • MCP Server (FastMCP and Context modules)

3. Install required Python packages (if not already installed):  
 pip install docker fastmcp

4. Clone or download the Docker MCP Server code to your local environment.

Configuration
-------------

• The Docker client is created using the environment settings (docker.from_env()), so ensure that your environment is configured to connect to the Docker daemon correctly.  
• Logging is configured at the INFO level to provide runtime feedback on operations and errors.

Usage
-----

To start the Docker MCP Server, simply run the Python script:

 python docker_mcp_server.py

This will initialize the MCP server with the “docker” context and bind all the defined tools for container, image, network, and volume management.

Tools Reference
---------------

Below is an overview of the available MCP tools and their key parameters:

Container Tools
~~~~~~~~~~~~~~~~
1. list_containers(show_all: bool = False)  
 • Lists running containers by default; set show_all=True to include stopped containers.

2. create_container(...):  
 • Creates a new container without starting it.  
 • Parameters include image, name, command, ports, environment, volumes, and detach flag.

3. run_container(...):  
 • Creates and starts a container based on the provided configuration.

4. recreate_container(container_id: str, start: bool = True)  
 • Recreates a container using its current settings. Optionally starts the container.

5. start_container(container_id: str)  
 • Starts a stopped container.

6. fetch_container_logs(container_id: str, tail: int = 100)  
 • Retrieves container logs, showing the last ‘tail’ number of lines.

7. stop_container(container_id: str, timeout: int = 10)  
 • Stops a running container with a given timeout before forcefully stopping it.

8. remove_container(container_id: str, force: bool = False)  
 • Removes a container, with an option to force removal even if running.

Image Tools
~~~~~~~~~~~
1. list_images()  
 • Lists all available Docker images with details such as size and creation time.

2. pull_image(image_name: str, tag: str = "latest")  
 • Pulls an image from a Docker registry.

3. push_image(image_name: str, tag: str = "latest")  
 • Pushes a local image to a registry.

4. build_image(path: str, tag: str, dockerfile: str = "Dockerfile", rm: bool = True, nocache: bool = False)  
 • Builds an image from a specified Dockerfile.

5. remove_image(image_id: str, force: bool = False)  
 • Removes a Docker image.

Network Tools
~~~~~~~~~~~~~
1. list_networks()  
 • Lists Docker networks with details including driver and associated containers.

2. create_network(name: str, driver: str = "bridge", internal: bool = False, labels: Optional[Dict[str, str]] = None)  
 • Creates a new Docker network with customizable settings.

3. remove_network(network_id: str)  
 • Removes a Docker network by ID or name.

Volume Tools
~~~~~~~~~~~~
1. list_volumes()  
 • Lists all Docker volumes with metadata such as mountpoint and creation time.

2. create_volume(name: str, driver: str = "local", labels: Optional[Dict[str, str]] = None)  
 • Creates a new volume using the specified driver and labels.

3. remove_volume(volume_name: str, force: bool = False)  
 • Removes a volume, with an option to force removal.

Logging & Error Handling
-------------------------
• The server utilizes the Python logging module configured at the INFO level to report successful operations and errors.  
• Each tool function is designed to catch exceptions and return concise error messages, ensuring proper feedback during interactions.

Conclusion
----------
The Docker MCP Server offers a robust, standardized interface for managing Docker resources. Whether you are integrating it into larger orchestration workflows or need a simple way to manage Docker via MCP, this server provides the necessary tools in an organized, asynchronous framework.

For further questions or contributions, please refer to the project repository and associated documentation.

Happy Dockering!