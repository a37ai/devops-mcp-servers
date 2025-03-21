from mcp import FastMCP, Context
from datadog_api_client import ApiClient, Configuration
from datadog_api_client.v1.api.dashboards_api import DashboardsApi
from datadog_api_client.v1.api.metrics_api import MetricsApi
from datadog_api_client.v1.api.events_api import EventsApi
from datadog_api_client.v1.api.monitors_api import MonitorsApi
from datadog_api_client.v1.api.logs_api import LogsApi
from datadog_api_client.v2.api.logs_api import LogsApi as LogsApiV2
from datadog_api_client.v1.api.hosts_api import HostsApi
from datadog_api_client.v1.api.tags_api import TagsApi
from datadog_api_client.v1.api.users_api import UsersApi
from contextlib import asynccontextmanager
from typing import AsyncIterator, Dict, Any
import os

class DatadogMCPServer:
    def __init__(self, name="Datadog MCP Server", api_key=None, app_key=None, api_url=None):
        """Initialize the Datadog MCP server"""
        # Set up FastMCP with dependencies
        self.mcp = FastMCP(
            name, 
            dependencies=["datadog-api-client"]
        )
        
        # Store auth information
        self.api_key = api_key
        self.app_key = app_key
        self.api_url = api_url
        
        # Configure lifespan for api client
        self.mcp.lifespan = self._api_client_lifespan
    
    @asynccontextmanager
    async def _api_client_lifespan(self, server: FastMCP) -> AsyncIterator[Dict[str, Any]]:
        """Manage API client lifecycle and authentication"""
        # Initialize configuration
        configuration = Configuration()
        
        # Set API/APP keys from instance, environment, or raise error
        configuration.api_key["apiKeyAuth"] = self.api_key or os.environ.get("DATADOG_API_KEY")
        configuration.api_key["appKeyAuth"] = self.app_key or os.environ.get("DATADOG_APP_KEY")
        
        if not configuration.api_key["apiKeyAuth"] or not configuration.api_key["appKeyAuth"]:
            raise ValueError("Datadog API and APP keys must be provided")
        
        # Set API URL if provided
        if self.api_url:
            configuration.server_variables["site"] = self.api_url
            
        # Create API client and specific API instances
        api_client = ApiClient(configuration)
        
        # Create context with API instances
        context = {
            "api_client": api_client,
            "dashboards_api": DashboardsApi(api_client),
            "metrics_api": MetricsApi(api_client),
            "events_api": EventsApi(api_client),
            "monitors_api": MonitorsApi(api_client),
            "logs_api": LogsApi(api_client),
            "logs_api_v2": LogsApiV2(api_client),
            "hosts_api": HostsApi(api_client),
            "tags_api": TagsApi(api_client),
            "users_api": UsersApi(api_client)
        }
        
        try:
            yield context
        finally:
            # Clean up when server shuts down
            api_client.close()
def register_metrics_resources_and_tools(self):
    """Register resources and tools for Datadog Metrics API"""
    
    @self.mcp.resource("metrics://{from_time}/{to_time}/{query}")
    def get_metric_data(from_time: str, to_time: str, query: str, ctx: Context) -> str:
        """Get metric data for a specific query and time range"""
        metrics_api = ctx.request_context.lifespan_context["metrics_api"]
        response = metrics_api.query_metrics(
            _from=int(from_time),
            to=int(to_time),
            query=query
        )
        return response.to_json()
    
    @self.mcp.resource("metrics://list/{from_time}")
    def list_metrics(from_time: str, ctx: Context) -> str:
        """List available metrics from a specific time"""
        metrics_api = ctx.request_context.lifespan_context["metrics_api"]
        response = metrics_api.list_metrics(
            _from=int(from_time)
        )
        return response.to_json()
    
    @self.mcp.tool()
    def submit_metric(ctx: Context, metric_name: str, points: list, 
                      metric_type: str = "gauge", host: str = None, tags: list = None) -> str:
        """Submit a metric to Datadog"""
        metrics_api = ctx.request_context.lifespan_context["metrics_api"]
        
        # Create series payload
        series = {
            "metric": metric_name,
            "points": points,
            "type": metric_type
        }
        
        if host:
            series["host"] = host
            
        if tags:
            series["tags"] = tags
        
        try:
            metrics_api.submit_metrics(series=[series])
            return f"Successfully submitted metric: {metric_name}"
        except Exception as e:
            return f"Error submitting metric: {str(e)}"
def register_events_resources_and_tools(self):
    """Register resources and tools for Datadog Events API"""
    
    @self.mcp.resource("events://{start}/{end}")
    def get_events(start: str, end: str, ctx: Context) -> str:
        """Get events for a specific time range"""
        events_api = ctx.request_context.lifespan_context["events_api"]
        response = events_api.list_events(
            start=int(start),
            end=int(end)
        )
        return response.to_json()
    
    @self.mcp.resource("events://{event_id}")
    def get_event(event_id: str, ctx: Context) -> str:
        """Get a specific event by ID"""
        events_api = ctx.request_context.lifespan_context["events_api"]
        response = events_api.get_event(event_id)
        return response.to_json()
    
    @self.mcp.tool()
    def create_event(ctx: Context, title: str, text: str, 
                      priority: str = "normal", tags: list = None, 
                      alert_type: str = "info", host: str = None) -> str:
        """Create an event in Datadog"""
        events_api = ctx.request_context.lifespan_context["events_api"]
        
        # Validate alert_type
        valid_alert_types = ["error", "warning", "info", "success"]
        if alert_type not in valid_alert_types:
            return f"Invalid alert_type. Must be one of: {', '.join(valid_alert_types)}"
        
        try:
            response = events_api.create_event(
                title=title,
                text=text,
                priority=priority,
                tags=tags,
                alert_type=alert_type,
                host=host
            )
            return response.to_json()
        except Exception as e:
            return f"Error creating event: {str(e)}"
def register_logs_resources_and_tools(self):
    """Register resources and tools for Datadog Logs API"""
    
    @self.mcp.tool()
    def submit_logs(ctx: Context, logs: list) -> str:
        """Submit logs to Datadog"""
        logs_api = ctx.request_context.lifespan_context["logs_api"]
        
        try:
            logs_api.submit_log(
                body=logs
            )
            return f"Successfully submitted {len(logs)} logs"
        except Exception as e:
            return f"Error submitting logs: {str(e)}"
    
    @self.mcp.tool()
    def query_logs(ctx: Context, query: str, time_from: int, time_to: int, limit: int = 10) -> str:
        """Query logs from Datadog"""
        logs_api_v2 = ctx.request_context.lifespan_context["logs_api_v2"]
        
        try:
            response = logs_api_v2.list_logs(
                filter_query=query,
                filter_from=time_from,
                filter_to=time_to,
                page_limit=limit
            )
            return response.to_json()
        except Exception as e:
            return f"Error querying logs: {str(e)}"
def register_dashboards_resources_and_tools(self):
    """Register resources and tools for Datadog Dashboards API"""
    
    @self.mcp.resource("dashboards://list")
    def list_dashboards(ctx: Context) -> str:
        """List all dashboards"""
        dashboards_api = ctx.request_context.lifespan_context["dashboards_api"]
        response = dashboards_api.list_dashboards()
        return response.to_json()
    
    @self.mcp.resource("dashboards://{dashboard_id}")
    def get_dashboard(dashboard_id: str, ctx: Context) -> str:
        """Get dashboard by ID"""
        dashboards_api = ctx.request_context.lifespan_context["dashboards_api"]
        response = dashboards_api.get_dashboard(dashboard_id)
        return response.to_json()
    
    @self.mcp.tool()
    def create_dashboard(ctx: Context, title: str, description: str = "", 
                         widgets: list = None, layout_type: str = "ordered") -> str:
        """Create a dashboard in Datadog"""
        from datadog_api_client.v1.model.dashboard import Dashboard
        from datadog_api_client.v1.model.dashboard_layout_type import DashboardLayoutType
        from datadog_api_client.v1.model.dashboard_widget import DashboardWidget
        
        dashboards_api = ctx.request_context.lifespan_context["dashboards_api"]
        
        # Set up default widgets if none provided
        if widgets is None:
            widgets = []
        
        try:
            # Create dashboard with specified parameters
            dashboard = Dashboard(
                title=title,
                description=description,
                layout_type=DashboardLayoutType(layout_type),
                widgets=[DashboardWidget(**widget) for widget in widgets]
            )
            
            response = dashboards_api.create_dashboard(body=dashboard)
            return response.to_json()
        except Exception as e:
            return f"Error creating dashboard: {str(e)}"
def register_monitors_resources_and_tools(self):
    """Register resources and tools for Datadog Monitors API"""
    
    @self.mcp.resource("monitors://list")
    def list_monitors(ctx: Context) -> str:
        """List all monitors"""
        monitors_api = ctx.request_context.lifespan_context["monitors_api"]
        response = monitors_api.list_monitors()
        return response.to_json()
    
    @self.mcp.resource("monitors://{monitor_id}")
    def get_monitor(monitor_id: int, ctx: Context) -> str:
        """Get monitor by ID"""
        monitors_api = ctx.request_context.lifespan_context["monitors_api"]
        response = monitors_api.get_monitor(monitor_id)
        return response.to_json()
    
    @self.mcp.tool()
    def create_monitor(ctx: Context, name: str, type: str, query: str, message: str = "", 
                      options: dict = None, tags: list = None) -> str:
        """Create a monitor in Datadog"""
        from datadog_api_client.v1.model.monitor import Monitor
        from datadog_api_client.v1.model.monitor_type import MonitorType
        from datadog_api_client.v1.model.monitor_options import MonitorOptions
        
        monitors_api = ctx.request_context.lifespan_context["monitors_api"]
        
        try:
            # Set up monitor options
            monitor_options = MonitorOptions(**(options or {}))
            
            # Create monitor
            monitor = Monitor(
                name=name,
                type=MonitorType(type),
                query=query,
                message=message,
                options=monitor_options,
                tags=tags or []
            )
            
            response = monitors_api.create_monitor(body=monitor)
            return response.to_json()
        except Exception as e:
            return f"Error creating monitor: {str(e)}"
def register_hosts_resources_and_tools(self):
    """Register resources and tools for Datadog Hosts API"""
    
    @self.mcp.resource("hosts://list")
    def list_hosts(ctx: Context) -> str:
        """List all hosts"""
        hosts_api = ctx.request_context.lifespan_context["hosts_api"]
        response = hosts_api.list_hosts()
        return response.to_json()
    
    @self.mcp.tool()
    def mute_host(ctx: Context, host_name: str, message: str = None, end: int = None) -> str:
        """Mute a host"""
        hosts_api = ctx.request_context.lifespan_context["hosts_api"]
        
        try:
            response = hosts_api.mute_host(
                host_name=host_name,
                body={
                    "message": message,
                    "end": end
                }
            )
            return response.to_json()
        except Exception as e:
            return f"Error muting host: {str(e)}"
def register_users_resources_and_tools(self):
    """Register resources and tools for Datadog Users API"""
    
    @self.mcp.resource("users://list")
    def list_users(ctx: Context) -> str:
        """List all users"""
        users_api = ctx.request_context.lifespan_context["users_api"]
        response = users_api.list_users()
        return response.to_json()
    
    @self.mcp.tool()
    def create_user(ctx: Context, user_handle: str, access_role: str = "st") -> str:
        """Create a user"""
        users_api = ctx.request_context.lifespan_context["users_api"]
        
        try:
            response = users_api.create_user(
                body={
                    "handle": user_handle,
                    "access_role": access_role
                }
            )
            return response.to_json()
        except Exception as e:
            return f"Error creating user: {str(e)}"

def register_all_resources_and_tools(self):
    """Register all resources and tools for all Datadog APIs"""
    self.register_metrics_resources_and_tools()
    self.register_events_resources_and_tools()
    self.register_logs_resources_and_tools()
    self.register_dashboards_resources_and_tools()
    self.register_monitors_resources_and_tools()
    self.register_hosts_resources_and_tools()
    self.register_tags_resources_and_tools()
    self.register_users_resources_and_tools()

def run(self, transport="stdio"):
    """Run the MCP server"""
    self.mcp.run(transport=transport)

# Main function to run the server
def main():
    # Create server
    server = DatadogMCPServer()
    
    # Register all resources and tools
    server.register_all_resources_and_tools()
    
    # Run the server
    server.run()

if __name__ == "__main__":
    main()
