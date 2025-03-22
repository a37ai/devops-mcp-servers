#!/usr/bin/env python3
"""
Test script for Grafana MCP Server.
This script tests all available tools defined in the MCP server, including plugin management.
"""

import os
import json
import asyncio
import random
from datetime import datetime, timedelta

# Import all tools from the Grafana MCP server
from servers.grafana.grafana_mcp import *

async def run_tests():
    """Run tests for all Grafana MCP tools, including plugin management."""
    print("Starting Grafana MCP Server Tests...")
    print("=" * 50)
    
    # Generate timestamps for testing
    now = datetime.now()
    current_time = now.isoformat()
    one_hour_ago = (now - timedelta(hours=1)).isoformat()
    one_day_ago = (now - timedelta(days=1)).isoformat()
    test_id = now.strftime("%Y%m%d%H%M%S")
    
    # Health check
    print("Testing: check_grafana_health")
    try:
        result = await check_grafana_health()
        health_info = json.loads(result)
        print(f"Health check result: {result[:100]}...")
        print(f"Grafana version: {health_info.get('version')}")
    except Exception as e:
        print(f"Health check failed: {str(e)}")
    print("-" * 50)
    
    # ===== Test Plugin Management =====
    print("Testing plugin management functions...")
    
    # Test plugin search
    print("Testing: search_plugins")
    try:
        result = await search_plugins()
        plugins_data = json.loads(result)
        print(f"Plugin search result: {result[:100]}...")
        print(f"Found {len(plugins_data)} plugins")
        
        # Get a list of plugin IDs for further testing
        plugin_ids = [plugin.get("id") for plugin in plugins_data]
        print(f"Available plugins: {', '.join(plugin_ids[:5])}...")
    except Exception as e:
        print(f"Plugin search failed: {str(e)}")
        plugin_ids = ["grafana-piechart-panel", "grafana-clock-panel", "grafana-worldmap-panel"]
    print("-" * 50)
    
    # Test if specific plugins are installed
    test_plugins = ["prometheus", "loki", "alertmanager"]
    for plugin_id in test_plugins:
        print(f"Testing: is_plugin_installed for {plugin_id}")
        try:
            result = await is_plugin_installed(plugin_id)
            install_status = json.loads(result)
            print(f"{plugin_id} installed: {install_status.get('installed')}")
        except Exception as e:
            print(f"Plugin check failed for {plugin_id}: {str(e)}")
    print("-" * 50)
    
    # Select a plugin to install for testing
    # First try to find a plugin that's not installed
    test_plugin = None
    install_candidates = ["grafana-piechart-panel", "grafana-clock-panel", "grafana-worldmap-panel"]
    
    for candidate in install_candidates:
        try:
            result = await is_plugin_installed(candidate)
            install_status = json.loads(result)
            if not install_status.get('installed'):
                test_plugin = candidate
                break
        except:
            pass
    
    # If all candidates are installed, just pick one
    if not test_plugin and len(plugin_ids) > 0:
        test_plugin = random.choice(plugin_ids)
    elif not test_plugin:
        test_plugin = "grafana-piechart-panel"
    
    # Test plugin installation
    print(f"Testing: install_plugin for {test_plugin}")
    try:
        result = await install_plugin(test_plugin)
        print(f"Plugin installation result: {result[:100]}...")
    except Exception as e:
        print(f"Plugin installation failed for {test_plugin}: {str(e)}")
    print("-" * 50)
    
    # Test plugin settings
    print(f"Testing: get_plugin_settings for {test_plugin}")
    try:
        result = await get_plugin_settings(test_plugin)
        print(f"Plugin settings result: {result[:100]}...")
    except Exception as e:
        print(f"Plugin settings retrieval failed for {test_plugin}: {str(e)}")
    print("-" * 50)
    
    # Test plugin uninstallation
    print(f"Testing: uninstall_plugin for {test_plugin}")
    try:
        result = await uninstall_plugin(test_plugin)
        print(f"Plugin uninstallation result: {result[:100]}...")
    except Exception as e:
        print(f"Plugin uninstallation failed for {test_plugin}: {str(e)}")
    print("-" * 50)
    
    # ===== Setup and Test Data Sources =====
    print("Setting up required data sources...")
    
    # Setup Mimir/Prometheus
    mimir_ds_id = None
    print("Setting up Mimir/Prometheus data source")
    mimir_datasource = {
        "name": f"Mimir-{test_id}",
        "type": "prometheus",
        "url": "http://mimir:9009/prometheus",  # Default Mimir URL
        "access": "proxy",
        "basicAuth": False,
        "isDefault": False,
        "jsonData": {
            "httpMethod": "GET",
            "prometheusType": "Mimir"
        }
    }
    try:
        result = await create_data_source(json.dumps(mimir_datasource))
        result_json = json.loads(result)
        mimir_ds_id = result_json.get("datasource", {}).get("id")
        mimir_ds_uid = result_json.get("datasource", {}).get("uid")
        print(f"Mimir data source created. ID: {mimir_ds_id}, UID: {mimir_ds_uid}")
    except Exception as e:
        print(f"Mimir data source creation failed: {str(e)}")
    print("-" * 50)
    
    # Setup Loki
    loki_ds_id = None
    print("Setting up Loki data source")
    loki_datasource = {
        "name": f"Loki-{test_id}",
        "type": "loki",
        "url": "http://loki:3100",  # Default Loki URL
        "access": "proxy",
        "basicAuth": False,
        "isDefault": False
    }
    try:
        result = await create_data_source(json.dumps(loki_datasource))
        result_json = json.loads(result)
        loki_ds_id = result_json.get("datasource", {}).get("id")
        loki_ds_uid = result_json.get("datasource", {}).get("uid")
        print(f"Loki data source created. ID: {loki_ds_id}, UID: {loki_ds_uid}")
    except Exception as e:
        print(f"Loki data source creation failed: {str(e)}")
    print("-" * 50)
    
    # Create a dashboard with panels for each data source
    print("Creating test dashboard with panels for each data source")
    test_dashboard = {
        "title": f"Test Dashboard {test_id}",
        "uid": f"test-dashboard-{test_id}",
        "tags": ["test", "mcp"],
        "timezone": "browser",
        "panels": [
            {
                "id": 1,
                "gridPos": {"h": 8, "w": 12, "x": 0, "y": 0},
                "type": "graph",
                "title": "Mimir Test Panel",
                "datasource": {"type": "prometheus", "uid": mimir_ds_uid if mimir_ds_uid else None},
                "targets": [
                    {
                        "expr": "up",
                        "refId": "A"
                    }
                ]
            },
            {
                "id": 2,
                "gridPos": {"h": 8, "w": 12, "x": 12, "y": 0},
                "type": "logs",
                "title": "Loki Test Panel",
                "datasource": {"type": "loki", "uid": loki_ds_uid if loki_ds_uid else None},
                "targets": [
                    {
                        "expr": "{job=\"varlogs\"}",
                        "refId": "A"
                    }
                ]
            }
        ]
    }
    
    dashboard_uid = None
    try:
        result = await create_dashboard(json.dumps(test_dashboard), True)
        print(f"Dashboard creation result: {result[:100]}...")
        result_json = json.loads(result)
        dashboard_uid = result_json.get("uid") or test_dashboard["uid"]
    except Exception as e:
        print(f"Dashboard creation failed: {str(e)}")
    print("-" * 50)
    
    # Retrieve dashboard to confirm it was created
    if dashboard_uid:
        print(f"Testing: get_dashboard (UID: {dashboard_uid})")
        try:
            result = await get_dashboard(dashboard_uid)
            print(f"Dashboard retrieval result: {result[:100]}...")
        except Exception as e:
            print(f"Dashboard retrieval failed: {str(e)}")
        print("-" * 50)
    
    # ===== Test Mimir API Tools =====
    if mimir_ds_id:
        print("Testing Mimir API tools with configured data source")
        
        # Test instant query
        print("Testing: mimir_instant_query")
        try:
            result = await mimir_instant_query("up")
            print(f"Instant query result: {result[:100]}...")
        except Exception as e:
            print(f"Instant query failed: {str(e)}")
            print("Attempting to query using the data source query API instead")
            try:
                query = {
                    "refId": "A",
                    "expr": "up",
                    "instant": True
                }
                result = await query_data_source(mimir_ds_uid, json.dumps(query))
                print(f"Query via data source API result: {result[:100]}...")
            except Exception as e2:
                print(f"Query via data source API failed: {str(e2)}")
        print("-" * 50)
        
        # Test range query
        print("Testing: mimir_range_query")
        try:
            result = await mimir_range_query("up", one_hour_ago, current_time, "15s")
            print(f"Range query result: {result[:100]}...")
        except Exception as e:
            print(f"Range query failed: {str(e)}")
            print("Attempting to query using the data source query API instead")
            try:
                query = {
                    "refId": "A",
                    "expr": "up",
                    "range": True,
                    "start": one_hour_ago,
                    "end": current_time,
                    "step": "15s"
                }
                result = await query_data_source(mimir_ds_uid, json.dumps(query))
                print(f"Range query via data source API result: {result[:100]}...")
            except Exception as e2:
                print(f"Range query via data source API failed: {str(e2)}")
        print("-" * 50)
    
    # ===== Test Loki API Tools =====
    if loki_ds_id:
        print("Testing Loki API tools with configured data source")
        
        # Test Loki query
        print("Testing: loki_query")
        try:
            result = await loki_query('{job="varlogs"}', 10)
            print(f"Loki query result: {result[:100]}...")
        except Exception as e:
            print(f"Loki query failed: {str(e)}")
            print("Attempting to query using the data source query API instead")
            try:
                query = {
                    "refId": "A",
                    "expr": '{job="varlogs"}',
                    "limit": 10
                }
                result = await query_data_source(loki_ds_uid, json.dumps(query))
                print(f"Loki query via data source API result: {result[:100]}...")
            except Exception as e2:
                print(f"Loki query via data source API failed: {str(e2)}")
        print("-" * 50)
    
    # ===== Test Organization, Users, and Plugins =====
    
    # Test users list
    print("Testing: get_users")
    try:
        result = await get_users()
        print(f"Users list result: {result[:100]}...")
    except Exception as e:
        print(f"Users list failed: {str(e)}")
    print("-" * 50)
    
    # Test organization info
    print("Testing: get_organization")
    try:
        result = await get_organization()
        print(f"Organization info result: {result[:100]}...")
    except Exception as e:
        print(f"Organization info failed: {str(e)}")
    print("-" * 50)
    
    # Test plugins list
    print("Testing: get_plugins")
    try:
        result = await get_plugins()
        print(f"Plugins list result: {result[:100]}...")
    except Exception as e:
        print(f"Plugins list failed: {str(e)}")
    print("-" * 50)
    
    # ===== Try to set up Alert Rules if possible =====
    print("Testing alert rule functionality")
    try:
        # First check if any alert rules exist
        result = await get_alert_rules()
        print(f"Alert rules result: {result[:100]}...")
        
        # Try to create a test alert rule
        test_alert = {
            "name": f"Test Alert Rule {test_id}",
            "group": "test-group",
            "namespace": "test-namespace",
            "for": "5m",
            "conditions": [
                {
                    "evaluator": {
                        "params": [3],
                        "type": "gt"
                    },
                    "operator": {
                        "type": "and"
                    },
                    "query": {
                        "params": ["A"]
                    },
                    "reducer": {
                        "params": [],
                        "type": "last"
                    },
                    "type": "query"
                }
            ],
            "data": [
                {
                    "refId": "A",
                    "datasourceUid": mimir_ds_uid if mimir_ds_uid else "",
                    "model": {
                        "expr": "up",
                        "intervalMs": 1000,
                        "maxDataPoints": 43200
                    }
                }
            ]
        }
        
        try:
            result = await create_alert_rule(json.dumps(test_alert))
            print(f"Alert rule creation result: {result[:100]}...")
        except Exception as e:
            print(f"Alert rule creation failed: {str(e)}")
    except Exception as e:
        print(f"Alert rule testing failed: {str(e)}")
    print("-" * 50)
    
    # ===== Clean up created resources =====
    print("Cleaning up created resources")
    
    # Delete data sources
    if mimir_ds_id:
        print(f"Deleting Mimir data source (ID: {mimir_ds_id})")
        try:
            result = await delete_data_source(mimir_ds_id)
            print(f"Mimir data source deletion result: {result[:100]}...")
        except Exception as e:
            print(f"Mimir data source deletion failed: {str(e)}")
    
    if loki_ds_id:
        print(f"Deleting Loki data source (ID: {loki_ds_id})")
        try:
            result = await delete_data_source(loki_ds_id)
            print(f"Loki data source deletion result: {result[:100]}...")
        except Exception as e:
            print(f"Loki data source deletion failed: {str(e)}")
    
    # Delete dashboard
    if dashboard_uid:
        print(f"Deleting dashboard (UID: {dashboard_uid})")
        try:
            result = await delete_dashboard(dashboard_uid)
            print(f"Dashboard deletion result: {result[:100]}...")
        except Exception as e:
            print(f"Dashboard deletion failed: {str(e)}")
    
    print("All tests completed!")
    print("=" * 50)

if __name__ == "__main__":
    asyncio.run(run_tests())