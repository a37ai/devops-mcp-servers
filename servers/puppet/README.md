Puppet MCP Server
==================

Overview
--------
The Puppet MCP Server is an implementation of an MCP server that integrates with the Puppet API. It facilitates various Puppet operations such as listing environments, fetching node details, retrieving facts, and running Puppet commands through orchestrated tools. With this server, you can easily interact with your Puppet infrastructure programmatically.

Features
--------
• Environment Listing: Retrieve a list of all available Puppet environments using the Puppet API.  
• Node Information: Get detailed information about specific nodes by their certname.  
• Fact Retrieval: Fetch node-specific facts to assist with infrastructure troubleshooting or reporting.  
• Puppet Command Execution: Run Puppet on specific nodes via an orchestrated command, with options for no-operation (noop) mode.  
• PuppetDB Querying: Execute PuppetDB queries to fetch detailed inventory data from your Puppet database.  

Tools & Resources
-----------------
The server exposes several resources and tools via its MCP endpoints:

Resources:
- puppet://environments  
  • Function: List all Puppet environments.  
  • Usage: Sends a GET request to /puppet/v3/environments through the Puppet API.

- puppet://nodes/{certname}  
  • Function: Retrieve node information by certname.  
  • Usage: Sends a GET request to /puppet/v3/nodes/{certname}.

- puppet://facts/{certname}  
  • Function: Get facts for a specific node.  
  • Usage: Sends a GET request to /puppet/v3/facts/{certname}.

Tools:
- run_puppet  
  • Function: Execute a Puppet run on specified nodes  
  • Inputs:  
    - nodes (list of strings): List of node identifiers  
    - environment (string, default: "production"): The target environment for the Puppet run  
    - noop (boolean, default: False): Whether to run in no-operation mode  
  • Usage: Sends a POST request to /orchestrator/v1/command/deploy with the provided data.

- query_puppetdb  
  • Function: Execute a PuppetDB query  
  • Inputs:  
    - query (string): The query to run against PuppetDB  
  • Usage: Sends a GET request to /pdb/query/v4 with the query as a parameter.

Configuration
-------------
Before running the Puppet MCP Server, ensure the following environment variables are properly set:

• PUPPET_URL  
  - Description: The base URL for your Puppet API.  
  - Example: export PUPPET_URL=https://puppet.example.com:4433

• PUPPET_AUTH_TOKEN  
  - Description: Your authentication token for accessing the Puppet API.  
  - Example: export PUPPET_AUTH_TOKEN=your_auth_token_here

Installation & Setup
----------------------
1. Prerequisites:
   - Python 3.7 or higher
   - Required dependencies: requests, mcp.server.fastmcp (Ensure you have the appropriate MCP server library installed)

2. Installation:
   - Clone the repository or download the server script.
   - Install necessary Python packages using pip. For example:
     
         pip install requests

3. Setting Environment Variables:
   - Set the required environment variables (PUPPET_URL and PUPPET_AUTH_TOKEN) in your shell or configuration file before starting the server.
   
         export PUPPET_URL=https://puppet.example.com:4433
         export PUPPET_AUTH_TOKEN=your_auth_token_here

Usage
-----
Run the Puppet MCP Server using:
     
     python <script_name>.py

Upon execution, the server will start and listen for MCP resource and tool requests. The logging is configured at the INFO level to help track operations and errors.

Handling Requests:
- For authenticated communication with the Puppet API, the server uses the helper function which automatically appends the required X-Authentication header.
- In case of request failures, errors are logged, and exceptions are raised for further analysis.

Troubleshooting
---------------
- If the environment variables PUPPET_URL or PUPPET_AUTH_TOKEN are not set, the server will log an error and request you to set these before running.
- Ensure that the Puppet API is reachable from your network, and the provided credentials have the necessary permissions for the desired endpoints.

License
-------
This project is provided as-is under the terms of its respective open-source license. Please refer to the LICENSE file for further details.

Contact
-------
For any further queries or assistance, please contact the project maintainer.

This README provides all the necessary information to setup, configure, and use the Puppet MCP Server for interacting with your Puppet infrastructure efficiently.