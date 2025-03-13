# newrelic_mcp_server.py
from typing import Dict, List, Optional, Any, Union
import os
import httpx
import json
from datetime import datetime, timedelta
from mcp.server.fastmcp import FastMCP, Context

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
    return json.dumps(response, indent=2)

@mcp.tool()
async def get_application(app_id: int) -> str:
    """
    Get details for a specific application.
    
    Args:
        app_id: Application ID
    """
    response = await make_request("get", f"/applications/{app_id}.json")
    return json.dumps(response, indent=2)

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
    settings = {}
    if app_apdex_threshold is not None:
        settings["app_apdex_threshold"] = app_apdex_threshold
    if end_user_apdex_threshold is not None:
        settings["end_user_apdex_threshold"] = end_user_apdex_threshold
    if enable_real_user_monitoring is not None:
        settings["enable_real_user_monitoring"] = enable_real_user_monitoring
    
    data = {"application": {}}
    if name:
        data["application"]["name"] = name
    if settings:
        data["application"]["settings"] = settings
    
    response = await make_request("put", f"/applications/{app_id}.json", data=data)
    return json.dumps(response, indent=2)

@mcp.tool()
async def delete_application(app_id: int) -> str:
    """
    Delete an application.
    
    Args:
        app_id: Application ID
    """
    response = await make_request("delete", f"/applications/{app_id}.json")
    return json.dumps(response, indent=2)

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
    return json.dumps(response, indent=2)

@mcp.tool()
async def create_alert_policy(name: str, incident_preference: str) -> str:
    """
    Create an alert policy.
    
    Args:
        name: Policy name
        incident_preference: Incident rollup preference (PER_POLICY, PER_CONDITION, or PER_CONDITION_AND_TARGET)
    """
    data = {
        "policy": {
            "name": name,
            "incident_preference": incident_preference
        }
    }
    
    response = await make_request("post", "/alerts_policies.json", data=data)
    return json.dumps(response, indent=2)

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
    data = {"policy": {}}
    if name:
        data["policy"]["name"] = name
    if incident_preference:
        data["policy"]["incident_preference"] = incident_preference
    
    response = await make_request("put", f"/alerts_policies/{policy_id}.json", data=data)
    return json.dumps(response, indent=2)

@mcp.tool()
async def delete_alert_policy(policy_id: int) -> str:
    """
    Delete an alert policy.
    
    Args:
        policy_id: Policy ID
    """
    response = await make_request("delete", f"/alerts_policies/{policy_id}.json")
    return json.dumps(response, indent=2)

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

@mcp.resource("nr://alerts/incidents")
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

@mcp.resource("nr://alerts/violations")
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