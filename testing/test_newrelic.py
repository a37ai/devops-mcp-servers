#!/usr/bin/env python3
import asyncio
import json
import os
import sys
from datetime import datetime, timedelta, timezone

# Import all functions from the MCP server
from servers.newrelic.newrelic_mcp import *

async def test_newrelic_api():
    """Test New Relic MCP tools with focus on creating and testing a real application."""
    print("Testing New Relic MCP Tools...")
    print("=" * 80)
    
    # Store application IDs and other resources for later use
    resources = {}
    
    # Step 1: Create a test application (via API call rather than MCP tool since it might not exist)
    print("\n--- CREATING TEST APPLICATION ---\n")
    
    try:
        # Note: New Relic API doesn't directly support application creation through REST API
        # Instead we'll look for existing applications first
        print("Checking for existing applications:")
        result = await list_applications()
        apps_data = json.loads(result)
        
        if apps_data.get("applications") and len(apps_data["applications"]) > 0:
            # Use an existing application if available
            app = apps_data["applications"][0]
            app_id = app["id"]
            app_name = app["name"]
            print(f"Using existing application: '{app_name}' (ID: {app_id})")
            resources["app_id"] = app_id
            resources["app_name"] = app_name
        else:
            # If no applications exist, we'll create a fake ID for testing
            # In real usage, applications are created by installing the New Relic agent
            print("No existing applications found.")
            print("Creating a new NRQL alert condition as a fallback test...")
            
            # First create a policy if one doesn't exist
            policy_result = await list_alert_policies()
            policy_data = json.loads(policy_result)
            
            if policy_data.get("policies") and len(policy_data["policies"]) > 0:
                policy_id = policy_data["policies"][0]["id"]
                policy_name = policy_data["policies"][0]["name"]
                print(f"Using existing policy: '{policy_name}' (ID: {policy_id})")
            else:
                policy_create_result = await create_alert_policy(
                    name="Test Policy for MCP Script",
                    incident_preference="PER_POLICY"
                )
                policy_data = json.loads(policy_create_result)
                policy_id = policy_data["policy"]["id"]
                print(f"Created new policy with ID: {policy_id}")
            
            resources["policy_id"] = policy_id
            
            # Create a NRQL alert condition which works even without applications
            condition_result = await create_nrql_alert_condition(
                policy_id=policy_id,
                name=f"Test Condition {datetime.now().strftime('%Y%m%d%H%M%S')}",
                nrql={"query": "SELECT count(*) FROM Transaction", "since_value": "5"},
                terms=[{
                    "duration": "5",
                    "operator": "above",
                    "priority": "critical",
                    "threshold": "1",
                    "time_function": "all"
                }],
                value_function="single_value"
            )
            condition_data = json.loads(condition_result)
            condition_id = condition_data["nrql_condition"]["id"]
            print(f"Created test NRQL condition with ID: {condition_id}")
            resources["condition_id"] = condition_id
            
            # Use a placeholder app_id for the functions that require it
            app_id = None
    except Exception as e:
        print(f"Error during setup: {e}")
        app_id = None
    
    # Test different aspects of the API based on what we could set up
    if resources.get("app_id"):
        await test_application_endpoints(resources["app_id"])
    
    if resources.get("policy_id"):
        await test_alert_policy_endpoints(resources["policy_id"])
    
    # Test generic endpoints that don't require specific resources
    await test_generic_endpoints()
    
    # Test resource endpoints
    await test_resource_endpoints(resources)
    
    # Test prompts
    await test_prompts(resources)
    
    print("\n" + "=" * 80)
    print("New Relic MCP tools test completed!")
    print("=" * 80)


async def test_application_endpoints(app_id):
    """Test endpoints that require an application ID."""
    print("\n--- TESTING APPLICATION ENDPOINTS ---\n")
    
    print("Testing get_application:")
    try:
        result = await get_application(app_id)
        print(f"Response (truncated): {result[:200]}...")
    except Exception as e:
        print(f"Error in get_application: {e}")
    
    print("\nTesting get_application_metrics:")
    try:
        result = await get_application_metrics(app_id)
        print(f"Response (truncated): {result[:200]}...")
    except Exception as e:
        print(f"Error in get_application_metrics: {e}")
    
    print("\nTesting get_application_metric_data:")
    try:
        # Get current time and one hour ago for the time range
        now = datetime.now(timezone.utc)
        one_hour_ago = now - timedelta(hours=1)
        from_date = one_hour_ago.isoformat()
        to_date = now.isoformat()
        
        # Make a simplified request with common metrics
        result = await get_application_metric_data(
            app_id, 
            names=["HttpDispatcher"], 
            from_date=from_date,
            to_date=to_date,
            summarize=True
        )
        print(f"Response (truncated): {result[:200]}...")
    except Exception as e:
        print(f"Error in get_application_metric_data: {e}")
    
    print("\nTesting list_deployments:")
    try:
        result = await list_deployments(app_id)
        print(f"Response (truncated): {result[:200]}...")
    except Exception as e:
        print(f"Error in list_deployments: {e}")
    
    print("\nTesting list_application_hosts:")
    try:
        result = await list_application_hosts(app_id)
        print(f"Response (truncated): {result[:200]}...")
        
        # Extract a host ID for further testing
        hosts_data = json.loads(result)
        if hosts_data.get("application_hosts") and len(hosts_data["application_hosts"]) > 0:
            host_id = hosts_data["application_hosts"][0]["id"]
            print(f"Found host ID: {host_id} for further tests")
            
            print("\nTesting get_application_host:")
            try:
                result = await get_application_host(app_id, host_id)
                print(f"Response (truncated): {result[:200]}...")
            except Exception as e:
                print(f"Error in get_application_host: {e}")
        else:
            print("No hosts found for this application.")
    except Exception as e:
        print(f"Error in list_application_hosts: {e}")
    
    print("\nTesting list_application_instances:")
    try:
        result = await list_application_instances(app_id)
        print(f"Response (truncated): {result[:200]}...")
        
        # Extract an instance ID for further testing
        instances_data = json.loads(result)
        if instances_data.get("application_instances") and len(instances_data["application_instances"]) > 0:
            instance_id = instances_data["application_instances"][0]["id"]
            print(f"Found instance ID: {instance_id} for further tests")
            
            print("\nTesting get_application_instance:")
            try:
                result = await get_application_instance(app_id, instance_id)
                print(f"Response (truncated): {result[:200]}...")
            except Exception as e:
                print(f"Error in get_application_instance: {e}")
        else:
            print("No instances found for this application.")
    except Exception as e:
        print(f"Error in list_application_instances: {e}")


async def test_alert_policy_endpoints(policy_id):
    """Test endpoints that require a policy ID."""
    print("\n--- TESTING ALERT POLICY ENDPOINTS ---\n")
    
    print("Testing list_alert_conditions:")
    try:
        result = await list_alert_conditions(policy_id)
        print(f"Response (truncated): {result[:200]}...")
        
        # Extract a condition ID for further testing
        condition_data = json.loads(result)
        if condition_data.get("conditions") and len(condition_data["conditions"]) > 0:
            condition_id = condition_data["conditions"][0]["id"]
            print(f"Found condition ID: {condition_id} for further tests")
            
            print("\nTesting update_alert_condition (read-only test):")
            try:
                result = await update_alert_condition(
                    condition_id=condition_id,
                    name=f"Updated Test Condition {datetime.now().strftime('%Y%m%d%H%M%S')}"
                )
                print(f"Response: {result}")
            except Exception as e:
                print(f"Error in update_alert_condition: {e}")
    except Exception as e:
        print(f"Error in list_alert_conditions: {e}")
    
    print("\nTesting list_nrql_alert_conditions:")
    try:
        result = await list_nrql_alert_conditions(policy_id)
        print(f"Response (truncated): {result[:200]}...")
        
        # Extract a NRQL condition ID for further testing
        nrql_condition_data = json.loads(result)
        if nrql_condition_data.get("nrql_conditions") and len(nrql_condition_data["nrql_conditions"]) > 0:
            nrql_condition_id = nrql_condition_data["nrql_conditions"][0]["id"]
            print(f"Found NRQL condition ID: {nrql_condition_id} for further tests")
            
            print("\nTesting update_nrql_alert_condition:")
            try:
                result = await update_nrql_alert_condition(
                    condition_id=nrql_condition_id,
                    name=f"Updated Test NRQL Condition {datetime.now().strftime('%Y%m%d%H%M%S')}"
                )
                print(f"Response (truncated): {result[:200]}...")
            except Exception as e:
                print(f"Error in update_nrql_alert_condition: {e}")
    except Exception as e:
        print(f"Error in list_nrql_alert_conditions: {e}")


async def test_generic_endpoints():
    """Test endpoints that don't require specific resources."""
    print("\n--- TESTING GENERIC ENDPOINTS ---\n")
    
    print("Testing list_key_transactions:")
    try:
        result = await list_key_transactions()
        print(f"Response (truncated): {result[:200]}...")
        
        # Extract a transaction ID for further testing
        txn_data = json.loads(result)
        if txn_data.get("key_transactions") and len(txn_data["key_transactions"]) > 0:
            txn_id = txn_data["key_transactions"][0]["id"]
            print(f"Found transaction ID: {txn_id} for further tests")
            
            print("\nTesting get_key_transaction:")
            try:
                result = await get_key_transaction(txn_id)
                print(f"Response (truncated): {result[:200]}...")
            except Exception as e:
                print(f"Error in get_key_transaction: {e}")
        else:
            print("No key transactions found.")
    except Exception as e:
        print(f"Error in list_key_transactions: {e}")
    
    print("\nTesting list_mobile_applications:")
    try:
        result = await list_mobile_applications()
        print(f"Response (truncated): {result[:200]}...")
        
        # Extract a mobile app ID for further testing
        mobile_data = json.loads(result)
        if mobile_data.get("applications") and len(mobile_data["applications"]) > 0:
            mobile_id = mobile_data["applications"][0]["id"]
            print(f"Found mobile app ID: {mobile_id} for further tests")
            
            print("\nTesting get_mobile_application:")
            try:
                result = await get_mobile_application(mobile_id)
                print(f"Response (truncated): {result[:200]}...")
            except Exception as e:
                print(f"Error in get_mobile_application: {e}")
        else:
            print("No mobile applications found.")
    except Exception as e:
        print(f"Error in list_mobile_applications: {e}")
    
    print("\nTesting list_alerts_incidents:")
    try:
        result = await list_alerts_incidents(only_open=True)
        print(f"Response (truncated): {result[:200]}...")
        
        # Extract an incident ID for further testing
        incidents_data = json.loads(result)
        if incidents_data.get("incidents") and len(incidents_data["incidents"]) > 0:
            incident_id = incidents_data["incidents"][0]["id"]
            print(f"Found incident ID: {incident_id} for further tests")
        else:
            print("No open incidents found.")
    except Exception as e:
        print(f"Error in list_alerts_incidents: {e}")
    
    print("\nTesting list_alerts_violations:")
    try:
        # Create date range for last 24 hours
        now = datetime.now(timezone.utc)
        one_day_ago = now - timedelta(days=1)
        start_date = one_day_ago.isoformat()
        end_date = now.isoformat()
        
        result = await list_alerts_violations(
            start_date=start_date,
            end_date=end_date,
            only_open=True
        )
        print(f"Response (truncated): {result[:200]}...")
    except Exception as e:
        print(f"Error in list_alerts_violations: {e}")


async def test_resource_endpoints(resources):
    """Test resource endpoints."""
    print("\n--- TESTING RESOURCE ENDPOINTS ---\n")
    
    print("Testing get_applications_resource:")
    try:
        result = await get_applications_resource()
        print(f"Response (truncated): {result[:200]}...")
    except Exception as e:
        print(f"Error in get_applications_resource: {e}")
    
    print("\nTesting get_alert_policies_resource:")
    try:
        result = await get_alert_policies_resource()
        print(f"Response (truncated): {result[:200]}...")
    except Exception as e:
        print(f"Error in get_alert_policies_resource: {e}")
    
    if resources.get("app_id"):
        print("\nTesting get_application_resource:")
        try:
            result = await get_application_resource(resources["app_id"])
            print(f"Response (truncated): {result[:200]}...")
        except Exception as e:
            print(f"Error in get_application_resource: {e}")
    
    print("\nTesting get_mobile_applications_resource:")
    try:
        result = await get_mobile_applications_resource()
        print(f"Response (truncated): {result[:200]}...")
    except Exception as e:
        print(f"Error in get_mobile_applications_resource: {e}")
    
    print("\nTesting get_key_transactions_resource:")
    try:
        result = await get_key_transactions_resource()
        print(f"Response (truncated): {result[:200]}...")
    except Exception as e:
        print(f"Error in get_key_transactions_resource: {e}")
    
    print("\nTesting get_alerts_incidents_resource:")
    try:
        # Try different parameter values
        result = await get_alerts_incidents_resource(only_open=True)
        print(f"Response (truncated): {result[:200]}...")
    except Exception as e:
        print(f"Error in get_alerts_incidents_resource: {e}")
    
    print("\nTesting get_alerts_violations_resource:")
    try:
        # Current time for date range
        now = datetime.now(timezone.utc)
        one_day_ago = now - timedelta(days=1)
        start_date = one_day_ago.isoformat()
        end_date = now.isoformat()
        
        result = await get_alerts_violations_resource(
            only_open=True,
            start_date=start_date,
            end_date=end_date
        )
        print(f"Response (truncated): {result[:200]}...")
    except Exception as e:
        print(f"Error in get_alerts_violations_resource: {e}")
    
    print("\nTesting get_dashboard_resource:")
    try:
        result = await get_dashboard_resource()
        print(f"Response (truncated): {result[:200]}...")
    except Exception as e:
        print(f"Error in get_dashboard_resource: {e}")


async def test_prompts(resources):
    """Test prompt templates."""
    print("\n--- TESTING PROMPTS ---\n")
    
    if resources.get("app_id"):
        print("Testing analyze_application_performance prompt:")
        try:
            result = analyze_application_performance(resources["app_id"])
            print(f"Response: {result}")
        except Exception as e:
            print(f"Error in analyze_application_performance: {e}")
    
    print("\nTesting investigate_alert_incident prompt:")
    try:
        # Using a placeholder ID or a real one if we found it
        incident_id = resources.get("incident_id", 12345)
        result = investigate_alert_incident(incident_id)
        print(f"Response: {result}")
    except Exception as e:
        print(f"Error in investigate_alert_incident: {e}")
    
    if resources.get("app_id"):
        print("\nTesting compare_environments prompt:")
        try:
            # Using the same app_id twice for testing
            result = compare_environments(resources["app_id"], resources["app_id"])
            print(f"Response: {result}")
        except Exception as e:
            print(f"Error in compare_environments: {e}")
        
        print("\nTesting deployment_analysis prompt:")
        try:
            result = deployment_analysis(resources["app_id"], days=7)
            print(f"Response: {result}")
        except Exception as e:
            print(f"Error in deployment_analysis: {e}")


if __name__ == "__main__":
    asyncio.run(test_newrelic_api())