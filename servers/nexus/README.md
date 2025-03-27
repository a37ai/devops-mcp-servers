Nexus MCP API Integration
===========================

Overview
--------
The Nexus MCP API Integration is a robust implementation built on top of the FastMCP framework. It provides a suite of tools to manage Nexus repositories, users, roles, components, LDAP servers, content selectors, webhooks, and repository firewall configuration through a series of RESTful endpoints. This implementation leverages Pydantic models to validate data and provides flexible fallback mechanisms across different API versions for improved resilience.

Features
--------
• Repository Management  
  – Retrieve, create, update, and delete repositories (hosted, proxy, and group)  
  – Support for Nexus-specific configurations (e.g., Maven, npm)  

• User and Role Management  
  – Create, update, and delete users  
  – Manage roles and privileges  

• Content Management  
  – Search for components or assets in repositories  
  – Upload new components  

• LDAP & External Authentication  
  – List and create LDAP server configurations  

• Webhooks and Automation  
  – List and create webhooks for event notifications  

• Repository Firewall Configuration  
  – Retrieve and update firewall settings (IQ server integration)

Installation
------------
1. Clone the repository:
  git clone https://github.com/yourusername/nexus-mcp-api.git

2. Change into the project directory:
  cd nexus-mcp-api

3. (Optional) Create and activate a virtual environment:
  python -m venv venv  
  source venv/bin/activate      # On Windows use: venv\Scripts\activate

4. Install the dependencies:
  pip install -r requirements.txt

Dependencies include:
  • requests  
  • python-dotenv  
  • pydantic  
  • FastMCP (from mcp.server.fastmcp)

Configuration
-------------
Before running the server, create a .env file in the project root directory and configure the following environment variables:

  NEXUS_URL=https://nexus.example.com  
  NEXUS_USERNAME=admin  
  NEXUS_PASSWORD=yourpassword

These variables ensure that the API requests are properly authenticated and are directed to the correct Nexus instance.

Endpoints & Usage
-----------------
The server defines a number of endpoints organized into several functional areas. Each function is decorated with @mcp.tool() and can be invoked via the FastMCP server. The main endpoint categories include:

1. Repository Management Endpoints:
  • get_all_repositories() – Retrieves a list of all repositories.
  • create_repository(...) – Creates a new repository (configurable as hosted, proxy, or group).
  • update_repository(...) – Updates an existing repository’s configuration.
  • delete_repository(...) – Deletes a repository by its name.

2. User and Role Management Endpoints:
  • get_all_users() – Fetches all users configured in Nexus.
  • create_user(...) – Creates a new user using provided credentials and role assignments.
  • update_user(...) – Updates user details, supporting various endpoint formats.
  • delete_user(...) – Deletes a user from the system.
  • list_roles(), create_role(...) – Manage roles.
  • list_privileges() – Lists all privileges available in the system.

3. Content Management Endpoints:
  • search_components(...) – Searches repositories for components or assets using flexible query parameters.
  • upload_component(...) – Uploads a new component to a specified repository.

4. LDAP and External Authentication Endpoints:
  • list_ldap_servers() – Lists current LDAP server configurations.
  • create_ldap_server(...) – Creates a new LDAP server configuration with customizable connection settings.

5. Content Selectors Endpoints:
  • list_content_selectors() – Retrieves content selector definitions.
  • create_content_selector(...) – Creates a new content selector based on CSEL expressions.

6. Webhooks and Automation Endpoints:
  • list_webhooks() – Fetches all configured webhooks.
  • create_webhook(...) – Creates a new webhook for handling various Nexus events.

7. Repository Firewall Configuration Endpoints:
  • get_firewall_config() – Retrieves the current firewall configuration.
  • update_firewall_config(...) – Updates firewall settings for repository IQ integration.

Each endpoint includes detailed inline documentation describing the expected inputs, HTTP method (GET, POST, PUT, DELETE), and the endpoint’s behavior. The implementation also handles fallback across multiple API versions (v1, beta, v1/beta, and REST v0) if the primary endpoint does not yield a successful response.

Running the Server
------------------
To start the MCP server, simply run the main Python file:

  python your_script.py

The FastMCP server instance (initialized as “mcp”) will start up and listen for incoming requests. Tools can be accessed and executed according to your FastMCP deployment strategy.

Error Handling & Fallbacks
--------------------------
The “make_request” helper function encapsulates the HTTP calls to the Nexus API. It handles errors gracefully and employs multiple fallback attempts by trying alternate endpoint prefixes or different API versions. In the case of no content responses (HTTP 204), it provides a success message; otherwise, it returns detailed error information.

Contributing
------------
Contributions are welcome. Please fork the repository, make your changes, and open a pull request. Ensure that any changes are properly documented and that the code adheres to the project’s style guidelines.

License
-------
This project is licensed under the [MIT License](LICENSE).

Contact
-------
For issues, questions, or feature requests, please open an issue in the repository or contact the maintainer at your.email@example.com.

Enjoy managing your Nexus instance with the Nexus MCP API Integration!