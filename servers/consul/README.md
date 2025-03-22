Consul MCP Server
=================

Overview
--------
Consul MCP Server is a Model Context Protocol server that exposes Consul API functionality as easily accessible tools for LLMs. It enables programmatic access to various Consul operations, making service discovery, registration, and configuration management tasks seamless.

Features
--------
• Interact with Consul’s Catalog:  
  – List available datacenters  
  – Query nodes and services within a datacenter

• Service Management:  
  – Register new services  
  – Deregister existing services

• Health and Query Tools:  
  – Retrieve service health information  
  – Execute prepared queries

• ACL & Service Mesh Controls:  
  – Create ACL tokens with customizable policies, roles, and service identities  
  – Manage service mesh intentions (allow/deny) with metadata support

• KV Store Operations:  
  – Get, put, and delete key-value pairs in Consul’s KV store with options for recursive deletion and raw retrieval

Tools and Endpoints
-------------------
The server exposes its functionality as a suite of tools via MCP. Each tool corresponds to a specific Consul API operation:

1. list_datacenters  
  • Returns a list of all known Consul datacenters.

2. list_nodes(dc, near, filter)  
  • Retrieves nodes registered in a datacenter, with options for sorting (near) and filtering.

3. list_services(dc)  
  • Fetches the list of registered services in the catalog.

4. register_service(name, id, address, port, tags, meta, dc)  
  • Registers a new service. Inputs include name, optional unique ID, address, port, tags (as a comma-separated list), and metadata (JSON string).

5. deregister_service(service_id, node, dc)  
  • Deregisters a service from the catalog. Requires the node identifier.

6. health_service(service, dc, passing, near, filter)  
  • Retrieves health check information for a specific service with optional filtering and sorting.

7. create_acl_token(description, policies, roles, service_identities, expires_after)  
  • Creates a new ACL token, allowing association with policies, roles, and service identities. Tokens can be set to expire after a defined duration.

8. execute_prepared_query(query_id, dc)  
  • Executes a pre-defined query against the Consul catalog.

9. create_intention(source_name, destination_name, action, description, meta)  
  • Creates or updates service mesh intentions, defining the allowed or denied interactions between services.

10. KV Store Operations – kv_get(key, dc, recurse, raw), kv_put(key, value, dc, flags, cas), kv_delete(key, dc, recurse)  
  • Perform get, put, and delete operations on Consul’s key-value store with various options for precision and recursion.

Configuration
-------------
• Environment Variables  
  – CONSUL_URL: Base URL of your Consul server (e.g., http://localhost:8500)  
  – CONSUL_TOKEN: (Optional) Access token for authenticated Consul API calls

• Dotenv Integration  
  The server uses python-dotenv to load environment variables from a .env file. Make sure to create and configure your .env file accordingly.

Installation and Setup
----------------------
1. Clone the Repository  
  Download or clone the repository containing the MCP server implementation.

2. Install Dependencies  
  Use pip to install the required packages:  
   pip install -r requirements.txt

3. Configure Environment Variables  
  Create a .env file at the root of the project and define the CONSUL_URL and (if needed) the CONSUL_TOKEN variable.

4. Run the MCP Server  
  Launch the server by executing the main module:  
   python <filename.py>  
  The MCP server will initialize and begin exposing Consul API tools for LLM integration.

Usage
-----
Once running, the server exposes its tools over the defined MCP interface. Call any of the available functions (e.g., list_datacenters, register_service) from your LLM or integration client. Outputs are returned as formatted JSON strings suitable for further processing.

Contributing
------------
Contributions, issues, and feature requests are welcome. Please feel free to submit pull requests or open an issue to improve the functionality and robustness of the Consul MCP Server.

License
-------
This project is open source. Please refer to the LICENSE file for details.

Contact
-------
For questions and further information, please contact the project maintainers or open an issue in the project's repository.

By integrating Consul's powerful service discovery and configuration management capabilities into a unified MCP server, this project aims to simplify and enhance automation and orchestration tasks for modern distributed systems.