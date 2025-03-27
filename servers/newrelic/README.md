New Relic MCP Server
=====================

Overview
--------
The New Relic MCP Server is an implementation of an MCP (Micro Call Protocol) server that integrates with New Relic’s APIs and NerdGraph (GraphQL) endpoints. It provides a comprehensive set of tools and resources to interact with various New Relic services including Applications, Deployments, Alerts, Synthetic Monitors, Infrastructure, Workloads, Dashboards, NRQL queries, and more. The server is built on top of FastMCP for rapid integration and uses Pydantic for data validation.

Features
--------
•  Comprehensive API integrations:
   – Applications: List, retrieve details, update settings, and delete applications.
   – Deployments: List deployments, create new deployments (using revision, changelog, description, and user details), and delete deployments.
   – Alerts: Manage alert policies and conditions (including NRQL alert conditions) with full create, update, list, and delete operations.
   – Synthetic Monitoring: List synthetic monitors; get details; create, update, and delete monitors via the dedicated Synthetics API.
   – Infrastructure: Query host details and alerts using the New Relic Infrastructure API.
   – Workloads and Dashboards: Leverage NerdGraph to list, create, update, and delete workloads and dashboards.
   – Browser Applications & Service Levels: Retrieve browser application details and manage service level indicators.
   – Logs & Errors: Query logs using NRQL via NerdGraph and retrieve error details with full diagnostics.
   – Prompts: Built-in prompts enable analysis for synthetic monitoring performance, deployment recommendations, application performance comparisons, and more.
   
•  Extensive data validation using Pydantic models to ensure API responses and request payloads conform to expected structures.

•  Flexible resource endpoints (prefixed with “nr://”) that produce human-readable markdown-like summaries (e.g., for applications, synthetic monitors, dashboards, key transactions, etc.) for quick review.

•  Integration across several New Relic services including:
   – REST endpoints for core data (applications, deployments, alert policies/conditions)
   – Synthetics API endpoints (using a separate base URL)
   – NerdGraph (GraphQL) queries and mutations for workloads, dashboards, logs, accounts, and service levels.

Configuration
-------------
•  Environment Variable:
   – NEW_RELIC_API_KEY: The API key required to authenticate with New Relic services. This is loaded automatically from a .env file by python-dotenv. (Ensure you have set this variable before running the server.)

•  API Base URLs:
   – Core New Relic API: https://api.newrelic.com/v2
   – Synthetic Monitoring API: https://synthetics.newrelic.com/synthetics/api
   – Infrastructure API: https://infra-api.newrelic.com/v2
   – NerdGraph API: https://api.newrelic.com/graphql

Dependencies
------------
•  Python 3.7+
•  httpx – For making asynchronous HTTP requests.
•  pydantic – For data models and request/response validation.
•  FastMCP – For defining and running MCP tools and resources.
•  python-dotenv – For loading environment variables from a .env file.

Installation
------------
1. Clone the repository or copy the newrelic_mcp_server.py file into your working directory.
2. Create a virtual environment and install necessary dependencies. For example:

   python -m venv venv
   source venv/bin/activate      (or venv\Scripts\activate on Windows)
   pip install httpx pydantic python-dotenv fastmcp

3. Create a .env file in the root directory and set:
   
      NEW_RELIC_API_KEY=your_actual_new_relic_api_key

Usage
-----
Run the server from the command line:

   python newrelic_mcp_server.py

When executed, the MCP server will start and listen for incoming requests using stdio transport. Each tool (e.g., list_applications, get_application, create_deployment, list_monitors, etc.) and resource endpoint (e.g., nr://applications, nr://alerts/policies, nr://dashboards/{account_id}, etc.) is exposed and can be called through the MCP server interface.

Tools & Endpoints
------------------
Below is an overview of the major groups and functionalities provided:

1. Applications Tools
   – list_applications: Filter by name, host, or language with pagination.
   – get_application: Retrieve detailed information for a particular application.
   – update_application: Update application settings (name, Apdex thresholds, real user monitoring).
   – delete_application: Remove an application.
   – get_application_metrics & get_application_metric_data: Retrieve available metrics and timeslice data.

2. Deployment Tools
   – list_deployments, create_deployment, delete_deployment: Manage application deployments.

3. Alert Tools
   – Manage alert policies (list, create, update, delete).
   – Manage alert conditions and NRQL alert conditions.
   – Retrieve alerts incidents and violations.

4. Synthetic Monitoring Tools
   – list_monitors, get_monitor, create_simple_monitor, update_monitor, delete_monitor: Full management of synthetic monitors.
   – Resource endpoint (nr://synthetics/monitors) to display monitors in a summary format.
   – Prompt (synthetic_monitoring_analysis) for performance analysis of monitors.

5. Workloads & Dashboards
   – Tools for listing, retrieving, creating, updating, and deleting workloads (via NerdGraph API).
   – Dashboard management including simple dashboards creation and deletion.
   – Resource endpoints to generate human-readable summaries.

6. Browser Applications & Service Levels
   – Tools to list browser applications and manage browser application details.
   – Manage Service Level Indicators, including creation with objectives and event queries.

7. NRQL & Logs
   – execute_nrql_query: Run custom NRQL queries.
   – query_logs: Fetch logs from New Relic using GraphQL queries.

8. Infrastructure Monitoring
   – list_infrastructure_hosts & get_infrastructure_host: View host details.
   – list_infrastructure_alerts to retrieve infrastructure alerts.

9. Error Tracking & Account Management
   – list_errors & get_error_details: Retrieve error diagnostics.
   – list_accounts & get_account_users: Discover account information and user details.

10. Prompts for Analysis & Recommendations
    – deployment_recommendations: Analyze deployments and advise on potential rollback or improvements.
    – analyze_application_performance, investigate_alert_incident, compare_environments, and deployment_analysis: Custom prompts for in-depth investigations.

Contributing
------------
Contributions are welcome. If you plan to extend the functionality or add new tools, please follow similar documentation and Pydantic validation strategies as demonstrated in the code.

License
-------
This project is provided as-is with no warranty. Use it responsibly and ensure proper authentication and authorization when integrating with production New Relic environments.

Contact
-------
For questions or contributions, please reach out to the project maintainer or consult the documentation on your internal repository.

Enjoy monitoring and analyzing your New Relic data with the New Relic MCP Server!