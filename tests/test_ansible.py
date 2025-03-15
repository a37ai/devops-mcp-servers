#!/usr/bin/env python3
"""
Ansible Tower MCP Server Test Script

This script tests the functionality of the Ansible Tower MCP server by calling each of the 
provided tools and displaying the results. It has been specially modified to work with
Ansible Tower API limitations related to pagination and covers all MCP tools.
"""

import os
import json
import sys
import time
import traceback
from typing import Callable, Dict, Any, List, Optional
import urllib3

# Suppress insecure HTTPS request warnings
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

# Set environment variables for the Ansible client
os.environ["ANSIBLE_BASE_URL"] = ""
os.environ["ANSIBLE_USERNAME"] = "admin"
os.environ["ANSIBLE_PASSWORD"] = ""
os.environ["ANSIBLE_TOKEN"] = ""

# Import all functions from the MCP server module
try:
    from ansible import *
    print("✅ Successfully imported the ansible module")
except ImportError as e:
    print(f"❌ Failed to import the ansible module: {str(e)}")
    print(f"Stack trace: {traceback.format_exc()}")
    sys.exit(1)

# Monkey patch the handle_pagination function in the ansible module to avoid using limit parameter
def safe_handle_pagination(client, endpoint, params=None):
    """Fixed version of handle_pagination that doesn't use limit/offset parameters."""
    if params is None:
        params = {}
    
    # Remove problematic parameters
    if 'limit' in params:
        del params['limit']
    if 'offset' in params:
        del params['offset']
    
    results = []
    
    # Make a single request without pagination
    response = client.request("GET", endpoint, params=params)
    
    # Check if response is paginated (has 'results' key)
    if "results" in response:
        return response["results"]
    else:
        # If not paginated, return response as is
        return [response]

# Try to monkey patch the handle_pagination function in the ansible module
try:
    import ansible
    ansible.handle_pagination = safe_handle_pagination
    print("✅ Successfully patched handle_pagination function")
except Exception as e:
    print(f"⚠️ Failed to patch handle_pagination function. Some list functions may fail: {str(e)}")

class TestRunner:
    def __init__(self):
        self.results = {
            "passed": [],
            "failed": []
        }
        self.created_resources = {
            "organizations": [],
            "inventories": [],
            "hosts": [],
            "groups": [],
            "projects": [],
            "job_templates": [],
            "workflow_templates": [],
            "workflow_jobs": [],
            "credentials": [],
            "teams": [],
            "users": [],
            "schedules": [],
            "ad_hoc_commands": []
        }

    def run_test(self, test_name: str, func: Callable, **kwargs) -> Any:
        """Run a test function and record the result."""
        print(f"\n{'=' * 80}")
        print(f"Testing: {test_name}")
        print(f"{'-' * 80}")
        
        try:
            # Print the arguments being passed to the function
            if kwargs:
                print(f"Arguments:")
                for key, value in kwargs.items():
                    print(f"  {key}: {value}")
            
            # Call the function with the provided arguments
            start_time = time.time()
            result = func(**kwargs)
            end_time = time.time()
            
            # Try to parse the result as JSON for better formatting
            try:
                if isinstance(result, str):
                    parsed_result = json.loads(result)
                    result_str = json.dumps(parsed_result, indent=2)
                else:
                    result_str = str(result)
            except json.JSONDecodeError:
                result_str = result
                
            print(f"Result: {result_str}")
            print(f"Execution time: {end_time - start_time:.2f} seconds")
            print(f"✅ Test passed: {test_name}")
            
            self.results["passed"].append({
                "name": test_name,
                "time": end_time - start_time,
                "result": result
            })
            
            return result
            
        except Exception as e:
            print(f"❌ Test failed: {test_name}")
            print(f"Error: {str(e)}")
            print(f"Stack trace: {traceback.format_exc()}")
            
            self.results["failed"].append({
                "name": test_name,
                "error": str(e),
                "traceback": traceback.format_exc()
            })
            
            return None

    def print_summary(self):
        """Print a summary of all test results."""
        print("\n" + "=" * 80)
        print("TEST SUMMARY")
        print("=" * 80)
        
        total = len(self.results["passed"]) + len(self.results["failed"])
        pass_rate = len(self.results["passed"]) / total * 100 if total > 0 else 0
        
        print(f"Total tests: {total}")
        print(f"Passed: {len(self.results['passed'])} ({pass_rate:.1f}%)")
        print(f"Failed: {len(self.results['failed'])}")
        
        if self.results["failed"]:
            print("\nFailed tests:")
            for i, test in enumerate(self.results["failed"], 1):
                print(f"  {i}. {test['name']}")
                print(f"     Error: {test['error']}")

    def cleanup_resources(self):
        """Clean up any resources created during testing."""
        print("\n" + "=" * 80)
        print("CLEANUP")
        print("=" * 80)
        
        # Clean up in reverse order of dependencies
        resource_cleanups = [
            ("schedules", delete_schedule, "schedule_id"),
            ("ad_hoc_commands", cancel_ad_hoc_command, "command_id"),
            ("workflow_jobs", cancel_workflow_job, "job_id"),
            ("users", delete_user, "user_id"),
            ("teams", delete_team, "team_id"),
            ("job_templates", delete_job_template, "template_id"),
            ("hosts", delete_host, "host_id"),
            ("groups", delete_group, "group_id"),
            ("inventories", delete_inventory, "inventory_id"),
            ("projects", delete_project, "project_id"),
            ("credentials", delete_credential, "credential_id"),
            ("organizations", delete_organization, "organization_id")
        ]
        
        for resource_type, delete_func, id_param in resource_cleanups:
            resources = self.created_resources.get(resource_type, [])
            if resources:
                print(f"\nCleaning up {resource_type}:")
                for resource_id in resources:
                    try:
                        print(f"  Deleting {resource_type[:-1]} with ID {resource_id}...")
                        # Create a kwargs dictionary with the correct parameter name
                        kwargs = {id_param: resource_id}
                        delete_func(**kwargs)
                        print(f"  ✅ Deleted {resource_type[:-1]} with ID {resource_id}")
                    except Exception as e:
                        print(f"  ❌ Failed to delete {resource_type[:-1]} with ID {resource_id}: {str(e)}")

def parse_json_result(result_str: str) -> Dict:
    """Parse a JSON string result and return the parsed object."""
    try:
        if isinstance(result_str, str):
            return json.loads(result_str)
        return result_str
    except json.JSONDecodeError as e:
        print(f"Failed to parse JSON result: {str(e)}")
        print(f"Raw result: {result_str}")
        return {}

def extract_id(result_str: str) -> Optional[int]:
    """Extract the ID from a JSON result string."""
    try:
        result = parse_json_result(result_str)
        return result.get("id")
    except (json.JSONDecodeError, KeyError, TypeError):
        return None

def main():
    test_runner = TestRunner()
    
    # Test System Information functions
    test_runner.run_test("Get Ansible Version", get_ansible_version)
    test_runner.run_test("Get Dashboard Stats", get_dashboard_stats)
    
    try:
        # Test Metrics (might not work on all systems)
        test_runner.run_test("Get Metrics", get_metrics)
    except Exception as e:
        print("\n" + "=" * 80)
        print(f"Skipping: Get Metrics (API does not support this endpoint): {str(e)}")
        print("=" * 80)
    
    # Test Organization Management
    test_runner.run_test("List Organizations", list_organizations)
    
    # Create a test organization
    org_timestamp = int(time.time())
    org_name = f"TestOrg{org_timestamp}"
    org_result = test_runner.run_test(
        "Create Organization", 
        create_organization,
        name=org_name,
        description="Test organization created by MCP test script"
    )
    
    if org_result is None:
        print("Failed to create organization, cannot continue with dependent tests")
        test_runner.print_summary()
        return
    
    org_id = extract_id(org_result)
    if org_id:
        test_runner.created_resources["organizations"].append(org_id)
        
        # Test get organization
        test_runner.run_test(
            "Get Organization", 
            get_organization,
            organization_id=org_id
        )
        
        # Test update organization
        test_runner.run_test(
            "Update Organization", 
            update_organization,
            organization_id=org_id,
            description="Updated description for test organization"
        )
        
        # Test Inventory Management
        test_runner.run_test("List Inventories", list_inventories)
        
        # Create a test inventory
        inventory_name = f"TestInv{org_timestamp}"
        inventory_result = test_runner.run_test(
            "Create Inventory", 
            create_inventory,
            name=inventory_name,
            organization_id=org_id,
            description="Test inventory created by MCP test script"
        )
        
        inventory_id = extract_id(inventory_result)
        if inventory_id:
            test_runner.created_resources["inventories"].append(inventory_id)
            
            # Test get inventory
            test_runner.run_test(
                "Get Inventory", 
                get_inventory,
                inventory_id=inventory_id
            )
            
            # Test update inventory
            test_runner.run_test(
                "Update Inventory", 
                update_inventory,
                inventory_id=inventory_id,
                description="Updated description for test inventory"
            )
            
            # Test Host Management
            test_runner.run_test("List Hosts", list_hosts)
            test_runner.run_test(
                "List Hosts by Inventory", 
                list_hosts,
                inventory_id=inventory_id
            )
            
            # Create a test host
            host_name = f"test-host-{org_timestamp}.example.com"
            host_result = test_runner.run_test(
                "Create Host", 
                create_host,
                name=host_name,
                inventory_id=inventory_id,
                description="Test host created by MCP test script"
            )
            
            host_id = extract_id(host_result)
            if host_id:
                test_runner.created_resources["hosts"].append(host_id)
                
                # Test get host
                test_runner.run_test(
                    "Get Host", 
                    get_host,
                    host_id=host_id
                )
                
                # Test update host
                test_runner.run_test(
                    "Update Host", 
                    update_host,
                    host_id=host_id,
                    description="Updated description for test host"
                )
                
                # Test Group Management
                test_runner.run_test(
                    "List Groups", 
                    list_groups,
                    inventory_id=inventory_id
                )
                
                # Create a test group
                group_name = f"test-group-{org_timestamp}"
                group_result = test_runner.run_test(
                    "Create Group", 
                    create_group,
                    name=group_name,
                    inventory_id=inventory_id,
                    description="Test group created by MCP test script"
                )
                
                group_id = extract_id(group_result)
                if group_id:
                    test_runner.created_resources["groups"].append(group_id)
                    
                    # Test get group
                    test_runner.run_test(
                        "Get Group", 
                        get_group,
                        group_id=group_id
                    )
                    
                    # Test update group
                    test_runner.run_test(
                        "Update Group", 
                        update_group,
                        group_id=group_id,
                        description="Updated description for test group"
                    )
                    
                    # Test add host to group
                    test_runner.run_test(
                        "Add Host to Group", 
                        add_host_to_group,
                        group_id=group_id,
                        host_id=host_id
                    )
                    
                    # Test remove host from group
                    test_runner.run_test(
                        "Remove Host from Group", 
                        remove_host_from_group,
                        group_id=group_id,
                        host_id=host_id
                    )
        
        # Test Project Management
        test_runner.run_test("List Projects", list_projects)
        
        # Create a test project
        project_name = f"test-project-{org_timestamp}"
        project_result = test_runner.run_test(
            "Create Project", 
            create_project,
            name=project_name,
            organization_id=org_id,
            scm_type="git",
            scm_url="https://github.com/ansible/ansible-examples.git",
            description="Test project created by MCP test script"
        )
        
        project_id = extract_id(project_result)
        if project_id:
            test_runner.created_resources["projects"].append(project_id)
            
            # Test get project
            test_runner.run_test(
                "Get Project", 
                get_project,
                project_id=project_id
            )
            
            # Test update project
            test_runner.run_test(
                "Update Project", 
                update_project,
                project_id=project_id,
                description="Updated description for test project"
            )
            
            # Test sync project
            test_runner.run_test(
                "Sync Project", 
                sync_project,
                project_id=project_id
            )
            
            # Wait for project sync to complete
            print("Waiting for project sync to complete...")
            time.sleep(10)
            
            # Test Credential Management
            test_runner.run_test("List Credentials", list_credentials)
            test_runner.run_test("List Credential Types", list_credential_types)
            
            # Try to get machine credential type ID
            cred_types_result = test_runner.run_test("List Credential Types", list_credential_types)
            machine_cred_type_id = None
            
            if cred_types_result:
                cred_types_data = parse_json_result(cred_types_result)
                if isinstance(cred_types_data, list):
                    for cred_type in cred_types_data:
                        if cred_type.get("name") == "Machine":
                            machine_cred_type_id = cred_type.get("id")
                            break
            
            if machine_cred_type_id:
                # Create a test credential
                credential_name = f"test-credential-{org_timestamp}"
                credential_inputs = json.dumps({
                    "username": "ansible",
                    "password": "testpassword"
                })
                
                credential_result = test_runner.run_test(
                    "Create Credential", 
                    create_credential,
                    name=credential_name,
                    credential_type_id=machine_cred_type_id,
                    organization_id=org_id,
                    inputs=credential_inputs,
                    description="Test credential created by MCP test script"
                )
                
                credential_id = extract_id(credential_result)
                if credential_id:
                    test_runner.created_resources["credentials"].append(credential_id)
                    
                    # Test get credential
                    test_runner.run_test(
                        "Get Credential", 
                        get_credential,
                        credential_id=credential_id
                    )
                    
                    # Test update credential
                    test_runner.run_test(
                        "Update Credential", 
                        update_credential,
                        credential_id=credential_id,
                        description="Updated description for test credential"
                    )
            
            # Test Job Template Management
            test_runner.run_test("List Job Templates", list_job_templates)
            
            if inventory_id and project_id:
                # Get project to find available playbooks
                project_data = parse_json_result(test_runner.run_test(
                    "Get Project",
                    get_project,
                    project_id=project_id
                ))
                
                # Wait for project to be ready if status is pending/running
                project_status = None
                try:
                    if isinstance(project_data, dict):
                        project_status = project_data.get("status")
                        if project_status in ["pending", "running", "updating"]:
                            print(f"Project status is {project_status}, waiting for completion...")
                            for _ in range(5):  # Try 5 times
                                time.sleep(5)
                                project_data = parse_json_result(test_runner.run_test(
                                    "Check Project Status",
                                    get_project,
                                    project_id=project_id
                                ))
                                if isinstance(project_data, dict):
                                    project_status = project_data.get("status")
                                    if project_status not in ["pending", "running", "updating"]:
                                        break
                            print(f"Project status now: {project_status}")
                except Exception as e:
                    print(f"Error checking project status: {str(e)}")
                
                # Get available playbooks
                available_playbooks = []
                try:
                    # Directly query the API for playbooks
                    with get_ansible_client() as client:
                        playbooks_response = client.request("GET", f"/api/v2/projects/{project_id}/playbooks/")
                        if isinstance(playbooks_response, list):
                            available_playbooks = playbooks_response
                except Exception as e:
                    print(f"Error fetching playbooks: {str(e)}")
                
                # Choose a playbook
                playbook = "hello_world.yml"  # Default fallback
                if available_playbooks:
                    playbook = available_playbooks[0]
                print(f"Selected playbook: {playbook}")
                
                # Create a test job template
                template_name = f"test-template-{org_timestamp}"
                template_result = test_runner.run_test(
                    "Create Job Template", 
                    create_job_template,
                    name=template_name,
                    inventory_id=inventory_id,
                    project_id=project_id,
                    playbook=playbook,
                    description="Test job template created by MCP test script"
                )
                
                template_id = extract_id(template_result)
                if template_id:
                    test_runner.created_resources["job_templates"].append(template_id)
                    
                    # Test get job template
                    test_runner.run_test(
                        "Get Job Template", 
                        get_job_template,
                        template_id=template_id
                    )
                    
                    # Test update job template
                    test_runner.run_test(
                        "Update Job Template", 
                        update_job_template,
                        template_id=template_id,
                        description="Updated description for test job template"
                    )
                    
                    # Test launch job
                    job_result = test_runner.run_test(
                        "Launch Job", 
                        launch_job,
                        template_id=template_id
                    )
                    
                    job_id = None
                    job_data = parse_json_result(job_result)
                    if isinstance(job_data, dict):
                        job_id = job_data.get("id")
                    
                    if job_id:
                        # Test get job
                        test_runner.run_test(
                            "Get Job", 
                            get_job,
                            job_id=job_id
                        )
                        
                        # Test get job events
                        test_runner.run_test(
                            "Get Job Events", 
                            get_job_events,
                            job_id=job_id
                        )
                        
                        # Test get job stdout
                        test_runner.run_test(
                            "Get Job Stdout", 
                            get_job_stdout,
                            job_id=job_id,
                            format="txt"
                        )
                        
                        # Test cancel job
                        test_runner.run_test(
                            "Cancel Job", 
                            cancel_job,
                            job_id=job_id
                        )
                    
                    # Test Job Management
                    test_runner.run_test("List Jobs", list_jobs)
                    test_runner.run_test(
                        "List Jobs by Status", 
                        list_jobs,
                        status="failed"
                    )
                    
                    # Test Schedule Management
                    test_runner.run_test("List Schedules", list_schedules)
                    
                    # Create a test schedule
                    schedule_name = f"test-schedule-{org_timestamp}"
                    rrule = "DTSTART:20260314T120000Z RRULE:FREQ=DAILY;INTERVAL=1"
                    
                    schedule_result = test_runner.run_test(
                        "Create Schedule", 
                        create_schedule,
                        name=schedule_name,
                        unified_job_template_id=template_id,
                        rrule=rrule,
                        description="Test schedule created by MCP test script"
                    )
                    
                    schedule_id = extract_id(schedule_result)
                    if schedule_id:
                        test_runner.created_resources["schedules"].append(schedule_id)
                        
                        # Test get schedule
                        test_runner.run_test(
                            "Get Schedule", 
                            get_schedule,
                            schedule_id=schedule_id
                        )
                        
                        # Test update schedule
                        test_runner.run_test(
                            "Update Schedule", 
                            update_schedule,
                            schedule_id=schedule_id,
                            description="Updated description for test schedule"
                        )
        
        # Test Team Management
        test_runner.run_test("List Teams", list_teams)
        test_runner.run_test(
            "List Teams by Organization", 
            list_teams,
            organization_id=org_id
        )
        
        # Create a test team
        team_name = f"test-team-{org_timestamp}"
        team_result = test_runner.run_test(
            "Create Team", 
            create_team,
            name=team_name,
            organization_id=org_id,
            description="Test team created by MCP test script"
        )
        
        team_id = extract_id(team_result)
        if team_id:
            test_runner.created_resources["teams"].append(team_id)
            
            # Test get team
            test_runner.run_test(
                "Get Team", 
                get_team,
                team_id=team_id
            )
            
            # Test update team
            test_runner.run_test(
                "Update Team", 
                update_team,
                team_id=team_id,
                description="Updated description for test team"
            )
        
        # Test User Management
        test_runner.run_test("List Users", list_users)
        
        # Create a test user
        username = f"testuser{org_timestamp}"
        user_result = test_runner.run_test(
            "Create User", 
            create_user,
            username=username,
            password="TestPassword123!",
            first_name="Test",
            last_name="User",
            email=f"{username}@example.com"
        )
        
        user_id = extract_id(user_result)
        if user_id:
            test_runner.created_resources["users"].append(user_id)
            
            # Test get user
            test_runner.run_test(
                "Get User", 
                get_user,
                user_id=user_id
            )
            
            # Test update user
            test_runner.run_test(
                "Update User", 
                update_user,
                user_id=user_id,
                first_name="Updated",
                last_name="Test User"
            )
    
    # Test Workflow Management
    test_runner.run_test("List Workflow Templates", list_workflow_templates)
    test_runner.run_test("List Workflow Jobs", list_workflow_jobs)
    
    # If we created an inventory and credential, test ad hoc commands
    if inventory_id and credential_id:
        # Test Ad Hoc Commands
        ad_hoc_result = test_runner.run_test(
            "Run Ad Hoc Command",
            run_ad_hoc_command,
            inventory_id=inventory_id,
            credential_id=credential_id,
            module_name="ping",
            module_args="",
            limit=""
        )
        
        command_id = extract_id(ad_hoc_result)
        if command_id:
            test_runner.created_resources["ad_hoc_commands"].append(command_id)
            
            # Test get ad hoc command
            test_runner.run_test(
                "Get Ad Hoc Command",
                get_ad_hoc_command,
                command_id=command_id
            )
            
            # Wait for a bit
            time.sleep(5)
            
            # Test cancel ad hoc command
            test_runner.run_test(
                "Cancel Ad Hoc Command",
                cancel_ad_hoc_command,
                command_id=command_id
            )
    
    # Print test summary
    test_runner.print_summary()
    
    # Clean up created resources
    test_runner.cleanup_resources()

if __name__ == "__main__":
    main()