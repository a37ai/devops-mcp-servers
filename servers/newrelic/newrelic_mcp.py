# newrelic_mcp_server.py
from typing import Dict, List, Optional, Any, Union
import os
import httpx
import json
from datetime import datetime, timedelta
from typing import List, Dict, Optional, Any, Union
from mcp.server.fastmcp import FastMCP, Context
from dotenv import load_dotenv

load_dotenv()
from pydantic import BaseModel, Field, ValidationError


# Base Models
class ErrorResponse(BaseModel):
    """Model for error responses"""
    error: str
    message: Optional[str] = None


# Application Models
class ApplicationSummary(BaseModel):
    """Summary metrics for an application"""
    throughput: Optional[float] = None
    response_time: Optional[float] = None
    error_rate: Optional[float] = None
    apdex_score: Optional[float] = None


class Application(BaseModel):
    """Model for application data"""
    id: int
    name: str
    language: Optional[str] = None
    health_status: Optional[str] = None
    application_summary: Optional[ApplicationSummary] = None
    settings: Optional[Dict[str, Any]] = None


class ApplicationList(BaseModel):
    """Response model for application listing"""
    applications: List[Application]


class ApplicationRequest(BaseModel):
    """Model for application update/create requests"""
    name: str
    settings: Optional[Dict[str, Any]] = None


# Alert Models
class AlertPolicy(BaseModel):
    """Model for alert policy data"""
    id: int
    incident_preference: str
    name: str
    created_at: Optional[int] = None
    updated_at: Optional[int] = None


class AlertPolicyList(BaseModel):
    """Response model for alert policy listing"""
    policies: List[AlertPolicy]


class AlertPolicyRequest(BaseModel):
    """Model for creating/updating alert policies"""
    policy: Dict[str, Any]


class AlertCondition(BaseModel):
    """Model for alert condition data"""
    id: int
    type: str
    name: str
    enabled: bool
    entities: List[int]
    metric: Optional[str] = None
    terms: Optional[List[Dict[str, Any]]] = None
    violation_close_timer: Optional[int] = None
    user_defined: Optional[Dict[str, Any]] = None


class AlertConditionList(BaseModel):
    """Response model for alert condition listing"""
    conditions: List[AlertCondition]


class AlertConditionRequest(BaseModel):
    """Model for creating/updating alert conditions"""
    condition: Dict[str, Any]


class NrqlAlertCondition(BaseModel):
    """Model for NRQL alert condition data"""
    id: int
    name: str
    enabled: bool
    value_function: Optional[str] = None
    terms: List[Dict[str, Any]]
    nrql: Dict[str, Any]


class NrqlAlertConditionList(BaseModel):
    """Response model for NRQL alert condition listing"""
    nrql_conditions: List[NrqlAlertCondition]


class NrqlAlertConditionRequest(BaseModel):
    """Model for creating/updating NRQL alert conditions"""
    nrql_condition: Dict[str, Any]


# Synthetic Monitoring Models
class Monitor(BaseModel):
    """Model for synthetic monitor data"""
    id: str
    name: str
    type: str
    frequency: int
    uri: Optional[str] = None
    status: str
    locations: List[str]
    slaThreshold: Optional[float] = None


class MonitorList(BaseModel):
    """Response model for monitor listing"""
    monitors: List[Monitor]


class MonitorRequest(BaseModel):
    """Model for creating/updating monitors"""
    name: str
    type: str
    frequency: int
    uri: Optional[str] = None
    locations: List[str]
    status: str = "ENABLED"
    slaThreshold: Optional[float] = None


class MonitorUpdate(BaseModel):
    """Model for updating monitor data"""
    name: Optional[str] = None
    frequency: Optional[int] = None
    status: Optional[str] = None
    slaThreshold: Optional[float] = None
    locations: Optional[List[str]] = None


# Infrastructure Models
class InfrastructureHost(BaseModel):
    """Model for infrastructure host data"""
    id: str
    name: str
    type: Optional[str] = None
    os: Optional[str] = None
    cpuCores: Optional[int] = None
    cpuMhz: Optional[float] = None
    memoryGB: Optional[float] = None
    lastReportedAt: Optional[int] = None


class InfrastructureHostList(BaseModel):
    """Response model for infrastructure host listing"""
    hosts: List[InfrastructureHost]


# Workload Models
class Workload(BaseModel):
    """Model for workload data"""
    guid: str
    name: str
    entitySearchQuery: str
    entityCount: Optional[int] = None
    entityGuids: Optional[List[str]] = None


class WorkloadRequest(BaseModel):
    """Model for creating/updating workloads"""
    name: str
    entitySearchQuery: str
    entityGuids: Optional[List[str]] = None


# Dashboard Models
class Dashboard(BaseModel):
    """Model for dashboard data"""
    id: str
    title: str
    permissions: str
    created_at: Optional[str] = None
    updated_at: Optional[str] = None


class DashboardList(BaseModel):
    """Response model for dashboard listing"""
    dashboards: List[Dashboard]


# Browser Application Models
class BrowserApplication(BaseModel):
    """Model for browser application data"""
    id: int
    name: str
    browser_monitoring_key: Optional[str] = None
    js_agent_version: Optional[str] = None
    loader_type: Optional[str] = None


class BrowserApplicationList(BaseModel):
    """Response model for browser application listing"""
    browser_applications: List[BrowserApplication]


class BrowserApplicationRequest(BaseModel):
    """Model for creating/updating browser applications"""
    name: str


# Mobile Application Models
class MobileApplication(BaseModel):
    """Model for mobile application data"""
    id: int
    name: str
    platform: Optional[str] = None
    version: Optional[str] = None


class MobileApplicationList(BaseModel):
    """Response model for mobile application listing"""
    applications: List[MobileApplication]


# Deployment Models
class Deployment(BaseModel):
    """Model for deployment data"""
    id: int
    revision: str
    changelog: Optional[str] = None
    description: Optional[str] = None
    user: Optional[str] = None
    timestamp: Optional[str] = None


class DeploymentList(BaseModel):
    """Response model for deployment listing"""
    deployments: List[Deployment]


class DeploymentRequest(BaseModel):
    """Model for creating deployments"""
    revision: str
    changelog: Optional[str] = None
    description: Optional[str] = None
    user: Optional[str] = None


# Key Transaction Models
class KeyTransaction(BaseModel):
    """Model for key transaction data"""
    id: int
    name: str
    application_id: int
    transaction_name: str
    health_status: Optional[str] = None
    response_time: Optional[float] = None
    apdex_score: Optional[float] = None
    throughput: Optional[float] = None


class KeyTransactionList(BaseModel):
    """Response model for key transaction listing"""
    key_transactions: List[KeyTransaction]


# Service Level Models
class ServiceLevelIndicator(BaseModel):
    """Model for service level indicator data"""
    guid: str
    name: str
    description: Optional[str] = None
    entityGuid: str
    entityCount: Optional[int] = None


class ServiceLevelIndicatorList(BaseModel):
    """Response model for service level indicator listing"""
    indicators: List[ServiceLevelIndicator]


# Error Tracking Models
class ErrorAttribute(BaseModel):
    """Model for error attribute data"""
    key: str
    value: Any


class ErrorLocation(BaseModel):
    """Model for error location data"""
    file: Optional[str] = None
    lineNumber: Optional[int] = None
    columnNumber: Optional[int] = None


class ErrorStackTrace(BaseModel):
    """Model for error stack trace data"""
    formatted: Optional[str] = None
    rawTrace: Optional[str] = None


class Error(BaseModel):
    """Model for error data"""
    id: str
    message: str
    entityGuid: Optional[str] = None
    occurrences: Optional[int] = None
    occurrenceLocation: Optional[ErrorLocation] = None
    attributes: Optional[List[ErrorAttribute]] = None
    stackTrace: Optional[ErrorStackTrace] = None
    firstSeen: Optional[str] = None
    lastSeen: Optional[str] = None


class ErrorList(BaseModel):
    """Response model for error listing"""
    results: List[Error]


# Initialize FastMCP server
mcp = FastMCP("newrelic-api")

# Get API key from environment variable
API_KEY = os.environ.get("NEW_RELIC_API_KEY")
if not API_KEY:
    raise ValueError("NEW_RELIC_API_KEY environment variable must be set")

BASE_URL = "https://api.newrelic.com/v2"
HEADERS = {
    "API-Key": API_KEY,
    "Content-Type": "application/json"
}

# Helper function for making API requests
async def make_request(
    method: str, 
    endpoint: str, 
    params: Optional[Dict] = None, 
    data: Optional[Dict] = None
) -> Dict:
    """Make a request to the New Relic API."""
    url = f"{BASE_URL}{endpoint}"
    
    try:
        async with httpx.AsyncClient() as client:
            if method.lower() == "get":
                response = await client.get(url, headers=HEADERS, params=params)
            elif method.lower() == "post":
                response = await client.post(url, headers=HEADERS, params=params, json=data)
            elif method.lower() == "put":
                response = await client.put(url, headers=HEADERS, params=params, json=data)
            elif method.lower() == "delete":
                response = await client.delete(url, headers=HEADERS, params=params)
            else:
                raise ValueError(f"Unsupported method: {method}")
            
            response.raise_for_status()
            return response.json()
    except httpx.HTTPError as e:
        return {"error": f"HTTP Error: {str(e)}"}
    except ValidationError as e:
        return {"error": f"Validation Error: {str(e)}"}
    except Exception as e:
        return {"error": f"Error: {str(e)}"}

# Applications Tools
@mcp.tool()
async def list_applications(
    filter_name: Optional[str] = None,
    filter_host: Optional[str] = None,
    filter_language: Optional[str] = None,
    page: Optional[int] = None
) -> str:
    """
    List applications associated with your New Relic account.
    
    Args:
        filter_name: Filter by application name
        filter_host: Filter by application host
        filter_language: Filter by application language
        page: Pagination index
    """
    params = {}
    if filter_name:
        params["filter[name]"] = filter_name
    if filter_host:
        params["filter[host]"] = filter_host
    if filter_language:
        params["filter[language]"] = filter_language
    if page:
        params["page"] = page
    
    response = await make_request("get", "/applications.json", params)
    
    try:
        # Validate response data with Pydantic model
        app_list = ApplicationList(**response)
        return json.dumps(app_list.dict(), indent=2)
    except ValidationError as e:
        error_resp = ErrorResponse(error="Validation error", message=str(e))
        return json.dumps(error_resp.dict(), indent=2)

@mcp.tool()
async def get_application(app_id: int) -> str:
    """
    Get details for a specific application.
    
    Args:
        app_id: Application ID
    """
    response = await make_request("get", f"/applications/{app_id}.json")
    
    try:
        # Validate response data with Pydantic model
        if "application" in response:
            app = Application(**response["application"])
            return json.dumps(app.dict(), indent=2)
        else:
            return json.dumps(response, indent=2)
    except ValidationError as e:
        error_resp = ErrorResponse(error="Validation error", message=str(e))
        return json.dumps(error_resp.dict(), indent=2)

@mcp.tool()
async def update_application(
    app_id: int,
    name: Optional[str] = None,
    app_apdex_threshold: Optional[float] = None,
    end_user_apdex_threshold: Optional[float] = None,
    enable_real_user_monitoring: Optional[bool] = None
) -> str:
    """
    Update an application's settings.
    
    Args:
        app_id: Application ID
        name: New application name
        app_apdex_threshold: New application Apdex threshold
        end_user_apdex_threshold: New end user Apdex threshold
        enable_real_user_monitoring: Enable or disable real user monitoring
    """
    try:
        settings = {}
        if app_apdex_threshold is not None:
            settings["app_apdex_threshold"] = app_apdex_threshold
        if end_user_apdex_threshold is not None:
            settings["end_user_apdex_threshold"] = end_user_apdex_threshold
        if enable_real_user_monitoring is not None:
            settings["enable_real_user_monitoring"] = enable_real_user_monitoring
        
        # Validate request data with Pydantic model
        request_data = ApplicationRequest(
            name=name or "",
            settings=settings
        )
        
        data = {"application": {}}
        if name:
            data["application"]["name"] = name
        if settings:
            data["application"]["settings"] = settings
        
        response = await make_request("put", f"/applications/{app_id}.json", data=data)
        
        # Validate response
        if "application" in response:
            app = Application(**response["application"])
            return json.dumps(app.dict(), indent=2)
        else:
            return json.dumps(response, indent=2)
    except ValidationError as e:
        error_resp = ErrorResponse(error="Validation error", message=str(e))
        return json.dumps(error_resp.dict(), indent=2)

@mcp.tool()
async def delete_application(app_id: int) -> str:
    """
    Delete an application.
    
    Args:
        app_id: Application ID
    """
    try:
        response = await make_request("delete", f"/applications/{app_id}.json")
        return json.dumps(response, indent=2)
    except ValidationError as e:
        error_resp = ErrorResponse(error="Validation error", message=str(e))
        return json.dumps(error_resp.dict(), indent=2)

@mcp.tool()
async def get_application_metrics(app_id: int, name_filter: Optional[str] = None, page: Optional[int] = None) -> str:
    """
    Get available metrics for an application.
    
    Args:
        app_id: Application ID
        name_filter: Filter metrics by name
        page: Pagination index
    """
    params = {}
    if name_filter:
        params["name"] = name_filter
    if page:
        params["page"] = page
    
    response = await make_request("get", f"/applications/{app_id}/metrics.json", params)
    return json.dumps(response, indent=2)

@mcp.tool()
async def get_application_metric_data(
    app_id: int,
    names: List[str],
    values: Optional[List[str]] = None,
    from_date: Optional[str] = None,
    to_date: Optional[str] = None,
    period: Optional[int] = None,
    summarize: bool = False
) -> str:
    """
    Get metric data for an application.
    
    Args:
        app_id: Application ID
        names: List of metric names to retrieve
        values: List of specific metric values to retrieve
        from_date: Start time in ISO 8601 format (e.g. 2023-03-01T00:00:00+00:00)
        to_date: End time in ISO 8601 format
        period: Period of timeslices in seconds
        summarize: Whether to summarize the data
    """
    params = {"names[]": names}
    if values:
        params["values[]"] = values
    if from_date:
        params["from"] = from_date
    if to_date:
        params["to"] = to_date
    if period:
        params["period"] = period
    if summarize:
        params["summarize"] = "true"
    
    response = await make_request("get", f"/applications/{app_id}/metrics/data.json", params)
    return json.dumps(response, indent=2)

# Deployments Tools
@mcp.tool()
async def list_deployments(app_id: int, page: Optional[int] = None) -> str:
    """
    List deployments for an application.
    
    Args:
        app_id: Application ID
        page: Pagination index
    """
    params = {}
    if page:
        params["page"] = page
    
    response = await make_request("get", f"/applications/{app_id}/deployments.json", params)
    return json.dumps(response, indent=2)

@mcp.tool()
async def create_deployment(
    app_id: int,
    revision: str,
    changelog: Optional[str] = None,
    description: Optional[str] = None,
    user: Optional[str] = None
) -> str:
    """
    Create a deployment for an application.
    
    Args:
        app_id: Application ID
        revision: Deployment revision (e.g. git SHA)
        changelog: Deployment changelog
        description: Deployment description
        user: User who performed the deployment
    """
    data = {
        "deployment": {
            "revision": revision
        }
    }
    
    if changelog:
        data["deployment"]["changelog"] = changelog
    if description:
        data["deployment"]["description"] = description
    if user:
        data["deployment"]["user"] = user
    
    response = await make_request("post", f"/applications/{app_id}/deployments.json", data=data)
    return json.dumps(response, indent=2)

@mcp.tool()
async def delete_deployment(app_id: int, deployment_id: int) -> str:
    """
    Delete a deployment.
    
    Args:
        app_id: Application ID
        deployment_id: Deployment ID
    """
    response = await make_request("delete", f"/applications/{app_id}/deployments/{deployment_id}.json")
    return json.dumps(response, indent=2)

# Application Hosts Tools
@mcp.tool()
async def list_application_hosts(
    app_id: int,
    filter_hostname: Optional[str] = None,
    page: Optional[int] = None
) -> str:
    """
    List hosts for an application.
    
    Args:
        app_id: Application ID
        filter_hostname: Filter by hostname
        page: Pagination index
    """
    params = {}
    if filter_hostname:
        params["filter[hostname]"] = filter_hostname
    if page:
        params["page"] = page
    
    response = await make_request("get", f"/applications/{app_id}/hosts.json", params)
    return json.dumps(response, indent=2)

@mcp.tool()
async def get_application_host(app_id: int, host_id: int) -> str:
    """
    Get details for a specific application host.
    
    Args:
        app_id: Application ID
        host_id: Application host ID
    """
    response = await make_request("get", f"/applications/{app_id}/hosts/{host_id}.json")
    return json.dumps(response, indent=2)

# Application Instances Tools
@mcp.tool()
async def list_application_instances(
    app_id: int,
    filter_hostname: Optional[str] = None,
    page: Optional[int] = None
) -> str:
    """
    List instances for an application.
    
    Args:
        app_id: Application ID
        filter_hostname: Filter by hostname
        page: Pagination index
    """
    params = {}
    if filter_hostname:
        params["filter[hostname]"] = filter_hostname
    if page:
        params["page"] = page
    
    response = await make_request("get", f"/applications/{app_id}/instances.json", params)
    return json.dumps(response, indent=2)

@mcp.tool()
async def get_application_instance(app_id: int, instance_id: int) -> str:
    """
    Get details for a specific application instance.
    
    Args:
        app_id: Application ID
        instance_id: Application instance ID
    """
    response = await make_request("get", f"/applications/{app_id}/instances/{instance_id}.json")
    return json.dumps(response, indent=2)

# Key Transactions Tools
@mcp.tool()
async def list_key_transactions(
    filter_name: Optional[str] = None,
    page: Optional[int] = None
) -> str:
    """
    List key transactions.
    
    Args:
        filter_name: Filter by name
        page: Pagination index
    """
    params = {}
    if filter_name:
        params["filter[name]"] = filter_name
    if page:
        params["page"] = page
    
    response = await make_request("get", "/key_transactions.json", params)
    return json.dumps(response, indent=2)

@mcp.tool()
async def get_key_transaction(transaction_id: int) -> str:
    """
    Get details for a specific key transaction.
    
    Args:
        transaction_id: Key transaction ID
    """
    response = await make_request("get", f"/key_transactions/{transaction_id}.json")
    return json.dumps(response, indent=2)

# Mobile Applications Tools
@mcp.tool()
async def list_mobile_applications() -> str:
    """
    List mobile applications.
    """
    response = await make_request("get", "/mobile_applications.json")
    return json.dumps(response, indent=2)

@mcp.tool()
async def get_mobile_application(app_id: int) -> str:
    """
    Get details for a specific mobile application.
    
    Args:
        app_id: Mobile application ID
    """
    response = await make_request("get", f"/mobile_applications/{app_id}.json")
    return json.dumps(response, indent=2)

# Alerts Policies Tools
@mcp.tool()
async def list_alert_policies(
    filter_name: Optional[str] = None,
    page: Optional[int] = None
) -> str:
    """
    List alert policies.
    
    Args:
        filter_name: Filter by name (exact match)
        page: Pagination index
    """
    params = {}
    if filter_name:
        params["filter[name]"] = filter_name
    if page:
        params["page"] = page
    
    response = await make_request("get", "/alerts_policies.json", params)
    
    try:
        # Validate response data with Pydantic model
        policy_list = AlertPolicyList(**response)
        return json.dumps(policy_list.dict(), indent=2)
    except ValidationError as e:
        error_resp = ErrorResponse(error="Validation error", message=str(e))
        return json.dumps(error_resp.dict(), indent=2)

@mcp.tool()
async def create_alert_policy(name: str, incident_preference: str) -> str:
    """
    Create an alert policy.
    
    Args:
        name: Policy name
        incident_preference: Incident rollup preference (PER_POLICY, PER_CONDITION, or PER_CONDITION_AND_TARGET)
    """
    try:
        # Validate request data with Pydantic model
        policy_request = AlertPolicyRequest(
            policy={
                "name": name,
                "incident_preference": incident_preference
            }
        )
        
        data = {
            "policy": {
                "name": name,
                "incident_preference": incident_preference
            }
        }
        
        response = await make_request("post", "/alerts_policies.json", data=data)
        
        # Validate response
        if "policy" in response:
            policy = AlertPolicy(**response["policy"])
            return json.dumps(policy.dict(), indent=2)
        else:
            return json.dumps(response, indent=2)
    except ValidationError as e:
        error_resp = ErrorResponse(error="Validation error", message=str(e))
        return json.dumps(error_resp.dict(), indent=2)

@mcp.tool()
async def update_alert_policy(
    policy_id: int,
    name: Optional[str] = None,
    incident_preference: Optional[str] = None
) -> str:
    """
    Update an alert policy.
    
    Args:
        policy_id: Policy ID
        name: New policy name
        incident_preference: New incident rollup preference
    """
    try:
        policy_data = {}
        if name:
            policy_data["name"] = name
        if incident_preference:
            policy_data["incident_preference"] = incident_preference
        
        # Validate request data with Pydantic model
        policy_request = AlertPolicyRequest(policy=policy_data)
        
        data = {"policy": {}}
        if name:
            data["policy"]["name"] = name
        if incident_preference:
            data["policy"]["incident_preference"] = incident_preference
        
        response = await make_request("put", f"/alerts_policies/{policy_id}.json", data=data)
        
        # Validate response
        if "policy" in response:
            policy = AlertPolicy(**response["policy"])
            return json.dumps(policy.dict(), indent=2)
        else:
            return json.dumps(response, indent=2)
    except ValidationError as e:
        error_resp = ErrorResponse(error="Validation error", message=str(e))
        return json.dumps(error_resp.dict(), indent=2)

@mcp.tool()
async def delete_alert_policy(policy_id: int) -> str:
    """
    Delete an alert policy.
    
    Args:
        policy_id: Policy ID
    """
    try:
        response = await make_request("delete", f"/alerts_policies/{policy_id}.json")
        return json.dumps(response, indent=2)
    except ValidationError as e:
        error_resp = ErrorResponse(error="Validation error", message=str(e))
        return json.dumps(error_resp.dict(), indent=2)

# Alerts Conditions Tools
@mcp.tool()
async def list_alert_conditions(policy_id: int, page: Optional[int] = None) -> str:
    """
    List alert conditions for a policy.
    
    Args:
        policy_id: Policy ID
        page: Pagination index
    """
    params = {
        "policy_id": policy_id
    }
    if page:
        params["page"] = page
    
    response = await make_request("get", "/alerts_conditions.json", params)
    return json.dumps(response, indent=2)

@mcp.tool()
async def create_alert_condition(
    policy_id: int,
    name: str,
    type: str,
    entities: List[int],
    metric: str,
    terms: List[Dict],
    condition_scope: Optional[str] = None,
    violation_close_timer: Optional[int] = None,
    user_defined: Optional[Dict] = None
) -> str:
    """
    Create an alert condition for a policy.
    
    Args:
        policy_id: Policy ID
        name: Condition name
        type: Condition type (apm_app_metric, apm_kt_metric, servers_metric, browser_metric, mobile_metric)
        entities: List of entity IDs to monitor
        metric: Metric to monitor
        terms: Alert terms (list of dicts with duration, operator, priority, threshold, time_function)
        condition_scope: Condition scope (instance or application)
        violation_close_timer: Hours after which violations will close (1, 2, 4, 8, 12, 24)
        user_defined: User-defined metrics configuration (dict with metric and value_function)
    """
    data = {
        "condition": {
            "name": name,
            "type": type,
            "entities": entities,
            "metric": metric,
            "terms": terms
        }
    }
    
    if condition_scope:
        data["condition"]["condition_scope"] = condition_scope
    if violation_close_timer:
        data["condition"]["violation_close_timer"] = violation_close_timer
    if user_defined:
        data["condition"]["user_defined"] = user_defined
    
    response = await make_request("post", f"/alerts_conditions/policies/{policy_id}.json", data=data)
    return json.dumps(response, indent=2)

@mcp.tool()
async def update_alert_condition(
    condition_id: int,
    name: Optional[str] = None,
    entities: Optional[List[int]] = None,
    metric: Optional[str] = None,
    terms: Optional[List[Dict]] = None,
    condition_scope: Optional[str] = None,
    violation_close_timer: Optional[int] = None,
    user_defined: Optional[Dict] = None
) -> str:
    """
    Update an alert condition.
    
    Args:
        condition_id: Condition ID
        name: New condition name
        entities: New list of entity IDs to monitor
        metric: New metric to monitor
        terms: New alert terms
        condition_scope: New condition scope
        violation_close_timer: New violation close timer
        user_defined: New user-defined metrics configuration
    """
    data = {"condition": {}}
    if name:
        data["condition"]["name"] = name
    if entities:
        data["condition"]["entities"] = entities
    if metric:
        data["condition"]["metric"] = metric
    if terms:
        data["condition"]["terms"] = terms
    if condition_scope:
        data["condition"]["condition_scope"] = condition_scope
    if violation_close_timer:
        data["condition"]["violation_close_timer"] = violation_close_timer
    if user_defined:
        data["condition"]["user_defined"] = user_defined
    
    response = await make_request("put", f"/alerts_conditions/{condition_id}.json", data=data)
    return json.dumps(response, indent=2)

@mcp.tool()
async def delete_alert_condition(condition_id: int) -> str:
    """
    Delete an alert condition.
    
    Args:
        condition_id: Condition ID
    """
    response = await make_request("delete", f"/alerts_conditions/{condition_id}.json")
    return json.dumps(response, indent=2)

# NRQL Alert Conditions Tools
@mcp.tool()
async def list_nrql_alert_conditions(policy_id: int, page: Optional[int] = None) -> str:
    """
    List NRQL alert conditions for a policy.
    
    Args:
        policy_id: Policy ID
        page: Pagination index
    """
    params = {
        "policy_id": policy_id
    }
    if page:
        params["page"] = page
    
    response = await make_request("get", "/alerts_nrql_conditions.json", params)
    return json.dumps(response, indent=2)

@mcp.tool()
async def create_nrql_alert_condition(
    policy_id: int,
    name: str,
    nrql: Dict[str, str],
    terms: List[Dict],
    value_function: str,
    enabled: bool = True,
    runbook_url: Optional[str] = None,
    expected_groups: Optional[int] = None,
    ignore_overlap: Optional[bool] = None
) -> str:
    """
    Create a NRQL alert condition for a policy.
    
    Args:
        policy_id: Policy ID
        name: Condition name
        nrql: NRQL query (dict with query and since_value)
        terms: Alert terms
        value_function: How to use the NRQL data (single_value, sum, etc.)
        enabled: Whether the condition is enabled
        runbook_url: URL to the runbook
        expected_groups: Number of expected groups
        ignore_overlap: Whether to ignore overlapping time windows
    """
    data = {
        "nrql_condition": {
            "name": name,
            "nrql": nrql,
            "terms": terms,
            "value_function": value_function,
            "enabled": enabled
        }
    }
    
    if runbook_url:
        data["nrql_condition"]["runbook_url"] = runbook_url
    if expected_groups is not None:
        data["nrql_condition"]["expected_groups"] = expected_groups
    if ignore_overlap is not None:
        data["nrql_condition"]["ignore_overlap"] = ignore_overlap
    
    response = await make_request("post", f"/alerts_nrql_conditions/policies/{policy_id}.json", data=data)
    return json.dumps(response, indent=2)

@mcp.tool()
async def update_nrql_alert_condition(
    condition_id: int,
    name: Optional[str] = None,
    nrql: Optional[Dict[str, str]] = None,
    terms: Optional[List[Dict]] = None,
    value_function: Optional[str] = None,
    enabled: Optional[bool] = None,
    runbook_url: Optional[str] = None,
    expected_groups: Optional[int] = None,
    ignore_overlap: Optional[bool] = None
) -> str:
    """
    Update a NRQL alert condition.
    
    Args:
        condition_id: Condition ID
        name: New condition name
        nrql: New NRQL query
        terms: New alert terms
        value_function: New value function
        enabled: New enabled status
        runbook_url: New runbook URL
        expected_groups: New number of expected groups
        ignore_overlap: New ignore overlap setting
    """
    data = {"nrql_condition": {}}
    if name:
        data["nrql_condition"]["name"] = name
    if nrql:
        data["nrql_condition"]["nrql"] = nrql
    if terms:
        data["nrql_condition"]["terms"] = terms
    if value_function:
        data["nrql_condition"]["value_function"] = value_function
    if enabled is not None:
        data["nrql_condition"]["enabled"] = enabled
    if runbook_url:
        data["nrql_condition"]["runbook_url"] = runbook_url
    if expected_groups is not None:
        data["nrql_condition"]["expected_groups"] = expected_groups
    if ignore_overlap is not None:
        data["nrql_condition"]["ignore_overlap"] = ignore_overlap
    
    response = await make_request("put", f"/alerts_nrql_conditions/{condition_id}.json", data=data)
    return json.dumps(response, indent=2)

@mcp.tool()
async def delete_nrql_alert_condition(condition_id: int) -> str:
    """
    Delete a NRQL alert condition.
    
    Args:
        condition_id: Condition ID
    """
    response = await make_request("delete", f"/alerts_nrql_conditions/{condition_id}.json")
    return json.dumps(response, indent=2)

# Alerts Incidents Tools
@mcp.tool()
async def list_alerts_incidents(
    page: Optional[int] = None,
    only_open: Optional[bool] = None
) -> str:
    """
    List alert incidents.
    
    Args:
        page: Pagination index
        only_open: Filter to only open incidents
    """
    params = {}
    if page:
        params["page"] = page
    if only_open is not None:
        params["only_open"] = "true" if only_open else "false"
    
    response = await make_request("get", "/alerts_incidents.json", params)
    return json.dumps(response, indent=2)

# Alerts Violations Tools
@mcp.tool()
async def list_alerts_violations(
    page: Optional[int] = None,
    start_date: Optional[str] = None,
    end_date: Optional[str] = None,
    only_open: Optional[bool] = None
) -> str:
    """
    List alert violations.
    
    Args:
        page: Pagination index
        start_date: Retrieve violations created after this time (ISO 8601)
        end_date: Retrieve violations created before this time (ISO 8601)
        only_open: Filter by open violations
    """
    params = {}
    if page:
        params["page"] = page
    if start_date:
        params["start_date"] = start_date
    if end_date:
        params["end_date"] = end_date
    if only_open is not None:
        params["only_open"] = "true" if only_open else "false"
    
    response = await make_request("get", "/alerts_violations.json", params)
    return json.dumps(response, indent=2)

@mcp.resource("nr://applications")
async def get_applications_resource() -> str:
    """Get a list of New Relic applications as a resource."""
    params = {"exclude_links": "true"}
    response = await make_request("get", "/applications.json", params)
    applications = response.get("applications", [])
    
    result = "# New Relic Applications\n\n"
    for app in applications:
        result += f"## {app.get('name')}\n"
        result += f"- ID: {app.get('id')}\n"
        result += f"- Language: {app.get('language')}\n"
        result += f"- Health: {app.get('health_status')}\n"
        result += f"- Reporting: {'Yes' if app.get('reporting') else 'No'}\n"
        if app.get('application_summary'):
            summary = app.get('application_summary')
            result += "- Summary:\n"
            result += f"  - Apdex: {summary.get('apdex_score')}\n"
            result += f"  - Response Time: {summary.get('response_time')}ms\n"
            result += f"  - Throughput: {summary.get('throughput')} rpm\n"
            result += f"  - Error Rate: {summary.get('error_rate')}%\n"
        result += "\n"
    
    return result

@mcp.resource("nr://alerts/policies")
async def get_alert_policies_resource() -> str:
    """Get a list of New Relic alert policies as a resource."""
    response = await make_request("get", "/alerts_policies.json")
    policies = response.get("policies", [])
    
    result = "# New Relic Alert Policies\n\n"
    for policy in policies:
        result += f"## {policy.get('name')}\n"
        result += f"- ID: {policy.get('id')}\n"
        result += f"- Incident Preference: {policy.get('incident_preference')}\n"
        created_at = datetime.fromtimestamp(policy.get('created_at', 0)).strftime('%Y-%m-%d %H:%M:%S')
        updated_at = datetime.fromtimestamp(policy.get('updated_at', 0)).strftime('%Y-%m-%d %H:%M:%S')
        result += f"- Created: {created_at}\n"
        result += f"- Updated: {updated_at}\n\n"
    
    return result

@mcp.resource("nr://application/{app_id}")
async def get_application_resource(app_id: int) -> str:
    """
    Get detailed information about a specific New Relic application.
    
    Args:
        app_id: Application ID
    """
    response = await make_request("get", f"/applications/{app_id}.json")
    app = response.get("application", {})
    
    result = f"# New Relic Application: {app.get('name')}\n\n"
    result += f"- ID: {app.get('id')}\n"
    result += f"- Language: {app.get('language')}\n"
    result += f"- Health: {app.get('health_status')}\n"
    result += f"- Last Reported: {app.get('last_reported_at')}\n"
    result += f"- Reporting: {'Yes' if app.get('reporting') else 'No'}\n\n"
    
    if app.get('application_summary'):
        summary = app.get('application_summary')
        result += "## Application Summary\n"
        result += f"- Apdex Score: {summary.get('apdex_score')}\n"
        result += f"- Apdex Target: {summary.get('apdex_target')}s\n"
        result += f"- Response Time: {summary.get('response_time')}ms\n"
        result += f"- Throughput: {summary.get('throughput')} rpm\n"
        result += f"- Error Rate: {summary.get('error_rate')}%\n"
        result += f"- Instance Count: {summary.get('instance_count')}\n"
        result += f"- Host Count: {summary.get('host_count')}\n\n"
    
    if app.get('end_user_summary'):
        summary = app.get('end_user_summary')
        result += "## End User Summary\n"
        result += f"- Apdex Score: {summary.get('apdex_score')}\n"
        result += f"- Apdex Target: {summary.get('apdex_target')}s\n"
        result += f"- Response Time: {summary.get('response_time')}ms\n"
        result += f"- Throughput: {summary.get('throughput')} rpm\n\n"
    
    if app.get('settings'):
        settings = app.get('settings')
        result += "## Settings\n"
        result += f"- App Apdex Threshold: {settings.get('app_apdex_threshold')}s\n"
        result += f"- End User Apdex Threshold: {settings.get('end_user_apdex_threshold')}s\n"
        result += f"- Real User Monitoring: {'Enabled' if settings.get('enable_real_user_monitoring') else 'Disabled'}\n"
        result += f"- Server-Side Config: {'Enabled' if settings.get('use_server_side_config') else 'Disabled'}\n\n"
    
    return result

@mcp.resource("nr://mobile_applications")
async def get_mobile_applications_resource() -> str:
    """Get a list of New Relic mobile applications as a resource."""
    response = await make_request("get", "/mobile_applications.json")
    apps = response.get("applications", [])
    
    result = "# New Relic Mobile Applications\n\n"
    for app in apps:
        result += f"## {app.get('name')}\n"
        result += f"- ID: {app.get('id')}\n"
        result += f"- Health: {app.get('health_status')}\n"
        result += f"- Reporting: {'Yes' if app.get('reporting') else 'No'}\n"
        
        if app.get('mobile_summary'):
            summary = app.get('mobile_summary')
            result += "- Summary:\n"
            result += f"  - Active Users: {summary.get('active_users')}\n"
            result += f"  - Launch Count: {summary.get('launch_count')}\n"
            result += f"  - Response Time: {summary.get('response_time')}ms\n"
            result += f"  - Throughput: {summary.get('throughput')} rpm\n"
            result += f"  - Error Rate: {summary.get('remote_error_rate')}%\n"
        
        if app.get('crash_summary'):
            crash = app.get('crash_summary')
            result += "- Crash Summary:\n"
            result += f"  - Crash Count: {crash.get('crash_count')}\n"
            result += f"  - Crash Rate: {crash.get('crash_rate')}%\n"
            result += f"  - Unresolved Crashes: {crash.get('unresolved_crash_count')}\n"
        
        result += "\n"
    
    return result

@mcp.resource("nr://mobile_application/{app_id}")
async def get_mobile_application_resource(app_id: int) -> str:
    """
    Get detailed information about a specific New Relic mobile application.
    
    Args:
        app_id: Mobile Application ID
    """
    response = await make_request("get", f"/mobile_applications/{app_id}.json")
    app = response.get("application", {})
    
    result = f"# New Relic Mobile Application: {app.get('name')}\n\n"
    result += f"- ID: {app.get('id')}\n"
    result += f"- Health: {app.get('health_status')}\n"
    result += f"- Reporting: {'Yes' if app.get('reporting') else 'No'}\n\n"
    
    if app.get('mobile_summary'):
        summary = app.get('mobile_summary')
        result += "## Mobile Summary\n"
        result += f"- Active Users: {summary.get('active_users')}\n"
        result += f"- Launch Count: {summary.get('launch_count')}\n"
        result += f"- Response Time: {summary.get('response_time')}ms\n"
        result += f"- Throughput: {summary.get('throughput')} rpm\n"
        result += f"- Remote Error Rate: {summary.get('remote_error_rate')}%\n"
        result += f"- Calls Per Session: {summary.get('calls_per_session')}\n"
        result += f"- Interaction Time: {summary.get('interaction_time')}ms\n"
        result += f"- Failed Call Rate: {summary.get('failed_call_rate')}%\n\n"
    
    if app.get('crash_summary'):
        crash = app.get('crash_summary')
        result += "## Crash Summary\n"
        result += f"- Crash Count: {crash.get('crash_count')}\n"
        result += f"- Crash Rate: {crash.get('crash_rate')}%\n"
        result += f"- Unresolved Crashes: {crash.get('unresolved_crash_count')}\n"
        result += f"- Supports Crash Data: {'Yes' if crash.get('supports_crash_data') else 'No'}\n\n"
    
    return result

@mcp.resource("nr://key_transactions")
async def get_key_transactions_resource() -> str:
    """Get a list of New Relic key transactions as a resource."""
    response = await make_request("get", "/key_transactions.json")
    transactions = response.get("key_transactions", [])
    
    result = "# New Relic Key Transactions\n\n"
    for txn in transactions:
        result += f"## {txn.get('name')}\n"
        result += f"- ID: {txn.get('id')}\n"
        result += f"- Transaction Name: {txn.get('transaction_name')}\n"
        result += f"- Health: {txn.get('health_status')}\n"
        result += f"- Last Reported: {txn.get('last_reported_at')}\n"
        result += f"- Reporting: {'Yes' if txn.get('reporting') else 'No'}\n"
        result += f"- Application ID: {txn.get('links', {}).get('application')}\n"
        
        if txn.get('application_summary'):
            summary = txn.get('application_summary')
            result += "- Summary:\n"
            result += f"  - Apdex: {summary.get('apdex_score')}\n"
            result += f"  - Response Time: {summary.get('response_time')}ms\n"
            result += f"  - Throughput: {summary.get('throughput')} rpm\n"
            result += f"  - Error Rate: {summary.get('error_rate')}%\n"
        
        result += "\n"
    
    return result

@mcp.resource("nr://key_transaction/{txn_id}")
async def get_key_transaction_resource(txn_id: int) -> str:
    """
    Get detailed information about a specific New Relic key transaction.
    
    Args:
        txn_id: Key Transaction ID
    """
    response = await make_request("get", f"/key_transactions/{txn_id}.json")
    txn = response.get("key_transaction", {})
    
    result = f"# New Relic Key Transaction: {txn.get('name')}\n\n"
    result += f"- ID: {txn.get('id')}\n"
    result += f"- Transaction Name: {txn.get('transaction_name')}\n"
    result += f"- Health: {txn.get('health_status')}\n"
    result += f"- Last Reported: {txn.get('last_reported_at')}\n"
    result += f"- Reporting: {'Yes' if txn.get('reporting') else 'No'}\n"
    result += f"- Application ID: {txn.get('links', {}).get('application')}\n\n"
    
    if txn.get('application_summary'):
        summary = txn.get('application_summary')
        result += "## Application Summary\n"
        result += f"- Apdex Score: {summary.get('apdex_score')}\n"
        result += f"- Apdex Target: {summary.get('apdex_target')}s\n"
        result += f"- Response Time: {summary.get('response_time')}ms\n"
        result += f"- Throughput: {summary.get('throughput')} rpm\n"
        result += f"- Error Rate: {summary.get('error_rate')}%\n"
        result += f"- Instance Count: {summary.get('instance_count')}\n"
        result += f"- Host Count: {summary.get('host_count')}\n\n"
    
    if txn.get('end_user_summary'):
        summary = txn.get('end_user_summary')
        result += "## End User Summary\n"
        result += f"- Apdex Score: {summary.get('apdex_score')}\n"
        result += f"- Apdex Target: {summary.get('apdex_target')}s\n"
        result += f"- Response Time: {summary.get('response_time')}ms\n"
        result += f"- Throughput: {summary.get('throughput')} rpm\n\n"
    
    return result

@mcp.resource("nr://alerts/incidents/{only_open}")
async def get_alerts_incidents_resource(only_open: bool = True) -> str:
    """
    Get a list of New Relic alert incidents as a resource.
    
    Args:
        only_open: Whether to show only open incidents (default: True)
    """
    params = {"only_open": "true" if only_open else "false"}
    response = await make_request("get", "/alerts_incidents.json", params)
    incidents = response.get("incidents", [])
    
    result = f"# New Relic {'Open ' if only_open else ''}Alert Incidents\n\n"
    for incident in incidents:
        opened_at = datetime.fromtimestamp(incident.get('opened_at', 0)).strftime('%Y-%m-%d %H:%M:%S')
        status = "Open"
        closed_info = ""
        
        if incident.get('closed_at'):
            status = "Closed"
            closed_at = datetime.fromtimestamp(incident.get('closed_at')).strftime('%Y-%m-%d %H:%M:%S')
            closed_info = f"- Closed: {closed_at}\n"
        
        result += f"## Incident {incident.get('id')}\n"
        result += f"- Status: {status}\n"
        result += f"- Opened: {opened_at}\n"
        result += closed_info
        result += f"- Policy ID: {incident.get('links', {}).get('policy_id')}\n"
        
        if incident.get('links', {}).get('violations'):
            result += "- Violations:\n"
            for violation_id in incident.get('links', {}).get('violations', []):
                result += f"  - {violation_id}\n"
        
        result += "\n"
    
    return result

@mcp.resource("nr://alerts/violations/{only_open}/{start_date}/{end_date}")
async def get_alerts_violations_resource(
    only_open: bool = True,
    start_date: Optional[str] = None,
    end_date: Optional[str] = None
) -> str:
    """
    Get a list of New Relic alert violations as a resource.
    
    Args:
        only_open: Whether to show only open violations (default: True)
        start_date: ISO 8601 start date (default: 24 hours ago)
        end_date: ISO 8601 end date (default: now)
    """
    if not start_date:
        start_date = (datetime.now() - timedelta(days=1)).isoformat()
    
    if not end_date:
        end_date = datetime.now().isoformat()
    
    params = {
        "only_open": "true" if only_open else "false",
        "start_date": start_date,
        "end_date": end_date
    }
    
    response = await make_request("get", "/alerts_violations.json", params)
    violations = response.get("violations", [])
    
    result = f"# New Relic {'Open ' if only_open else ''}Alert Violations\n\n"
    result += f"Time range: {start_date} to {end_date}\n\n"
    
    for violation in violations:
        opened_at = datetime.fromtimestamp(violation.get('opened_at', 0)).strftime('%Y-%m-%d %H:%M:%S')
        status = "Open"
        closed_info = ""
        
        if violation.get('closed_at'):
            status = "Closed"
            closed_at = datetime.fromtimestamp(violation.get('closed_at')).strftime('%Y-%m-%d %H:%M:%S')
            closed_info = f"- Closed: {closed_at}\n"
        
        entity = violation.get('entity', {})
        
        result += f"## {violation.get('condition_name')} - {entity.get('name')}\n"
        result += f"- ID: {violation.get('id')}\n"
        result += f"- Status: {status}\n"
        result += f"- Priority: {violation.get('priority')}\n"
        result += f"- Opened: {opened_at}\n"
        result += closed_info
        result += f"- Duration: {violation.get('duration')} minutes\n"
        result += f"- Policy: {violation.get('policy_name')} (ID: {violation.get('links', {}).get('policy_id')})\n"
        result += f"- Condition ID: {violation.get('links', {}).get('condition_id')}\n"
        result += f"- Incident ID: {violation.get('links', {}).get('incident_id')}\n"
        
        result += "- Entity:\n"
        result += f"  - Name: {entity.get('name')}\n"
        result += f"  - Type: {entity.get('type')}\n"
        result += f"  - Product: {entity.get('product')}\n"
        result += f"  - ID: {entity.get('id')}\n"
        result += f"  - Group ID: {entity.get('group_id')}\n"
        
        result += "\n"
    
    return result

@mcp.resource("nr://dashboard")
async def get_dashboard_resource() -> str:
    """Get a simple New Relic dashboard with key metrics."""
    # Get applications
    apps_response = await make_request("get", "/applications.json", {"exclude_links": "true"})
    applications = apps_response.get("applications", [])
    
    # Get mobile applications
    mobile_response = await make_request("get", "/mobile_applications.json")
    mobile_apps = mobile_response.get("applications", [])
    
    # Get alert policies
    policies_response = await make_request("get", "/alerts_policies.json")
    policies = policies_response.get("policies", [])
    
    # Get open incidents
    incidents_response = await make_request("get", "/alerts_incidents.json", {"only_open": "true"})
    incidents = incidents_response.get("incidents", [])
    
    result = "# New Relic Dashboard\n\n"
    
    # Application summary
    result += "## Applications\n\n"
    result += f"Total Applications: {len(applications)}\n\n"
    
    # Top 5 applications by throughput
    apps_by_throughput = sorted(
        [a for a in applications if a.get('application_summary', {}).get('throughput') is not None],
        key=lambda x: x.get('application_summary', {}).get('throughput', 0),
        reverse=True
    )[:5]
    
    if apps_by_throughput:
        result += "### Top Applications by Throughput\n\n"
        for app in apps_by_throughput:
            name = app.get('name')
            throughput = app.get('application_summary', {}).get('throughput', 0)
            response_time = app.get('application_summary', {}).get('response_time', 0)
            error_rate = app.get('application_summary', {}).get('error_rate', 0)
            
            result += f"- **{name}**\n"
            result += f"  - Throughput: {throughput} rpm\n"
            result += f"  - Response Time: {response_time} ms\n"
            result += f"  - Error Rate: {error_rate}%\n\n"
    
    # Mobile applications summary
    result += "## Mobile Applications\n\n"
    result += f"Total Mobile Applications: {len(mobile_apps)}\n\n"
    
    if mobile_apps:
        result += "### Mobile Application Details\n\n"
        for app in mobile_apps[:5]:  # Show top 5
            name = app.get('name')
            crash_rate = app.get('crash_summary', {}).get('crash_rate', 0)
            error_rate = app.get('mobile_summary', {}).get('remote_error_rate', 0)
            
            result += f"- **{name}**\n"
            result += f"  - Crash Rate: {crash_rate}%\n"
            result += f"  - API Error Rate: {error_rate}%\n\n"
    
    # Alerts summary
    result += "## Alerts\n\n"
    result += f"Total Alert Policies: {len(policies)}\n"
    result += f"Open Incidents: {len(incidents)}\n\n"
    
    if incidents:
        result += "### Open Incidents\n\n"
        for incident in incidents[:5]:  # Show top 5
            policy_id = incident.get('links', {}).get('policy_id')
            policy_name = next((p.get('name') for p in policies if p.get('id') == policy_id), f"Policy {policy_id}")
            opened_at = datetime.fromtimestamp(incident.get('opened_at', 0)).strftime('%Y-%m-%d %H:%M:%S')
            
            result += f"- **Incident {incident.get('id')}**\n"
            result += f"  - Policy: {policy_name}\n"
            result += f"  - Opened: {opened_at}\n"
            result += f"  - Violations: {len(incident.get('links', {}).get('violations', []))}\n\n"
    
    return result

# Browser Applications Tools
@mcp.tool()
async def list_browser_applications(
    filter_name: Optional[str] = None,
    page: Optional[int] = None
) -> str:
    """
    List browser applications.
    
    Args:
        filter_name: Filter by name (exact match)
        page: Pagination index
    """
    params = {}
    if filter_name:
        params["filter[name]"] = filter_name
    if page:
        params["page"] = page
    
    response = await make_request("get", "/browser_applications.json", params)
    return json.dumps(response, indent=2)

@mcp.tool()
async def get_browser_application(app_id: int) -> str:
    """
    Get details for a specific browser application.
    
    Args:
        app_id: Browser application ID
    """
    response = await make_request("get", f"/browser_applications/{app_id}.json")
    return json.dumps(response, indent=2)

@mcp.tool()
async def create_browser_application(name: str) -> str:
    """
    Create a browser application.
    
    Args:
        name: Name of the browser application
    """
    data = {
        "browser_application": {
            "name": name
        }
    }
    
    response = await make_request("post", "/browser_applications.json", data=data)
    return json.dumps(response, indent=2)

@mcp.tool()
async def update_browser_application(
    app_id: int,
    name: Optional[str] = None
) -> str:
    """
    Update a browser application.
    
    Args:
        app_id: Browser application ID
        name: New name for the browser application
    """
    data = {"browser_application": {}}
    if name:
        data["browser_application"]["name"] = name
    
    response = await make_request("put", f"/browser_applications/{app_id}.json", data=data)
    return json.dumps(response, indent=2)

@mcp.tool()
async def delete_browser_application(app_id: int) -> str:
    """
    Delete a browser application.
    
    Args:
        app_id: Browser application ID
    """
    response = await make_request("delete", f"/browser_applications/{app_id}.json")
    return json.dumps(response, indent=2)

# Synthetic Monitoring Tools
@mcp.tool()
async def list_monitors(
    limit: Optional[int] = None,
    offset: Optional[int] = None
) -> str:
    """
    List synthetic monitors.
    
    Args:
        limit: Maximum number of monitors to return
        offset: Pagination offset
    """
    # Synthetic monitoring uses a different base URL
    synthetics_url = "https://synthetics.newrelic.com/synthetics/api"
    
    # Create headers specific to synthetics API
    headers = {
        "X-Api-Key": API_KEY,
        "Content-Type": "application/json"
    }
    
    params = {}
    if limit:
        params["limit"] = limit
    if offset:
        params["offset"] = offset
    
    try:
        async with httpx.AsyncClient() as client:
            response = await client.get(f"{synthetics_url}/v3/monitors", headers=headers, params=params)
            response.raise_for_status()
            result = response.json()
            
            # Validate response with Pydantic model
            monitor_list = MonitorList(monitors=result["monitors"])
            return json.dumps(monitor_list.dict(), indent=2)
    except ValidationError as e:
        error_resp = ErrorResponse(error="Validation error", message=str(e))
        return json.dumps(error_resp.dict(), indent=2)
    except httpx.HTTPError as e:
        error_resp = ErrorResponse(error="HTTP error", message=str(e))
        return json.dumps(error_resp.dict(), indent=2)

@mcp.tool()
async def get_monitor(monitor_id: str) -> str:
    """
    Get details for a specific synthetic monitor.
    
    Args:
        monitor_id: Synthetic monitor ID (UUID format)
    """
    # Synthetic monitoring uses a different base URL
    synthetics_url = "https://synthetics.newrelic.com/synthetics/api"
    
    # Create headers specific to synthetics API
    headers = {
        "X-Api-Key": API_KEY,
        "Content-Type": "application/json"
    }
    
    try:
        async with httpx.AsyncClient() as client:
            response = await client.get(f"{synthetics_url}/v3/monitors/{monitor_id}", headers=headers)
            response.raise_for_status()
            result = response.json()
            
            # Validate response with Pydantic model
            monitor = Monitor(**result["monitor"])
            return json.dumps(monitor.dict(), indent=2)
    except ValidationError as e:
        error_resp = ErrorResponse(error="Validation error", message=str(e))
        return json.dumps(error_resp.dict(), indent=2)
    except httpx.HTTPError as e:
        error_resp = ErrorResponse(error="HTTP error", message=str(e))
        return json.dumps(error_resp.dict(), indent=2)

@mcp.tool()
async def create_simple_monitor(
    name: str,
    uri: str,
    type: str,
    frequency: int,
    locations: List[str],
    status: str = "ENABLED",
    sla_threshold: Optional[float] = None
) -> str:
    """
    Create a simple synthetic monitor.
    
    Args:
        name: Monitor name
        uri: URI to monitor
        type: Monitor type (SIMPLE, BROWSER, SCRIPT_API, SCRIPT_BROWSER)
        frequency: Check frequency in minutes (1, 5, 10, 15, 30, 60, 360, 720, or 1440)
        locations: List of location IDs where the monitor will run
        status: Monitor status (ENABLED or DISABLED)
        sla_threshold: SLA threshold in seconds
    """
    # Synthetic monitoring uses a different base URL
    synthetics_url = "https://synthetics.newrelic.com/synthetics/api"
    
    # Create headers specific to synthetics API
    headers = {
        "X-Api-Key": API_KEY,
        "Content-Type": "application/json"
    }
    
    try:
        # Validate request data with Pydantic model
        monitor_request = MonitorRequest(
            name=name,
            type=type,
            frequency=frequency,
            uri=uri,
            locations=locations,
            status=status,
            slaThreshold=sla_threshold
        )
        
        data = monitor_request.dict(exclude_none=True)
        
        async with httpx.AsyncClient() as client:
            response = await client.post(f"{synthetics_url}/v3/monitors", headers=headers, json=data)
            response.raise_for_status()
            result = response.json()
            
            # Validate response with Pydantic model
            monitor = Monitor(**result["monitor"])
            return json.dumps(monitor.dict(), indent=2)
    except ValidationError as e:
        error_resp = ErrorResponse(error="Validation error", message=str(e))
        return json.dumps(error_resp.dict(), indent=2)
    except httpx.HTTPError as e:
        error_resp = ErrorResponse(error="HTTP error", message=str(e))
        return json.dumps(error_resp.dict(), indent=2)

@mcp.tool()
async def update_monitor(
    monitor_id: str,
    name: Optional[str] = None,
    frequency: Optional[int] = None,
    status: Optional[str] = None,
    sla_threshold: Optional[float] = None,
    locations: Optional[List[str]] = None
) -> str:
    """
    Update a synthetic monitor.
    
    Args:
        monitor_id: Monitor ID (UUID format)
        name: New monitor name
        frequency: New check frequency in minutes
        status: New monitor status (ENABLED or DISABLED)
        sla_threshold: New SLA threshold in seconds
        locations: New list of location IDs
    """
    # Synthetic monitoring uses a different base URL
    synthetics_url = "https://synthetics.newrelic.com/synthetics/api"
    
    # Create headers specific to synthetics API
    headers = {
        "X-Api-Key": API_KEY,
        "Content-Type": "application/json"
    }
    
    try:
        # Get current monitor details first
        async with httpx.AsyncClient() as client:
            get_response = await client.get(f"{synthetics_url}/v3/monitors/{monitor_id}", headers=headers)
            get_response.raise_for_status()
            current_monitor = get_response.json()
            
            # Validate the update data with Pydantic model
            monitor_update = MonitorUpdate(
                name=name,
                frequency=frequency,
                status=status,
                slaThreshold=sla_threshold,
                locations=locations
            )
            
            # Update only the provided fields
            data = monitor_update.dict(exclude_none=True)
            
            # If type is SCRIPT_API or SCRIPT_BROWSER, we need to include script property
            if current_monitor.get("monitor", {}).get("type") in ["SCRIPT_API", "SCRIPT_BROWSER"]:
                data["script"] = current_monitor.get("monitor", {}).get("script", "")
            
            # For browser and simple monitors, include URI
            if current_monitor.get("monitor", {}).get("type") in ["SIMPLE", "BROWSER"]:
                data["uri"] = current_monitor.get("monitor", {}).get("uri", "")
            
            response = await client.put(f"{synthetics_url}/v3/monitors/{monitor_id}", headers=headers, json=data)
            response.raise_for_status()
            result = response.json()
            
            # Validate response with Pydantic model
            monitor = Monitor(**result["monitor"])
            return json.dumps(monitor.dict(), indent=2)
    except ValidationError as e:
        error_resp = ErrorResponse(error="Validation error", message=str(e))
        return json.dumps(error_resp.dict(), indent=2)
    except httpx.HTTPError as e:
        error_resp = ErrorResponse(error="HTTP error", message=str(e))
        return json.dumps(error_resp.dict(), indent=2)

@mcp.tool()
async def delete_monitor(monitor_id: str) -> str:
    """
    Delete a synthetic monitor.
    
    Args:
        monitor_id: Monitor ID (UUID format)
    """
    # Synthetic monitoring uses a different base URL
    synthetics_url = "https://synthetics.newrelic.com/synthetics/api"
    
    # Create headers specific to synthetics API
    headers = {
        "X-Api-Key": API_KEY,
        "Content-Type": "application/json"
    }
    
    try:
        async with httpx.AsyncClient() as client:
            response = await client.delete(f"{synthetics_url}/v3/monitors/{monitor_id}", headers=headers)
            response.raise_for_status()
            return json.dumps({"success": True, "message": "Monitor deleted successfully"}, indent=2)
    except ValidationError as e:
        error_resp = ErrorResponse(error="Validation error", message=str(e))
        return json.dumps(error_resp.dict(), indent=2)
    except httpx.HTTPError as e:
        error_resp = ErrorResponse(error="HTTP error", message=str(e))
        return json.dumps(error_resp.dict(), indent=2)
    
# Workloads Tools (using NerdGraph API)
@mcp.tool()
async def list_workloads() -> str:
    """
    List workloads using NerdGraph API.
    """
    # NerdGraph API uses a different URL and approach
    nerdgraph_url = "https://api.newrelic.com/graphql"
    
    # Create headers for NerdGraph API
    headers = {
        "API-Key": API_KEY,
        "Content-Type": "application/json"
    }
    
    # GraphQL query to list workloads
    query = """
    {
      actor {
        workloads {
          collections {
            id
            name
            accountId
            status {
              value
            }
            entitySearchQuery
            createdBy
            permalink
            entityCount
          }
        }
      }
    }
    """
    
    data = {"query": query}
    
    async with httpx.AsyncClient() as client:
        response = await client.post(nerdgraph_url, headers=headers, json=data)
        response.raise_for_status()
        return json.dumps(response.json(), indent=2)

@mcp.tool()
async def get_workload(
    account_id: int,
    workload_id: str
) -> str:
    """
    Get details for a specific workload using NerdGraph API.
    
    Args:
        account_id: New Relic account ID
        workload_id: Workload entity GUID
    """
    # NerdGraph API uses a different URL and approach
    nerdgraph_url = "https://api.newrelic.com/graphql"
    
    # Create headers for NerdGraph API
    headers = {
        "API-Key": API_KEY,
        "Content-Type": "application/json"
    }
    
    # GraphQL query to get workload details
    query = """
    {
      actor {
        account(id: %d) {
          workload(guid: "%s") {
            id
            name
            status {
              value
            }
            entitySearchQuery
            createdBy
            permalink
            entityCount
            entities {
              results {
                guid
                name
                entityType
                alertSeverity
              }
            }
          }
        }
      }
    }
    """ % (account_id, workload_id)
    
    data = {"query": query}
    
    async with httpx.AsyncClient() as client:
        response = await client.post(nerdgraph_url, headers=headers, json=data)
        response.raise_for_status()
        return json.dumps(response.json(), indent=2)

@mcp.tool()
async def create_workload(
    account_id: int,
    name: str,
    entity_search_query: str,
    entity_guids: Optional[List[str]] = None
) -> str:
    """
    Create a workload using NerdGraph API.
    
    Args:
        account_id: New Relic account ID
        name: Workload name
        entity_search_query: NRQL-like query to select entities for the workload
        entity_guids: Optional list of specific entity GUIDs to include
    """
    # NerdGraph API uses a different URL and approach
    nerdgraph_url = "https://api.newrelic.com/graphql"
    
    # Create headers for NerdGraph API
    headers = {
        "API-Key": API_KEY,
        "Content-Type": "application/json"
    }
    
    # Prepare the input variables
    variables = {
        "accountId": account_id,
        "name": name,
        "entitySearchQuery": entity_search_query
    }
    
    if entity_guids:
        variables["entityGuids"] = entity_guids
    
    # GraphQL mutation to create a workload
    mutation = """
    mutation($accountId: Int!, $name: String!, $entitySearchQuery: String!, $entityGuids: [EntityGuid]) {
      workloadCreate(accountId: $accountId, workload: {
        name: $name,
        entitySearchQuery: $entitySearchQuery,
        entityGuids: $entityGuids
      }) {
        guid
        name
        permalink
      }
    }
    """
    
    data = {
        "query": mutation,
        "variables": variables
    }
    
    async with httpx.AsyncClient() as client:
        response = await client.post(nerdgraph_url, headers=headers, json=data)
        response.raise_for_status()
        return json.dumps(response.json(), indent=2)

@mcp.tool()
async def update_workload(
    account_id: int,
    workload_guid: str,
    name: Optional[str] = None,
    entity_search_query: Optional[str] = None
) -> str:
    """
    Update a workload using NerdGraph API.
    
    Args:
        account_id: New Relic account ID
        workload_guid: Workload entity GUID
        name: New workload name
        entity_search_query: New entity search query
    """
    # NerdGraph API uses a different URL and approach
    nerdgraph_url = "https://api.newrelic.com/graphql"
    
    # Create headers for NerdGraph API
    headers = {
        "API-Key": API_KEY,
        "Content-Type": "application/json"
    }
    
    # Prepare the input variables
    variables = {
        "accountId": account_id,
        "guid": workload_guid
    }
    
    update_fields = {}
    if name:
        update_fields["name"] = name
    if entity_search_query:
        update_fields["entitySearchQuery"] = entity_search_query
    
    variables["updateFields"] = update_fields
    
    # GraphQL mutation to update a workload
    mutation = """
    mutation($accountId: Int!, $guid: EntityGuid!, $updateFields: WorkloadUpdateInput!) {
      workloadUpdate(accountId: $accountId, guid: $guid, updateFields: $updateFields) {
        guid
        name
        permalink
        entitySearchQuery
      }
    }
    """
    
    data = {
        "query": mutation,
        "variables": variables
    }
    
    async with httpx.AsyncClient() as client:
        response = await client.post(nerdgraph_url, headers=headers, json=data)
        response.raise_for_status()
        return json.dumps(response.json(), indent=2)

@mcp.tool()
async def delete_workload(
    account_id: int,
    workload_guid: str
) -> str:
    """
    Delete a workload using NerdGraph API.
    
    Args:
        account_id: New Relic account ID
        workload_guid: Workload entity GUID
    """
    # NerdGraph API uses a different URL and approach
    nerdgraph_url = "https://api.newrelic.com/graphql"
    
    # Create headers for NerdGraph API
    headers = {
        "API-Key": API_KEY,
        "Content-Type": "application/json"
    }
    
    # GraphQL mutation to delete a workload
    mutation = """
    mutation($accountId: Int!, $guid: EntityGuid!) {
      workloadDelete(accountId: $accountId, guid: $guid) {
        guid
      }
    }
    """
    
    variables = {
        "accountId": account_id,
        "guid": workload_guid
    }
    
    data = {
        "query": mutation,
        "variables": variables
    }
    
    async with httpx.AsyncClient() as client:
        response = await client.post(nerdgraph_url, headers=headers, json=data)
        response.raise_for_status()
        return json.dumps(response.json(), indent=2)
    
# Dashboards Tools (using NerdGraph API)
@mcp.tool()
async def list_dashboards(
    account_id: int,
    page: Optional[int] = None,
    per_page: Optional[int] = None
) -> str:
    """
    List dashboards using NerdGraph API.
    
    Args:
        account_id: New Relic account ID
        page: Page number for pagination
        per_page: Number of items per page
    """
    # NerdGraph API uses a different URL and approach
    nerdgraph_url = "https://api.newrelic.com/graphql"
    
    # Create headers for NerdGraph API
    headers = {
        "API-Key": API_KEY,
        "Content-Type": "application/json"
    }
    
    # Default pagination
    page = page or 1
    per_page = per_page or 20
    
    # GraphQL query to list dashboards
    query = """
    {
      actor {
        account(id: %d) {
          dashboards(limit: %d, offset: %d) {
            totalCount
            previousCursor
            nextCursor
            dashboards {
              id
              title
              permissions
              pages {
                name
              }
              owner {
                email
                userId
              }
              createdAt
              updatedAt
            }
          }
        }
      }
    }
    """ % (account_id, per_page, (page - 1) * per_page)
    
    data = {"query": query}
    
    async with httpx.AsyncClient() as client:
        response = await client.post(nerdgraph_url, headers=headers, json=data)
        response.raise_for_status()
        return json.dumps(response.json(), indent=2)

@mcp.tool()
async def get_dashboard(
    account_id: int,
    dashboard_id: str
) -> str:
    """
    Get details for a specific dashboard using NerdGraph API.
    
    Args:
        account_id: New Relic account ID
        dashboard_id: Dashboard entity ID
    """
    # NerdGraph API uses a different URL and approach
    nerdgraph_url = "https://api.newrelic.com/graphql"
    
    # Create headers for NerdGraph API
    headers = {
        "API-Key": API_KEY,
        "Content-Type": "application/json"
    }
    
    # GraphQL query to get dashboard details
    query = """
    {
      actor {
        account(id: %d) {
          dashboard(id: "%s") {
            id
            title
            permissions
            pages {
              name
              widgets {
                id
                title
                visualization {
                  id
                }
                layout {
                  width
                  height
                  row
                  column
                }
                rawConfiguration
              }
            }
            owner {
              email
              userId
            }
            createdAt
            updatedAt
          }
        }
      }
    }
    """ % (account_id, dashboard_id)
    
    data = {"query": query}
    
    async with httpx.AsyncClient() as client:
        response = await client.post(nerdgraph_url, headers=headers, json=data)
        response.raise_for_status()
        return json.dumps(response.json(), indent=2)

@mcp.tool()
async def create_simple_dashboard(
    account_id: int,
    title: str,
    page_name: str = "Main Page",
    widgets: Optional[List[Dict]] = None
) -> str:
    """
    Create a simple dashboard using NerdGraph API.
    
    Args:
        account_id: New Relic account ID
        title: Dashboard title
        page_name: Page name
        widgets: List of widget configurations (optional)
    """
    # NerdGraph API uses a different URL and approach
    nerdgraph_url = "https://api.newrelic.com/graphql"
    
    # Create headers for NerdGraph API
    headers = {
        "API-Key": API_KEY,
        "Content-Type": "application/json"
    }
    
    # Default empty list if widgets not provided
    widgets = widgets or []
    
    # Prepare widget inputs for GraphQL
    widget_inputs = []
    for i, widget in enumerate(widgets):
        widget_input = {
            "visualization": {"id": widget.get("visualization_id")},
            "layout": widget.get("layout", {"width": 6, "height": 3, "row": i // 2, "column": i % 2 * 6}),
            "title": widget.get("title", f"Widget {i+1}"),
            "rawConfiguration": widget.get("raw_configuration", {})
        }
        widget_inputs.append(widget_input)
    
    # GraphQL mutation to create a dashboard
    mutation = """
    mutation($accountId: Int!, $dashboard: DashboardInput!) {
      dashboardCreate(accountId: $accountId, dashboard: $dashboard) {
        entityResult {
          guid
          name
        }
      }
    }
    """
    
    variables = {
        "accountId": account_id,
        "dashboard": {
            "name": title,
            "permissions": "PUBLIC_READ_WRITE",
            "pages": [
                {
                    "name": page_name,
                    "widgets": widget_inputs
                }
            ]
        }
    }
    
    data = {
        "query": mutation,
        "variables": variables
    }
    
    async with httpx.AsyncClient() as client:
        response = await client.post(nerdgraph_url, headers=headers, json=data)
        response.raise_for_status()
        return json.dumps(response.json(), indent=2)

@mcp.tool()
async def delete_dashboard(
    account_id: int,
    dashboard_guid: str
) -> str:
    """
    Delete a dashboard using NerdGraph API.
    
    Args:
        account_id: New Relic account ID
        dashboard_guid: Dashboard entity GUID
    """
    # NerdGraph API uses a different URL and approach
    nerdgraph_url = "https://api.newrelic.com/graphql"
    
    # Create headers for NerdGraph API
    headers = {
        "API-Key": API_KEY,
        "Content-Type": "application/json"
    }
    
    # GraphQL mutation to delete a dashboard
    mutation = """
    mutation($guid: EntityGuid!) {
      dashboardDelete(guid: $guid) {
        status
        error {
          description
        }
      }
    }
    """
    
    variables = {
        "guid": dashboard_guid
    }
    
    data = {
        "query": mutation,
        "variables": variables
    }
    
    async with httpx.AsyncClient() as client:
        response = await client.post(nerdgraph_url, headers=headers, json=data)
        response.raise_for_status()
        return json.dumps(response.json(), indent=2)
    
# NRQL Query Tool (using NerdGraph API)
@mcp.tool()
async def execute_nrql_query(
    account_id: int,
    query: str,
    timeout: Optional[int] = None
) -> str:
    """
    Execute a NRQL query using NerdGraph API.
    
    Args:
        account_id: New Relic account ID
        query: NRQL query string
        timeout: Query timeout in seconds (optional)
    """
    # NerdGraph API uses a different URL and approach
    nerdgraph_url = "https://api.newrelic.com/graphql"
    
    # Create headers for NerdGraph API
    headers = {
        "API-Key": API_KEY,
        "Content-Type": "application/json"
    }
    
    # Prepare variables
    variables = {
        "accountId": account_id,
        "query": query
    }
    
    if timeout:
        variables["timeout"] = timeout
    
    # GraphQL query to execute NRQL
    nrql_query = """
    query($accountId: Int!, $query: Nrql!, $timeout: Int) {
      actor {
        account(id: $accountId) {
          nrql(query: $query, timeout: $timeout) {
            results
            metadata {
              facets
              timeRange {
                begin
                end
              }
            }
          }
        }
      }
    }
    """
    
    data = {
        "query": nrql_query,
        "variables": variables
    }
    
    async with httpx.AsyncClient() as client:
        response = await client.post(nerdgraph_url, headers=headers, json=data)
        response.raise_for_status()
        return json.dumps(response.json(), indent=2)
    
@mcp.tool()
async def get_metric_timeslice_data(
    metric_names: List[str],
    start_time: str,
    end_time: str,
    period: Optional[int] = None,
    summarize: bool = False
) -> str:
    """
    Get metric timeslice data across all applications.
    
    Args:
        metric_names: List of metric names
        start_time: ISO 8601 format start time
        end_time: ISO 8601 format end time
        period: Period in seconds (optional)
        summarize: Whether to summarize the data
    """
    params = {
        "names[]": metric_names,
        "from": start_time,
        "to": end_time
    }
    
    if period:
        params["period"] = period
    
    if summarize:
        params["summarize"] = "true"
    
    response = await make_request("get", "/metrics/data.json", params)
    return json.dumps(response, indent=2)

@mcp.resource("nr://synthetics/monitors")
async def get_synthetic_monitors_resource() -> str:
    """Get a list of New Relic synthetic monitors as a resource."""
    # Synthetic monitoring uses a different base URL
    synthetics_url = "https://synthetics.newrelic.com/synthetics/api"
    
    # Create headers specific to synthetics API
    headers = {
        "X-Api-Key": API_KEY,
        "Content-Type": "application/json"
    }
    
    async with httpx.AsyncClient() as client:
        response = await client.get(f"{synthetics_url}/v3/monitors", headers=headers)
        response.raise_for_status()
        monitors = response.json().get("monitors", [])
    
    result = "# New Relic Synthetic Monitors\n\n"
    
    for monitor in monitors:
        result += f"## {monitor.get('name')}\n"
        result += f"- ID: {monitor.get('id')}\n"
        result += f"- Type: {monitor.get('type')}\n"
        result += f"- Status: {monitor.get('status')}\n"
        result += f"- Frequency: {monitor.get('frequency')} minutes\n"
        
        # Include URI for SIMPLE and BROWSER types
        if monitor.get('type') in ['SIMPLE', 'BROWSER'] and 'uri' in monitor:
            result += f"- URI: {monitor.get('uri')}\n"
        
        # Include locations
        if 'locations' in monitor:
            result += "- Locations:\n"
            for location in monitor.get('locations', []):
                result += f"  - {location}\n"
        
        result += "\n"
    
    return result

@mcp.resource("nr://dashboards/{account_id}")
async def get_dashboards_resource(account_id: int) -> str:
    """
    Get a list of New Relic dashboards as a resource.
    
    Args:
        account_id: New Relic account ID
    """
    # NerdGraph API uses a different URL and approach
    nerdgraph_url = "https://api.newrelic.com/graphql"
    
    # Create headers for NerdGraph API
    headers = {
        "API-Key": API_KEY,
        "Content-Type": "application/json"
    }
    
    # GraphQL query to list dashboards
    query = """
    {
      actor {
        account(id: %d) {
          dashboards {
            dashboards {
              id
              title
              permissions
              createdAt
              updatedAt
              pages {
                name
              }
            }
          }
        }
      }
    }
    """ % account_id
    
    data = {"query": query}
    
    async with httpx.AsyncClient() as client:
        response = await client.post(nerdgraph_url, headers=headers, json=data)
        response.raise_for_status()
        result_data = response.json()
    
    dashboards = result_data.get("data", {}).get("actor", {}).get("account", {}).get("dashboards", {}).get("dashboards", [])
    
    result = f"# New Relic Dashboards (Account: {account_id})\n\n"
    
    for dashboard in dashboards:
        created_at = datetime.fromisoformat(dashboard.get('createdAt').replace('Z', '+00:00')).strftime('%Y-%m-%d %H:%M:%S')
        updated_at = datetime.fromisoformat(dashboard.get('updatedAt').replace('Z', '+00:00')).strftime('%Y-%m-%d %H:%M:%S')
        
        result += f"## {dashboard.get('title')}\n"
        result += f"- ID: {dashboard.get('id')}\n"
        result += f"- Permissions: {dashboard.get('permissions')}\n"
        result += f"- Created: {created_at}\n"
        result += f"- Updated: {updated_at}\n"
        
        if dashboard.get('pages'):
            result += "- Pages:\n"
            for page in dashboard.get('pages'):
                result += f"  - {page.get('name')}\n"
        
        result += "\n"
    
    return result

# New Prompt for Synthetic Monitoring
@mcp.prompt()
def synthetic_monitoring_analysis(monitor_id: str, time_period: int = 24) -> str:
    """
    Prompt for analyzing synthetic monitor performance.
    
    Args:
        monitor_id: Monitor ID to analyze
        time_period: Time period in hours to analyze (default: 24)
    """
    return f"""Please analyze the performance of synthetic monitor with ID {monitor_id} over the past {time_period} hours.

I need to understand:
1. Check failure patterns and their frequency
2. Average response times and trends
3. Geographical performance differences
4. Any correlation between failures and specific conditions (time of day, location, etc.)

Based on the data, please provide:
- Key performance insights
- Recommendations for improving the monitored endpoint
- Suggestions for adjusting monitor settings or thresholds
- Whether additional monitoring should be implemented"""

# Infrastructure Monitoring Tools
@mcp.tool()
async def list_infrastructure_hosts(
    filter_hostname: Optional[str] = None,
    filter_os: Optional[str] = None,
    page: Optional[int] = None
) -> str:
    """
    List infrastructure hosts.
    
    Args:
        filter_hostname: Filter by hostname
        filter_os: Filter by operating system
        page: Pagination index
    """
    # Infrastructure API uses a different base URL
    infra_url = "https://infra-api.newrelic.com/v2"
    
    # Create headers
    headers = {
        "Api-Key": API_KEY,
        "Content-Type": "application/json"
    }
    
    params = {}
    if filter_hostname:
        params["filter[hostname]"] = filter_hostname
    if filter_os:
        params["filter[os]"] = filter_os
    if page:
        params["page"] = page
    
    try:
        async with httpx.AsyncClient() as client:
            response = await client.get(f"{infra_url}/hosts", headers=headers, params=params)
            response.raise_for_status()
            result = response.json()
            
            # Validate response with Pydantic model
            host_list = InfrastructureHostList(hosts=result["hosts"])
            return json.dumps(host_list.dict(), indent=2)
    except ValidationError as e:
        error_resp = ErrorResponse(error="Validation error", message=str(e))
        return json.dumps(error_resp.dict(), indent=2)
    except httpx.HTTPError as e:
        error_resp = ErrorResponse(error="HTTP error", message=str(e))
        return json.dumps(error_resp.dict(), indent=2)

@mcp.tool()
async def get_infrastructure_host(host_id: str) -> str:
    """
    Get details for a specific infrastructure host.
    
    Args:
        host_id: Host ID
    """
    # Infrastructure API uses a different base URL
    infra_url = "https://infra-api.newrelic.com/v2"
    
    # Create headers
    headers = {
        "Api-Key": API_KEY,
        "Content-Type": "application/json"
    }
    
    try:
        async with httpx.AsyncClient() as client:
            response = await client.get(f"{infra_url}/hosts/{host_id}", headers=headers)
            response.raise_for_status()
            result = response.json()
            
            # Validate response with Pydantic model
            host = InfrastructureHost(**result["host"])
            return json.dumps(host.dict(), indent=2)
    except ValidationError as e:
        error_resp = ErrorResponse(error="Validation error", message=str(e))
        return json.dumps(error_resp.dict(), indent=2)
    except httpx.HTTPError as e:
        error_resp = ErrorResponse(error="HTTP error", message=str(e))
        return json.dumps(error_resp.dict(), indent=2)

@mcp.tool()
async def list_infrastructure_alerts() -> str:
    """
    List infrastructure alerts.
    """
    # Infrastructure API uses a different base URL
    infra_url = "https://infra-api.newrelic.com/v2"
    
    # Create headers
    headers = {
        "Api-Key": API_KEY,
        "Content-Type": "application/json"
    }
    
    try:
        async with httpx.AsyncClient() as client:
            response = await client.get(f"{infra_url}/alerts/conditions", headers=headers)
            response.raise_for_status()
            result = response.json()
            
            # Validate response with Pydantic model
            # Using AlertConditionList since infrastructure alerts are similar to regular alert conditions
            alert_list = AlertConditionList(conditions=result["data"])
            return json.dumps(alert_list.dict(), indent=2)
    except ValidationError as e:
        error_resp = ErrorResponse(error="Validation error", message=str(e))
        return json.dumps(error_resp.dict(), indent=2)
    except httpx.HTTPError as e:
        error_resp = ErrorResponse(error="HTTP error", message=str(e))
        return json.dumps(error_resp.dict(), indent=2)

# Logs API Tools
@mcp.tool()
async def query_logs(
    account_id: int,
    query: str,
    from_time: Optional[str] = None,
    to_time: Optional[str] = None,
    limit: int = 100
) -> str:
    """
    Query logs using NerdGraph.
    
    Args:
        account_id: New Relic account ID
        query: NRQL query for logs
        from_time: Start time in ISO 8601 format
        to_time: End time in ISO 8601 format
        limit: Maximum number of log entries to return
    """
    # NerdGraph API uses a different URL and approach
    nerdgraph_url = "https://api.newrelic.com/graphql"
    
    # Create headers for NerdGraph API
    headers = {
        "API-Key": API_KEY,
        "Content-Type": "application/json"
    }
    
    # Construct the full query with time range if provided
    full_query = query
    if not "FROM Log" in full_query and not "FROM Logs" in full_query:
        full_query = f"{query} FROM Log"
    
    if not "LIMIT" in full_query:
        full_query = f"{full_query} LIMIT {limit}"
    
    if from_time and to_time:
        if not "SINCE" in full_query and not "UNTIL" in full_query:
            full_query = f"{full_query} SINCE '{from_time}' UNTIL '{to_time}'"
    
    # GraphQL query to fetch logs
    graphql_query = """
    {
      actor {
        account(id: %d) {
          nrql(query: "%s") {
            results
          }
        }
      }
    }
    """ % (account_id, full_query.replace('"', '\\"'))
    
    data = {"query": graphql_query}
    
    async with httpx.AsyncClient() as client:
        response = await client.post(nerdgraph_url, headers=headers, json=data)
        response.raise_for_status()
        return json.dumps(response.json(), indent=2)

# Browser Applications Resource
@mcp.resource("nr://browser_applications")
async def get_browser_applications_resource() -> str:
    """Get a list of New Relic browser applications as a resource."""
    response = await make_request("get", "/browser_applications.json")
    apps = response.get("browser_applications", [])
    
    result = "# New Relic Browser Applications\n\n"
    for app in apps:
        result += f"## {app.get('name')}\n"
        result += f"- ID: {app.get('id')}\n"
        result += f"- Browser Monitoring Key: {app.get('browser_monitoring_key')}\n"
        result += f"- JS Agent Version: {app.get('js_agent_version')}\n"
        result += f"- Loader Type: {app.get('loader_type')}\n"
        
        if app.get('application_summary'):
            summary = app.get('application_summary')
            result += "- Summary:\n"
            result += f"  - Page Views: {summary.get('page_views_per_minute')} per minute\n"
            result += f"  - Page Load Time: {summary.get('page_load_time')}ms\n"
            result += f"  - Ajax Response Time: {summary.get('ajax_response_time')}ms\n"
            result += f"  - JavaScript Errors: {summary.get('javascript_errors_per_minute')} per minute\n"
        
        result += "\n"
    
    return result

# Service Levels API
@mcp.tool()
async def list_service_levels(account_id: int) -> str:
    """
    List service level indicators (SLIs) using NerdGraph API.
    
    Args:
        account_id: New Relic account ID
    """
    # NerdGraph API uses a different URL and approach
    nerdgraph_url = "https://api.newrelic.com/graphql"
    
    # Create headers for NerdGraph API
    headers = {
        "API-Key": API_KEY,
        "Content-Type": "application/json"
    }
    
    # GraphQL query to list service levels
    query = """
    {
      actor {
        account(id: %d) {
          serviceLevels {
            indicators {
              guid
              name
              description
              entityGuid
              events {
                valid {
                  name
                  query
                }
                bad {
                  name
                  query
                }
                total {
                  name
                  query
                }
              }
              objectives {
                name
                target
                timeWindow {
                  rolling {
                    count
                    unit
                  }
                }
              }
            }
          }
        }
      }
    }
    """ % account_id
    
    data = {"query": query}
    
    async with httpx.AsyncClient() as client:
        response = await client.post(nerdgraph_url, headers=headers, json=data)
        response.raise_for_status()
        return json.dumps(response.json(), indent=2)

@mcp.tool()
async def create_service_level_indicator(
    account_id: int,
    name: str,
    entity_guid: str,
    description: str,
    valid_events_query: str,
    bad_events_query: str,
    total_events_query: str,
    target_percentage: float,
    time_window_value: int,
    time_window_unit: str
) -> str:
    """
    Create a service level indicator (SLI) using NerdGraph API.
    
    Args:
        account_id: New Relic account ID
        name: SLI name
        entity_guid: Entity GUID
        description: SLI description
        valid_events_query: NRQL query for valid events
        bad_events_query: NRQL query for bad events
        total_events_query: NRQL query for total events
        target_percentage: Target percentage (0-100)
        time_window_value: Time window value
        time_window_unit: Time window unit (MINUTE, HOUR, DAY, WEEK, MONTH)
    """
    # NerdGraph API uses a different URL and approach
    nerdgraph_url = "https://api.newrelic.com/graphql"
    
    # Create headers for NerdGraph API
    headers = {
        "API-Key": API_KEY,
        "Content-Type": "application/json"
    }
    
    # GraphQL mutation to create a service level
    mutation = """
    mutation($accountId: Int!, $sli: ServiceLevelIndicatorInput!) {
      serviceLevelIndicatorCreate(accountId: $accountId, indicator: $sli) {
        guid
      }
    }
    """
    
    variables = {
        "accountId": account_id,
        "sli": {
            "name": name,
            "entityGuid": entity_guid,
            "description": description,
            "events": {
                "valid": {
                    "name": "Valid events",
                    "query": valid_events_query
                },
                "bad": {
                    "name": "Bad events",
                    "query": bad_events_query
                },
                "total": {
                    "name": "Total events",
                    "query": total_events_query
                }
            },
            "objectives": [
                {
                    "name": "Target",
                    "target": target_percentage / 100,  # API expects decimal between 0-1
                    "timeWindow": {
                        "rolling": {
                            "count": time_window_value,
                            "unit": time_window_unit
                        }
                    }
                }
            ]
        }
    }
    
    data = {
        "query": mutation,
        "variables": variables
    }
    
    async with httpx.AsyncClient() as client:
        response = await client.post(nerdgraph_url, headers=headers, json=data)
        response.raise_for_status()
        return json.dumps(response.json(), indent=2)

# Service Level Resource
@mcp.resource("nr://service_levels/{account_id}")
async def get_service_levels_resource(account_id: int) -> str:
    """
    Get service level indicators (SLIs) as a resource.
    
    Args:
        account_id: New Relic account ID
    """
    # NerdGraph API uses a different URL and approach
    nerdgraph_url = "https://api.newrelic.com/graphql"
    
    # Create headers for NerdGraph API
    headers = {
        "API-Key": API_KEY,
        "Content-Type": "application/json"
    }
    
    # GraphQL query to list service levels
    query = """
    {
      actor {
        account(id: %d) {
          serviceLevels {
            indicators {
              guid
              name
              description
              entityGuid
              events {
                valid {
                  name
                  query
                }
                bad {
                  name
                  query
                }
                total {
                  name
                  query
                }
              }
              objectives {
                name
                target
                timeWindow {
                  rolling {
                    count
                    unit
                  }
                }
              }
            }
          }
        }
      }
    }
    """ % account_id
    
    data = {"query": query}
    
    async with httpx.AsyncClient() as client:
        response = await client.post(nerdgraph_url, headers=headers, json=data)
        response.raise_for_status()
        result_data = response.json()
    
    indicators = result_data.get("data", {}).get("actor", {}).get("account", {}).get("serviceLevels", {}).get("indicators", [])
    
    result = f"# New Relic Service Level Indicators (Account: {account_id})\n\n"
    
    for sli in indicators:
        result += f"## {sli.get('name')}\n"
        result += f"- GUID: {sli.get('guid')}\n"
        result += f"- Entity GUID: {sli.get('entityGuid')}\n"
        
        if sli.get('description'):
            result += f"- Description: {sli.get('description')}\n"
        
        if sli.get('objectives'):
            for objective in sli.get('objectives'):
                target_pct = float(objective.get('target', 0)) * 100
                time_window = objective.get('timeWindow', {}).get('rolling', {})
                time_count = time_window.get('count', 0)
                time_unit = time_window.get('unit', '')
                
                result += f"- Objective: {objective.get('name')}\n"
                result += f"  - Target: {target_pct}%\n"
                result += f"  - Time Window: {time_count} {time_unit.lower()}\n"
        
        if sli.get('events'):
            events = sli.get('events')
            result += "- Events:\n"
            
            if events.get('valid'):
                result += f"  - Valid Events: {events.get('valid', {}).get('name')}\n"
                result += f"    - Query: `{events.get('valid', {}).get('query')}`\n"
            
            if events.get('bad'):
                result += f"  - Bad Events: {events.get('bad', {}).get('name')}\n"
                result += f"    - Query: `{events.get('bad', {}).get('query')}`\n"
            
            if events.get('total'):
                result += f"  - Total Events: {events.get('total', {}).get('name')}\n"
                result += f"    - Query: `{events.get('total', {}).get('query')}`\n"
        
        result += "\n"
    
    return result

# Errors Inbox API
@mcp.tool()
async def list_errors(
    account_id: int,
    query: Optional[str] = None,
    cursor: Optional[str] = None,
    limit: int = 10
) -> str:
    """
    List error events from Error Tracking using NerdGraph API.
    
    Args:
        account_id: New Relic account ID
        query: Search query string
        cursor: Pagination cursor
        limit: Maximum number of errors to return
    """
    # NerdGraph API uses a different URL and approach
    nerdgraph_url = "https://api.newrelic.com/graphql"
    
    # Create headers for NerdGraph API
    headers = {
        "API-Key": API_KEY,
        "Content-Type": "application/json"
    }
    
    # GraphQL query to list errors
    graphql_query = """
    query($accountId: Int!, $filters: ErrorTrackingFilterInput, $cursor: String) {
      actor {
        account(id: $accountId) {
          errorTracking {
            errors(filters: $filters, cursor: $cursor) {
              results {
                id
                message
                attributes {
                  ... on ErrorTrackingErrorAttribute {
                    key
                    value
                  }
                }
                entityGuid
                occurrences
                occurrenceLocation {
                  file
                  lineNumber
                  columnNumber
                }
                stackTrace {
                  formatted
                }
                firstSeen
                lastSeen
              }
              pageInfo {
                hasNextPage
                endCursor
              }
            }
          }
        }
      }
    }
    """
    
    variables = {
        "accountId": account_id,
        "filters": {},
        "cursor": cursor
    }
    
    if query:
        variables["filters"]["searchQuery"] = query
    
    data = {
        "query": graphql_query,
        "variables": variables
    }
    
    async with httpx.AsyncClient() as client:
        response = await client.post(nerdgraph_url, headers=headers, json=data)
        response.raise_for_status()
        return json.dumps(response.json(), indent=2)

@mcp.tool()
async def get_error_details(
    account_id: int,
    error_id: str
) -> str:
    """
    Get details for a specific error.
    
    Args:
        account_id: New Relic account ID
        error_id: Error ID
    """
    # NerdGraph API uses a different URL and approach
    nerdgraph_url = "https://api.newrelic.com/graphql"
    
    # Create headers for NerdGraph API
    headers = {
        "API-Key": API_KEY,
        "Content-Type": "application/json"
    }
    
    # GraphQL query to get error details
    graphql_query = """
    query($accountId: Int!, $errorId: ID!) {
      actor {
        account(id: $accountId) {
          errorTracking {
            error(id: $errorId) {
              id
              message
              entityGuid
              occurrences
              occurrenceLocation {
                file
                lineNumber
                columnNumber
              }
              attributes {
                ... on ErrorTrackingErrorAttribute {
                  key
                  value
                }
              }
              stackTrace {
                formatted
                rawTrace
              }
              firstSeen
              lastSeen
            }
          }
        }
      }
    }
    """
    
    variables = {
        "accountId": account_id,
        "errorId": error_id
    }
    
    data = {
        "query": graphql_query,
        "variables": variables
    }
    
    async with httpx.AsyncClient() as client:
        response = await client.post(nerdgraph_url, headers=headers, json=data)
        response.raise_for_status()
        return json.dumps(response.json(), indent=2)

# Account Settings and Management
@mcp.tool()
async def list_accounts() -> str:
    """
    List all New Relic accounts the API key has access to.
    """
    # NerdGraph API uses a different URL and approach
    nerdgraph_url = "https://api.newrelic.com/graphql"
    
    # Create headers for NerdGraph API
    headers = {
        "API-Key": API_KEY,
        "Content-Type": "application/json"
    }
    
    # GraphQL query to list accounts
    query = """
    {
      actor {
        accounts {
          id
          name
          reportingEventTypes
        }
      }
    }
    """
    
    data = {"query": query}
    
    async with httpx.AsyncClient() as client:
        response = await client.post(nerdgraph_url, headers=headers, json=data)
        response.raise_for_status()
        return json.dumps(response.json(), indent=2)

@mcp.tool()
async def get_account_users(account_id: int) -> str:
    """
    Get users associated with a New Relic account.
    
    Args:
        account_id: New Relic account ID
    """
    # NerdGraph API uses a different URL and approach
    nerdgraph_url = "https://api.newrelic.com/graphql"
    
    # Create headers for NerdGraph API
    headers = {
        "API-Key": API_KEY,
        "Content-Type": "application/json"
    }
    
    # GraphQL query to get account users
    query = """
    {
      actor {
        account(id: %d) {
          users {
            authenticationDomains {
              name
              users {
                id
                name
                email
                lastActive
                groups {
                  displayName
                }
              }
            }
          }
        }
      }
    }
    """ % account_id
    
    data = {"query": query}
    
    async with httpx.AsyncClient() as client:
        response = await client.post(nerdgraph_url, headers=headers, json=data)
        response.raise_for_status()
        return json.dumps(response.json(), indent=2)

# APM Application Deployment Marker Prompt
@mcp.prompt()
def deployment_recommendations(app_id: int, deployment_id: int) -> str:
    """
    Prompt for generating deployment recommendations.
    
    Args:
        app_id: Application ID
        deployment_id: Deployment ID
    """
    return f"""Please analyze deployment {deployment_id} for application with ID {app_id} and provide recommendations.

I need to understand:
1. The impact of this deployment on application performance
2. Any new errors or issues introduced by this deployment
3. Comparison of key metrics before and after the deployment
4. Apdex score changes

Based on this analysis, please provide:
- A summary of the deployment's impact
- Recommendations for addressing any negative effects
- Suggestions for future deployments to minimize risks
- A recommendation on whether to roll back or keep this deployment"""

# Add prompt templates
@mcp.prompt()
def analyze_application_performance(app_id: int) -> str:
    """
    Prompt for analyzing the performance of a specific application.
    
    Args:
        app_id: Application ID to analyze
    """
    return f"""Please analyze the performance of the New Relic application with ID {app_id}.

Focus on:
1. Response time trends
2. Error rates
3. Throughput patterns
4. Apdex score interpretation
5. Any concerning metrics or potential bottlenecks

Give specific, actionable recommendations for performance improvements based on the metrics."""

@mcp.prompt()
def investigate_alert_incident(incident_id: int) -> str:
    """
    Prompt for investigating an alert incident.
    
    Args:
        incident_id: Incident ID to investigate
    """
    return f"""Please help me investigate New Relic alert incident {incident_id}.

I need to understand:
1. What conditions triggered this incident
2. The affected applications or services
3. The timeline of the incident
4. The severity and impact
5. Any related historical patterns

Based on the available information, please provide:
- A root cause analysis
- Possible remediation steps
- Recommendations to prevent similar incidents"""

@mcp.prompt()
def compare_environments(prod_app_id: int, staging_app_id: int) -> str:
    """
    Prompt for comparing performance between production and staging environments.
    
    Args:
        prod_app_id: Production application ID
        staging_app_id: Staging application ID
    """
    return f"""Please compare the performance metrics between our production application (ID: {prod_app_id}) and staging application (ID: {staging_app_id}).

I need to understand:
1. Key differences in response times, throughput, and error rates
2. Significant disparities in resource utilization
3. Whether staging accurately represents production load characteristics
4. Any concerning metrics that appear in one environment but not the other

Please provide recommendations on:
- Improving staging to better represent production
- Potential optimizations based on the differences observed
- Any metrics that suggest problems in the production deployment pipeline"""

@mcp.prompt()
def deployment_analysis(app_id: int, days: int = 7) -> str:
    """
    Prompt for analyzing the impact of recent deployments.
    
    Args:
        app_id: Application ID
        days: Number of days of deployment history to analyze
    """
    return f"""Please analyze the impact of deployments over the past {days} days for application ID {app_id}.

I need to understand:
1. The correlation between deployments and performance changes
2. Any deployments that caused significant errors or performance degradation
3. The overall stability trend following deployments
4. How our deployment patterns affect user experience (Apdex)

Please provide:
- A summary of each significant deployment and its impact
- Patterns or trends across deployments
- Recommendations for improving our deployment process and reducing negative impacts"""

# Run the server if executed directly
if __name__ == "__main__":
    mcp.run(transport='stdio')