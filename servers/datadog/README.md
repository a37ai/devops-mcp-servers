Datadog MCP Server
==================

Overview
--------
The Datadog MCP Server is a Python-based implementation that integrates the Datadog API with the Model Context Protocol (MCP). Built using the FastMCP framework, this server provides a suite of tools to interact with various aspects of Datadog—including metrics, events, monitors, and dashboards—through validated and well-structured endpoints.

Features
--------
• Metrics Management  
 – Submit metrics to Datadog with customizable values and timestamps  
 – Query historical metric data with defined time ranges

• Events Management  
 – Create events with configurable titles, texts, tags, alert types, and priorities  
 – Retrieve events based on custom queries and time filters

• Monitors Management  
 – Create, retrieve, update, and delete monitors  
 – Validate monitor types and customize monitor messages and tags

• Dashboards Management  
 – Create dashboards with customizable layouts and widgets  
 – Retrieve and delete dashboards

• Input Validation  
 – Leverages Pydantic models to validate inputs and ensure API consistency  
 – Provides clear error handling through structured JSON responses

Installation & Setup
--------------------
1. Prerequisites  
 • Python 3.7 or higher  
 • Datadog API Client library  
 • dotenv, pydantic, and FastMCP modules

2. Clone the repository and install dependencies:
  $ git clone <repository_url>
  $ cd <repository_folder>
  $ pip install -r requirements.txt

3. Environment Configuration  
 Create a .env file in the project root and set the following variables:
  DATADOG_API_KEY=<your_datadog_api_key>
  DATADOG_APP_KEY=<your_datadog_application_key>
  DATADOG_SITE=<datadog_site (default: datadoghq.com)>

Usage
-----
Once configured, you can start the MCP server and interact with Datadog using the provided tools.

To start the server:
  $ ./<filename>.py
*Note:* The server uses 'stdio' as the default transport mechanism.

Available Tools & Endpoints
---------------------------
Metrics Management
~~~~~~~~~~~~~~~~~~
• submit_metric(metric_name: str, value: float, timestamp: Optional[int] = None, tags: Optional[List[str]] = None)  
 Submit a metric to Datadog. If no timestamp is provided, the current time is used.

• query_metrics(query: str, from_time: int, to_time: int)  
 Query Datadog metrics within a specified time range using a metrics query string.

Events Management
~~~~~~~~~~~~~~~~~
• create_event(title: str, text: str, tags: Optional[List[str]] = None, alert_type: str = "info", priority: str = "normal")  
 Create an event in Datadog with validation on alert type and priority.  
 Valid Alert Types: info, warning, error, success  
 Valid Priorities: normal, low

• get_events(query: Optional[str] = None, from_time: Optional[int] = None, to_time: Optional[int] = None)  
 Retrieve events based on an optional query string and time filters.

Monitors Management
~~~~~~~~~~~~~~~~~~~
• create_monitor(name: str, query: str, type: str, message: str, tags: Optional[List[str]] = None)  
 Create a monitor. The monitor type must be one of the following: "metric alert", "service check", "event alert", "query alert", "composite".

• get_monitor(monitor_id: int)  
 Retrieve a specific monitor by its unique ID.

• update_monitor(monitor_id: int, name: Optional[str] = None, query: Optional[str] = None, message: Optional[str] = None, tags: Optional[List[str]] = None)  
 Update selected fields of an existing monitor.

• delete_monitor(monitor_id: int)  
 Delete a monitor by its unique ID.

Dashboards Management
~~~~~~~~~~~~~~~~~~~~~
• create_dashboard(title: str, description: str = "", widgets: Optional[List[Dict]] = None, layout_type: str = "ordered")  
 Create a new dashboard. The layout type must be either "ordered" or "free".

• get_dashboard(dashboard_id: str)  
 Retrieve a dashboard using its unique ID.

• delete_dashboard(dashboard_id: str)  
 Delete a dashboard by its unique ID.

Development & Contributing
--------------------------
• The server is built with modularity in mind, with clear separation between API clients, models, and MCP tools.  
• Contributions are welcome—feel free to submit pull requests or open issues for enhancements and bug fixes.

Error Handling
--------------
All MCP tools return structured JSON responses. On error, the server responds with a model containing:
  status: "error"  
  message: Detailed error description

License
-------
This project is open source. See the LICENSE file for more details.

Contact
-------
For any questions or support, please open an issue in the repository or contact the project maintainers.

With the Datadog MCP Server, integrating and managing your Datadog metrics, events, monitors, and dashboards becomes simple, efficient, and structured—empowering you to better monitor and manage your applications.