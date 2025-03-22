JFrog Artifactory MCP Server
=============================

Overview
--------
The JFrog Artifactory MCP Server provides a comprehensive set of tools to manage your JFrog Artifactory instance via its REST API endpoints. With this MCP server integration, you can deploy and manage artifacts, configure repositories, manage users, monitor system health, integrate builds, manage webhooks, and control access permissions―all from a unified interface.

This implementation leverages the FastMCP framework for MCP server tooling and httpx for asynchronous HTTP operations. Whether automating artifact deployments or integrating with your build pipeline, these tools aim to streamline your DevOps and artifact management processes.

Features
--------
● Artifact Management  
  ○ Deploy artifacts to a repository  
  ○ Retrieve artifact information  
  ○ Delete artifacts  
  ○ Search for artifacts using basic parameters or the Artifactory Query Language (AQL)

● Repository Management  
  ○ Create, list, retrieve, and delete repositories  
  ○ Create federated repositories for distributed environments  
  ○ Configure repository replication

● User Management  
  ○ Create, update, retrieve, list, and delete users  
  ○ Manage user details and administrator privileges

● System Management  
  ○ Retrieve system information and configuration  
  ○ Check system health and storage details  
  ○ Retrieve Artifactory version information

● Build Integration  
  ○ Integrate build tools (e.g., Maven, Gradle) to capture build metadata

● Webhook Management  
  ○ Create webhooks for real-time event notifications

● Access Control  
  ○ Configure roles and fine-grained access permissions for repositories

Installation
------------
1. Ensure you are using Python 3.7 or later.
2. Install project dependencies using pip:

   pip install httpx python-dotenv mcp-fastmcp

3. Clone or download the repository and navigate to the project directory.

Configuration
-------------
Before running the server, configure the necessary environment variables. Create a .env file in the root directory with the following values:

   JFROG_URL="https://your.jfrog.instance.url"
   JFROG_ACCESS_TOKEN="your_access_token"

Ensure that:
• JFROG_URL points to your Artifactory server.
• JFROG_ACCESS_TOKEN contains a valid access token for API authentication.

Server Execution
----------------
The main execution is handled via the MCP server’s transport layer (using stdio by default). To start the server, execute the module:

   python your_module.py

This will activate the MCP server interface and allow you to invoke the available tools.

Tools & Endpoints
-----------------

Artifact Management Tools
~~~~~~~~~~~~~~~~~~~~~~~~~
• deploy_artifact(repo_key, item_path, file_path)  
  Deploy a local file as an artifact to the specified repository and path.

• get_artifact_info(repo_key, item_path)  
  Retrieve metadata and details about a specific artifact.

• delete_artifact(repo_key, item_path)  
  Delete an artifact from a repository.

• search_artifacts(name, repos, properties)  
  Search for artifacts by name, repository or properties.

• advanced_search(query)  
  Execute complex searches using the Artifactory Query Language (AQL).

Repository Management Tools
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
• create_repository(repo_key, repo_type, package_type)  
  Create a new repository with a specified type (local, remote, virtual, federated) and package type.

• get_repository(repo_key)  
  Retrieve repository details.

• list_repositories(repo_type)  
  List all repositories, optionally filtering by repository type.

• delete_repository(repo_key)  
  Delete a repository.

• create_federated_repository(repo_key, package_type)  
  Create a federated repository for distributed environments.

• setup_repository_replication(repo_key, target_url, username, password)  
  Configure replication between repositories for redundancy.

User Management Tools
~~~~~~~~~~~~~~~~~~~~~
• create_user(username, email, password, admin)  
  Create a new user with specified details and optionally grant admin privileges.

• get_user(username)  
  Retrieve information about a specific user.

• list_users()  
  List all users.

• update_user(username, email, password, admin)  
  Update an existing user’s details.

• delete_user(username)  
  Delete a specified user.

System Management Tools
~~~~~~~~~~~~~~~~~~~~~~~
• get_system_info()  
  Retrieve overall system information from Artifactory.

• get_system_health()  
  Check the system’s health across multiple endpoints.

• get_system_configuration()  
  Retrieve system configuration (admin privileges required).

• get_storage_info()  
  Get detailed storage information.

• get_version()  
  Retrieve Artifactory version details.

Build Integration Tool
~~~~~~~~~~~~~~~~~~~~~~
• integrate_build(build_name, build_number)  
  Integrate with build tools to capture build metadata in Artifactory.

Webhook Management
~~~~~~~~~~~~~~~~~~
• create_webhook(name, url, events)  
  Create a webhook for real-time notifications based on system events.

Access Control
~~~~~~~~~~~~~~
• manage_permissions(name, repositories, principals)  
  Configure fine-grained permissions and access roles across repositories.

Usage Examples
--------------
Example: Deploy an Artifact  
---------------------------------------------------
To deploy an artifact:

   result = await deploy_artifact("example-repo", "path/to/artifact.txt", "/local/path/artifact.txt")
   print(result)

Example: Get Artifact Information  
---------------------------------------------------
To retrieve artifact details:

   info = await get_artifact_info("example-repo", "path/to/artifact.txt")
   print(info)

Example: Create a New Repository  
---------------------------------------------------
To create a repository:

   message = await create_repository("new-repo", "local", "generic")
   print(message)

Contributing
------------
Contributions to enhance the tools or documentation are welcome. Please adhere to standard contribution practices: fork the repository, commit changes with descriptive messages, and submit a pull request.

License
-------
This project is provided under the MIT License. See the LICENSE file for details.

Contact
-------
For further inquiries or assistance with the JFrog Artifactory MCP Server, please reach out to the project maintainer or consult the project repository for support channels.

Conclusion
----------
The JFrog Artifactory MCP Server is a powerful solution for managing your artifact lifecycle directly through the JFrog REST API. Its wide array of tools enables swift deployment, management, and monitoring of repositories and artifacts, blending seamlessly into modern DevOps workflows.