Datadog MCP Server
==================

Overview
--------
The Datadog MCP Server is a full-featured implementation that leverages the FastMCP framework and the Datadog API Client to provide seamless integration with Datadog’s suite of APIs. With this server, you can interact with Datadog’s Metrics, Events, Logs, Dashboards, Monitors, Hosts, and Users APIs via simple resource endpoints and tools.

Features
--------
• Comprehensive API Integration:  
  – Metrics API: Query and list metrics, submit new metric data.  
  – Events API: Retrieve and create events.  
  – Logs API: Submit and query logs with support for both v1 and v2 endpoints.  
  – Dashboards API: List and retrieve dashboards.  
  – Monitors API: Query, retrieve, and create monitors.  
  – Hosts API: List hosts and mute specific hosts.  
  – Users API: List and create users.

• Flexible Resource Registration:  
  Each API has dedicated resource endpoints that allow direct calls using URI patterns (e.g., "metrics://{from_time}/{to_time}/{query}").

• Tool-Based Operations:  
  Custom tools are available to perform actions such as submitting metrics, creating events, submitting logs, creating monitors, muting hosts, and creating users.

• Dynamic API Client Lifecycle Management:  
  Utilizes an asynchronous context manager to handle the lifecycle and authentication credentials for the Datadog API client.

Installation
------------
1. **Clone the Repository**  
  Clone or download the source code to your local machine.

2. **Install Dependencies**  
  Ensure you have Python 3.7+ installed and then run:  
    pip install fastmcp datadog-api-client

3. **Configure Environment Variables (Optional)**  
  The server can read your Datadog API credentials from environment variables if not provided directly during initialization.  
    • DATADOG_API_KEY – Your Datadog API key  
    • DATADOG_APP_KEY – Your Datadog Application key

Configuration
-------------
The Datadog MCP Server requires authentication to interact with the various Datadog APIs.

- **API Keys**:  
 You can provide your Datadog API key and Application key either directly when instantiating the server or via the environment variables DATADOG_API_KEY and DATADOG_APP_KEY.  
 If these keys are missing, the server will throw an error to ensure proper authentication.

- **API URL (Optional)**:  
 If you need to override the default API URL, pass the custom URL during the server initialization.

Usage
-----
1. **Registering Resources and Tools**  
 The server method `register_all_resources_and_tools()` automatically registers all available endpoints and tools for Metrics, Events, Logs, Dashboards, Monitors, Hosts, Tags, and Users APIs.

2. **Running the Server**  
 Execute the main file to start the MCP server with the default transport (stdio):  
   python <filename>.py  
 Replace \<filename> with the name of your Python file.

3. **Using the Endpoints**  
 Once running, the server listens for resource-based requests with URI patterns. For example:  

  - Metrics Data Query:  
   Send a request to "metrics://{from_time}/{to_time}/{query}" to get metric data for a specific query and time range.

  - Listing Metrics:  
   Access "metrics://list/{from_time}" to list available metrics.

  - Submit a Metric:  
   Call the tool "submit_metric" with parameters like metric name, data points, type, host details, and tags.

  - Get Events:  
   Use "events://{start}/{end}" to list events within a specified timeframe.

  - Create an Event:  
   Invoke the "create_event" tool with a title, text, and additional parameters to create an event in Datadog.

  - Logs Submission/Querying:  
   Access the logs tools to either submit logs ("submit_logs") or query logs ("query_logs") using appropriate filters and time ranges.

  - Dashboards, Monitors, Hosts, and Users:  
   Similarly, use the respective resource endpoints and tools to interact with dashboards, monitors, hosts, and users.

Project Structure
-----------------
• DatadogMCPServer Class  
 – Initializes the FastMCP server with dependency on the "datadog-api-client".  
 – Manages API client lifecycle and authentication through an asynchronous context manager.

• Resource and Tool Registration Methods  
 – Separate functions register endpoints and tools for each Datadog API group.  
 – Example endpoints include:  
  • Metrics: get_metric_data, list_metrics, submit_metric  
  • Events: get_events, get_event, create_event  
  • Logs: submit_logs, query_logs  
  • Dashboards: list_dashboards, get_dashboard  
  • Monitors: list_monitors, get_monitor, create_monitor  
  • Hosts: list_hosts, mute_host  
  • Users: list_users, create_user

• The main() Function  
 – Instantiates the Datadog MCP Server, registers all resources and tools, and launches the server with the specified transport.

Contributing
------------
Contributions to enhance or expand the features of the Datadog MCP Server are welcome. Please ensure that changes are well documented and include appropriate tests where applicable.

License
-------
This project is distributed under an open source license. (Specify your license here, e.g., MIT License.)

Contact
-------
For any issues, feature requests, or improvements, please open an issue in the repository or reach out via [email/contact information].

Conclusion
----------
The Datadog MCP Server offers a robust, flexible, and modular way to interact with various Datadog APIs. By abstracting away the complexities of API authentication and endpoint management, it provides a streamlined interface tailored for efficient monitoring and data management in a Datadog environment.

Enjoy seamless integration with Datadog and enhance your operational workflows with the power of FastMCP!