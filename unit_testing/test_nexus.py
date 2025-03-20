#!/usr/bin/env python3
import os
import json
import uuid
import sys

# Make sure to import from our fixed module
from servers.nexus.nexus_mcp import *

# Helper function to print test results
def print_result(function_name, result):
    print(f"\n===== Testing {function_name} =====")
    print(result)
    print("=" * 50)
    
    # Check if there's an error in the result
    try:
        result_obj = json.loads(result)
        if isinstance(result_obj, dict) and "error" in result_obj:
            print(f"ERROR in {function_name}: {result_obj['error']}")
            return False
        return True
    except:
        print(f"WARNING: Could not parse JSON result from {function_name}")
        return False

def run_tests():
    # Set up environment first
    setup_environment()
    
    print("Starting Nexus API Tests...")
    print(f"Using Nexus URL: {os.environ.get('NEXUS_URL')}")
    print(f"Using Nexus Username: {os.environ.get('NEXUS_USERNAME')}")
    print(f"Using Nexus Password: {'*' * len(os.environ.get('NEXUS_PASSWORD', ''))}")
    
    # Generate unique identifiers for test resources
    test_id = str(uuid.uuid4())[:8]
    repo_name = f"test-repo-{test_id}"
    user_id = f"test-user-{test_id}"
    role_id = f"test-role-{test_id}"
    ldap_name = f"test-ldap-{test_id}"
    selector_name = f"test-selector-{test_id}"
    privilege_name = f"test-privilege-{test_id}"
    webhook_name = f"test-webhook-{test_id}"
    
    # List of all test functions to run
    test_results = {}
    
    # 1. Repository Management Tests
    print("\n\n========== REPOSITORY MANAGEMENT TESTS ==========")
    
    # Get all repositories
    try:
        result = get_all_repositories()
        test_results["get_all_repositories"] = print_result("get_all_repositories", result)
    except Exception as e:
        print(f"ERROR in get_all_repositories: {str(e)}")
        test_results["get_all_repositories"] = False
    
    # Create a new repository
    try:
        result = create_repository(
            repository_type="hosted",
            repository_format="maven2",
            repository_name=repo_name,
            blob_store_name="default",
            online=True,
            write_policy="ALLOW"
        )
        test_results["create_repository"] = print_result("create_repository", result)
    except Exception as e:
        print(f"ERROR in create_repository: {str(e)}")
        test_results["create_repository"] = False
    
    # Update the repository with new configuration
    try:
        repo_config = {
            "name": repo_name,
            "online": True,
            "storage": {
                "blobStoreName": "default",
                "strictContentTypeValidation": False,
                "writePolicy": "ALLOW_ONCE"
            }
        }
        result = update_repository(
            repository_name=repo_name,
            repository_type="hosted",
            repository_format="maven2",
            repository_data=json.dumps(repo_config)
        )
        test_results["update_repository"] = print_result("update_repository", result)
    except Exception as e:
        print(f"ERROR in update_repository: {str(e)}")
        test_results["update_repository"] = False
    
    # 2. User and Role Management Tests
    print("\n\n========== USER AND ROLE MANAGEMENT TESTS ==========")
    
    # List all users
    try:
        result = get_all_users()
        test_results["get_all_users"] = print_result("get_all_users", result)
    except Exception as e:
        print(f"ERROR in get_all_users: {str(e)}")
        test_results["get_all_users"] = False
    
    # List roles
    try:
        result = list_roles()
        test_results["list_roles"] = print_result("list_roles", result)
    except Exception as e:
        print(f"ERROR in list_roles: {str(e)}")
        test_results["list_roles"] = False
    
    # List privileges
    try:
        result = list_privileges()
        test_results["list_privileges"] = print_result("list_privileges", result)
        
        # Find a privilege ID to use for role creation
        privilege_id = None
        try:
            privileges_data = json.loads(result)
            if privileges_data and len(privileges_data) > 0:
                privilege_id = privileges_data[0].get("name")
                print(f"Using privilege ID for tests: {privilege_id}")
        except:
            print("Could not find a privilege ID to use for role creation")
    except Exception as e:
        print(f"ERROR in list_privileges: {str(e)}")
        test_results["list_privileges"] = False
    
    # Create a new role
    if privilege_id:
        try:
            result = create_role(
                role_id=role_id,
                name=f"Test Role {test_id}",
                description="Role created by automated test",
                privileges=[privilege_id],
                roles=[]
            )
            test_results["create_role"] = print_result("create_role", result)
        except Exception as e:
            print(f"ERROR in create_role: {str(e)}")
            test_results["create_role"] = False
    
    # Create a new user
    try:
        result = create_user(
            user_id=user_id,
            first_name="Test",
            last_name="User",
            email=f"test.user.{test_id}@example.com",
            password="TestPassword123!",
            status="active",
            roles=["nx-admin"]  # Default admin role
        )
        test_results["create_user"] = print_result("create_user", result)
    except Exception as e:
        print(f"ERROR in create_user: {str(e)}")
        test_results["create_user"] = False
    
    # Update the user
    try:
        result = update_user(
            user_id=user_id,
            first_name="Updated",
            last_name="TestUser",
            email=f"updated.test.user.{test_id}@example.com",
            status="active",
            roles=["nx-admin"]
        )
        test_results["update_user"] = print_result("update_user", result)
    except Exception as e:
        print(f"ERROR in update_user: {str(e)}")
        test_results["update_user"] = False
    
    # 3. Content Management Tests
    print("\n\n========== CONTENT MANAGEMENT TESTS ==========")
    
    # Search for components
    try:
        result = search_components(repository="maven-central")
        test_results["search_components"] = print_result("search_components", result)
    except Exception as e:
        print(f"ERROR in search_components: {str(e)}")
        test_results["search_components"] = False
    
    # 4. Content Selectors Tests
    print("\n\n========== CONTENT SELECTORS TESTS ==========")
    
    # List content selectors
    try:
        result = list_content_selectors()
        test_results["list_content_selectors"] = print_result("list_content_selectors", result)
    except Exception as e:
        print(f"ERROR in list_content_selectors: {str(e)}")
        test_results["list_content_selectors"] = False
    
    # Create a content selector
    try:
        result = create_content_selector(
            name=selector_name,
            description="Test selector created by automated test",
            expression="format == 'maven2'"
        )
        test_results["create_content_selector"] = print_result("create_content_selector", result)
    except Exception as e:
        print(f"ERROR in create_content_selector: {str(e)}")
        test_results["create_content_selector"] = False
    
    # 5. LDAP Tests
    print("\n\n========== LDAP TESTS ==========")
    
    # List LDAP servers
    try:
        result = list_ldap_servers()
        test_results["list_ldap_servers"] = print_result("list_ldap_servers", result)
    except Exception as e:
        print(f"ERROR in list_ldap_servers: {str(e)}")
        test_results["list_ldap_servers"] = False
    
    # 6. Webhooks Tests
    print("\n\n========== WEBHOOKS TESTS ==========")
    
    # List webhooks
    try:
        result = list_webhooks()
        test_results["list_webhooks"] = print_result("list_webhooks", result)
    except Exception as e:
        print(f"ERROR in list_webhooks: {str(e)}")
        test_results["list_webhooks"] = False
    
    # Create webhook
    try:
        result = create_webhook(
            name=webhook_name,
            url="https://webhook.example.com/endpoint",
            webhook_type="repository_created"
        )
        test_results["create_webhook"] = print_result("create_webhook", result)
    except Exception as e:
        print(f"ERROR in create_webhook: {str(e)}")
        test_results["create_webhook"] = False
    
    # 7. Firewall Configuration Tests
    print("\n\n========== FIREWALL CONFIGURATION TESTS ==========")
    
    # Get firewall config
    try:
        result = get_firewall_config()
        test_results["get_firewall_config"] = print_result("get_firewall_config", result)
    except Exception as e:
        print(f"ERROR in get_firewall_config: {str(e)}")
        test_results["get_firewall_config"] = False
    
    # 8. Clean up
    print("\n\n========== CLEANUP ==========")
    
    # Delete user (only if we created one successfully)
    if test_results.get("create_user", False):
        try:
            result = delete_user(user_id)
            cleanup_success = print_result("delete_user", result)
            if not cleanup_success:
                print(f"WARNING: Failed to clean up test user {user_id}")
        except Exception as e:
            print(f"ERROR cleaning up user {user_id}: {str(e)}")
    
    # Delete repository (only if we created one successfully)
    if test_results.get("create_repository", False):
        try:
            result = delete_repository(repo_name)
            cleanup_success = print_result("delete_repository", result)
            if not cleanup_success:
                print(f"WARNING: Failed to clean up test repository {repo_name}")
        except Exception as e:
            print(f"ERROR cleaning up repository {repo_name}: {str(e)}")
    
    # Print summary
    print("\n\n========== TEST SUMMARY ==========")
    passed = sum(1 for result in test_results.values() if result)
    total = len(test_results)
    
    if total > 0:
        print(f"Tests passed: {passed}/{total} ({passed/total*100:.1f}%)")
    else:
        print("No tests were run successfully.")
    
    for test_name, passed in test_results.items():
        status = "✅ PASS" if passed else "❌ FAIL"
        print(f"{status}: {test_name}")
    
    return passed == total  # Return True if all tests passed

if __name__ == "__main__":
    success = run_tests()
    sys.exit(0 if success else 1)  # Exit with appropriate status code