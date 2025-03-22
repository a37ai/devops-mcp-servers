Nexus MCP Server
================

Overview
--------
The Nexus MCP Server is a modular control panel (MCP) implementation that integrates with Nexus Repository Manager via its REST API. This server provides a collection of endpoints to manage repositories, users, roles, content, LDAP configurations, content selectors, privileges, repository firewall configurations, IQ server features, and webhooks. Each function is exposed as a tool, making it easy to orchestrate and automate various administrative tasks in Nexus.

Features
--------
• Repository Management: Retrieve, create, update, and delete repositories with support for different repository types and formats.  
• User & Role Management: Manage users and roles including creation, updates, and deletion with detailed configurations.  
• Content Management: Search for and upload components to repositories.  
• LDAP & External Authentication: List and configure LDAP servers for external authentication.  
• Content Selectors: Define custom content selectors via CSEL expressions.  
• Privileges Management: Configure and manage repository privileges.  
• Repository Firewall Configuration: Retrieve and update firewall settings to secure your repositories.  
• IQ Server Integration: Enable or disable SBOM binary scanning via Nexus IQ server endpoints.  
• Webhooks & Automation: Configure webhooks for automated notifications and integrations with external systems.  
• Version Checking: Retrieve Nexus version information using multiple fallback endpoints.

Installation & Setup
--------------------
1. Prerequisites:
   • Python 3.7 or higher  
   • Pip package manager

2. Clone this repository and install the required dependencies:
   • Install dependencies using pip:
     
     pip install requests python-dotenv

3. Environment Configuration:
   Create a .env file in the project root with the following variables:
     
     NEXUS_URL=https://your-nexus-instance-url
     NEXUS_USERNAME=your_nexus_username  # (default is "admin" if not provided)
     NEXUS_PASSWORD=your_nexus_password

   • Ensure that the NEXUS_URL does not have a trailing slash. The server reads environment variables at runtime, ensuring up-to-date configuration.

Usage
-----
1. Run the MCP Server:
   
      python your_script_name.py

   This action will start the server and expose all configured MCP tools/endpoints.

2. Tool Endpoints:
   Each function is decorated with @mcp.tool(), making it invocable as a command. Tools include:

   • Repository Management Endpoints:
     - get_all_repositories(): Retrieves a list of all repositories.
     - create_repository(...): Creates a new repository.
     - update_repository(...): Updates a repository configuration.
     - delete_repository(...): Deletes a specified repository.

   • User & Role Management Endpoints:
     - get_all_users(): Retrieves all users.
     - create_user(...): Creates a new user.
     - update_user(...): Updates an existing user.
     - delete_user(...): Deletes a specified user.
     - list_roles(): Lists all roles.
     - create_role(...): Creates a new role.

   • Content Management Endpoints:
     - search_components(...): Searches assets within repositories.
     - upload_component(...): Uploads a component to a repository.

   • LDAP & External Authentication Endpoints:
     - list_ldap_servers(): Retrieves all configured LDAP servers.
     - create_ldap_server(...): Configures a new LDAP server.
     - delete_ldap_server(...): Deletes an existing LDAP server configuration.

   • Content Selectors Endpoints:
     - list_content_selectors(): Lists defined content selectors.
     - create_content_selector(...): Creates a new content selector.

   • Privileges Management Endpoints:
     - list_privileges(): Lists all defined privileges.
     - create_privilege(...): Creates a new privilege with specific properties (provide JSON formatted properties).

   • Repository Firewall Configuration Endpoints:
     - get_firewall_config(): Retrieves current firewall configuration.
     - update_firewall_config(...): Updates firewall settings.

   • IQ Server Feature Endpoints:
     - update_sbom_scanning(...): Enables or disables SBOM binary scanning.

   • Webhooks & Automation Endpoints:
     - list_webhooks(): Lists all configured webhooks.
     - create_webhook(...): Creates a new webhook with optional additional configurations.
     - check_nexus_version(): Retrieves Nexus version information using multiple fallback endpoints.

3. Making API Requests:
   Each tool function internally calls the Nexus API via helper functions like make_request(). This function manages requests with proper error handling and even supports fallback strategies (e.g., alternative API versions or prefixes). HTTP methods such as GET, POST, PUT, and DELETE are supported.

Configuration Details
---------------------
• Base URL Resolution:
  The function get_base_url() constructs the API base URL using the NEXUS_URL environment variable and the specified API version (default is v1).
  
• Authentication:
  The function get_auth() retrieves the Nexus username and password from environment variables, defaulting to "admin" for username if not provided.

• Error Handling:
  HTTP errors are captured and parsed. In cases of 404 errors, the server attempts alternate endpoints or API versions (like "beta") to gracefully handle differences in Nexus implementations.

Advanced Customizations
-----------------------
• Tailor Endpoints:  
  Each endpoint is configurable. For instance, the repository creation payload is simplified and can be extended based on the repository type and format details.
  
• Extension Capability:  
  The tool-based approach makes it straightforward to add additional endpoints or integrations. Simply create new functions, decorate them with @mcp.tool(), and implement the appropriate API interactions.

Support & Contribution
----------------------
Feel free to open issues or contribute by forking the repository and submitting pull requests. Contributions and improvements are welcome to enhance the Nexus MCP Server capabilities and integrations.

License
-------
Distributed under the MIT License. See LICENSE for more information.

Contact
-------
For questions or support, please contact the maintainers via the project's issue tracker on GitHub.

By following this guide, you can efficiently manage your Nexus Repository Manager instance using a robust, API-driven control panel setup. Happy managing!