import pytest
import pytest_asyncio
import os
import json
import uuid
import sys
from pathlib import Path

# Fix import paths
sys.path.append(str(Path(__file__).parent.parent))
import servers.bitbucket_cloud.bitbucket_cloud_mcp as bitbucket_mcp

# Custom Context class
class TestContext:
    def get_config(self, key):
        return os.environ.get(key)
    
    def error(self, message):
        print(f"ERROR: {message}")

# Test configuration
TEST_PREFIX = f"test-{uuid.uuid4().hex[:8]}"
TEST_REPO_SLUG = f"{TEST_PREFIX}-repo"
TEST_PROJECT_KEY = f"T{TEST_PREFIX[:7].upper()}"
TEST_BRANCH = f"test-branch-{TEST_PREFIX}"
TEST_COMMIT = None
TEST_PR_ID = None

# Storage for created resources 
created_resources = {}

@pytest.fixture(scope="session")  # Changed to session scope
def ctx():
    """Create a custom test context."""
    return TestContext()

@pytest_asyncio.fixture(scope="session")
async def test_environment(ctx):
    """Set up test environment and clean up after tests."""
    global created_resources
    
    # Make sure we have credentials
    if not os.environ.get("BITBUCKET_USERNAME") or not os.environ.get("BITBUCKET_APP_PASSWORD"):
        pytest.skip("BITBUCKET_USERNAME and BITBUCKET_APP_PASSWORD must be set in environment")
    
    try:
        # Test credentials by getting current user
        user_result = await bitbucket_mcp.get_current_user(ctx)
        user_data = json.loads(user_result)
        print(f"Testing as user: {user_data['username']}")
        
        # Find a workspace to use
        workspaces_result = await bitbucket_mcp.list_workspaces(ctx)
        workspaces_data = json.loads(workspaces_result)
        
        if not workspaces_data.get('values') or len(workspaces_data['values']) == 0:
            pytest.skip("No workspaces available. Create one in Bitbucket before testing.")
        
        # Use first available workspace
        created_resources['workspace'] = workspaces_data['values'][0]['slug']
        print(f"Using workspace: {created_resources['workspace']}")
        
    except Exception as e:
        pytest.skip(f"Test environment setup failed: {e}")
    
    yield
    
    # Clean up all created resources
    print("Cleaning up test resources...")
    
    # Repository cleanup
    if 'repository' in created_resources:
        try:
            await bitbucket_mcp.delete_repository(ctx, created_resources['workspace'], TEST_REPO_SLUG)
            print(f"Deleted test repository: {TEST_REPO_SLUG}")
        except Exception as e:
            print(f"Error deleting repository: {e}")
    
    # Project cleanup
    if 'project' in created_resources:
        try:
            await bitbucket_mcp.delete_project(ctx, created_resources['workspace'], TEST_PROJECT_KEY)
            print(f"Deleted test project: {TEST_PROJECT_KEY}")
        except Exception as e:
            print(f"Error deleting project: {e}")

@pytest.mark.asyncio
async def test_01_user_operations(ctx, test_environment):
    """Test user-related operations."""
    # Get current user
    result = await bitbucket_mcp.get_current_user(ctx)
    user_data = json.loads(result)
    assert "username" in user_data
    
    # Get user profile
    result = await bitbucket_mcp.get_user_profile(ctx, user_data["username"])
    profile_data = json.loads(result)
    assert profile_data["username"] == user_data["username"]

@pytest.mark.asyncio
async def test_02_create_project(ctx, test_environment):
    """Test creating a project."""
    global created_resources
    
    workspace = created_resources['workspace']
    result = await bitbucket_mcp.create_project(
        ctx, workspace, f"Test Project {TEST_PREFIX}", 
        TEST_PROJECT_KEY, "Project for integration testing", True
    )
    
    project_data = json.loads(result)
    assert "key" in project_data
    assert project_data["key"] == TEST_PROJECT_KEY
    
    created_resources['project'] = TEST_PROJECT_KEY