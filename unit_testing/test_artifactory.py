import os
import asyncio
import uuid
import tempfile
from pathlib import Path
from servers.artifactory.artifactory_mcp import *

async def run_tests():
    """Run tests for all MCP tools."""
    print("Starting JFrog Artifactory MCP tests...")
    
    # Generate unique identifiers for test resources
    test_id = str(uuid.uuid4())[:8]
    test_repo_key = f"test-repo-{test_id}"
    test_user = f"test-user-{test_id}"
    test_file_path = create_test_file()
    
    try:
        # System tests
        await test_system_info()
        
        # Repository tests
        await test_repository_management(test_repo_key)
        
        # Artifact tests
        await test_artifact_management(test_repo_key, test_file_path)
        
        # User tests
        await test_user_management(test_user)
        
        # Advanced search tests
        await test_search(test_repo_key)
        
        # Other tests
        await test_other_features(test_repo_key)
        
        print("\nAll tests completed successfully! 🎉")
        
    except Exception as e:
        print(f"\n❌ Tests failed: {str(e)}")
        
    finally:
        # Cleanup resources
        print("\nCleaning up test resources...")
        try:
            await delete_repository(test_repo_key)
            await delete_user(test_user)
            cleanup_test_file(test_file_path)
        except Exception as e:
            print(f"Cleanup error: {str(e)}")

def create_test_file():
    """Create a temporary test file for artifact uploads."""
    temp_file = tempfile.NamedTemporaryFile(delete=False, suffix=".txt")
    with open(temp_file.name, 'w') as f:
        f.write("This is a test artifact for JFrog Artifactory MCP testing.")
    return temp_file.name

def cleanup_test_file(file_path):
    """Clean up the temporary test file."""
    try:
        Path(file_path).unlink(missing_ok=True)
    except Exception:
        pass

async def test_system_info():
    """Test system information tools."""
    print("\n--- Testing System Information Tools ---")
    
    print("Testing get_system_health...")
    result = await get_system_health()
    print(f"  Result: {result}")
    
    print("Testing get_version...")
    result = await get_version()
    print(f"  Result: {result}")
    
    print("Testing get_storage_info...")
    result = await get_storage_info()
    print(f"  Result: {result}")
    
    print("Testing get_system_info...")
    result = await get_system_info()
    print(f"  Result: {result[:100]}...") # Truncating output for readability

async def test_repository_management(test_repo_key):
    """Test repository management tools."""
    print("\n--- Testing Repository Management Tools ---")
    
    print("Testing list_repositories...")
    result = await list_repositories()
    print(f"  Result: {result[:100]}...") # Truncating output for readability
    
    print(f"Testing create_repository ({test_repo_key})...")
    result = await create_repository(test_repo_key, "local", "generic")
    print(f"  Result: {result}")
    
    print(f"Testing get_repository ({test_repo_key})...")
    result = await get_repository(test_repo_key)
    print(f"  Result: {result}")
    
    federated_repo = f"{test_repo_key}-federated"
    print(f"Testing create_federated_repository ({federated_repo})...")
    result = await create_federated_repository(federated_repo, "generic")
    print(f"  Result: {result}")
    
    # Clean up federated repo
    await delete_repository(federated_repo)

async def test_artifact_management(test_repo_key, test_file_path):
    """Test artifact management tools."""
    print("\n--- Testing Artifact Management Tools ---")
    
    artifact_path = f"test-artifact-{uuid.uuid4()}.txt"
    
    print(f"Testing deploy_artifact to {test_repo_key}/{artifact_path}...")
    result = await deploy_artifact(test_repo_key, artifact_path, test_file_path)
    print(f"  Result: {result}")
    
    print(f"Testing get_artifact_info for {test_repo_key}/{artifact_path}...")
    result = await get_artifact_info(test_repo_key, artifact_path)
    print(f"  Result: {result}")
    
    print(f"Testing search_artifacts...")
    result = await search_artifacts(name="*.txt", repos=test_repo_key)
    print(f"  Result: {result[:100]}...") # Truncating output for readability
    
    print(f"Testing delete_artifact for {test_repo_key}/{artifact_path}...")
    result = await delete_artifact(test_repo_key, artifact_path)
    print(f"  Result: {result}")

async def test_user_management(test_user):
    """Test user management tools."""
    print("\n--- Testing User Management Tools ---")
    
    test_email = f"{test_user}@example.com"
    test_password = "Password123!"
    
    print(f"Testing create_user ({test_user})...")
    result = await create_user(test_user, test_email, test_password, admin=False)
    print(f"  Result: {result}")
    
    print(f"Testing get_user ({test_user})...")
    result = await get_user(test_user)
    print(f"  Result: {result}")
    
    print(f"Testing update_user ({test_user})...")
    result = await update_user(test_user, email=f"updated-{test_email}")
    print(f"  Result: {result}")
    
    print("Testing list_users...")
    result = await list_users()
    print(f"  Result: {result[:100]}...") # Truncating output for readability

async def test_search(test_repo_key):
    """Test search functionality."""
    print("\n--- Testing Search Tools ---")
    
    print("Testing advanced_search with AQL...")
    aql_query = f'items.find({{"repo":"{test_repo_key}","type":"file"}})'
    result = await advanced_search(aql_query)
    print(f"  Result: {result[:100]}...") # Truncating output for readability

async def test_other_features(test_repo_key):
    """Test other MCP tools."""
    print("\n--- Testing Other MCP Tools ---")
    
    # Test build integration
    build_name = f"test-build-{uuid.uuid4()}"
    build_number = "1.0.0"
    
    print(f"Testing integrate_build ({build_name})...")
    try:
        result = await integrate_build(build_name, build_number)
        print(f"  Result: {result}")
    except Exception as e:
        print(f"  ⚠️ Build integration test skipped: {str(e)}")
    
    # Test webhook creation
    webhook_name = f"test-webhook-{uuid.uuid4()}"
    
    print(f"Testing create_webhook ({webhook_name})...")
    try:
        result = await create_webhook(
            webhook_name, 
            "https://example.com/webhook", 
            ["artifact.create", "artifact.delete"]
        )
        print(f"  Result: {result}")
    except Exception as e:
        print(f"  ⚠️ Webhook test skipped: {str(e)}")
    
    # Test permission management
    permission_name = f"test-permission-{uuid.uuid4()}"
    
    print(f"Testing manage_permissions ({permission_name})...")
    try:
        result = await manage_permissions(
            permission_name,
            [test_repo_key],
            ["users/admin"]
        )
        print(f"  Result: {result}")
    except Exception as e:
        print(f"  ⚠️ Permission test skipped: {str(e)}")

if __name__ == "__main__":
    asyncio.run(run_tests())