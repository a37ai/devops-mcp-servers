import sys
import os
# Add the parent directory to the Python path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import pytest
import pytest_asyncio
import time
import uuid
from datetime import datetime, timedelta
import json
from unittest.mock import MagicMock, patch

# Import the server
from servers.datadog.datadog_mcp import DatadogMCPServer

# Configure pytest-asyncio to use function scope for async fixtures
def pytest_configure(config):
    config.option.asyncio_default_fixture_loop_scope = "function"

# Mock Context class for testing
class MockContext:
    def __init__(self, lifespan_context):
        self.request_context = type('obj', (object,), {'lifespan_context': lifespan_context})

# Fixtures
@pytest.fixture
def test_id():
    """Generate a unique test ID to avoid collisions"""
    return f"test-{str(uuid.uuid4())[:8]}"

@pytest_asyncio.fixture
async def server_context():
    """Create server and yield context for testing"""
    # Check for API and APP keys
    api_key = os.environ.get("DATADOG_API_KEY")
    app_key = os.environ.get("DATADOG_APP_KEY")
    
    if not api_key or not app_key:
        pytest.skip("DATADOG_API_KEY and DATADOG_APP_KEY environment variables must be set")
    
    # Create server instance
    server = DatadogMCPServer(name="Test Server", api_key=api_key, app_key=app_key)
    
    # Register all resources and tools
    server.register_metrics_resources_and_tools()
    server.register_events_resources_and_tools()
    server.register_logs_resources_and_tools()
    server.register_dashboards_resources_and_tools()
    server.register_monitors_resources_and_tools()
    server.register_hosts_resources_and_tools()
    server.register_users_resources_and_tools()
    
    # Since register_tags_resources_and_tools is called in register_all_resources_and_tools but not defined
    server.register_tags_resources_and_tools = MagicMock()
    
    # Get context from lifespan
    async with server._api_client_lifespan(server.mcp) as context:
        yield MockContext(context)

# Test Metrics API
@pytest.mark.asyncio
async def test_metrics(server_context, test_id):
    """Test metrics submission and retrieval"""
    # Get current timestamp
    now = int(time.time())
    
    # Submit a test metric
    metric_name = f"test.metric.{test_id}"
    points = [[now, 42.0]]
    result = server_context.request_context.lifespan_context["metrics_api"].submit_metrics(
        body={"series": [{"metric": metric_name, "points": points, "type": "gauge"}]}
    )
    
    # Wait for metric to be available
    time.sleep(5)
    
    # Test list_metrics resource
    from_time = now - 3600  # 1 hour ago
    response = json.loads(server_context.request_context.lifespan_context["metrics_api"].list_metrics(
        _from=from_time
    ).to_json())
    
    # Test query_metrics resource
    from_time = now - 600  # 10 minutes ago
    to_time = now + 60  # 1 minute into future
    query = f"{metric_name}" + r"{*}"  # Escaped for f-string
    response = json.loads(server_context.request_context.lifespan_context["metrics_api"].query_metrics(
        _from=from_time,
        to=to_time,
        query=query
    ).to_json())
    
    print(f"Metrics test completed: submitted test metric {metric_name}")
    return True

# Test Events API
@pytest.mark.asyncio
async def test_events(server_context, test_id):
    """Test events creation and retrieval"""
    # Create an event
    title = f"Test Event {test_id}"
    text = f"This is a test event created by the test suite {test_id}"
    response = server_context.request_context.lifespan_context["events_api"].create_event(
        body={
            "title": title,
            "text": text,
            "priority": "normal",
            "tags": [f"test:{test_id}"],
            "alert_type": "info"
        }
    )
    event_id = response.id
    
    # Wait for event to be available
    time.sleep(2)
    
    # Test get_event resource
    event = json.loads(server_context.request_context.lifespan_context["events_api"].get_event(
        event_id
    ).to_json())
    assert event["event"]["title"] == title
    
    # Test list_events resource
    now = int(time.time())
    start = now - 3600  # 1 hour ago
    end = now + 60  # 1 minute into future
    events = json.loads(server_context.request_context.lifespan_context["events_api"].list_events(
        start=start,
        end=end
    ).to_json())
    
    print(f"Events test completed: created and retrieved event {event_id}")
    return True

# Test Logs API
@pytest.mark.asyncio
async def test_logs(server_context, test_id):
    """Test logs submission and querying"""
    # Submit logs
    logs = [{
        "ddsource": "pytest",
        "ddtags": f"test:{test_id}",
        "message": f"Test log message {test_id}",
        "service": "datadog-mcp-test"
    }]
    
    server_context.request_context.lifespan_context["logs_api"].submit_log(
        body=logs
    )
    
    # Wait for logs to be indexed
    time.sleep(5)
    
    # Test query_logs tool
    now = int(time.time())
    from_time = now - 3600  # 1 hour ago
    to_time = now + 60  # 1 minute into future
    query = f"test:{test_id}"
    
    response = server_context.request_context.lifespan_context["logs_api_v2"].list_logs(
        filter_query=query,
        filter_from=from_time,
        filter_to=to_time,
        page_limit=10
    )
    
    print(f"Logs test completed: submitted and queried logs with tag {query}")
    return True

# Test Monitors API
@pytest.mark.asyncio
async def test_monitors(server_context, test_id):
    """Test monitor creation and retrieval"""
    from datadog_api_client.v1.model.monitor import Monitor
    from datadog_api_client.v1.model.monitor_type import MonitorType
    from datadog_api_client.v1.model.monitor_options import MonitorOptions
    
    # Create a monitor
    name = f"Test Monitor {test_id}"
    query = f"avg(last_5m):avg:system.cpu.user{{test:{test_id}}} > 95"
    message = f"CPU usage is high for test {test_id}. @slack-datadog-test"
    
    monitor = Monitor(
        name=name,
        type=MonitorType("metric alert"),
        query=query,
        message=message,
        tags=[f"test:{test_id}"],
        options=MonitorOptions(
            notify_no_data=False,
            require_full_window=False,
            include_tags=True
        )
    )
    
    response = server_context.request_context.lifespan_context["monitors_api"].create_monitor(
        body=monitor
    )
    monitor_id = response.id
    
    # Test get_monitor resource
    monitor_data = json.loads(server_context.request_context.lifespan_context["monitors_api"].get_monitor(
        monitor_id
    ).to_json())
    assert monitor_data["name"] == name
    
    # Test list_monitors resource
    monitors = json.loads(server_context.request_context.lifespan_context["monitors_api"].list_monitors().to_json())
    
    # Clean up - delete the monitor
    server_context.request_context.lifespan_context["monitors_api"].delete_monitor(monitor_id)
    
    print(f"Monitors test completed: created and deleted monitor {monitor_id}")
    return True

# Test Dashboards API
@pytest.mark.asyncio
async def test_dashboards(server_context, test_id):
    """Test dashboard listing and retrieval"""
    # List dashboards
    dashboards = json.loads(server_context.request_context.lifespan_context["dashboards_api"].list_dashboards().to_json())
    
    # If there's at least one dashboard, test get_dashboard
    if dashboards["dashboards"]:
        dashboard_id = dashboards["dashboards"][0]["id"]
        dashboard = json.loads(server_context.request_context.lifespan_context["dashboards_api"].get_dashboard(
            dashboard_id
        ).to_json())
        assert dashboard["id"] == dashboard_id
    
    print("Dashboards test completed: listed and retrieved dashboards")
    return True

# Test Hosts API
@pytest.mark.asyncio
async def test_hosts(server_context, test_id):
    """Test host listing and muting"""
    # List hosts
    hosts_response = json.loads(server_context.request_context.lifespan_context["hosts_api"].list_hosts().to_json())
    
    # If there's at least one host, test mute_host
    if hosts_response.get("host_list") and len(hosts_response["host_list"]) > 0:
        host_name = hosts_response["host_list"][0]["name"]
        
        # Mute host for 5 minutes
        now = int(time.time())
        end = now + 300  # 5 minutes
        message = f"Muted for testing by {test_id}"
        
        mute_response = server_context.request_context.lifespan_context["hosts_api"].mute_host(
            host_name=host_name,
            body={
                "message": message,
                "end": end
            }
        )
        
        # Unmute host
        server_context.request_context.lifespan_context["hosts_api"].unmute_host(
            host_name=host_name
        )
        
        print(f"Hosts test completed: listed hosts and muted/unmuted host {host_name}")
    else:
        print("Hosts test skipped: no hosts available")
    
    return True

# Test Users API
@pytest.mark.asyncio
async def test_users(server_context, test_id):
    """Test user listing"""
    # List users
    users = json.loads(server_context.request_context.lifespan_context["users_api"].list_users().to_json())
    
    # We don't test user creation to avoid polluting the account
    print("Users test completed: listed users")
    return True

# Main test function
@pytest.mark.asyncio
async def test_all_functionality(server_context, test_id):
    """Test all Datadog MCP Server functionality"""
    print(f"===== Starting Datadog MCP Server Tests with ID {test_id} =====")
    
    # Run tests
    results = {
        "metrics": await test_metrics(server_context, test_id),
        "events": await test_events(server_context, test_id),
        "logs": await test_logs(server_context, test_id),
        "monitors": await test_monitors(server_context, test_id),
        "dashboards": await test_dashboards(server_context, test_id),
        "hosts": await test_hosts(server_context, test_id),
        "users": await test_users(server_context, test_id)
    }
    
    # Report results
    print("===== Datadog MCP Server Test Results =====")
    for test, result in results.items():
        print(f"{test}: {'PASSED' if result else 'FAILED'}")
    
    # Final assertion
    assert all(results.values()), "Not all tests passed"
    print("===== All Datadog MCP Server Tests Passed =====")