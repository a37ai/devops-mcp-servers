Puppet MCP Server
==================

Overview
--------
The Puppet MCP Server is an implementation built on top of FastMCP that provides a straightforward integration with a Puppet API. With this server, users can easily query Puppet environments, retrieve node details, fetch node facts, execute Puppet runs, and perform PuppetDB queries. The server handles authenticated requests to the Puppet API and offers a well-organized set of resources and tools to simplify managing Puppet operations.

Features
--------
• Authenticated Requests: Automates the authentication process using environment variables.  
• Environment Listing: Retrieve a list of all available Puppet environments.  
• Node Information: Get detailed information for a specific Puppet node by its certificate name.  
• Facts Retrieval: Fetch detailed facts for a given node.  
• Puppet Run: Trigger Puppet runs on a set of nodes with customization options (environment and noop mode).  
• PuppetDB Query: Execute custom queries against the PuppetDB endpoint.

Setup & Configuration
---------------------
1. Requirements:
   • Python 3.x  
   • The required dependencies listed in your project’s requirements.txt (typically includes requests and mcp.server.fastmcp libraries)

2. Environment Variables:  
   The server requires the following environment variables to be set for authentication with the Puppet API:
   - PUPPET_URL: The base URL of the Puppet server (e.g., https://puppet.example.com:4433).  
   - PUPPET_AUTH_TOKEN: Your Puppet authentication token.  

   Example (Linux/Mac):
     $ export PUPPET_URL=https://puppet.example.com:4433  
     $ export PUPPET_AUTH_TOKEN=your_auth_token_here

3. Logging:  
   Basic logging is set up to output timestamped logs that include the server, level, and message. Adjust logging configurations if needed.

Resources & Endpoints
----------------------
The server defines several resources corresponding to Puppet API endpoints:

• List Environments  
  Resource: puppet://environments  
  Description: Returns a list of all available Puppet environments via a GET request.

• Get Node Information  
  Resource: puppet://nodes/{certname}  
  Description: Retrieves node details using the node’s unique certificate name.  

• Get Node Facts  
  Resource: puppet://facts/{certname}  
  Description: Fetches facts pertaining to the specified node.

Tools
-----
The following tools are exposed to perform actions that modify or query Puppet’s state:

• run_puppet  
  Description: Executes a Puppet run on specified nodes.  
  Inputs:
   - nodes (list of strings): The list of node certificate names to target.  
   - environment (string, optional): Specifies the environment (default is “production”).  
   - noop (boolean, optional): Set to true if you want a no-operation (dry-run) mode.  
  Endpoint Invoked: POST on /orchestrator/v1/command/deploy

• query_puppetdb  
  Description: Executes a query against PuppetDB and returns the results.  
  Inputs:
   - query (string): The PuppetDB query string.  
  Endpoint Invoked: GET on /pdb/query/v4

Implementation Details
----------------------
• The server uses the FastMCP framework to define resources and tools with clear decorators (@mcp.resource and @mcp.tool).  
• The helper function puppet_request centralizes API calls to the Puppet server, ensuring that all API requests are authenticated via the “X-Authentication” header.  
• Error handling is in place to log issues when requests fail, making troubleshooting easier.

Running the Server
------------------
Before running the server, ensure that the required environment variables (PUPPET_URL and PUPPET_AUTH_TOKEN) are properly set. If these variables are missing, the server will log an error and exit.

To start the server, simply run the Python script:
   $ python <script_name>.py

Once running, the server will expose the defined resources and tools so that clients can perform operations on the Puppet API endpoints.

Conclusion
----------
The Puppet MCP Server streamlines interacting with your Puppet infrastructure by abstracting the direct API interactions into simple, declarative resources and tools. Whether you need to retrieve environment or node details, fetch facts, execute Puppet runs, or query PuppetDB, this server provides a robust and extendable solution for managing Puppet operations.

For further customization and advanced configurations, refer to the FastMCP documentation and integrate additional endpoints as needed.