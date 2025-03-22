CircleCI MCP Server
=====================

Overview
--------
The CircleCI MCP Server is an implementation that maps CircleCI API endpoints to a suite of tools, enabling a Language Model (LLM) to interact directly with CircleCI projects, pipelines, workflows, jobs, and more. With this server, you can perform a wide range of operations – from creating and managing contexts and environment variables to triggering pipelines, fetching insights, handling webhooks, and managing policies.

Key Features
------------
•  Comprehensive API Coverage:  
   - Interact with CircleCI contexts, pipelines, jobs, workflows, projects, schedules, webhooks, and policies.  
   - Query insights and metrics including summary and timeseries data.

•  Context Management:  
   - Create, list, update, and delete contexts.  
   - Manage environment variables and project restrictions within contexts.

•  Pipeline & Job Control:  
   - Trigger new pipelines, continue pipelines from the setup phase, and fetch detailed pipeline configurations.
   - Cancel and retrieve job details and artifacts.

•  Workflow Operations:  
   - Approve, cancel, and rerun workflows.
   - Retrieve workflow summary details and associated jobs.

•  Project & Schedule Administration:  
   - Create projects, manage checkout keys, and environment variables.
   - Create, list, update, and delete project schedules.

•  Webhook & Policy Management:  
   - Setup, update, and delete outbound webhooks to receive event notifications.
   - Manage custom OIDC claims and policy bundles to enforce security and access controls.

•  User & Collaboration Endpoints:  
   - Fetch current user details and list collaborations for seamless integration with CircleCI accounts.

Configuration & Setup
---------------------
1. Environment Variables
   - Ensure the following environment variables are set in your environment (e.g., via a .env file):

     • CIRCLECI_API_KEY  
       Your CircleCI API key obtained from the CircleCI developer dashboard.
     
     • CIRCLECI_API_BASE (optional)  
       Defaults to "https://circleci.com/api/v2" if not provided.
   
   Example .env file:
   
       CIRCLECI_API_KEY=your_circleci_api_key_here
       CIRCLECI_API_BASE=https://circleci.com/api/v2

2. API Key Requirement
   - The MCP server checks for the presence of the CIRCLECI_API_KEY on startup. Failure to set this environment variable will result in a ValueError. Make sure you sign up for an API account with CircleCI and follow their guidelines to obtain your API key.

3. Dependencies
   - Python 3.7+
   - Required libraries: httpx, pydantic, python-dotenv, FastMCP (from mcp.server.fastmcp)

4. Installation
   - Install the dependencies with pip:

         pip install httpx pydantic python-dotenv fastmcp

   - Add any additional dependencies as needed by your project.

Usage
-----
The MCP server is designed to expose a variety of tools (decorated with @mcp.tool()) which map directly to CircleCI API endpoints. You can run the server directly:

     python your_script.py

When executed, the server initializes and starts listening for incoming tool requests. Each tool function corresponds to a specific CircleCI API endpoint, performing actions such as:
  
   • Creating and retrieving contexts  
   • Listing project pipelines and triggering new pipelines  
   • Cancelling jobs and retrieving job details/artifacts  
   • Managing workflow actions (approve, cancel, rerun)  
   • Creating schedules, setting webhooks, and updating project settings  
   • Handling OIDC token claims and policy bundles for secure interactions  
   • Retrieving user and collaboration information
   
For each tool, the function arguments are clearly documented. For example:

   - create_context(name: str, owner: Dict)  
     Creates a new context with the specified name and owner details.
   
   - trigger_pipeline(project_slug: str, branch: Optional[str]=None, tag: Optional[str]=None, parameters: Optional[Dict]=None)  
     Triggers a new pipeline for the given project.

Refer to each function’s docstring in the source code for detailed usage instructions and expected input parameters.

Advanced Usage & Customization
-------------------------------
• Middleware & Error Handling:
  - The server uses httpx for asynchronous HTTP requests and handles errors with proper exception messages including HTTP status codes and error details.

• Extensibility:
  - Additional endpoints can be integrated by adding new tool functions decorated with @mcp.tool(), following the provided examples.
  
• Integration with LLMs:
  - The server is ideally designed for LLM-based interactions, where high-level commands are translated into API calls against a CircleCI environment.

Support & Additional Information
----------------------------------
For further details, refer to the CircleCI API documentation:  
https://circleci.com/docs/api/v2/  

Contributions and enhancements are welcome. Please follow best practices and ensure that any modifications maintain the professional and descriptive structure of tool implementations.

License
-------
This project is released under an open source license. Please review the LICENSE file for more information.

Contact
-------
For questions or further details, feel free to reach out via the project's repository issues or the support channel provided by your organization.

Happy automating your CircleCI projects with the CircleCI MCP Server!