#!/usr/bin/env python3
"""
Grafana MCP Server - A Model Context Protocol server for interacting with Grafana API.
This server provides tools to interact with Grafana Mimir, Loki, Core API, Alertmanager, and Alerting APIs.

This version uses Pydantic models for input/output validation.
"""

import os
import json
import httpx
from typing import Optional, Dict, Any, List, Union
from dotenv import load_dotenv
from pydantic import BaseModel, Field, validator

# ============= MCP Mock Implementation =============

from typing import Callable
import functools

class Context:
    """Mock Context class for MCP."""
    def __init__(self):
        self.data = {}

class FastMCP:
    """Mock FastMCP class for testing."""
    
    def __init__(self, name: str):
        self.name = name
        self.tools = {}
    
    def tool(self, name: Optional[str] = None):
        """Decorator for registering tools."""
        def decorator(func: Callable):
            @functools.wraps(func)
            async def wrapper(*args, **kwargs):
                return await func(*args, **kwargs)
            
            tool_name = name or func.__name__
            self.tools[tool_name] = wrapper
            return wrapper
        
        return decorator
    
    def run(self):
        """Mock run method."""
        print(f"Running MCP server: {self.name}")
        print(f"Registered tools: {list(self.tools.keys())}")

# Create MCP instance
mcp = FastMCP("grafana-mcp")

# ============= Pydantic Models =============

# Base Models
class BaseResponse(BaseModel):
    """Base model for API responses."""
    pass

class ErrorResponse(BaseResponse):
    """Model for error responses."""
    error: str

# Mimir API Models
class MimirQueryRequest(BaseModel):
    """Model for Mimir instant query requests."""
    query: str = Field(..., description="Prometheus query string")
    time: Optional[str] = Field(None, description="Evaluation timestamp (RFC3339 or Unix timestamp)")

class MimirRangeQueryRequest(BaseModel):
    """Model for Mimir range query requests."""
    query: str = Field(..., description="Prometheus query string")
    start: str = Field(..., description="Start timestamp (RFC3339 or Unix timestamp)")
    end: str = Field(..., description="End timestamp (RFC3339 or Unix timestamp)")
    step: str = Field(..., description="Query resolution step width (duration format or float seconds)")

class MimirGetSeriesRequest(BaseModel):
    """Model for Mimir series requests."""
    match: List[str] = Field(..., description="Series selectors")
    start: Optional[str] = Field(None, description="Start timestamp")
    end: Optional[str] = Field(None, description="End timestamp")

# Loki API Models
class LokiQueryRequest(BaseModel):
    """Model for Loki query requests."""
    query: str = Field(..., description="LogQL query string")
    limit: Optional[int] = Field(None, description="Maximum number of entries to return")
    time: Optional[str] = Field(None, description="Evaluation timestamp")

class LokiQueryRangeRequest(BaseModel):
    """Model for Loki range query requests."""
    query: str = Field(..., description="LogQL query string")
    start: str = Field(..., description="Start timestamp (RFC3339 or Unix timestamp)")
    end: str = Field(..., description="End timestamp (RFC3339 or Unix timestamp)")
    limit: Optional[int] = Field(None, description="Maximum number of entries to return")
    step: Optional[str] = Field(None, description="Query resolution step width")

# Dashboard API Models
class CreateDashboardRequest(BaseModel):
    """Model for creating dashboards."""
    dashboard_json: str = Field(..., description="Dashboard JSON")
    overwrite: bool = Field(False, description="Whether to overwrite existing dashboard")
    message: Optional[str] = Field(None, description="Commit message")
    
    @validator('dashboard_json')
    def validate_json(cls, v):
        try:
            json.loads(v)
            return v
        except json.JSONDecodeError as e:
            raise ValueError(f"Invalid JSON: {str(e)}")

class GetDashboardRequest(BaseModel):
    """Model for retrieving dashboards."""
    dashboard_uid: str = Field(..., description="Dashboard UID")

class DeleteDashboardRequest(BaseModel):
    """Model for deleting dashboards."""
    dashboard_uid: str = Field(..., description="Dashboard UID")

class GetAllDashboardsRequest(BaseModel):
    """Model for retrieving all dashboards."""
    type: Optional[str] = Field(None, description="Dashboard type filter")
    tag: Optional[str] = Field(None, description="Dashboard tag filter")
    limit: Optional[int] = Field(None, description="Maximum number of dashboards to return")

# Data Source API Models
class GetDataSourceRequest(BaseModel):
    """Model for retrieving data sources."""
    datasource_id: int = Field(..., description="Data source ID")

class CreateDataSourceRequest(BaseModel):
    """Model for creating data sources."""
    datasource_json: str = Field(..., description="Data source JSON")
    
    @validator('datasource_json')
    def validate_json(cls, v):
        try:
            json.loads(v)
            return v
        except json.JSONDecodeError as e:
            raise ValueError(f"Invalid JSON: {str(e)}")

class DeleteDataSourceRequest(BaseModel):
    """Model for deleting data sources."""
    datasource_id: int = Field(..., description="Data source ID")

# User API Models
class CreateUserRequest(BaseModel):
    """Model for creating users."""
    name: str = Field(..., description="User name")
    email: str = Field(..., description="User email")
    login: str = Field(..., description="User login")
    password: str = Field(..., description="User password")

# Organization API Models
class OrganizationRequest(BaseModel):
    """Model for organization requests."""
    pass

# Plugin API Models
class GetPluginsRequest(BaseModel):
    """Model for retrieving plugins."""
    pass

class InstallPluginRequest(BaseModel):
    """Model for installing plugins."""
    plugin_id: str = Field(..., description="Plugin ID")
    version: Optional[str] = Field(None, description="Plugin version")

class UninstallPluginRequest(BaseModel):
    """Model for uninstalling plugins."""
    plugin_id: str = Field(..., description="Plugin ID")

class GetPluginSettingsRequest(BaseModel):
    """Model for retrieving plugin settings."""
    plugin_id: str = Field(..., description="Plugin ID")

class UpdatePluginSettingsRequest(BaseModel):
    """Model for updating plugin settings."""
    plugin_id: str = Field(..., description="Plugin ID")
    settings_json: str = Field(..., description="Plugin settings JSON")
    
    @validator('settings_json')
    def validate_json(cls, v):
        try:
            json.loads(v)
            return v
        except json.JSONDecodeError as e:
            raise ValueError(f"Invalid JSON: {str(e)}")

class SearchPluginsRequest(BaseModel):
    """Model for searching plugins."""
    query: Optional[str] = Field(None, description="Search query")
    type: Optional[str] = Field(None, description="Plugin type filter")
    limit: Optional[int] = Field(None, description="Maximum number of plugins to return")

class IsPluginInstalledRequest(BaseModel):
    """Model for checking if a plugin is installed."""
    plugin_id: str = Field(..., description="Plugin ID")

# Alertmanager API Models
class SetAlertmanagerConfigRequest(BaseModel):
    """Model for updating Alertmanager configuration."""
    config_json: str = Field(..., description="Configuration JSON")
    
    @validator('config_json')
    def validate_json(cls, v):
        try:
            json.loads(v)
            return v
        except json.JSONDecodeError as e:
            raise ValueError(f"Invalid JSON: {str(e)}")

# Alerting API Models
class GetAlertRulesRequest(BaseModel):
    """Model for retrieving alert rules."""
    dashboard_uid: Optional[str] = Field(None, description="Dashboard UID filter")
    panel_id: Optional[int] = Field(None, description="Panel ID filter")

class CreateAlertRuleRequest(BaseModel):
    """Model for creating alert rules."""
    rule_json: str = Field(..., description="Alert rule JSON")
    
    @validator('rule_json')
    def validate_json(cls, v):
        try:
            json.loads(v)
            return v
        except json.JSONDecodeError as e:
            raise ValueError(f"Invalid JSON: {str(e)}")

class DeleteAlertRuleRequest(BaseModel):
    """Model for deleting alert rules."""
    rule_uid: str = Field(..., description="Alert rule UID")

# Query API Models
class QueryDataSourceRequest(BaseModel):
    """Model for querying data sources."""
    datasource_id: int = Field(..., description="Data source ID")
    query_json: str = Field(..., description="Query JSON")
    
    @validator('query_json')
    def validate_json(cls, v):
        try:
            json.loads(v)
            return v
        except json.JSONDecodeError as e:
            raise ValueError(f"Invalid JSON: {str(e)}")

# ============= Environment Setup =============

load_dotenv()

# Configure environment variables
GRAFANA_URL = os.environ.get("GRAFANA_URL")
GRAFANA_API_KEY = os.environ.get("GRAFANA_API_KEY")

if not GRAFANA_URL:
    raise ValueError("GRAFANA_URL environment variable must be set")
if not GRAFANA_API_KEY:
    raise ValueError("GRAFANA_API_KEY environment variable must be set")

# Setup HTTP client
http_client = httpx.AsyncClient(
    base_url=GRAFANA_URL,
    headers={
        "Authorization": f"Bearer {GRAFANA_API_KEY}",
        "Content-Type": "application/json",
        "Accept": "application/json",
    },
    timeout=30.0,
)

# Helper function to handle errors
def format_error(error: Exception) -> str:
    """Format error messages for consistent output."""
    if isinstance(error, httpx.HTTPStatusError):
        try:
            error_json = error.response.json()
            if isinstance(error_json, dict) and "message" in error_json:
                return json.dumps({"error": error_json["message"]})
        except:
            pass
        return json.dumps({"error": f"HTTP Error {error.response.status_code}: {error.response.reason_phrase}"})
    return json.dumps({"error": str(error)})

# ============= Grafana Mimir API Tools =============

@mcp.tool()
async def mimir_instant_query(query: str, time: Optional[str] = None) -> str:
    """
    Execute an instant query against Grafana Mimir.
    
    Args:
        query: Prometheus query string
        time: Optional evaluation timestamp (RFC3339 or Unix timestamp)
    """
    request = MimirQueryRequest(query=query, time=time)
    try:
        params = {"query": request.query}
        if request.time:
            params["time"] = request.time
        
        response = await http_client.get("/api/v1/query", params=params)
        response.raise_for_status()
        return json.dumps(response.json(), indent=2)
    except Exception as e:
        return format_error(e)

@mcp.tool()
async def mimir_range_query(query: str, start: str, end: str, step: str) -> str:
    """
    Execute a range query against Grafana Mimir.
    
    Args:
        query: Prometheus query string
        start: Start timestamp (RFC3339 or Unix timestamp)
        end: End timestamp (RFC3339 or Unix timestamp)
        step: Query resolution step width (duration format or float seconds)
    """
    request = MimirRangeQueryRequest(query=query, start=start, end=end, step=step)
    try:
        params = {
            "query": request.query,
            "start": request.start,
            "end": request.end,
            "step": request.step,
        }
        
        response = await http_client.get("/api/v1/query_range", params=params)
        response.raise_for_status()
        return json.dumps(response.json(), indent=2)
    except Exception as e:
        return format_error(e)

@mcp.tool()
async def mimir_get_series(match: List[str], start: Optional[str] = None, end: Optional[str] = None) -> str:
    """
    Get series metadata from Grafana Mimir.
    
    Args:
        match: Series selectors
        start: Optional start timestamp
        end: Optional end timestamp
    """
    request = MimirGetSeriesRequest(match=match, start=start, end=end)
    try:
        params = {"match[]": request.match}
        if request.start:
            params["start"] = request.start
        if request.end:
            params["end"] = request.end
        
        response = await http_client.get("/api/v1/series", params=params)
        response.raise_for_status()
        return json.dumps(response.json(), indent=2)
    except Exception as e:
        return format_error(e)

# ============= Grafana Loki API Tools =============

@mcp.tool()
async def loki_query(query: str, limit: Optional[int] = None, time: Optional[str] = None) -> str:
    """
    Execute an instant query against Grafana Loki.
    
    Args:
        query: LogQL query string
        limit: Maximum number of entries to return
        time: Optional query evaluation timestamp
    """
    request = LokiQueryRequest(query=query, limit=limit, time=time)
    try:
        params = {"query": request.query}
        if request.limit:
            params["limit"] = str(request.limit)
        if request.time:
            params["time"] = request.time
        
        response = await http_client.get("/loki/api/v1/query", params=params)
        response.raise_for_status()
        return json.dumps(response.json(), indent=2)
    except Exception as e:
        return format_error(e)

@mcp.tool()
async def loki_query_range(query: str, start: str, end: str, limit: Optional[int] = None, step: Optional[str] = None) -> str:
    """
    Execute a range query against Grafana Loki.
    
    Args:
        query: LogQL query string
        start: Start timestamp (RFC3339 or Unix timestamp)
        end: End timestamp (RFC3339 or Unix timestamp)
        limit: Maximum number of entries to return
        step: Optional step parameter for aggregation
    """
    request = LokiQueryRangeRequest(query=query, start=start, end=end, limit=limit, step=step)
    try:
        params = {
            "query": request.query,
            "start": request.start,
            "end": request.end,
        }
        if request.limit:
            params["limit"] = str(request.limit)
        if request.step:
            params["step"] = request.step
        
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
async def check_grafana_health() -> str:
    """Check the health of the Grafana instance."""
    try:
        response = await http_client.get("/api/health")
        response.raise_for_status()
        return json.dumps(response.json(), indent=2)
    except Exception as e:
        return format_error(e)

@mcp.tool()
async def get_dashboard(dashboard_uid: str) -> str:
    """
    Retrieve a dashboard by UID.
    
    Args:
        dashboard_uid: Dashboard UID
    """
    request = GetDashboardRequest(dashboard_uid=dashboard_uid)
    try:
        response = await http_client.get(f"/api/dashboards/uid/{request.dashboard_uid}")
        response.raise_for_status()
        return json.dumps(response.json(), indent=2)
    except Exception as e:
        return format_error(e)

@mcp.tool()
async def create_dashboard(dashboard_json: str, overwrite: bool = False, message: Optional[str] = None) -> str:
    """
    Create or update a dashboard.
    
    Args:
        dashboard_json: Dashboard JSON
        overwrite: Whether to overwrite existing dashboard
        message: Optional commit message
    """
    request = CreateDashboardRequest(dashboard_json=dashboard_json, overwrite=overwrite, message=message)
    try:
        dashboard_data = json.loads(request.dashboard_json)
        payload = {
            "dashboard": dashboard_data,
            "overwrite": request.overwrite,
        }
        if request.message:
            payload["message"] = request.message
        
        response = await http_client.post("/api/dashboards/db", json=payload)
        response.raise_for_status()
        return json.dumps(response.json(), indent=2)
    except Exception as e:
        return format_error(e)

@mcp.tool()
async def delete_dashboard(dashboard_uid: str) -> str:
    """
    Delete a dashboard by UID.
    
    Args:
        dashboard_uid: Dashboard UID
    """
    request = DeleteDashboardRequest(dashboard_uid=dashboard_uid)
    try:
        response = await http_client.delete(f"/api/dashboards/uid/{request.dashboard_uid}")
        response.raise_for_status()
        return json.dumps(response.json(), indent=2)
    except Exception as e:
        return format_error(e)

@mcp.tool()
async def get_all_dashboards(type: Optional[str] = None, tag: Optional[str] = None, limit: Optional[int] = None) -> str:
    """
    Retrieve all dashboards.
    
    Args:
        type: Optional dashboard type filter
        tag: Optional dashboard tag filter
        limit: Optional maximum number of dashboards to return
    """
    request = GetAllDashboardsRequest(type=type, tag=tag, limit=limit)
    try:
        params = {}
        if request.type:
            params["type"] = request.type
        if request.tag:
            params["tag"] = request.tag
        if request.limit:
            params["limit"] = str(request.limit)
        
        response = await http_client.get("/api/search", params=params)
        response.raise_for_status()
        return json.dumps(response.json(), indent=2)
    except Exception as e:
        return format_error(e)

@mcp.tool()
async def get_plugins() -> str:
    """Retrieve all installed plugins."""
    request = GetPluginsRequest()
    try:
        response = await http_client.get("/api/plugins")
        response.raise_for_status()
        return json.dumps(response.json(), indent=2)
    except Exception as e:
        return format_error(e)

@mcp.tool()
async def get_datasource(datasource_id: int) -> str:
    """
    Retrieve a data source by ID.
    
    Args:
        datasource_id: Data source ID
    """
    request = GetDataSourceRequest(datasource_id=datasource_id)
    try:
        response = await http_client.get(f"/api/datasources/{request.datasource_id}")
        response.raise_for_status()
        return json.dumps(response.json(), indent=2)
    except Exception as e:
        return format_error(e)

@mcp.tool()
async def create_datasource(datasource_json: str) -> str:
    """
    Create a data source.
    
    Args:
        datasource_json: Data source JSON
    """
    request = CreateDataSourceRequest(datasource_json=datasource_json)
    try:
        datasource_data = json.loads(request.datasource_json)
        response = await http_client.post("/api/datasources", json=datasource_data)
        response.raise_for_status()
        return json.dumps(response.json(), indent=2)
    except Exception as e:
        return format_error(e)

@mcp.tool()
async def delete_datasource(datasource_id: int) -> str:
    """
    Delete a data source by ID.
    
    Args:
        datasource_id: Data source ID
    """
    request = DeleteDataSourceRequest(datasource_id=datasource_id)
    try:
        response = await http_client.delete(f"/api/datasources/{request.datasource_id}")
        response.raise_for_status()
        return json.dumps(response.json(), indent=2)
    except Exception as e:
        return format_error(e)

# ============= Grafana Alertmanager API Tools =============

@mcp.tool()
async def get_alertmanager_config() -> str:
    """Retrieve the current Alertmanager configuration."""
    try:
        response = await http_client.get("/api/alertmanager/grafana/config/api/v1/alerts")
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
    request = SetAlertmanagerConfigRequest(config_json=config_json)
    try:
        config_data = json.loads(request.config_json)
        response = await http_client.post("/api/alertmanager/grafana/config/api/v1/alerts", json=config_data)
        response.raise_for_status()
        return json.dumps(response.json(), indent=2)
    except Exception as e:
        return format_error(e)

# ============= Grafana Alerting API Tools =============

@mcp.tool()
async def get_alert_rules(dashboard_uid: Optional[str] = None, panel_id: Optional[int] = None) -> str:
    """
    Retrieve alert rules.
    
    Args:
        dashboard_uid: Optional dashboard UID filter
        panel_id: Optional panel ID filter
    """
    request = GetAlertRulesRequest(dashboard_uid=dashboard_uid, panel_id=panel_id)
    try:
        params = {}
        if request.dashboard_uid:
            params["dashboardUID"] = request.dashboard_uid
        if request.panel_id:
            params["panelId"] = str(request.panel_id)
        
        response = await http_client.get("/api/alerting/rules", params=params)
        response.raise_for_status()
        return json.dumps(response.json(), indent=2)
    except Exception as e:
        return format_error(e)

@mcp.tool()
async def create_alert_rule(rule_json: str) -> str:
    """
    Create an alert rule.
    
    Args:
        rule_json: Alert rule JSON
    """
    request = CreateAlertRuleRequest(rule_json=rule_json)
    try:
        rule_data = json.loads(request.rule_json)
        response = await http_client.post("/api/alerting/rules", json=rule_data)
        response.raise_for_status()
        return json.dumps(response.json(), indent=2)
    except Exception as e:
        return format_error(e)

@mcp.tool()
async def delete_alert_rule(rule_uid: str) -> str:
    """
    Delete an alert rule by UID.
    
    Args:
        rule_uid: Alert rule UID
    """
    request = DeleteAlertRuleRequest(rule_uid=rule_uid)
    try:
        response = await http_client.delete(f"/api/alerting/rules/{request.rule_uid}")
        response.raise_for_status()
        return json.dumps(response.json(), indent=2)
    except Exception as e:
        return format_error(e)

# ============= Grafana Query API Tools =============

@mcp.tool()
async def query_data_source(datasource_id: int, query_json: str) -> str:
    """
    Query a data source.
    
    Args:
        datasource_id: Data source ID
        query_json: Query JSON
    """
    request = QueryDataSourceRequest(datasource_id=datasource_id, query_json=query_json)
    try:
        query_data = json.loads(request.query_json)
        response = await http_client.post(f"/api/datasources/{request.datasource_id}/query", json=query_data)
        response.raise_for_status()
        return json.dumps(response.json(), indent=2)
    except Exception as e:
        return format_error(e)

# ============= Remote Write API Tools =============

@mcp.tool()
async def mimir_remote_write(metrics_json: str) -> str:
    """
    Write metrics to Grafana Mimir using remote write.
    
    Args:
        metrics_json: Metrics JSON in Prometheus format
    """
    try:
        metrics_data = json.loads(metrics_json)
        response = await http_client.post("/api/v1/push", json=metrics_data)
        response.raise_for_status()
        return json.dumps({"status": "success", "message": "Metrics written successfully"})
    except Exception as e:
        return format_error(e)

# Main execution
if __name__ == "__main__":
    mcp.run()