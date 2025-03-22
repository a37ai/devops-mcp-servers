New Relic MCP Server
====================

Overview
--------
The New Relic MCP Server is a comprehensive implementation of an MCP (Modular Command Protocol) server that provides seamless integration with New Relic’s API ecosystem. Built on top of the FastMCP framework, this server enables you to manage and query your New Relic data from applications, mobile apps, browser apps, deployments, synthetic monitors, workloads, dashboards, and more—all via dedicated tools and resource endpoints.

This application leverages asynchronous HTTP requests (using the httpx library) and parses environment variables (using python-dotenv) to interact with New Relic’s REST and GraphQL APIs. With a vast array of tools at your disposal, you can perform operations such as listing applications, updating deployments, querying synthetic monitors, running NRQL queries, and accessing detailed performance insights.

Features
--------
•  Extensive API Integration – Access a wide range of New Relic endpoints including APM, mobile, browser, synthetic monitoring, infrastructure, logs, service levels, and more.

•  Modular Toolset – Each tool is exposed through the MCP framework allowing granular operations for listing, creating, updating, and deleting resources across applications, deployments, alerts, dashboards, and workloads.

•  Resource Endpoints – In addition to individual tools, several resource endpoints aggregate information (e.g., lists of applications, dashboards, synthetic monitors, service levels) into human-readable summaries.

•  Prompt Templates – Built-in prompt generators facilitate in-depth analysis, such as synthetic monitoring analysis, deployment recommendations, performance comparisons, and investigations into alert incidents.

•  Asynchronous Operations – All HTTP interactions are performed asynchronously for optimal performance when scaling operations or executing multiple commands concurrently.

Configuration
-------------
1. Environment Variables  
   •  The server requires a New Relic API Key. Set the environment variable:
     
     NEW_RELIC_API_KEY  
     
   •  A .env file can be used for local development. Ensure that the file includes:
     
       NEW_RELIC_API_KEY=your_new_relic_api_key_here

2. API Endpoints  
   •  REST endpoints (e.g., for applications, deployments, infrastructure hosts, etc.) use the base URL "https://api.newrelic.com/v2" (or another New Relic-specific URL for synthetics and infrastructure).  
   •  GraphQL endpoints (for dashboards, workloads, service levels, logs, and error tracking) use the NerdGraph API at "https://api.newrelic.com/graphql".  

Installation
------------
•  Ensure you have Python 3.7 or later installed.  
•  Install required dependencies using pip:
     
       pip install httpx python-dotenv fastmcp

Usage
-----
To run the server in a standalone mode (using stdio transport), execute:

    python newrelic_mcp_server.py

Once running, you can interact with the server through the MCP framework. Use the provided tools and resource endpoints to execute operations like:

•  Listing and managing New Relic applications  
•  Creating, updating, and deleting deployments and alerts  
•  Performing NRQL queries to retrieve metric data  
•  Accessing dashboards, synthetic monitors, and infrastructure data  
•  Generating natural language prompts for performance analysis and incident investigations

Tools and Endpoints
-------------------
The server exposes a rich set of tools including, but not limited to:

•  Application Tools  
   – list_applications, get_application, update_application, delete_application  
   – get_application_metrics, get_application_metric_data

•  Deployment Tools  
   – list_deployments, create_deployment, delete_deployment

•  Host and Instance Tools  
   – list_application_hosts, get_application_host, list_application_instances, get_application_instance

•  Key Transactions and Mobile Applications  
   – list_key_transactions, get_key_transaction, list_mobile_applications, get_mobile_application

•  Alerts and Conditions  
   – list_alert_policies, create_alert_policy, update_alert_policy, delete_alert_policy  
   – list_alert_conditions, create_alert_condition, update_alert_condition, delete_alert_condition  
   – NRQL alert conditions for advanced alerting setups

•  Synthetic Monitoring Tools  
   – list_monitors, get_monitor, create_simple_monitor, update_monitor, delete_monitor

•  Workloads and Dashboards (via NerdGraph)  
   – list_workloads, get_workload, create_workload, update_workload, delete_workload  
   – list_dashboards, get_dashboard, create_simple_dashboard, delete_dashboard

•  NRQL Query Tool  
   – execute_nrql_query for custom NRQL requests

•  Infrastructure and Logs  
   – list_infrastructure_hosts, get_infrastructure_host, list_infrastructure_alerts  
   – query_logs for retrieving log data via NRQL

•  Browser Applications and Service Levels  
   – list_browser_applications, get_browser_application, create_browser_application, update_browser_application, delete_browser_application  
   – list_service_levels, create_service_level_indicator

•  Errors and Account Management  
   – list_errors, get_error_details, list_accounts, get_account_users

Resource Endpoints
------------------
For human-readable summaries, the server provides several resource endpoints that compile and format information. For example:

•  "nr://applications" – Lists New Relic applications with key metrics (health, reporting, summary details).  
•  "nr://alerts/policies" – Summarizes alert policies with creation/upgrade timestamps.  
•  "nr://synthetics/monitors" – Presents a dashboard view of synthetic monitor details including frequency, type, status, and associated locations.  
•  "nr://dashboards/{account_id}" – Retrieves a formatted list of dashboards for a specified account.

Prompt Templates
----------------
Several prompt generators are included to assist in deeper operational analysis:

•  synthetic_monitoring_analysis – Generates a query prompt for analyzing synthetic monitor performance.  
•  deployment_recommendations – Suggests deployment improvement recommendations based on post-deployment metrics.  
•  analyze_application_performance – Creates a prompt focused on performance metrics and actionable insights for an application.  
•  investigate_alert_incident – Helps in troubleshooting critical alert incidents and suggesting remedial steps.  
•  compare_environments – Compares production and staging metrics to identify discrepancies and optimize configurations.  
•  deployment_analysis – Reviews recent deployments to identify performance trends and potential issues.

Contributing and Support
-------------------------
As this is an MCP server implementation designed to work with New Relic’s APIs, contributions to enhance functionality or add new tools are welcome. Please ensure that any pull requests or issues follow professional standards and include detailed change logs or descriptions.

License
-------
This project is provided as-is without any warranty. Please refer to the LICENSE file for more details.

Summary
-------
The New Relic MCP Server offers a powerful and flexible solution for integrating New Relic’s monitoring, alerting, and analytical capabilities into your workflow. With a wide variety of tools, resource endpoints, and prompt templates, you can streamline your operations, monitor performance in real time, and make data-driven decisions across all layers of your infrastructure.

For any further questions or support, please consult the documentation of the FastMCP framework or refer to New Relic’s official API documentation.

Happy Monitoring!