import os
from datetime import datetime, timedelta
import urllib.parse

from mcp.server.fastmcp import FastMCP, Context
from prometheus_api_client import PrometheusConnect
from dotenv import load_dotenv
from typing import Dict, List, Any, Optional, Union, Literal
from pydantic import BaseModel, Field, validator, ValidationError

class PrometheusResponse(BaseModel):
    status: str
    data: Optional[Dict[str, Any]] = None
    error: Optional[str] = None

class MetricLabel(BaseModel):
    name: str
    value: str

class MetricValue(BaseModel):
    timestamp: float
    value: str

class Metric(BaseModel):
    metric: Dict[str, str]
    values: Optional[List[List[Union[float, str]]]] = None  # For matrix results
    value: Optional[List[Union[float, str]]] = None  # For vector results

class QueryMetricsInput(BaseModel):
    query: str
    time: Optional[str] = None
    timeout: Optional[float] = None
    start: Optional[str] = None
    end: Optional[str] = None
    step: Optional[str] = None

class FindMetricsInput(BaseModel):
    pattern: str
    limit: int = 50

class AnalyzeMetricInput(BaseModel):
    metric: str
    duration: str = "1h"
    aggregation: Optional[str] = None
    labels: Optional[str] = None

    @validator('aggregation')
    def validate_aggregation(cls, v):
        if v is not None and v.lower() not in ['sum', 'avg', 'min', 'max', 'count']:
            raise ValueError(f"Unsupported aggregation function: {v}. Use sum, avg, min, max, or count.")
        return v

    @validator('duration')
    def validate_duration(cls, v):
        if not v[-1].lower() in ['h', 'd', 'w']:
            raise ValueError(f"Unsupported time unit: {v[-1]}. Use h (hours), d (days), or w (weeks).")
        try:
            int(v[:-1])
        except ValueError:
            raise ValueError(f"Invalid duration format: {v}. Use format like '1h', '2d', etc.")
        return v

class GetTargetsHealthInput(BaseModel):
    state: Optional[str] = None

    @validator('state')
    def validate_state(cls, v):
        if v is not None and v.lower() not in ['up', 'down']:
            raise ValueError(f"Invalid state filter: {v}. Use 'up' or 'down'.")
        return v

class GetAlertSummaryInput(BaseModel):
    state: Optional[str] = None

    @validator('state')
    def validate_state(cls, v):
        if v is not None and v.lower() not in ['firing', 'pending', 'inactive']:
            raise ValueError(f"Invalid state filter: {v}. Use 'firing', 'pending', or 'inactive'.")
        return v

class PerformanceAnalysisInput(BaseModel):
    service: str
    duration: str = "1d"

    @validator('duration')
    def validate_duration(cls, v):
        if not v[-1].lower() in ['h', 'd', 'w']:
            raise ValueError(f"Unsupported time unit: {v[-1]}. Use h (hours), d (days), or w (weeks).")
        try:
            int(v[:-1])
        except ValueError:
            raise ValueError(f"Invalid duration format: {v}. Use format like '1h', '2d', etc.")
        return v

class CapacityPlanningInput(BaseModel):
    service: str
    growth_rate: float = 10.0

class AlertInvestigationInput(BaseModel):
    alert_name: str

class Target(BaseModel):
    scrapeUrl: str
    health: str
    labels: Dict[str, str]
    lastScrape: str
    lastError: Optional[str] = None
    scrapeInterval: Optional[str] = None

class TargetsResponse(BaseModel):
    activeTargets: List[Target]

class Alert(BaseModel):
    labels: Dict[str, str]
    state: str
    annotations: Dict[str, str]
    activeAt: Optional[str] = None

class AlertsResponse(BaseModel):
    alerts: List[Alert]

class Rule(BaseModel):
    name: str
    type: str
    query: str
    labels: Optional[Dict[str, str]] = None
    annotations: Optional[Dict[str, str]] = None

class RuleGroup(BaseModel):
    name: str
    rules: List[Rule]

class RulesResponse(BaseModel):
    groups: List[RuleGroup]

class Series(BaseModel):
    __name__: str
    labels: Dict[str, str]

class SeriesResponse(BaseModel):
    data: List[Series]

class QueryResult(BaseModel):
    resultType: str
    result: List[Metric]

class QueryResponse(BaseModel):
    status: str
    data: QueryResult
    error: Optional[str] = None

load_dotenv()

# Create an MCP server
mcp = FastMCP("Prometheus", dependencies=["httpx"])

# Configuration
PROMETHEUS_URL = os.environ.get("PROMETHEUS_URL")
DEFAULT_TIMEOUT = 30.0  # seconds

prometheus_client = PrometheusConnect(
    url=PROMETHEUS_URL,
    disable_ssl=False
)

# Helper functions
async def make_prometheus_request(endpoint: str, params: Dict[str, Any]) -> Dict[str, Any]:
    """Make a request to the Prometheus API with proper error handling."""
    try:
        if endpoint == "query":
            result = prometheus_client.custom_query(query=params["query"])
            return {"status": "success", "data": {"resultType": "vector", "result": result}}
        elif endpoint == "query_range":
            result = prometheus_client.custom_query_range(
                query=params["query"],
                start_time=params["start"],
                end_time=params["end"],
                step=params["step"]
            )
            return {"status": "success", "data": {"resultType": "matrix", "result": result}}
        # Add handlers for other endpoints as needed
        return {"status": "error", "error": f"Unsupported endpoint: {endpoint}"}
    except Exception as e:
        return {"status": "error", "error": str(e)}


# Resources
@mcp.resource("prometheus://targets")
async def get_targets() -> str:
    """Get all Prometheus targets (scrape endpoints) and their status."""
    data = await make_prometheus_request("targets", {})
    
    try:
        response_model = PrometheusResponse(**data)
        if response_model.status == "error":
            return f"Error fetching targets: {response_model.error}"
    except ValidationError as e:
        return f"Response validation error: {str(e)}"
        
    active_targets = data.get("data", {}).get("activeTargets", [])
    
    result = "# Prometheus Targets\n\n"
    result += "| Target | State | Labels | Last Scrape |\n"
    result += "| ------ | ----- | ------ | ----------- |\n"
    
    for target in active_targets:
        labels = ", ".join([f"{k}={v}" for k, v in target.get("labels", {}).items()])
        result += f"| {target.get('scrapeUrl')} | {target.get('health')} | {labels} | {target.get('lastScrape')} |\n"
    
    return result


@mcp.resource("prometheus://alerts")
async def get_alerts() -> str:
    """Get all current Prometheus alerts."""
    data = await make_prometheus_request("alerts", {})
    
    try:
        response_model = PrometheusResponse(**data)
        if response_model.status == "error":
            return f"Error fetching alerts: {response_model.error}"
    except ValidationError as e:
        return f"Response validation error: {str(e)}"
    
    alerts = data.get("data", {}).get("alerts", [])
    
    result = "# Prometheus Alerts\n\n"
    
    if not alerts:
        return result + "No active alerts.\n"
    
    result += "| Alert | State | Labels | Annotations |\n"
    result += "| ----- | ----- | ------ | ----------- |\n"
    
    for alert in alerts:
        labels = ", ".join([f"{k}={v}" for k, v in alert.get("labels", {}).items()])
        annotations = ", ".join([f"{k}={v}" for k, v in alert.get("annotations", {}).items()])
        result += f"| {alert.get('labels', {}).get('alertname', 'Unknown')} | {alert.get('state')} | {labels} | {annotations} |\n"
    
    return result


@mcp.resource("prometheus://rules")
async def get_rules() -> str:
    """Get all Prometheus rules (recording rules and alerting rules)."""
    data = await make_prometheus_request("rules", {})
    
    try:
        response_model = PrometheusResponse(**data)
        if response_model.status == "error":
            return f"Error fetching rules: {response_model.error}"
    except ValidationError as e:
        return f"Response validation error: {str(e)}"
    
    groups = data.get("data", {}).get("groups", [])
    
    result = "# Prometheus Rules\n\n"
    
    for group in groups:
        result += f"## Group: {group.get('name')}\n\n"
        
        # Processing rules in the group
        for rule in group.get("rules", []):
            rule_type = rule.get("type")
            result += f"### {rule_type.title()} Rule: {rule.get('name')}\n\n"
            
            if rule_type == "recording":
                result += f"Expression: `{rule.get('query')}`\n\n"
            elif rule_type == "alerting":
                result += f"Expression: `{rule.get('query')}`\n\n"
                
                # Add alert specific information
                for k, v in rule.get("labels", {}).items():
                    result += f"- {k}: {v}\n"
                
                for k, v in rule.get("annotations", {}).items():
                    result += f"- {k}: {v}\n"
            
            result += "\n"
    
    return result


# Dynamic resource to fetch metrics by name pattern
@mcp.resource("prometheus://metrics/{pattern}")
async def get_metrics(pattern: str) -> str:
    """Get metrics matching the specified pattern using the label_values API."""
    # URL decode the pattern
    pattern = urllib.parse.unquote(pattern)
    
    # Use the series API to find metrics matching the pattern
    data = await make_prometheus_request("series", {"match[]": f"{pattern}"})
    
    try:
        response_model = PrometheusResponse(**data)
        if response_model.status == "error":
            return f"Error fetching metrics: {response_model.error}"
    except ValidationError as e:
        return f"Response validation error: {str(e)}"
    
    series = data.get("data", [])
    
    result = f"# Prometheus Metrics matching '{pattern}'\n\n"
    
    if not series:
        return result + "No metrics found matching this pattern.\n"
    
    # Group by metric name
    metrics_by_name = {}
    for s in series:
        name = s.get("__name__", "unknown")
        if name not in metrics_by_name:
            metrics_by_name[name] = []
        metrics_by_name[name].append(s)
    
    # Format the results
    for name, instances in metrics_by_name.items():
        result += f"## {name}\n\n"
        
        # Show a sample of label combinations
        result += "Sample label combinations:\n\n"
        for i, instance in enumerate(instances[:5]):  # Limit to 5 examples
            label_str = ", ".join([f"{k}={v}" for k, v in instance.items() if k != "__name__"])
            result += f"- {label_str}\n"
        
        if len(instances) > 5:
            result += f"- ... and {len(instances) - 5} more\n"
        
        result += "\n"
    
    return result


# Tools
@mcp.tool()
async def query_metrics(
    query: str,
    time: Optional[str] = None,
    timeout: Optional[float] = None,
    start: Optional[str] = None,
    end: Optional[str] = None,
    step: Optional[str] = None
) -> str:
    try:
        input_model = QueryMetricsInput(
            query=query,
            time=time,
            timeout=timeout,
            start=start,
            end=end,
            step=step
        )
    except ValidationError as e:
        return f"Input validation error: {str(e)}"
    """
    Query Prometheus using PromQL.
    
    Args:
        query: PromQL query string
        time: Evaluation timestamp (rfc3339 or unix timestamp), default: current time
        timeout: Evaluation timeout in seconds, default: server-side timeout
        start: Start timestamp for range queries (rfc3339 or unix timestamp)
        end: End timestamp for range queries (rfc3339 or unix timestamp)
        step: Query resolution step width for range queries (duration format or float seconds)
    """
    params = {"query": query}
    
    if time:
        params["time"] = time
    if timeout:
        params["timeout"] = str(timeout)
    
    # Determine if this is an instant query or range query
    if start and end:
        # This is a range query
        params["start"] = start
        params["end"] = end
        if step:
            params["step"] = step
        else:
            # Default step determination based on time range
            try:
                start_time = datetime.fromisoformat(start.replace('Z', '+00:00'))
                end_time = datetime.fromisoformat(end.replace('Z', '+00:00'))
                duration = (end_time - start_time).total_seconds()
                
                # Set a reasonable default step based on duration
                if duration <= 3600:  # 1 hour
                    params["step"] = "15s"
                elif duration <= 86400:  # 1 day
                    params["step"] = "5m"
                else:  # more than a day
                    params["step"] = "1h"
            except:
                # If parsing fails, use a reasonable default
                params["step"] = "5m"
        
        endpoint = "query_range"
    else:
        # This is an instant query
        endpoint = "query"
    
    data = await make_prometheus_request(endpoint, params)
    
    try:
        response_model = PrometheusResponse(**data)
        if response_model.status == "error":
            return f"Error executing query: {response_model.error}"
    except ValidationError as e:
        return f"Response validation error: {str(e)}"
    
    result_type = data.get("data", {}).get("resultType")
    results = data.get("data", {}).get("result", [])
    
    response = f"# Query Results\n\n"
    response += f"Query: `{query}`\n"
    response += f"Result Type: {result_type}\n\n"
    
    if result_type == "vector":
        # Instant vector result
        response += "| Metric | Value | Timestamp |\n"
        response += "| ------ | ----- | --------- |\n"
        
        for result in results:
            metric = str(result.get("metric", {}))
            value = result.get("value", ["", ""])[1]
            timestamp = datetime.fromtimestamp(result.get("value", [0, ""])[0]).strftime('%Y-%m-%d %H:%M:%S')
            response += f"| {metric} | {value} | {timestamp} |\n"
    
    elif result_type == "matrix":
        # Range vector result
        for result in results:
            metric = str(result.get("metric", {}))
            response += f"## {metric}\n\n"
            response += "| Timestamp | Value |\n"
            response += "| --------- | ----- |\n"
            
            values = result.get("values", [])
            
            # If there are too many values, sample them
            if len(values) > 20:
                sampling_rate = len(values) // 20 + 1
                values = values[::sampling_rate]
                response += "Note: Results are sampled to avoid excessive output.\n\n"
            
            for timestamp, value in values:
                time_str = datetime.fromtimestamp(timestamp).strftime('%Y-%m-%d %H:%M:%S')
                response += f"| {time_str} | {value} |\n"
            
            response += "\n"
    
    elif result_type == "scalar":
        # Scalar result
        timestamp, value = data.get("data", {}).get("result", [0, ""])
        time_str = datetime.fromtimestamp(timestamp).strftime('%Y-%m-%d %H:%M:%S')
        response += f"Scalar value: {value} at {time_str}\n"
    
    elif result_type == "string":
        # String result
        timestamp, value = data.get("data", {}).get("result", [0, ""])
        time_str = datetime.fromtimestamp(timestamp).strftime('%Y-%m-%d %H:%M:%S')
        response += f"String value: {value} at {time_str}\n"
    
    return response


@mcp.tool()
async def find_metrics(
    pattern: str,
    limit: int = 50
) -> str:
    """
    Find metrics matching a specified pattern.
    
    Args:
        pattern: Pattern to match against metric names (use .* as wildcard)
        limit: Maximum number of results to return
    """
    try:
        input_model = FindMetricsInput(
            pattern=pattern,
            limit=limit
        )
    except ValidationError as e:
        return f"Input validation error: {str(e)}"
    # Use the series API to find metrics matching the pattern
    data = await make_prometheus_request("series", {"match[]": f"{pattern}"})
    
    try:
        response_model = PrometheusResponse(**data)
        if response_model.status == "error":
            return f"Error finding metrics: {response_model.error}"
    except ValidationError as e:
        return f"Response validation error: {str(e)}"
    
    series = data.get("data", [])
    
    result = f"# Metrics matching '{pattern}'\n\n"
    
    if not series:
        return result + "No metrics found matching this pattern.\n"
    
    # Group by metric name
    metrics_by_name = {}
    for s in series:
        name = s.get("__name__", "unknown")
        if name not in metrics_by_name:
            metrics_by_name[name] = []
        metrics_by_name[name].append(s)
    
    # Format the results
    result += f"Found {len(metrics_by_name)} unique metric names (with {len(series)} total series):\n\n"
    
    # Sort by metric name
    sorted_metrics = sorted(metrics_by_name.items())
    
    # Apply limit
    if limit and len(sorted_metrics) > limit:
        result += f"Showing first {limit} metrics (out of {len(sorted_metrics)}):\n\n"
        sorted_metrics = sorted_metrics[:limit]
    
    for name, instances in sorted_metrics:
        result += f"## {name}\n\n"
        result += f"This metric has {len(instances)} series with different label combinations.\n\n"
        
        # Show a sample of label combinations
        result += "Sample label combinations:\n\n"
        for i, instance in enumerate(instances[:3]):  # Limit to 3 examples
            label_str = ", ".join([f"{k}={v}" for k, v in instance.items() if k != "__name__"])
            result += f"- {label_str}\n"
        
        if len(instances) > 3:
            result += f"- ... and {len(instances) - 3} more\n"
        
        result += "\n"
    
    return result


@mcp.tool()
async def analyze_metric(
    metric: str,
    duration: str = "1h",
    aggregation: Optional[str] = None,
    labels: Optional[str] = None,
) -> str:
    """
    Analyze a specific metric over time, including basic statistics.
    
    Args:
        metric: The name of the metric to analyze
        duration: Time duration to analyze (e.g., 1h, 1d, 7d)
        aggregation: Optional aggregation function (sum, avg, min, max)
        labels: Optional label filters in the format 'label1=value1,label2=value2'
    """
    try:
        input_model = AnalyzeMetricInput(
            metric=metric,
            duration=duration,
            aggregation=aggregation,
            labels=labels
        )
    except ValidationError as e:
        return f"Input validation error: {str(e)}"
    # Convert duration to start time
    now = datetime.now()
    
    # Parse the duration
    unit = duration[-1].lower()
    try:
        value = int(duration[:-1])
    except ValueError:
        return f"Invalid duration format: {duration}. Use format like '1h', '2d', etc."
    
    if unit == 'h':
        start_time = now - timedelta(hours=value)
    elif unit == 'd':
        start_time = now - timedelta(days=value)
    elif unit == 'w':
        start_time = now - timedelta(weeks=value)
    else:
        return f"Unsupported time unit: {unit}. Use h (hours), d (days), or w (weeks)."
    
    # Format times for Prometheus
    start_timestamp = start_time.isoformat()
    end_timestamp = now.isoformat()
    
    # Construct the query based on provided options
    query = metric
    
    # Add label filters if provided
    if labels:
        label_filters = []
        for label_pair in labels.split(','):
            if '=' in label_pair:
                key, value = label_pair.split('=', 1)
                label_filters.append(f'{key}="{value}"')
        
        if label_filters:
            query = f'{metric}{{{",".join(label_filters)}}}'
    
    # Add aggregation if provided
    if aggregation:
        if aggregation.lower() in ['sum', 'avg', 'min', 'max', 'count']:
            if aggregation.lower() == 'avg':
                # 'avg' is not a direct Prometheus function, use avg()
                query = f'avg({query})'
            else:
                query = f'{aggregation.lower()}({query})'
        else:
            return f"Unsupported aggregation function: {aggregation}. Use sum, avg, min, max, or count."
    
    # Execute the range query
    params = {
        "query": query,
        "start": start_timestamp,
        "end": end_timestamp,
        "step": calculate_step(start_time, now)
    }
    
    data = await make_prometheus_request("query_range", params)
    
    try:
        response_model = PrometheusResponse(**data)
        if response_model.status == "error":
            return f"Error analyzing metric: {response_model.error}"
    except ValidationError as e:
        return f"Response validation error: {str(e)}"
    
    result_type = data.get("data", {}).get("resultType")
    results = data.get("data", {}).get("result", [])
    
    response = f"# Analysis of '{metric}' over {duration}\n\n"
    
    if not results:
        return response + "No data found for this metric with the given parameters.\n"
    
    for result_idx, result in enumerate(results):
        metric_labels = result.get("metric", {})
        values = result.get("values", [])
        
        if not values:
            continue
        
        # Format metric information
        if metric_labels:
            label_str = ", ".join([f"{k}={v}" for k, v in metric_labels.items() if k != "__name__"])
            response += f"## Series {result_idx+1}: {label_str}\n\n"
        else:
            response += f"## Series {result_idx+1}\n\n"
        
        # Extract values for analysis
        timestamps = [v[0] for v in values]
        numeric_values = []
        
        for _, val in values:
            try:
                numeric_values.append(float(val))
            except (ValueError, TypeError):
                pass  # Skip non-numeric values
        
        if not numeric_values:
            response += "No numeric values available for analysis.\n\n"
            continue
        
        # Calculate basic statistics
        min_value = min(numeric_values)
        max_value = max(numeric_values)
        avg_value = sum(numeric_values) / len(numeric_values)
        
        # Calculate change and rate
        first_value = numeric_values[0]
        last_value = numeric_values[-1]
        absolute_change = last_value - first_value
        
        if first_value != 0:
            percent_change = (absolute_change / abs(first_value)) * 100
        else:
            percent_change = float('inf') if absolute_change > 0 else float('-inf') if absolute_change < 0 else 0
        
        time_range_seconds = timestamps[-1] - timestamps[0]
        if time_range_seconds > 0:
            rate_of_change = absolute_change / time_range_seconds
        else:
            rate_of_change = 0
        
        # Find time of minimum and maximum values
        min_idx = numeric_values.index(min_value)
        max_idx = numeric_values.index(max_value)
        min_time = datetime.fromtimestamp(timestamps[min_idx]).strftime('%Y-%m-%d %H:%M:%S')
        max_time = datetime.fromtimestamp(timestamps[max_idx]).strftime('%Y-%m-%d %H:%M:%S')
        
        # Format the statistics
        response += "### Basic Statistics\n\n"
        response += f"- **Minimum**: {min_value:.6g} (at {min_time})\n"
        response += f"- **Maximum**: {max_value:.6g} (at {max_time})\n"
        response += f"- **Average**: {avg_value:.6g}\n"
        response += f"- **First Value**: {first_value:.6g}\n"
        response += f"- **Last Value**: {last_value:.6g}\n"
        response += f"- **Absolute Change**: {absolute_change:.6g}\n"
        
        if not (abs(percent_change) == float('inf') or (percent_change == 0 and first_value == 0)):
            response += f"- **Percent Change**: {percent_change:.2f}%\n"
        
        response += f"- **Rate of Change**: {rate_of_change:.6g} per second\n\n"
        
        # Add more details based on the number of data points
        if len(numeric_values) > 1:
            response += "### Additional Insights\n\n"
            
            # Detect trends
            if absolute_change > 0:
                trend = "increasing"
            elif absolute_change < 0:
                trend = "decreasing"
            else:
                trend = "stable"
            
            response += f"- The metric is {trend} over the analyzed period.\n"
            
            # Check for stability
            if max_value - min_value < 0.05 * abs(avg_value) and abs(avg_value) > 0:
                response += "- The metric shows stable behavior with low variance.\n"
            elif max_value - min_value > 0.5 * abs(avg_value) and abs(avg_value) > 0:
                response += "- The metric shows high variability over the period.\n"
        
        response += "\n"
        
        # If there are multiple series, limit to 5 to avoid excessive output
        if result_idx >= 4 and len(results) > 5:
            response += f"... and {len(results) - 5} more series (output truncated to avoid excessive length)\n"
            break
    
    # Add query information
    response += "### Query Details\n\n"
    response += f"- **Query**: `{query}`\n"
    response += f"- **Time Range**: {start_time.strftime('%Y-%m-%d %H:%M:%S')} to {now.strftime('%Y-%m-%d %H:%M:%S')}\n"
    response += f"- **Duration**: {duration}\n"
    
    if aggregation:
        response += f"- **Aggregation**: {aggregation}\n"
    
    if labels:
        response += f"- **Label Filters**: {labels}\n"
    
    return response


@mcp.tool()
async def get_targets_health(
    state: Optional[str] = None
) -> str:
    """
    Get health status of all Prometheus targets.
    
    Args:
        state: Optional filter by target state ('up' or 'down')
    """
    try:
        input_model = GetTargetsHealthInput(state=state)
    except ValidationError as e:
        return f"Input validation error: {str(e)}"
    data = await make_prometheus_request("targets", {})
    
    try:
        response_model = PrometheusResponse(**data)
        if response_model.status == "error":
            return f"Error fetching targets: {response_model.error}"
    except ValidationError as e:
        return f"Response validation error: {str(e)}"
    
    active_targets = data.get("data", {}).get("activeTargets", [])
    
    # Filter by state if provided
    if state:
        state = state.lower()
        if state in ["up", "down"]:
            active_targets = [t for t in active_targets if t.get("health").lower() == state]
        else:
            return f"Invalid state filter: {state}. Use 'up' or 'down'."
    
    result = "# Prometheus Targets Health\n\n"
    
    if not active_targets:
        return result + "No matching targets found.\n"
    
    # Counts for summary
    up_count = sum(1 for t in active_targets if t.get("health").lower() == "up")
    down_count = sum(1 for t in active_targets if t.get("health").lower() == "down")
    
    result += f"## Summary\n\n"
    result += f"- **Total Targets**: {len(active_targets)}\n"
    result += f"- **Healthy (Up)**: {up_count}\n"
    result += f"- **Unhealthy (Down)**: {down_count}\n"
    
    if down_count > 0:
        result += f"\n## Unhealthy Targets\n\n"
        
        for target in active_targets:
            if target.get("health").lower() == "down":
                scrape_url = target.get("scrapeUrl")
                labels = ", ".join([f"{k}={v}" for k, v in target.get("labels", {}).items()])
                last_error = target.get("lastError", "")
                last_scrape = target.get("lastScrape")
                
                result += f"### {scrape_url}\n\n"
                result += f"- **Labels**: {labels}\n"
                result += f"- **Last Scrape**: {last_scrape}\n"
                
                if last_error:
                    result += f"- **Error**: {last_error}\n"
                
                result += "\n"
    
    result += "## All Targets\n\n"
    result += "| Target | State | Last Scrape | Scrape Duration |\n"
    result += "| ------ | ----- | ----------- | --------------- |\n"
    
    for target in active_targets:
        scrape_url = target.get("scrapeUrl")
        health = target.get("health")
        last_scrape = target.get("lastScrape")
        scrape_duration = target.get("scrapeInterval")
        
        result += f"| {scrape_url} | {health} | {last_scrape} | {scrape_duration} |\n"
    
    return result


@mcp.tool()
async def get_alert_summary(
    state: Optional[str] = None
) -> str:
    """
    Get a summary of all current Prometheus alerts.
    
    Args:
        state: Optional filter by alert state ('firing', 'pending', or 'inactive')
    """
    try:
        input_model = GetAlertSummaryInput(state=state)
    except ValidationError as e:
        return f"Input validation error: {str(e)}"
    
    data = await make_prometheus_request("alerts", {})
    
    try:
        response_model = PrometheusResponse(**data)
        if response_model.status == "error":
            return f"Error fetching alerts: {response_model.error}"
    except ValidationError as e:
        return f"Response validation error: {str(e)}"
    
    alerts = data.get("data", {}).get("alerts", [])
    
    # Filter by state if provided
    if state:
        state = state.lower()
        if state in ["firing", "pending", "inactive"]:
            alerts = [a for a in alerts if a.get("state").lower() == state]
        else:
            return f"Invalid state filter: {state}. Use 'firing', 'pending', or 'inactive'."
    
    result = "# Prometheus Alerts Summary\n\n"
    
    if not alerts:
        return result + "No alerts matching the specified criteria.\n"
    
    # Count alerts by state
    firing_count = sum(1 for a in alerts if a.get("state").lower() == "firing")
    pending_count = sum(1 for a in alerts if a.get("state").lower() == "pending")
    inactive_count = sum(1 for a in alerts if a.get("state").lower() == "inactive")
    
    result += "## Summary\n\n"
    result += f"- **Total Alerts**: {len(alerts)}\n"
    result += f"- **Firing**: {firing_count}\n"
    result += f"- **Pending**: {pending_count}\n"
    result += f"- **Inactive**: {inactive_count}\n\n"
    
    # Group alerts by name
    alerts_by_name = {}
    for alert in alerts:
        name = alert.get("labels", {}).get("alertname", "Unknown")
        if name not in alerts_by_name:
            alerts_by_name[name] = []
        alerts_by_name[name].append(alert)
    
    # Sort by alert name
    sorted_alerts = sorted(alerts_by_name.items())
    
    for name, alert_group in sorted_alerts:
        result += f"## {name}\n\n"
        
        # Count states within this alert group
        group_firing = sum(1 for a in alert_group if a.get("state").lower() == "firing")
        group_pending = sum(1 for a in alert_group if a.get("state").lower() == "pending")
        
        result += f"- **Instances**: {len(alert_group)}\n"
        result += f"- **Firing**: {group_firing}\n"
        result += f"- **Pending**: {group_pending}\n\n"
        
        # Get a sample alert to extract common information
        sample_alert = alert_group[0]
        
        # Extract annotations
        annotations = sample_alert.get("annotations", {})
        if annotations:
            result += "### Description\n\n"
            
            if "summary" in annotations:
                result += f"{annotations['summary']}\n\n"
            
            if "description" in annotations:
                result += f"{annotations['description']}\n\n"
        
        # Show detailed instances if there are any firing or pending
        if group_firing > 0 or group_pending > 0:
            result += "### Active Instances\n\n"
            result += "| State | Labels | Active Since |\n"
            result += "| ----- | ------ | ------------ |\n"
            
            for alert in alert_group:
                if alert.get("state").lower() in ["firing", "pending"]:
                    state = alert.get("state")
                    labels = ", ".join([f"{k}={v}" for k, v in alert.get("labels", {}).items() 
                                      if k != "alertname"])
                    active_since = alert.get("activeAt", "Unknown")
                    
                    result += f"| {state} | {labels} | {active_since} |\n"
            
            result += "\n"
    
    return result


# Prompts
@mcp.prompt()
def analyze_system_health() -> str:
    """Prompt to analyze overall system health based on Prometheus metrics."""
    return """
Please analyze the overall health of my systems monitored by Prometheus.
Focus on:
1. Any firing alerts
2. Down targets
3. CPU, memory, and disk usage
4. Network performance
5. Application-specific metrics

Provide a comprehensive health assessment with recommendations for any issues found.
"""


@mcp.prompt()
def performance_analysis(service: str, duration: str = "1d") -> str:
    """
    Prompt to analyze performance of a specific service over time.
    
    Args:
        service: The name of the service to analyze
        duration: Time duration to analyze (e.g., 1h, 1d, 7d)
    """
    return f"""
Please analyze the performance of the "{service}" service over the past {duration}.
Focus on:
1. Response times and latency
2. Error rates
3. Resource usage (CPU, memory)
4. Request volume/throughput
5. Any performance degradation or improvements

Provide a detailed analysis with comparisons to normal baselines when possible.
"""


@mcp.prompt()
def capacity_planning(service: str, growth_rate: float = 10.0) -> str:
    """
    Prompt to help with capacity planning based on current metrics.
    
    Args:
        service: The name of the service to analyze
        growth_rate: Expected growth rate in percentage
    """
    return f"""
Please help me plan capacity for the "{service}" service assuming a {growth_rate}% growth rate.
Focus on:
1. Current resource utilization
2. Resource usage trends over the past 7 days
3. Projected resource needs based on the growth rate
4. Recommendations for scaling and resource allocation
5. Potential bottlenecks to address

Use Prometheus metrics to provide evidence-based planning recommendations.
"""


@mcp.prompt()
def alert_investigation(alert_name: str) -> str:
    """
    Prompt to investigate a specific alert and recommend actions.
    
    Args:
        alert_name: The name of the alert to investigate
    """
    return f"""
Please investigate the "{alert_name}" alert that is currently firing.
Focus on:
1. The root cause of the alert
2. Systems and services affected
3. Historical patterns of this alert
4. Potential remediation steps
5. Long-term fixes to prevent recurrence

Use Prometheus metrics and graphs to analyze the situation and provide actionable recommendations.
"""


# Helper functions
def calculate_step(start_time: datetime, end_time: datetime) -> str:
    """Calculate an appropriate step size based on the time range."""
    duration = (end_time - start_time).total_seconds()
    
    if duration <= 3600:  # 1 hour
        return "15s"
    elif duration <= 86400:  # 1 day
        return "5m"
    elif duration <= 604800:  # 1 week
        return "1h"
    else:  # more than a week
        return "4h"


# Main entry point
if __name__ == "__main__":
    # Initialize and run the server
    mcp.run(transport='stdio')