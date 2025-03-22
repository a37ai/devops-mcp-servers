Grafana MCP Server
==================

Overview
--------
Grafana MCP Server is a Model Context Protocol (MCP) server implementation designed to interact with multiple Grafana APIs. This server provides a suite of tools that simplify communication with Grafana components such as Mimir, Loki, Core API, Alertmanager, and Alerting APIs. Whether you need to push time series data, execute queries, manage dashboards and data sources, or handle alert configurations, this server offers a comprehensive solution.

Features
--------
•  Grafana Mimir API Tools  
   – Write time series data via remote write  
   – Execute instant and range queries using PromQL  
   – Retrieve matching time series data

•  Grafana Loki API Tools  
   – Execute LogQL queries (instant & range)  
   – Retrieve available log labels

•  Grafana Core API Tools  
   – Manage dashboards (create, retrieve, delete)  
   – Manage data sources (retrieve, create, delete)  
   – Retrieve organization details, users, and plugins

•  Alertmanager and Alerting API Tools  
   – Get and update Alertmanager configuration  
   – Manage alert rules (create, retrieve, and delete)

•  Query API Tools  
   – Execute data source queries  
   – Manage plugin installations and settings  
   – Search for plugins and verify installations

•  Health Check  
   – Check Grafana API’s health status for quick diagnostics

Getting Started
---------------
### Prerequisites

• Python 3.7 or higher  
• Environment variables for Grafana connection:  
  – GRAFANA_URL: Base URL for your Grafana instance  
  – GRAFANA_API_KEY: Your Grafana API key (mandatory)  

• Required Python packages:  
  – httpx  
  – python-dotenv  
  – mcp (with FastMCP support)  
  – Other standard libraries (json, os, etc.)

### Installation

1. Clone the repository or copy the script to your project directory.
2. Create a virtual environment and activate it:
  • python3 -m venv venv  
  • source venv/bin/activate              (Unix/Linux/macOS)  
  • venv\Scripts\activate              (Windows)
3. Install the required dependencies:
  • pip install -r requirements.txt

4. Create a .env file in the same directory and add the required environment variables:

  GRAFANA_URL=https://your-grafana-instance.com  
  GRAFANA_API_KEY=your_api_key_here

Usage
-----
To run the Grafana MCP Server, simply execute the script:

  ./grafana_mcp_server.py  
                (or "python grafana_mcp_server.py")

The server will initialize and expose its tools via the MCP framework. These tools can then be invoked to interact with various Grafana APIs.

Tool Details
------------
Each tool in the server is built as an asynchronous method using the mcp.tool() decorator and provides detailed functionality:

•  Mimir API Tools  
  – mimir_remote_write(data: str): Pushes time series data in Prometheus format.  
  – mimir_instant_query(query: str, time: Optional[str]): Executes an instant PromQL query.  
  – mimir_range_query(query: str, start: str, end: str, step: str): Executes a range query over a specified time interval.  
  – mimir_get_series(match: List[str], start: Optional[str], end: Optional[str]): Retrieves time series matching given label matchers.

•  Loki API Tools  
  – loki_query(query: str, limit: Optional[int], time: Optional[str]): Executes an instant LogQL query.  
  – loki_query_range(query: str, start: str, end: str, limit: Optional[int], step: Optional[str]): Executes a range query on log data.  
  – loki_get_labels(): Retrieves available log labels.

•  Core API Tools  
  – create_dashboard(dashboard_json: str, overwrite: bool, message: Optional[str]): Creates a new dashboard.  
  – get_dashboard(dashboard_uid: str): Retrieves a dashboard by UID.  
  – delete_dashboard(dashboard_uid: str): Deletes a dashboard by UID.  
  – get_all_dashboards(type: Optional[str], tag: Optional[str], limit: Optional[int]): Lists available dashboards.  
  – get_data_source(datasource_id: int): Retrieves a data source by ID.  
  – create_data_source(datasource_json: str): Creates a new data source.  
  – delete_data_source(datasource_id: int): Deletes a data source by ID.  
  – get_users(), create_user(user_json: str): Manage organization users.  
  – get_organization(), get_plugins(): Retrieve organization details and plugin information.

•  Alertmanager & Alerting API Tools  
  – get_alertmanager_config() / set_alertmanager_config(config_json: str): Manage Alertmanager configuration.  
  – get_alert_rules(namespace: Optional[str]): Retrieves alert rules.  
  – create_alert_rule(alert_rule_json: str): Creates a new alert rule.  
  – delete_alert_rule(rule_id: str): Deletes an alert rule by ID.

•  Query API & Plugin Management Tools  
  – query_data_source(datasource_uid: str, query_json: str): Execute queries against a data source.  
  – install_plugin(plugin_id: str, version: Optional[str]): Installs a Grafana plugin.  
  – uninstall_plugin(plugin_id: str): Uninstalls a Grafana plugin.  
  – get_plugin_settings(plugin_id: str) / update_plugin_settings(plugin_id: str, settings_json: str): Manage plugin settings.  
  – search_plugins(query: Optional[str], type: Optional[str], limit: Optional[int]): Search for plugins in the catalog.  
  – is_plugin_installed(plugin_id: str): Checks if a specific plugin is installed.

•  Health Check Tool  
  – check_grafana_health(): Validates the accessibility and health of the Grafana API.

Error Handling
--------------
All tools are equipped with robust error handling. The helper function format_error() standardizes error responses by handling HTTP errors, request issues, and general exceptions. This ensures that any issues encountered during API interactions return clear and concise messages.

Configuration
-------------
Before deploying or using the server, ensure that:

• You have a valid Grafana API key with appropriate permissions.  
• The GRAFANA_URL environment variable points to your Grafana instance.  
• The .env file (loaded using python-dotenv) is properly configured.  

Contributing
------------
Contributions are welcome! If you encounter bugs or have suggestions for improvements, please submit an issue or pull request.

License
-------
Distributed under the terms of your preferred license. (Specify your license here.)

Contact
-------
For any questions or support, please contact [Your Name or Support Email].

Conclusion
----------
The Grafana MCP Server provides a unified interface for interacting with multiple Grafana APIs. With its extensive set of tools and robust error handling, it is an ideal solution for developers looking to integrate Grafana functionalities into their applications or workflows.