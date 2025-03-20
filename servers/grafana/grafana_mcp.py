#!/usr/bin/env python3
"""
Grafana MCP Server - A Model Context Protocol server for interacting with Grafana API.
This server provides tools to interact with Grafana Mimir, Loki, Core API, Alertmanager, and Alerting APIs.
"""

import os
import json
import httpx
from typing import Optional, Dict, Any, List, Union
from dataclasses import dataclass
from mcp.server.fastmcp import FastMCP, Context
from dotenv import load_dotenv
load_dotenv()

# Configure environment variables
GRAFANA_URL = os.environ.get("GRAFANA_URL")
GRAFANA_API_KEY = os.environ.get("GRAFANA_API_KEY")

if not GRAFANA_API_KEY:
    raise ValueError("GRAFANA_API_KEY environment variable must be set")

# Create MCP server
mcp = FastMCP("grafana-mcp-server")

# Setup HTTP client
http_client = httpx.AsyncClient(
    base_url=GRAFANA_URL,
    headers={
        "Authorization": f"Bearer {GRAFANA_API_KEY}",
        "Content-Type": "application/json",
    },
    timeout=30.0
)

# Helper function to handle errors
def format_error(error: Exception) -> str:
    """Format error messages for consistent output."""
    if isinstance(error, httpx.HTTPStatusError):
        try:
            error_data = error.response.json()
            message = error_data.get("message", str(error_data))
        except json.JSONDecodeError:
            message = error.response.text
        return f"HTTP Error {error.response.status_code}: {message}"
    elif isinstance(error, httpx.RequestError):
        return f"Request Error: {str(error)}"
    else:
        return f"Error: {str(error)}"

# ============= Grafana Mimir API Tools =============

@mcp.tool()
async def mimir_remote_write(data: str) -> str:
    """
    Write time series data to Grafana Mimir.
    
    Args:
        data: Time series data in Prometheus format
    """
    try:
        response = await http_client.post(
            "/api/v1/push", 
            content=data,
            headers={"Content-Type": "application/x-protobuf"}
        )
        response.raise_for_status()
        return f"Successfully pushed time series data. Status: {response.status_code}"
    except Exception as e:
        return format_error(e)

@mcp.tool()
async def mimir_instant_query(query: str, time: Optional[str] = None) -> str:
    """
    Execute an instant query on time series data in Grafana Mimir.
    
    Args:
        query: PromQL query string
        time: Optional evaluation timestamp (RFC3339 or Unix timestamp)
    """
    try:
        params = {"query": query}
        if time:
            params["time"] = time
        
        response = await http_client.get("/api/v1/query", params=params)
        response.raise_for_status()
        return json.dumps(response.json(), indent=2)
    except Exception as e:
        return format_error(e)

@mcp.tool()
async def mimir_range_query(query: str, start: str, end: str, step: str) -> str:
    """
    Execute a range query on time series data in Grafana Mimir.
    
    Args:
        query: PromQL query string
        start: Start timestamp (RFC3339 or Unix timestamp)
        end: End timestamp (RFC3339 or Unix timestamp)
        step: Query resolution step width (duration format or float seconds)
    """
    try:
        params = {
            "query": query,
            "start": start,
            "end": end,
            "step": step
        }
        
        response = await http_client.get("/api/v1/query_range", params=params)
        response.raise_for_status()
        return json.dumps(response.json(), indent=2)
    except Exception as e:
        return format_error(e)

@mcp.tool()
async def mimir_get_series(match: List[str], start: Optional[str] = None, end: Optional[str] = None) -> str:
    """
    Get time series matching the given label matchers.
    
    Args:
        match: List of label matchers
        start: Optional start timestamp
        end: Optional end timestamp
    """
    try:
        params = {"match[]": match}
        if start:
            params["start"] = start
        if end:
            params["end"] = end
        
        response = await http_client.get("/api/v1/series", params=params)
        response.raise_for_status()
        return json.dumps(response.json(), indent=2)
    except Exception as e:
        return format_error(e)

# ============= Grafana Loki API Tools =============

@mcp.tool()
async def loki_query(query: str, limit: Optional[int] = None, time: Optional[str] = None) -> str:
    """
    Execute a LogQL query on log data in Grafana Loki.
    
    Args:
        query: LogQL query string
        limit: Optional maximum number of entries to return
        time: Optional query evaluation timestamp
    """
    try:
        params = {"query": query}
        if limit:
            params["limit"] = limit
        if time:
            params["time"] = time
        
        response = await http_client.get("/loki/api/v1/query", params=params)
        response.raise_for_status()
        return json.dumps(response.json(), indent=2)
    except Exception as e:
        return format_error(e)

@mcp.tool()
async def loki_query_range(query: str, start: str, end: str, limit: Optional[int] = None, step: Optional[str] = None) -> str:
    """
    Execute a range query on log data in Grafana Loki.
    
    Args:
        query: LogQL query string
        start: Start timestamp (RFC3339 or Unix timestamp)
        end: End timestamp (RFC3339 or Unix timestamp)
        limit: Optional maximum number of entries to return
        step: Optional step parameter for aggregation
    """
    try:
        params = {
            "query": query,
            "start": start,
            "end": end
        }
        if limit:
            params["limit"] = limit
        if step:
            params["step"] = step
        
        response = await http_client.get("/loki/api/v1/query_range", params=params)
        response.raise_for_status()
        return json.dumps(response.json(), indent=2)
    except Exception as e:
        return format_error(e)

@mcp.tool()
async def loki_get_labels() -> str:
    """Retrieve available log labels from Grafana Loki."""
    try:
        response = await http_client.get("/loki/api/v1/labels")
        response.raise_for_status()
        return json.dumps(response.json(), indent=2)
    except Exception as e:
        return format_error(e)

# ============= Grafana Core API Tools =============

@mcp.tool()
async def create_dashboard(dashboard_json: str, overwrite: bool = False, message: Optional[str] = None) -> str:
    """
    Create a new dashboard in Grafana.
    
    Args:
        dashboard_json: Dashboard JSON definition
        overwrite: Whether to overwrite existing dashboard
        message: Optional message describing the change
    """
    try:
        # Parse dashboard JSON to validate it
        dashboard_data = json.loads(dashboard_json)
        
        # Create payload
        payload = {
            "dashboard": dashboard_data,
            "overwrite": overwrite
        }
        if message:
            payload["message"] = message
        
        response = await http_client.post("/api/dashboards/db", json=payload)
        response.raise_for_status()
        return json.dumps(response.json(), indent=2)
    except json.JSONDecodeError:
        return "Error: Invalid JSON provided for dashboard"
    except Exception as e:
        return format_error(e)

@mcp.tool()
async def get_dashboard(dashboard_uid: str) -> str:
    """
    Retrieve a dashboard by its UID.
    
    Args:
        dashboard_uid: The UID of the dashboard
    """
    try:
        response = await http_client.get(f"/api/dashboards/uid/{dashboard_uid}")
        response.raise_for_status()
        return json.dumps(response.json(), indent=2)
    except Exception as e:
        return format_error(e)

@mcp.tool()
async def delete_dashboard(dashboard_uid: str) -> str:
    """
    Delete a dashboard by its UID.
    
    Args:
        dashboard_uid: The UID of the dashboard
    """
    try:
        response = await http_client.delete(f"/api/dashboards/uid/{dashboard_uid}")
        response.raise_for_status()
        return json.dumps(response.json(), indent=2)
    except Exception as e:
        return format_error(e)

@mcp.tool()
async def get_all_dashboards(type: Optional[str] = None, tag: Optional[str] = None, limit: Optional[int] = None) -> str:
    """
    List all dashboards available in Grafana.
    
    Args:
        type: Optional filter by dashboard type
        tag: Optional filter by tag
        limit: Optional limit of results to return
    """
    try:
        params = {}
        if type:
            params["type"] = type
        if tag:
            params["tag"] = tag
        if limit:
            params["limit"] = limit
        
        response = await http_client.get("/api/search", params=params)
        response.raise_for_status()
        return json.dumps(response.json(), indent=2)
    except Exception as e:
        return format_error(e)

@mcp.tool()
async def get_data_source(datasource_id: int) -> str:
    """
    Retrieve a data source by its ID.
    
    Args:
        datasource_id: The ID of the data source
    """
    try:
        response = await http_client.get(f"/api/datasources/{datasource_id}")
        response.raise_for_status()
        return json.dumps(response.json(), indent=2)
    except Exception as e:
        return format_error(e)

@mcp.tool()
async def create_data_source(datasource_json: str) -> str:
    """
    Create a new data source in Grafana.
    
    Args:
        datasource_json: Data source JSON definition
    """
    try:
        # Parse to validate JSON
        datasource_data = json.loads(datasource_json)
        
        response = await http_client.post("/api/datasources", json=datasource_data)
        response.raise_for_status()
        return json.dumps(response.json(), indent=2)
    except json.JSONDecodeError:
        return "Error: Invalid JSON provided for data source"
    except Exception as e:
        return format_error(e)

@mcp.tool()
async def delete_data_source(datasource_id: int) -> str:
    """
    Delete a data source by its ID.
    
    Args:
        datasource_id: The ID of the data source
    """
    try:
        response = await http_client.delete(f"/api/datasources/{datasource_id}")
        response.raise_for_status()
        return json.dumps(response.json(), indent=2)
    except Exception as e:
        return format_error(e)

@mcp.tool()
async def get_users() -> str:
    """List all users in the current organization."""
    try:
        response = await http_client.get("/api/org/users")
        response.raise_for_status()
        return json.dumps(response.json(), indent=2)
    except Exception as e:
        return format_error(e)

@mcp.tool()
async def create_user(user_json: str) -> str:
    """
    Create a new user in Grafana.
    
    Args:
        user_json: User JSON definition with name, email, login, password
    """
    try:
        # Parse to validate JSON
        user_data = json.loads(user_json)
        
        response = await http_client.post("/api/admin/users", json=user_data)
        response.raise_for_status()
        return json.dumps(response.json(), indent=2)
    except json.JSONDecodeError:
        return "Error: Invalid JSON provided for user"
    except Exception as e:
        return format_error(e)

@mcp.tool()
async def get_organization() -> str:
    """Retrieve information about the current organization."""
    try:
        response = await http_client.get("/api/org")
        response.raise_for_status()
        return json.dumps(response.json(), indent=2)
    except Exception as e:
        return format_error(e)

@mcp.tool()
async def get_plugins() -> str:
    """List all installed plugins in Grafana."""
    try:
        response = await http_client.get("/api/plugins")
        response.raise_for_status()
        return json.dumps(response.json(), indent=2)
    except Exception as e:
        return format_error(e)

# ============= Alertmanager API Tools =============

@mcp.tool()
async def get_alertmanager_config() -> str:
    """Retrieve the current Alertmanager configuration."""
    try:
        response = await http_client.get("/api/v1/alerts")
        response.raise_for_status()
        return json.dumps(response.json(), indent=2)
    except Exception as e:
        return format_error(e)

@mcp.tool()
async def set_alertmanager_config(config_json: str) -> str:
    """
    Update the Alertmanager configuration.
    
    Args:
        config_json: Configuration JSON
    """
    try:
        # Parse to validate JSON
        config_data = json.loads(config_json)
        
        response = await http_client.post("/api/v1/alerts", json=config_data)
        response.raise_for_status()
        return json.dumps(response.json(), indent=2)
    except json.JSONDecodeError:
        return "Error: Invalid JSON provided for Alertmanager configuration"
    except Exception as e:
        return format_error(e)

# ============= Alerting API Tools =============

@mcp.tool()
async def get_alert_rules(namespace: Optional[str] = None) -> str:
    """
    Retrieve alert rules for a given namespace.
    
    Args:
        namespace: Optional namespace to filter rules
    """
    try:
        url = "/api/ruler/grafana/api/v1/rules"
        if namespace:
            url = f"{url}/{namespace}"
        
        response = await http_client.get(url)
        response.raise_for_status()
        return json.dumps(response.json(), indent=2)
    except Exception as e:
        return format_error(e)

@mcp.tool()
async def create_alert_rule(alert_rule_json: str) -> str:
    """
    Create a new alert rule.
    
    Args:
        alert_rule_json: Alert rule JSON definition
    """
    try:
        # Parse to validate JSON
        rule_data = json.loads(alert_rule_json)
        
        response = await http_client.post("/api/ruler/grafana/api/v1/rules", json=rule_data)
        response.raise_for_status()
        return json.dumps(response.json(), indent=2)
    except json.JSONDecodeError:
        return "Error: Invalid JSON provided for alert rule"
    except Exception as e:
        return format_error(e)

@mcp.tool()
async def delete_alert_rule(rule_id: str) -> str:
    """
    Delete an alert rule by its ID.
    
    Args:
        rule_id: The ID of the alert rule
    """
    try:
        response = await http_client.delete(f"/api/ruler/grafana/api/v1/rules/{rule_id}")
        response.raise_for_status()
        return json.dumps(response.json(), indent=2)
    except Exception as e:
        return format_error(e)

# ============= Query API Tools =============

@mcp.tool()
async def query_data_source(datasource_uid: str, query_json: str) -> str:
    """
    Execute a query against a data source.
    
    Args:
        datasource_uid: The UID of the data source
        query_json: Query JSON with query string, time range
    """
    try:
        # Parse to validate JSON
        query_data = json.loads(query_json)
        
        # Ensure datasourceId is set in the query
        if isinstance(query_data, dict):
            if not query_data.get("datasource"):
                query_data["datasource"] = {"uid": datasource_uid}
        
        payload = {
            "queries": [query_data]
        }
        
        response = await http_client.post("/api/ds/query", json=payload)
        response.raise_for_status()
        return json.dumps(response.json(), indent=2)
    except json.JSONDecodeError:
        return "Error: Invalid JSON provided for query"
    except Exception as e:
        return format_error(e)
    
@mcp.tool()
async def install_plugin(plugin_id: str, version: Optional[str] = None) -> str:
    """
    Install a Grafana plugin.
    
    Args:
        plugin_id: The ID of the plugin to install (e.g., 'grafana-piechart-panel')
        version: Optional specific version to install
    """
    try:
        url = f"/api/plugins/{plugin_id}/install"
        payload = {}
        if version:
            payload["version"] = version
        
        response = await http_client.post(url, json=payload)
        response.raise_for_status()
        return json.dumps(response.json(), indent=2)
    except Exception as e:
        return format_error(e)

@mcp.tool()
async def uninstall_plugin(plugin_id: str) -> str:
    """
    Uninstall a Grafana plugin.
    
    Args:
        plugin_id: The ID of the plugin to uninstall
    """
    try:
        response = await http_client.post(f"/api/plugins/{plugin_id}/uninstall")
        response.raise_for_status()
        return json.dumps(response.json(), indent=2)
    except Exception as e:
        return format_error(e)

@mcp.tool()
async def get_plugin_settings(plugin_id: str) -> str:
    """
    Retrieve settings for a specific Grafana plugin.
    
    Args:
        plugin_id: The ID of the plugin
    """
    try:
        response = await http_client.get(f"/api/plugins/{plugin_id}/settings")
        response.raise_for_status()
        return json.dumps(response.json(), indent=2)
    except Exception as e:
        return format_error(e)

@mcp.tool()
async def update_plugin_settings(plugin_id: str, settings_json: str) -> str:
    """
    Update settings for a specific Grafana plugin.
    
    Args:
        plugin_id: The ID of the plugin
        settings_json: JSON string containing the updated settings
    """
    try:
        # Parse to validate JSON
        settings_data = json.loads(settings_json)
        
        response = await http_client.post(f"/api/plugins/{plugin_id}/settings", json=settings_data)
        response.raise_for_status()
        return json.dumps(response.json(), indent=2)
    except json.JSONDecodeError:
        return "Error: Invalid JSON provided for plugin settings"
    except Exception as e:
        return format_error(e)

@mcp.tool()
async def search_plugins(query: Optional[str] = None, type: Optional[str] = None, limit: Optional[int] = None) -> str:
    """
    Search for Grafana plugins in the plugin catalog.
    
    Args:
        query: Optional search query string
        type: Optional plugin type filter ('panel', 'datasource', 'app', etc.)
        limit: Optional limit of results to return
    """
    try:
        params = {}
        if query:
            params["query"] = query
        if type:
            params["type"] = type
        if limit:
            params["limit"] = limit
        
        response = await http_client.get("/api/plugins", params=params)
        response.raise_for_status()
        return json.dumps(response.json(), indent=2)
    except Exception as e:
        return format_error(e)

# Additional function to check if a plugin is installed
@mcp.tool()
async def is_plugin_installed(plugin_id: str) -> str:
    """
    Check if a specific plugin is installed.
    
    Args:
        plugin_id: The ID of the plugin to check
    """
    try:
        all_plugins = await get_plugins()
        plugins_data = json.loads(all_plugins)
        
        installed = any(plugin.get("id") == plugin_id for plugin in plugins_data)
        return json.dumps({"installed": installed}, indent=2)
    except Exception as e:
        return format_error(e)

# ============= Health Check Tool =============

@mcp.tool()
async def check_grafana_health() -> str:
    """Check if the Grafana API is accessible and healthy."""
    try:
        response = await http_client.get("/api/health")
        response.raise_for_status()
        return json.dumps(response.json(), indent=2)
    except Exception as e:
        return format_error(e)

# ============= Run the server =============

if __name__ == "__main__":
    mcp.run()