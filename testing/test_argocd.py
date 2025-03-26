"""
Comprehensive Test Script for Argo CD MCP Server

This script tests all implemented MCP tools, including create and delete operations.
"""

import json
import time
import uuid
from servers.argocd.argocd_mcp import (
    list_applications,
    get_application,
    create_application,
    delete_application,
    sync_application,
    
    list_projects,
    get_project,
    create_project,
    delete_project,
    
    list_repositories,
    get_repository,
    create_repository,
    delete_repository,
    
    list_clusters,
    get_cluster,
    
    get_version,
    get_settings
)

def print_section(title):
    """Print a section title with formatting."""
    print("\n" + "=" * 80)
    print(f" {title} ".center(80, "="))
    print("=" * 80 + "\n")

def pretty_print(json_str):
    """Pretty print JSON string."""
    try:
        data = json.loads(json_str)
        print(json.dumps(data, indent=2))
    except json.JSONDecodeError:
        print(json_str)

def run_test(title, func, *args, **kwargs):
    """Run a test function and print results."""
    print_section(title)
    print(f"Running: {func.__name__}({', '.join([repr(a) for a in args] + [f'{k}={repr(v)}' for k, v in kwargs.items()])})")
    try:
        result = func(*args, **kwargs)
        print("\nResult:")
        pretty_print(result)
        return result
    except Exception as e:
        print(f"\nError: {str(e)}")
        return None

test_id = str(uuid.uuid4())[:8]
test_project_name = f"test-project-{test_id}"
test_app_name = f"test-app-{test_id}"
test_repo_url = f"https://github.com/test-org/test-repo-{test_id}"

print_section("STARTING COMPREHENSIVE TESTS")
print(f"Test ID: {test_id}")
print(f"Test Project: {test_project_name}")
print(f"Test Application: {test_app_name}")
print(f"Test Repository: {test_repo_url}")

run_test("VERSION", get_version)
run_test("SETTINGS", get_settings)

run_test("LIST CLUSTERS", list_clusters)
clusters_json = list_clusters()
clusters = json.loads(clusters_json)
if clusters.get("items"):
    cluster_server = clusters["items"][0]["server"]
    run_test("GET CLUSTER", get_cluster, cluster_server)

run_test("LIST PROJECTS (BEFORE)", list_projects)

run_test("CREATE PROJECT", create_project, 
         name=test_project_name, 
         description=f"Test project created by MCP test {test_id}",
         source_repos=["*"])

time.sleep(2)

run_test("GET PROJECT", get_project, test_project_name)

run_test("LIST PROJECTS (AFTER CREATE)", list_projects)

run_test("LIST REPOSITORIES (BEFORE)", list_repositories)

try:
    run_test("CREATE REPOSITORY", create_repository,
             repo=test_repo_url,
             username="test-user",
             password="test-password")
    
    time.sleep(2)
    
    run_test("GET REPOSITORY", get_repository, test_repo_url)
    
    run_test("LIST REPOSITORIES (AFTER CREATE)", list_repositories)
except Exception as e:
    print(f"Repository tests skipped due to error: {str(e)}")

run_test("LIST APPLICATIONS (BEFORE)", list_applications)

try:
    clusters_json = list_clusters()
    clusters = json.loads(clusters_json)
    if clusters.get("items"):
        cluster_server = clusters["items"][0]["server"]
        
        run_test("CREATE APPLICATION", create_application,
                name=test_app_name,
                project=test_project_name,
                repo_url="https://github.com/argoproj/argocd-example-apps",
                path="guestbook",
                dest_server=cluster_server,
                dest_namespace="default")
        
        time.sleep(2)
        
        run_test("GET APPLICATION", get_application, test_app_name)
        
        run_test("LIST APPLICATIONS (AFTER CREATE)", list_applications)
        
        run_test("SYNC APPLICATION", sync_application, test_app_name)
except Exception as e:
    print(f"Application creation tests skipped due to error: {str(e)}")

print_section("CLEANUP")

try:
    run_test("DELETE APPLICATION", delete_application, test_app_name)
    time.sleep(2)
except Exception as e:
    print(f"Application deletion skipped: {str(e)}")

try:
    run_test("DELETE REPOSITORY", delete_repository, test_repo_url)
    time.sleep(2)
except Exception as e:
    print(f"Repository deletion skipped: {str(e)}")

try:
    run_test("DELETE PROJECT", delete_project, test_project_name)
except Exception as e:
    print(f"Project deletion skipped: {str(e)}")

print_section("VERIFICATION AFTER CLEANUP")
run_test("LIST APPLICATIONS (AFTER CLEANUP)", list_applications)
run_test("LIST REPOSITORIES (AFTER CLEANUP)", list_repositories)
run_test("LIST PROJECTS (AFTER CLEANUP)", list_projects)

print_section("TEST SUMMARY")
print("Comprehensive tests completed!")
print("The Argo CD MCP Server has been tested with all implemented tools.")
