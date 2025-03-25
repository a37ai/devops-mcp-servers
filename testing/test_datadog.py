#!/usr/bin/env python3
"""
Comprehensive test script for Datadog MCP server
Tests all major functionality with the provided credentials
"""
import os
import time
import json
import random
from datetime import datetime, timedelta


# Import the MCP server functions
from servers.datadog.datadog_mcp import (
    submit_metric,
    query_metrics,
    create_event,
    get_events,
    create_monitor,
    get_monitor,
    update_monitor,
    delete_monitor,
    create_dashboard,
    get_dashboard,
    delete_dashboard
)

def print_result(name, result):
    """Print test result in a formatted way"""
    print(f"\n{'='*20} {name} {'='*20}")
    try:
        # Try to parse and pretty print JSON
        parsed = json.loads(result)
        print(json.dumps(parsed, indent=2))
    except:
        # If not JSON, print as is
        print(result)
    print(f"{'='*50}\n")

def test_metrics():
    """Test metrics submission and querying"""
    print("\n🔍 Testing Metrics API...")
    
    # Generate unique metric name with timestamp to avoid conflicts
    timestamp = int(time.time())
    metric_name = f"test.metric.{timestamp}"
    value = random.uniform(1.0, 100.0)
    tags = ["test:true", "env:dev", f"test_run:{timestamp}"]
    
    # Submit metric
    result = submit_metric(metric_name, value, tags=tags)
    print_result("Submit Metric", result)
    
    # Wait for metric to be available for querying
    print("Waiting 5 seconds for metric to be available...")
    time.sleep(5)
    
    # Query metrics
    from_time = timestamp - 60
    to_time = timestamp + 60
    query = f"{metric_name}{{{tags[0]}}}"
    
    result = query_metrics(query, from_time, to_time)
    print_result("Query Metrics", result)
    
    return json.loads(result)

def test_events():
    """Test events creation and retrieval"""
    print("\n🔍 Testing Events API...")
    
    # Generate unique event with timestamp
    timestamp = int(time.time())
    title = f"Test Event {timestamp}"
    text = f"This is a test event created at {datetime.now().isoformat()}"
    tags = ["test:true", "env:dev", f"test_run:{timestamp}"]
    
    # Create event
    result = create_event(title, text, tags=tags, alert_type="info", priority="normal")
    print_result("Create Event", result)
    
    # Wait for event to be available
    print("Waiting 5 seconds for event to be available...")
    time.sleep(5)
    
    # Get events
    from_time = timestamp - 60
    to_time = timestamp + 60
    result = get_events(query=f"tags:{tags[0]}", from_time=from_time, to_time=to_time)
    print_result("Get Events", result)
    
    return json.loads(result)

def test_monitors():
    """Test monitors creation, retrieval, update and deletion"""
    print("\n🔍 Testing Monitors API...")
    
    # Generate unique monitor with timestamp
    timestamp = int(time.time())
    name = f"Test Monitor {timestamp}"
    query = "avg(last_5m):avg:system.cpu.user{*} > 75"
    message = f"CPU usage is high on {{host.name}}. Created at {datetime.now().isoformat()}"
    tags = ["test:true", "env:dev", f"test_run:{timestamp}"]
    
    # Create monitor
    result = create_monitor(name, query, "metric alert", message, tags=tags)
    print_result("Create Monitor", result)
    
    try:
        # Parse result to get monitor ID
        monitor_data = json.loads(result)
        monitor_id = monitor_data.get("data", {}).get("id")
        
        if not monitor_id:
            print("❌ Could not get monitor ID from response")
            return None
            
        # Get monitor
        result = get_monitor(monitor_id)
        print_result("Get Monitor", result)
        
        # Update monitor
        new_name = f"Updated Test Monitor {timestamp}"
        result = update_monitor(monitor_id, name=new_name)
        print_result("Update Monitor", result)
        
        # Delete monitor
        result = delete_monitor(monitor_id)
        print_result("Delete Monitor", result)
        
        return monitor_data
    except Exception as e:
        print(f"❌ Error in monitor test: {e}")
        return None

def test_dashboards():
    """Test dashboards creation, retrieval and deletion"""
    print("\n🔍 Testing Dashboards API...")
    
    # Generate unique dashboard with timestamp
    timestamp = int(time.time())
    title = f"Test Dashboard {timestamp}"
    description = f"This is a test dashboard created at {datetime.now().isoformat()}"
    
    # Create simple widget
    widgets = [
        {
            "definition": {
                "type": "timeseries",
                "requests": [
                    {
                        "q": "avg:system.cpu.user{*}",
                        "display_type": "line"
                    }
                ],
                "title": "CPU Usage"
            }
        }
    ]
    
    # Create dashboard
    result = create_dashboard(title, description, widgets, "ordered")
    print_result("Create Dashboard", result)
    
    try:
        # Parse result to get dashboard ID
        dashboard_data = json.loads(result)
        dashboard_id = dashboard_data.get("data", {}).get("id")
        
        if not dashboard_id:
            print("❌ Could not get dashboard ID from response")
            return None
            
        # Get dashboard
        result = get_dashboard(dashboard_id)
        print_result("Get Dashboard", result)
        
        # Delete dashboard
        result = delete_dashboard(dashboard_id)
        print_result("Delete Dashboard", result)
        
        return dashboard_data
    except Exception as e:
        print(f"❌ Error in dashboard test: {e}")
        return None

def run_all_tests():
    """Run all tests and report results"""
    print("\n🚀 Starting comprehensive Datadog MCP server tests...")
    print(f"Time: {datetime.now().isoformat()}")
    print("API Keys: Using provided Datadog API and APP keys")
    
    results = {}
    
    # Test metrics
    print("\n📊 TESTING METRICS...")
    metrics_result = test_metrics()
    results["metrics"] = "✅ Success" if metrics_result else "❌ Failed"
    
    # Test events
    print("\n📅 TESTING EVENTS...")
    events_result = test_events()
    results["events"] = "✅ Success" if events_result else "❌ Failed"
    
    # Test monitors
    print("\n🔔 TESTING MONITORS...")
    monitors_result = test_monitors()
    results["monitors"] = "✅ Success" if monitors_result else "❌ Failed"
    
    # Test dashboards
    print("\n📈 TESTING DASHBOARDS...")
    dashboards_result = test_dashboards()
    results["dashboards"] = "✅ Success" if dashboards_result else "❌ Failed"
    
    # Print summary
    print("\n📋 TEST SUMMARY:")
    for test, result in results.items():
        print(f"{test.capitalize()}: {result}")
    
    overall = "✅ ALL TESTS PASSED" if all(["Failed" not in r for r in results.values()]) else "❌ SOME TESTS FAILED"
    print(f"\n{overall}")

if __name__ == "__main__":
    run_all_tests()
