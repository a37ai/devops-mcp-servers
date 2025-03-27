CircleCI MCP Server
===================

Overview
--------
The CircleCI MCP Server is an advanced Microservice Control Protocol (MCP) server that provides a comprehensive interface to the CircleCI API. It exposes a collection of tools mapped directly to CircleCI endpoints, enabling seamless interaction with CircleCI projects, pipelines, workflows, jobs, and additional resources. This server is designed to facilitate programmatic CircleCI operations, making it ideal for integrating with large language models (LLMs) or building custom automation workflows.

Features
--------
• Comprehensive API Coverage:  
  Interact with CircleCI projects, pipelines, workflows, jobs, contexts, environment variables, schedules, and more.  
• Context Management:  
  Create, retrieve, update, and delete contexts and related restrictions and environment variables.  
• Pipeline Operations:  
  List, trigger, continue, and extract configurations/details of pipelines including support for advanced pipeline triggers.  
• Workflow and Job Control:  
  Manage workflows (query, cancel, rerun, approve jobs) and access detailed job information and artifacts.  
• Insights and Metrics:  
  Retrieve summary and timeseries metrics for projects and organizations to monitor performance.  
• Webhook and Policy Management:  
  Manage outbound webhooks for event-driven integrations and configure policy-related endpoints for decision-making audits.  
• OIDC Token Custom Claims:  
  Provides endpoints for managing org- and project-level custom claims for OIDC identity tokens.

Tools & Endpoints
------------------
The server registers a diverse set of tools that use various HTTP methods to interact directly with CircleCI API endpoints. Some of the key tools include:

• Context Management  
  – create_context(name, owner)  
  – list_contexts(owner_id, owner_slug, owner_type, page_token)  
  – get_context(context_id)  
  – delete_context(context_id)  
  – Manage environment variables and restrictions (add, update, remove).  

• Pipeline Operations  
  – list_pipelines(org_slug, page_token, mine)  
  – continue_pipeline(continuation_key, configuration, parameters)  
  – get_pipeline(pipeline_id)  
  – get_pipeline_config(pipeline_id)  
  – trigger_pipeline(project_slug, branch, tag, parameters)  
  – Trigger a new pipeline with trigger_new_pipeline(...).  

• Workflow & Job Management  
  – Get workflow details, cancel or rerun workflows, and approve pending jobs.  
  – Retrieve job details, cancel jobs by number or ID, and list job artifacts and test metadata.

• Insight & Reporting  
  – get_project_summary_metrics, get_job_timeseries_data, get_org_summary_metrics  
  – Retrieve branch and workflow-level insights for precise monitoring and reporting.

• Webhook & Policy Endpoints  
  – Create, update, list, and delete webhooks.  
  – Manage decision audit logs, policy bundles, and custom claims for enhanced security and compliance.

• User & Collaboration Management  
  – get_current_user, get_collaborations, and get_user to provide user-specific information for integration.

Configuration & Setup
---------------------
1. Environment Variables:  
   Before running the server, ensure that the following environment variables are set:

   • CIRCLECI_API_KEY  
  Your CircleCI API key. This is required to authenticate API requests.

   • CIRCLECI_API_BASE (optional)  
  Defaults to "https://circleci.com/api/v2". Update this if using an alternative API endpoint.

2. Installation:  
   – Clone or download the repository containing the CircleCI MCP Server code.  
   – Install the required Python packages. For example:

   pip install httpx pydantic python-dotenv

3. Running the Server:  
   Execute the server directly from the command line:

   python your_script_name.py

   This will initialize the MCP server with the "CircleCI" namespace and expose all the defined tools for use.

Usage
-----
Each tool function is decorated with @mcp.tool() and represents an endpoint corresponding to a CircleCI API operation. Tools accept specific parameters and return JSON responses directly from CircleCI. This design allows an LLM or any client to seamlessly invoke these tools and manage CircleCI resources programmatically.

For example, to trigger a new pipeline for a given project, call the tool “trigger_pipeline” with the appropriate project slug, branch, tag, and optional parameters. Similarly, to manage contexts or fetch workflow details, utilize the corresponding tool endpoint as documented.

Development & Contributing
--------------------------
• Code Structure:  
  The server uses Pydantic models to clearly define request/response schemas for all endpoints.  
  HTTP requests are handled asynchronously via the httpx library to ensure efficient interaction with the CircleCI API.

• Contribution Guidelines:  
  Contributions for additional endpoints, bug fixes, or improvements are welcome. Please adhere to the project’s coding standards and include appropriate tests when submitting pull requests.

License
-------
Distributed under an open source license. See the LICENSE file for more information.

Contact
-------
For further questions or feedback, please open an issue in the repository or contact the maintainers directly.

By providing a rich set of tools and endpoints, the CircleCI MCP Server serves as a robust backbone for any integration that requires dynamic, API-based control over CircleCI resources. Get started today and streamline your CircleCI workflows seamlessly!