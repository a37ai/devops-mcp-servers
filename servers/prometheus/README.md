Prometheus MCP Server
=======================

Overview
--------
The Prometheus MCP Server is an MCP (Modular Content Processor) implementation that integrates directly with a Prometheus instance. It provides a comprehensive set of resources, tools, and prompts to:
 
• Query and analyze Prometheus metrics using PromQL  
• Retrieve targets, alerts, and rules from Prometheus  
• Dynamically search for metrics based on name patterns  
• Generate detailed statistical analyses and performance insights  
• Facilitate capacity planning and alert investigation  

Features
--------
• Resource Endpoints  
  – Get all Prometheus targets and their statuses  
  – Retrieve current alerts with detailed information  
  – List Prometheus rules (recording and alerting) with grouping support  
  – Dynamically fetch metrics matching a name pattern with sample label combinations  

• Query & Analysis Tools  
  – Perform instant and range queries using PromQL via the query_metrics tool  
  – Find metrics matching a specified pattern with the find_metrics tool  
  – Analyze metrics over a given duration, with basic statistical insights (min, max, average, change, rate) using the analyze_metric tool  
  – Retrieve target health summaries and detailed alert summaries  

• Prompts  
  – Analyze overall system health from a Prometheus perspective  
  – Review performance of a specific service over a designated period  
  – Plan capacity based on current metrics and anticipated growth  
  – Investigate specific alerts to identify root causes and recommend remediation  

Configuration
-------------
• Environment Variables  
  – The server expects a .env file to provide required configurations. At a minimum, you must set:  
    • PROMETHEUS_URL – The base URL to reach your Prometheus instance  

• Defaults and Dependencies  
  – The server uses a default request timeout of 30 seconds.  
  – Dependencies include “httpx”, “prometheus_api_client”, and “python-dotenv”.  
  – Ensure that your environment is properly configured and that all dependencies are installed.

Installation
------------
1. Clone the repository.  
2. Install required dependencies. For example:  

   pip install httpx prometheus_api_client python-dotenv

3. Create a .env file in the project root and define the PROMETHEUS_URL variable:

   PROMETHEUS_URL=<your_prometheus_instance_url>

Usage
-----
The server is built upon FastMCP and provides multiple endpoints and tools for interacting with Prometheus. When executed, the server will run with the specified transport (typically stdio), allowing for rapid testing and integration with other services.

To start the server, simply run:

   python <filename>.py

Server Endpoints & Tools
--------------------------
• Resource Endpoints (annotated with @mcp.resource):  
  – prometheus://targets – Returns a formatted table of all Prometheus targets with state, scrape labels, and last scrape timestamps.  
  – prometheus://alerts – Displays current alerts with state, labels, and annotations.  
  – prometheus://rules – Lists groups of Prometheus rules along with details on expressions and rule metadata.  
  – prometheus://metrics/{pattern} – Dynamically fetches all metrics that match a given name pattern and provides sample label combinations.

• Tools (annotated with @mcp.tool):  
  – query_metrics – Executes both instant and range PromQL queries. Automatically determines query type based on parameters provided (e.g., start and end times).  
  – find_metrics – Searches for metrics matching a provided pattern, groups results by metric name, and limits the number of output samples.  
  – analyze_metric – Provides a detailed analysis of a specific metric over a specified duration, including basic statistics, rate of change, and trends.  
  – get_targets_health – Retrieves the health status for all Prometheus targets with optional state-based filtering (“up” or “down”).  
  – get_alert_summary – Generates a summary for all current alerts, grouped by alert name, with the option to filter by state (firing, pending, or inactive).

• Prompts (annotated with @mcp.prompt):  
  – analyze_system_health – Provides a comprehensive health assessment across components such as firing alerts, target statuses, and resource consumptions (CPU, memory, disk, and network).  
  – performance_analysis – Reviews performance metrics for a specified service over a given period (e.g., service response times, error rates, throughput).  
  – capacity_planning – Helps forecast capacity requirements based on current trends and an expected growth rate.  
  – alert_investigation – Investigates a specified alert by analyzing its historical trends, root-cause, and remediation paths.

Helper Functions
----------------
A key helper function, calculate_step, computes an appropriate time step for range queries based on the duration between the start and end timestamps. This enhances the efficiency of queries and provides a reasonable balance between query resolution and performance.

Development & Running the Server
----------------------------------
1. Ensure that all dependencies are installed and the environment is configured correctly.  
2. Run the script with your chosen transport – in this example, stdio is used:

   if __name__ == "__main__":
       mcp.run(transport='stdio')

The server is built to be modular and easily extendable. You can add new endpoints or tools by decorating functions with @mcp.resource, @mcp.tool, or @mcp.prompt.

Conclusion
----------
This Prometheus MCP Server offers a robust solution for integrating Prometheus monitoring with your custom applications. Its blend of resources, tools, and prompts allows for in-depth analysis, performance evaluation, and problem diagnosis, empowering you to maintain system health and responsiveness through actionable insights.

For further customization and extension of functionality, refer to the code comments and explore adding new endpoints tailored to your specific monitoring requirements.

For questions or contributions, please refer to the repository’s contribution guidelines. Enjoy leveraging Prometheus metrics with the flexibility and power of MCP!