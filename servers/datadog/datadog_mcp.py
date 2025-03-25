#!/usr/bin/env python3
"""
Datadog MCP Server

This server provides tools for interacting with the Datadog API through the Model Context Protocol.
"""

import os
import json
import time
import requests
from typing import Dict, List, Any, Optional, Union
from urllib.parse import urljoin
from mcp.server.fastmcp import FastMCP, Context
from dotenv import load_dotenv
from pydantic import BaseModel, Field, Json, field_validator
from datadog_api_client import ApiClient, Configuration
from datadog_api_client.v1.api.metrics_api import MetricsApi
from datadog_api_client.v1.api.monitors_api import MonitorsApi
from datadog_api_client.v1.api.events_api import EventsApi
from datadog_api_client.v1.api.dashboards_api import DashboardsApi
from datadog_api_client.v1.model.metrics_payload import MetricsPayload
from datadog_api_client.v1.model.series import Series
from datadog_api_client.v1.model.point import Point

# Pydantic Models for API validation
class DatadogResponse(BaseModel):
    """Base model for Datadog API responses."""
    status: str = "success"
    message: str | None = None
    
class DatadogErrorResponse(DatadogResponse):
    """Error response model."""
    status: str = "error"

class PaginationParams(BaseModel):
    """Common pagination parameters."""
    page_size: int = Field(default=100, description="Maximum number of results to return")
    page: int = Field(default=1, description="Page number to retrieve")

class JSONString(BaseModel):
    """Model for validating JSON strings."""
    json_str: Json = Field(description="JSON string")
    
    def get_parsed_json(self) -> dict:
        """Return the parsed JSON as a Python dictionary."""
        return json.loads(self.json_str)

# Models for Metrics API
class MetricSubmit(BaseModel):
    """Model for submitting a metric."""
    metric_name: str = Field(description="Name of the metric")
    value: float = Field(description="Value of the metric")
    timestamp: Optional[int] = Field(default=None, description="Timestamp for the metric point")
    tags: Optional[List[str]] = Field(default=None, description="List of tags for the metric")
    
class MetricQuery(BaseModel):
    """Model for querying metrics."""
    query: str = Field(description="Metric query string")
    from_time: int = Field(description="Start time in seconds since epoch")
    to_time: int = Field(description="End time in seconds since epoch")

# Models for Events API
class EventCreate(BaseModel):
    """Model for creating an event."""
    title: str = Field(description="Title of the event")
    text: str = Field(description="Text of the event")
    tags: Optional[List[str]] = Field(default=None, description="List of tags for the event")
    alert_type: Optional[str] = Field(default="info", description="Alert type (info, warning, error, success)")
    priority: Optional[str] = Field(default="normal", description="Priority (normal, low)")
    
    @field_validator('alert_type')
    def validate_alert_type(cls, v):
        valid_types = ["info", "warning", "error", "success"]
        if v not in valid_types:
            raise ValueError(f"Alert type must be one of {valid_types}")
        return v
    
    @field_validator('priority')
    def validate_priority(cls, v):
        valid_priorities = ["normal", "low"]
        if v not in valid_priorities:
            raise ValueError(f"Priority must be one of {valid_priorities}")
        return v

# Models for Monitors API
class MonitorCreate(BaseModel):
    """Model for creating a monitor."""
    name: str = Field(description="Name of the monitor")
    query: str = Field(description="Query for the monitor")
    type: str = Field(description="Type of the monitor")
    message: str = Field(description="Message for the monitor")
    tags: Optional[List[str]] = Field(default=None, description="List of tags for the monitor")
    
    @field_validator('type')
    def validate_type(cls, v):
        valid_types = ["metric alert", "service check", "event alert", "query alert", "composite"]
        if v not in valid_types:
            raise ValueError(f"Monitor type must be one of {valid_types}")
        return v

class MonitorUpdate(BaseModel):
    """Model for updating a monitor."""
    monitor_id: int = Field(description="ID of the monitor")
    name: Optional[str] = Field(default=None, description="New name for the monitor")
    query: Optional[str] = Field(default=None, description="New query for the monitor")
    message: Optional[str] = Field(default=None, description="New message for the monitor")
    tags: Optional[List[str]] = Field(default=None, description="New list of tags for the monitor")

# Models for Dashboards API
class DashboardCreate(BaseModel):
    """Model for creating a dashboard."""
    title: str = Field(description="Title of the dashboard")
    description: Optional[str] = Field(default="", description="Description of the dashboard")
    widgets: List[Dict] = Field(default_factory=list, description="List of widgets for the dashboard")
    layout_type: str = Field(default="ordered", description="Layout type of the dashboard")
    
    @field_validator('layout_type')
    def validate_layout_type(cls, v):
        valid_types = ["ordered", "free"]
        if v not in valid_types:
            raise ValueError(f"Layout type must be one of {valid_types}")
        return v

# Initialize FastMCP server
mcp = FastMCP("datadog")

load_dotenv()

# Configuration
DATADOG_API_KEY = os.getenv("DATADOG_API_KEY")
DATADOG_APP_KEY = os.getenv("DATADOG_APP_KEY")
DATADOG_SITE = os.getenv("DATADOG_SITE", "datadoghq.com")

# API Client
class DatadogClient:
    def __init__(self, api_key: Optional[str] = None, app_key: Optional[str] = None, site: Optional[str] = None):
        self.api_key = api_key or DATADOG_API_KEY
        self.app_key = app_key or DATADOG_APP_KEY
        self.site = site or DATADOG_SITE
        
        if not self.api_key:
            raise ValueError("DATADOG_API_KEY is required")
        if not self.app_key:
            raise ValueError("DATADOG_APP_KEY is required")
            
        self.configuration = Configuration()
        self.configuration.api_key['apiKeyAuth'] = self.api_key
        self.configuration.api_key['appKeyAuth'] = self.app_key
        self.configuration.server_variables['site'] = self.site
        
        self.api_client = ApiClient(self.configuration)
        self.metrics_api = MetricsApi(self.api_client)
        self.monitors_api = MonitorsApi(self.api_client)
        self.events_api = EventsApi(self.api_client)
        self.dashboards_api = DashboardsApi(self.api_client)
    
    def __enter__(self):
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        self.api_client.close()

# Helper Functions
def get_datadog_client() -> DatadogClient:
    """Get an initialized Datadog API client."""
    client = DatadogClient(
        api_key=DATADOG_API_KEY,
        app_key=DATADOG_APP_KEY
    )
    return client

# MCP Tools - Metrics Management

@mcp.tool()
def submit_metric(metric_name: str, value: float, timestamp: Optional[int] = None, tags: Optional[List[str]] = None) -> str:
    """Submit a metric to Datadog.
    
    Args:
        metric_name: Name of the metric
        value: Value of the metric
        timestamp: Timestamp for the metric point (defaults to current time if not provided)
        tags: List of tags for the metric
    """
    try:
        # Create model instance to validate params
        metric_data = MetricSubmit(
            metric_name=metric_name,
            value=value,
            timestamp=timestamp,
            tags=tags
        )
        
        with get_datadog_client() as client:
            # If timestamp is not provided, it will be set to current time by the API
            current_timestamp = timestamp if timestamp else int(time.time())
            
            body = MetricsPayload(
                series=[
                    Series(
                        metric=metric_data.metric_name,
                        points=[[current_timestamp, metric_data.value]],
                        tags=metric_data.tags
                    )
                ]
            )
            
            response = client.metrics_api.submit_metrics(body=body)
            return json.dumps({"status": "success", "message": "Metric submitted successfully"})
            
    except ValueError as e:
        # Handle validation errors
        return json.dumps(DatadogErrorResponse(message=str(e)).model_dump())
    except Exception as e:
        # Handle API errors
        return json.dumps(DatadogErrorResponse(message=str(e)).model_dump())

@mcp.tool()
def query_metrics(query: str, from_time: int, to_time: int) -> str:
    """Query metrics from Datadog.
    
    Args:
        query: Metric query string
        from_time: Start time in seconds since epoch
        to_time: End time in seconds since epoch
    """
    try:
        # Create model instance to validate params
        query_data = MetricQuery(
            query=query,
            from_time=from_time,
            to_time=to_time
        )
        
        with get_datadog_client() as client:
            # In v1 API, we use the query_metrics endpoint directly with parameters
            params = {
                "query": query_data.query,
                "from": query_data.from_time,
                "to": query_data.to_time
            }
            
            response = client.metrics_api.query_metrics(**params)
            return json.dumps(response.to_dict())
            
    except ValueError as e:
        # Handle validation errors
        return json.dumps(DatadogErrorResponse(message=str(e)).model_dump())
    except Exception as e:
        # Handle API errors
        return json.dumps(DatadogErrorResponse(message=str(e)).model_dump())

# MCP Tools - Events Management

@mcp.tool()
def create_event(title: str, text: str, tags: Optional[List[str]] = None, alert_type: str = "info", priority: str = "normal") -> str:
    """Create an event in Datadog.
    
    Args:
        title: Title of the event
        text: Text of the event
        tags: List of tags for the event
        alert_type: Alert type (info, warning, error, success)
        priority: Priority (normal, low)
    """
    try:
        # Create model instance to validate params
        event_data = EventCreate(
            title=title,
            text=text,
            tags=tags,
            alert_type=alert_type,
            priority=priority
        )
        
        with get_datadog_client() as client:
            # Use v1 API for events - Event model is directly available in v1
            from datadog_api_client.v1.model.event import Event
            
            # Create event with v1 API format
            body = Event(
                title=event_data.title,
                text=event_data.text,
                tags=event_data.tags,
                alert_type=event_data.alert_type,
                priority=event_data.priority
            )
            
            response = client.events_api.create_event(body=body)
            return json.dumps(response.to_dict())
            
    except ValueError as e:
        # Handle validation errors
        return json.dumps(DatadogErrorResponse(message=str(e)).model_dump())
    except Exception as e:
        # Handle API errors
        return json.dumps(DatadogErrorResponse(message=str(e)).model_dump())

@mcp.tool()
def get_events(query: Optional[str] = None, from_time: Optional[int] = None, to_time: Optional[int] = None) -> str:
    """Get events from Datadog.
    
    Args:
        query: Event query string
        from_time: Start time in seconds since epoch
        to_time: End time in seconds since epoch
    """
    try:
        with get_datadog_client() as client:
            params = {}
            if query:
                params["filter[query]"] = query
            if from_time:
                params["filter[from]"] = from_time
            if to_time:
                params["filter[to]"] = to_time
                
            response = client.events_api.list_events(**params)
            return json.dumps(response.to_dict())
            
    except Exception as e:
        # Handle API errors
        return json.dumps(DatadogErrorResponse(message=str(e)).model_dump())

# MCP Tools - Monitors Management

@mcp.tool()
def create_monitor(name: str, query: str, type: str, message: str, tags: Optional[List[str]] = None) -> str:
    """Create a monitor in Datadog.
    
    Args:
        name: Name of the monitor
        query: Query for the monitor
        type: Type of the monitor (metric alert, service check, event alert, query alert, composite)
        message: Message for the monitor
        tags: List of tags for the monitor
    """
    try:
        # Create model instance to validate params
        monitor_data = MonitorCreate(
            name=name,
            query=query,
            type=type,
            message=message,
            tags=tags
        )
        
        with get_datadog_client() as client:
            # Use v1 API for monitors
            from datadog_api_client.v1.model.monitor import Monitor
            
            # In v1 API, we use the Monitor model directly
            body = Monitor(
                name=monitor_data.name,
                type=monitor_data.type,  # v1 API uses string types directly
                query=monitor_data.query,
                message=monitor_data.message,
                tags=monitor_data.tags
            )
            
            response = client.monitors_api.create_monitor(body=body)
            return json.dumps(response.to_dict())
            
    except ValueError as e:
        # Handle validation errors
        return json.dumps(DatadogErrorResponse(message=str(e)).model_dump())
    except Exception as e:
        # Handle API errors
        return json.dumps(DatadogErrorResponse(message=str(e)).model_dump())

@mcp.tool()
def get_monitor(monitor_id: int) -> str:
    """Get a monitor from Datadog.
    
    Args:
        monitor_id: ID of the monitor
    """
    try:
        with get_datadog_client() as client:
            response = client.monitors_api.get_monitor(monitor_id=monitor_id)
            return json.dumps(response.to_dict())
            
    except Exception as e:
        # Handle API errors
        return json.dumps(DatadogErrorResponse(message=str(e)).model_dump())

@mcp.tool()
def update_monitor(monitor_id: int, name: Optional[str] = None, query: Optional[str] = None, message: Optional[str] = None, tags: Optional[List[str]] = None) -> str:
    """Update a monitor in Datadog.
    
    Args:
        monitor_id: ID of the monitor
        name: New name for the monitor
        query: New query for the monitor
        message: New message for the monitor
        tags: New list of tags for the monitor
    """
    try:
        # Create model instance to validate params
        monitor_data = MonitorUpdate(
            monitor_id=monitor_id,
            name=name,
            query=query,
            message=message,
            tags=tags
        )
        
        with get_datadog_client() as client:
            # Use v1 API for monitor updates
            from datadog_api_client.v1.model.monitor import Monitor
            
            attributes = {}
            if monitor_data.name:
                attributes["name"] = monitor_data.name
            if monitor_data.query:
                attributes["query"] = monitor_data.query
            if monitor_data.message:
                attributes["message"] = monitor_data.message
            if monitor_data.tags:
                attributes["tags"] = monitor_data.tags
                
            # In v1 API, we create a Monitor object with only the fields we want to update
            body = Monitor(**attributes)
            
            response = client.monitors_api.update_monitor(monitor_id=monitor_data.monitor_id, body=body)
            return json.dumps(response.to_dict())
            
    except ValueError as e:
        # Handle validation errors
        return json.dumps(DatadogErrorResponse(message=str(e)).model_dump())
    except Exception as e:
        # Handle API errors
        return json.dumps(DatadogErrorResponse(message=str(e)).model_dump())

@mcp.tool()
def delete_monitor(monitor_id: int) -> str:
    """Delete a monitor from Datadog.
    
    Args:
        monitor_id: ID of the monitor
    """
    try:
        with get_datadog_client() as client:
            response = client.monitors_api.delete_monitor(monitor_id=monitor_id)
            return json.dumps({"status": "success", "message": f"Monitor {monitor_id} deleted successfully"})
            
    except Exception as e:
        # Handle API errors
        return json.dumps(DatadogErrorResponse(message=str(e)).model_dump())

# MCP Tools - Dashboards Management

@mcp.tool()
def create_dashboard(title: str, description: str = "", widgets: Optional[List[Dict]] = None, layout_type: str = "ordered") -> str:
    """Create a dashboard in Datadog.
    
    Args:
        title: Title of the dashboard
        description: Description of the dashboard
        widgets: List of widgets for the dashboard
        layout_type: Layout type of the dashboard (ordered, free)
    """
    try:
        # Create model instance to validate params
        dashboard_data = DashboardCreate(
            title=title,
            description=description,
            widgets=widgets or [],
            layout_type=layout_type
        )
        
        with get_datadog_client() as client:
            # Use v1 API for dashboards
            from datadog_api_client.v1.model.dashboard import Dashboard
            from datadog_api_client.v1.model.dashboard_layout_type import DashboardLayoutType
            
            # Create dashboard with v1 API format
            body = Dashboard(
                title=dashboard_data.title,
                description=dashboard_data.description,
                widgets=dashboard_data.widgets,
                layout_type=dashboard_data.layout_type
            )
            
            response = client.dashboards_api.create_dashboard(body=body)
            return json.dumps(response.to_dict())
            
    except ValueError as e:
        # Handle validation errors
        return json.dumps(DatadogErrorResponse(message=str(e)).model_dump())
    except Exception as e:
        # Handle API errors
        return json.dumps(DatadogErrorResponse(message=str(e)).model_dump())

@mcp.tool()
def get_dashboard(dashboard_id: str) -> str:
    """Get a dashboard from Datadog.
    
    Args:
        dashboard_id: ID of the dashboard
    """
    try:
        with get_datadog_client() as client:
            response = client.dashboards_api.get_dashboard(dashboard_id=dashboard_id)
            return json.dumps(response.to_dict())
            
    except Exception as e:
        # Handle API errors
        return json.dumps(DatadogErrorResponse(message=str(e)).model_dump())

@mcp.tool()
def delete_dashboard(dashboard_id: str) -> str:
    """Delete a dashboard from Datadog.
    
    Args:
        dashboard_id: ID of the dashboard
    """
    try:
        with get_datadog_client() as client:
            response = client.dashboards_api.delete_dashboard(dashboard_id=dashboard_id)
            return json.dumps({"status": "success", "message": f"Dashboard {dashboard_id} deleted successfully"})
            
    except Exception as e:
        # Handle API errors
        return json.dumps(DatadogErrorResponse(message=str(e)).model_dump())

# Main entry point
if __name__ == "__main__":
    # Initialize and run the server
    mcp.run(transport='stdio')
