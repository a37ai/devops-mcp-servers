Argo CD MCP Server
────────────────────

The Argo CD MCP Server is a server implementation that leverages the Model Context Protocol (MCP) to interact with the Argo CD API. It provides a collection of tools to manage applications, projects, repositories, and clusters, as well as retrieve version and settings information directly from an Argo CD instance.

Features
────────
• Application Management:
  - List applications with optional project filtering
  - Retrieve detailed information on a specific application
  - Create and delete applications with configurable parameters
  - Sync applications to ensure deployments are up to date

• Project Management:
  - List all projects
  - Inspect details of a specific project  
  - Create and delete projects

• Repository Management:
  - List all repositories
  - Retrieve, create, and delete repositories with credentials support  
   
• Cluster Management:
  - List available clusters
  - Retrieve details about a specific cluster just by providing its server URL

• Utility Tools:
  - Get Argo CD version information
  - Retrieve current Argo CD settings

Tools Overview
──────────────
The server exposes the following tools via MCP. Each tool corresponds to an API operation in Argo CD and accepts meaningful parameters as described below:

• list_applications
  • List all applications with optional filtering by project.
  • Inputs:
    – project (string, optional): Filter applications by project name
    – limit (number, optional): Maximum number of results (default 100)
    – offset (number, optional): Number of results to skip (default 0)

• get_application
  • Get detailed information about an application.
  • Inputs:
    – name (string): Application name
    – project (string, optional): Project name the application belongs to

• create_application
  • Create a new application in Argo CD.
  • Inputs:
    – name (string): Application name
    – project (string): Project name
    – repo_url (string): Repository URL for the source code
    – path (string): Path within the repository
    – dest_server (string): Destination server for deployment
    – dest_namespace (string): Destination namespace for deployment

• delete_application
  • Delete an application and optionally cascade delete associated resources.
  • Inputs:
    – name (string): Application name
    – cascade (boolean, optional): Whether to cascade delete resources (default: True)

• sync_application
  • Trigger synchronization of an application.
  • Inputs:
    – name (string): Application name
    – revision (string, optional): Git revision identifier (defaults to HEAD)
    – prune (boolean, optional): Whether to prune resources during sync (default: False)

• list_projects / get_project / create_project / delete_project
  • Manage projects with operations to list, inspect, create, and delete projects.
  • Inputs vary according to the operation (e.g., project name, description, and source repos for create_project)

• list_repositories / get_repository / create_repository / delete_repository
  • Handle repository operations in a similar fashion.
  • Inputs include repository URLs and optional credentials (username, password, or SSH key)

• list_clusters / get_cluster
  • List clusters and retrieve details for a specific cluster using its server URL.

• get_version
  • Retrieve Argo CD version information.

• get_settings
  • Retrieve current settings from the Argo CD instance.

Configuration
─────────────
Before running the server, ensure you configure the following environment variables, typically placed in a .env file:

• ARGOCD_URL       – The base URL of your Argo CD instance (e.g., https://argocd.example.com/)
• ARGOCD_USERNAME  – Username for authentication with Argo CD
• ARGOCD_PASSWORD  – Password for authentication
• ARGOCD_TOKEN     – (Optional) Pre-generated API token; if not provided, the client will attempt token retrieval using username and password

Getting Started
───────────────
1. Installation:
   • Ensure you have Python installed.
   • Install the required dependencies:
     $ pip install -r requirements.txt

2. Configuration:
   • Create a .env file in your project root and add your Argo CD credentials:
     
       ARGOCD_URL=https://your-argocd-instance.com/
       ARGOCD_USERNAME=your_username
       ARGOCD_PASSWORD=your_password
       ARGOCD_TOKEN=your_optional_token
     
3. Running the Server:
   • Start the MCP server with:
     
       $ python your_script_name.py
     
   • The server will run using stdio transport and expose all defined tools.

4. Using the Tools:
   • Invoke any tool (e.g., list_applications or create_application) via your MCP client. Every tool accepts clearly defined inputs that correspond to Argo CD API operations.

Development & Customization
─────────────────────────────
• The server code is built on top of the FastMCP framework which simplifies exposing functions as remote procedure calls.
• Each tool leverages structured models (using pydantic) to validate inputs, making customization and extension straightforward.
• To add new functionality, create additional tools following the existing pattern and register them with the MCP server.

Security Notice
───────────────
• SSL certificate verification is disabled by default for simplicity. In a production environment, it is recommended to enable certificate verification by setting up proper certificates or adjusting the code configuration.

License
───────
MIT License

For more detailed usage and API documentation, please refer to the official Argo CD API documentation and the FastMCP framework documentation.