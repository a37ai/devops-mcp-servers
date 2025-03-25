#!/usr/bin/env python3
"""
Test script for Datadog MCP server
"""
import os
import json
import requests

# Import the MCP server
from servers.datadog.datadog_mcp import mcp, submit_metric

def test_mcp_server():
    """Test the MCP server functionality"""
    print("Testing MCP server with Datadog credentials...")
    
    # Test submit_metric function
    metric_name = "test.metric"
    value = 1.0
    tags = ["test:true", "env:dev"]
    
    result = submit_metric(metric_name, value, tags=tags)
    print(f"Submit metric result: {result}")
    
    # Parse the result
    try:
        result_json = json.loads(result)
        if result_json.get("status") == "success":
            print("✅ MCP server test successful!")
            return True
        else:
            print(f"❌ MCP server test failed: {result_json.get('message')}")
            return False
    except Exception as e:
        print(f"❌ Error parsing result: {e}")
        return False

if __name__ == "__main__":
    test_mcp_server()
