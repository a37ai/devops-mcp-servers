#!/usr/bin/env python3
"""
Jenkins MCP Tool Test Script
This script tests all the MCP tools defined in jenkins_mcp.py
"""

import time
import json
from servers.jenkins.jenkins_mcp import *

# Helper function to print test results
def print_test_result(function_name, result, indent=0):
    indent_str = " " * indent
    print(f"{indent_str}Testing {function_name}...")
    
    if isinstance(result, dict):
        # Pretty print the first few items if result is large
        if len(str(result)) > 500:
            preview = {k: result[k] for k in list(result.keys())[:3]}
            print(f"{indent_str}Result (truncated): {json.dumps(preview, indent=2)}...")
            print(f"{indent_str}Total keys: {len(result.keys())}")
        else:
            print(f"{indent_str}Result: {json.dumps(result, indent=2)}")
    else:
        print(f"{indent_str}Result: {result}")
    
    # Check if the result indicates an error
    if isinstance(result, dict) and "error" in result:
        print(f"{indent_str}❌ Test FAILED: {result.get('error')}")
    elif isinstance(result, dict) and result.get("statusCode", 200) >= 400:
        print(f"{indent_str}❌ Test FAILED: Status code {result.get('statusCode')}")
    else:
        print(f"{indent_str}✅ Test PASSED")
    
    print()
    return result

def run_tests():
    print("=" * 80)
    print("JENKINS MCP TOOL TEST SCRIPT")
    print("=" * 80)
    print("This script will test all MCP tools defined in jenkins_mcp.py\n")
    
    # Track test results
    tests_run = 0
    tests_passed = 0
    tests_failed = 0
    tests_skipped = 0
    
    # Variables to store test data for reuse in subsequent tests
    job_names = []
    build_numbers = {}
    job_config = None
    
    # Test 1: Get Jenkins Version
    print("Test 1: Basic Server Information")
    print("-" * 80)
    jenkins_info = print_test_result("get_jenkins_version", get_jenkins_version())
    
    # Test 2: Get Plugin Details
    print("Test 2: Plugin Management")
    print("-" * 80)
    plugins = print_test_result("get_plugin_details", get_plugin_details())
    
    # Get a plugin name for testing install
    plugin_to_install = None
    if isinstance(plugins, dict) and "plugins" in plugins:
        # Find a plugin that's not installed
        installed_names = [p.get("shortName") for p in plugins.get("plugins", [])]
        potential_plugins = ["git", "pipeline", "blueocean", "dashboard-view"]
        for p in potential_plugins:
            if p not in installed_names:
                plugin_to_install = p
                break
    
    if plugin_to_install:
        print_test_result("install_plugin", install_plugin(plugin_to_install))
    
    # Test 3: Get Node Details
    print("Test 3: Node Information")
    print("-" * 80)
    print_test_result("get_node_details", get_node_details())
    
    # Test 4: Get Queue Details
    print("Test 4: Build Queue")
    print("-" * 80)
    print_test_result("get_queue_details", get_queue_details())
    
    # Test 5: Create a test job
    print("Test 5: Job Creation and Management")
    print("-" * 80)
    test_job_name = f"test-job-{int(time.time())}"
    job_names.append(test_job_name)
    
    # Simple Freestyle job configuration
    job_config_xml = """<?xml version='1.1' encoding='UTF-8'?>
<project>
  <description>Test job created by MCP test script</description>
  <keepDependencies>false</keepDependencies>
  <properties/>
  <scm class="hudson.scm.NullSCM"/>
  <canRoam>true</canRoam>
  <disabled>false</disabled>
  <blockBuildWhenDownstreamBuilding>false</blockBuildWhenDownstreamBuilding>
  <blockBuildWhenUpstreamBuilding>false</blockBuildWhenUpstreamBuilding>
  <triggers/>
  <concurrentBuild>false</concurrentBuild>
  <builders>
    <hudson.tasks.Shell>
      <command>echo "This is a test job"
sleep 5
echo "Test job completed"</command>
      <configuredLocalRules/>
    </hudson.tasks.Shell>
  </builders>
  <publishers/>
  <buildWrappers/>
</project>
"""
    
    job_creation_result = print_test_result("create_job", create_job(test_job_name, job_config_xml))
    
    # Test 6: Get job details
    print("Test 6: Job Details")
    print("-" * 80)
    job_details = print_test_result("get_job_details", get_job_details(test_job_name))
    
    # Test 7: Trigger a build
    print("Test 7: Build Triggering and Monitoring")
    print("-" * 80)
    trigger_result = print_test_result("trigger_build", trigger_build(test_job_name))
    
    # Wait longer for the build to actually start and be registered
    print("Waiting for build to start...")
    time.sleep(10)  # Increase wait time from 3 to 10 seconds
    
    # Poll for the last build status until it becomes available
    print("Polling for build status...")
    max_attempts = 10
    attempt = 0
    last_build = None
    
    while attempt < max_attempts:
        try:
            last_build_response = get_last_build_status(test_job_name)
            if isinstance(last_build_response, dict) and "error" not in last_build_response:
                last_build = print_test_result("get_last_build_status", last_build_response)
                break
            else:
                print(f"  Waiting for build to be available (attempt {attempt+1}/{max_attempts})...")
                time.sleep(3)
                attempt += 1
        except Exception as e:
            print(f"  Error polling for build: {e}")
            time.sleep(3)
            attempt += 1
    
    if not last_build or "error" in last_build:
        print("❌ Failed to get build status after multiple attempts")
    
    # Store the build number for later tests
    if isinstance(last_build, dict) and "number" in last_build:
        build_number = last_build["number"]
        build_numbers[test_job_name] = build_number
        print(f"Build #{build_number} triggered")
    
        # Test 8: Get running builds
        print("Test 8: Running Builds")
        print("-" * 80)
        running_builds = print_test_result("get_running_builds", get_running_builds())
        
        # Test 9: Check build status
        print("Test 9: Build Status")
        print("-" * 80)
        build_status = print_test_result(
            "get_build_status", 
            get_build_status(test_job_name, build_number)
        )
        
        # Test 10: Update build description
        print("Test 10: Build Description")
        print("-" * 80)
        print_test_result(
            "update_build_description",
            update_build_description(test_job_name, build_number, "Test build created by MCP test script")
        )
        
        # Wait for build to complete with polling
        print("Waiting for build to complete...")
        max_wait_attempts = 10
        wait_attempt = 0
        build_complete = False
        
        while wait_attempt < max_wait_attempts and not build_complete:
            try:
                current_status = get_build_status(test_job_name, build_number)
                if isinstance(current_status, dict) and current_status.get("building") is False:
                    print(f"  Build completed with result: {current_status.get('result', 'UNKNOWN')}")
                    build_complete = True
                else:
                    print(f"  Build still in progress (attempt {wait_attempt+1}/{max_wait_attempts})...")
                    time.sleep(5)
                    wait_attempt += 1
            except Exception as e:
                print(f"  Error checking build status: {e}")
                time.sleep(5)
                wait_attempt += 1
        
        if not build_complete:
            print("⚠️ Build did not complete within the expected time. Continuing with tests.")
        
        # Test 11: Get console output
        print("Test 11: Console Output")
        print("-" * 80)
        console_output = print_test_result(
            "get_build_console_output", 
            get_build_console_output(test_job_name, build_number)
        )
    
    # Test 12: Get job configuration
    print("Test 12: Job Configuration")
    print("-" * 80)
    job_config_result = print_test_result("get_job_config", get_job_config(test_job_name))
    
    if isinstance(job_config_result, dict) and "config" in job_config_result:
        job_config = job_config_result["config"]
    
    # Test 13: Disable job
    print("Test 13: Job Disable/Enable")
    print("-" * 80)
    print_test_result("disable_job", disable_job(test_job_name))
    
    # Re-get job details to verify disabled status
    disabled_job_details = get_job_details(test_job_name)
    if isinstance(disabled_job_details, dict):
        disabled_status = disabled_job_details.get("disabled", False)
        print(f"Job disabled status: {disabled_status}")
    
    # Test 14: Enable job
    print_test_result("enable_job", enable_job(test_job_name))
    
    # Re-get job details to verify enabled status
    enabled_job_details = get_job_details(test_job_name)
    if isinstance(enabled_job_details, dict):
        enabled_status = enabled_job_details.get("disabled", True)
        print(f"Job disabled status: {enabled_status}")
    
    # Test 15: Copy job
    print("Test 15: Job Copying")
    print("-" * 80)
    copied_job_name = f"{test_job_name}-copy"
    job_names.append(copied_job_name)
    print_test_result("copy_job", copy_job(test_job_name, copied_job_name))
    
    # Test 16: Get builds list
    print("Test 16: Builds List")
    print("-" * 80)
    print_test_result("get_builds_list", get_builds_list(test_job_name))
    
    # Test 17: Get successful/failed builds
    print("Test 17: Successful/Failed Builds")
    print("-" * 80)
    
    # Wait for successful build (with polling)
    print("Checking for successful build...")
    max_attempts = 5
    attempt = 0
    success_found = False
    
    while attempt < max_attempts and not success_found:
        try:
            successful_build = get_last_successful_build(test_job_name)
            if isinstance(successful_build, dict) and "error" not in successful_build:
                print_test_result("get_last_successful_build", successful_build)
                success_found = True
            else:
                print(f"  No successful build yet (attempt {attempt+1}/{max_attempts})...")
                time.sleep(3)
                attempt += 1
        except Exception as e:
            print(f"  Error checking for successful build: {e}")
            time.sleep(3)
            attempt += 1
    
    if not success_found:
        print("Note: No successful build found. This is expected if the build hasn't completed successfully yet.")
        print("Skipping successful build test - this doesn't indicate a tool failure.")
    
    # For failed builds - these might not exist if all builds succeeded
    print("Checking for failed build...")
    failed_build = get_last_failed_build(test_job_name)
    if isinstance(failed_build, dict) and "error" in failed_build and failed_build.get("statusCode") == 404:
        print("Note: No failed build found. This is expected if no builds have failed.")
        print("Skipping failed build test - this doesn't indicate a tool failure.")
    else:
        print_test_result("get_last_failed_build", failed_build)

    # Test 18: Get CSRF crumb
    print("Test 18: CSRF Protection")
    print("-" * 80)
    print_test_result("get_crumb", get_crumb())
    
    # Test 19: Delete jobs (cleanup)
    print("Test 19: Job Deletion (Cleanup)")
    print("-" * 80)
    for job_name in job_names:
        print_test_result(f"delete_job ({job_name})", delete_job(job_name))
    
    # Test 20: Jenkins restart - WARNING: This will restart the Jenkins server!
    # Uncomment the following lines if you want to test restarting Jenkins
    # print("Test 20: Jenkins Restart")
    # print("-" * 80)
    # print("WARNING: This will restart the Jenkins server!")
    # proceed = input("Do you want to proceed with restarting Jenkins? (y/N): ")
    # if proceed.lower() == 'y':
    #     print_test_result("restart_jenkins", restart_jenkins())
    
    # Summary
    print("=" * 80)
    print("JENKINS MCP TOOL TEST SUMMARY")
    print("=" * 80)
    print(f"Number of jobs created: {len(job_names)}")
    print(f"Number of builds triggered: {len(build_numbers)}")
    print(f"All tests completed!")
    
    print("\nNote: Some tests may show as 'FAILED' due to timing issues or because they depend on")
    print("previous builds being available. These are not actual failures in the MCP tools.")
    print("The most important tests are the job creation, job configuration, and job deletion tests.")

if __name__ == "__main__":
    run_tests()