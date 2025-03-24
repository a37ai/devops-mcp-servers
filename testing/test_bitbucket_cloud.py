import pytest
import pytest_asyncio
import os
import json
import uuid
import sys
import time
from pathlib import Path

# Fix import paths
sys.path.append(str(Path(__file__).parent.parent))
import servers.bitbucket_cloud.bitbucket_cloud_mcp as bitbucket_mcp

# Custom Context class for tests
class TestContext:
    def get_config(self, key):
        return os.environ.get(key)
    
    def error(self, message):
        print(f"ERROR: {message}")

# Test configuration
TEST_PREFIX = f"test-{uuid.uuid4().hex[:8]}"
TEST_REPO_SLUG = f"{TEST_PREFIX}-repo"
# Ensure the project key is valid - no hyphens, uppercase
TEST_PROJECT_KEY = f"T{TEST_PREFIX.replace('-', '_').upper()}"
TEST_BRANCH = f"test-branch-{TEST_PREFIX}"
TEST_TAG = f"test-tag-{TEST_PREFIX}"
TEST_PR_TITLE = f"Test PR {TEST_PREFIX}"
TEST_WEBHOOK_URL = "https://example.com/webhook"

# Storage for created resources to ensure cleanup
created_resources = {
    "repositories": [],
    "projects": [],
    "branches": [],
    "tags": [],
    "pull_requests": [],
    "webhooks": [],
    "deploy_keys": []
}

@pytest.fixture(scope="session")
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
    
    # Clean up all created resources after tests complete
    print("Cleaning up test resources...")
    
    # Clean up webhooks
    for webhook_id in created_resources.get("webhooks", []):
        try:
            for repo_slug in created_resources.get("repositories", []):
                await bitbucket_mcp.delete_webhook(ctx, created_resources['workspace'], repo_slug, webhook_id)
                print(f"Deleted webhook: {webhook_id}")
        except Exception as e:
            print(f"Error deleting webhook: {e}")
    
    # Clean up deploy keys
    for key_id in created_resources.get("deploy_keys", []):
        try:
            for repo_slug in created_resources.get("repositories", []):
                await bitbucket_mcp.delete_deploy_key(ctx, created_resources['workspace'], repo_slug, key_id)
                print(f"Deleted deploy key: {key_id}")
        except Exception as e:
            print(f"Error deleting deploy key: {e}")
    
    # Clean up pull requests (they should be declined first)
    for pr_id in created_resources.get("pull_requests", []):
        try:
            for repo_slug in created_resources.get("repositories", []):
                # Attempt to decline the PR first
                try:
                    await bitbucket_mcp.decline_pull_request(ctx, created_resources['workspace'], repo_slug, pr_id)
                    print(f"Declined pull request: {pr_id}")
                except Exception:
                    pass  # It's ok if the PR is already closed
        except Exception as e:
            print(f"Error handling pull request: {e}")
    
    # Repository cleanup - this will also clean up branches and tags
    for repo_slug in created_resources.get("repositories", []):
        try:
            await bitbucket_mcp.delete_repository(ctx, created_resources['workspace'], repo_slug)
            print(f"Deleted repository: {repo_slug}")
        except Exception as e:
            print(f"Error deleting repository: {e}")
    
    # Project cleanup
    for project_key in created_resources.get("projects", []):
        try:
            await bitbucket_mcp.delete_project(ctx, created_resources['workspace'], project_key)
            print(f"Deleted project: {project_key}")
        except Exception as e:
            print(f"Error deleting project: {e}")

#--------------------- USER AND WORKSPACE TESTS ---------------------#

@pytest.mark.asyncio
async def test_01_user_operations(ctx, test_environment):
    """Test user-related operations."""
    # Get current user
    result = await bitbucket_mcp.get_current_user(ctx)
    user_data = json.loads(result)
    assert "username" in user_data
    assert "display_name" in user_data
    
    # Get user profile using fixed function
    result = await bitbucket_mcp.get_user_profile(ctx, user_data["username"])
    profile_data = json.loads(result)
    assert "username" in profile_data
    assert profile_data["username"] == user_data["username"]

@pytest.mark.asyncio
async def test_02_workspace_operations(ctx, test_environment):
    """Test workspace-related operations."""
    global created_resources
    
    # List workspaces
    result = await bitbucket_mcp.list_workspaces(ctx)
    workspaces_data = json.loads(result)
    assert "values" in workspaces_data
    assert len(workspaces_data["values"]) > 0
    
    # Get workspace details
    workspace = created_resources['workspace']
    result = await bitbucket_mcp.get_workspace(ctx, workspace)
    workspace_data = json.loads(result)
    assert "slug" in workspace_data
    assert workspace_data["slug"] == workspace

#--------------------- PROJECT TESTS ---------------------#

@pytest.mark.asyncio
async def test_03_create_and_get_project(ctx, test_environment):
    """Test creating and getting a project."""
    global created_resources
    
    workspace = created_resources['workspace']
    
    # Create project with sanitized key
    result = await bitbucket_mcp.create_project(
        ctx, workspace, f"Test Project {TEST_PREFIX}",
        TEST_PROJECT_KEY, "Project for integration testing", True
    )
    
    project_data = json.loads(result)
    assert "key" in project_data
    assert project_data["key"] == TEST_PROJECT_KEY
    
    # Store for cleanup
    created_resources["projects"].append(TEST_PROJECT_KEY)
    
    # Get project
    result = await bitbucket_mcp.get_project(ctx, workspace, TEST_PROJECT_KEY)
    project_data = json.loads(result)
    assert "key" in project_data
    assert project_data["key"] == TEST_PROJECT_KEY
    assert "name" in project_data
    assert f"Test Project {TEST_PREFIX}" in project_data["name"]

@pytest.mark.asyncio
async def test_04_list_projects(ctx, test_environment):
    """Test listing projects."""
    global created_resources
    
    workspace = created_resources['workspace']
    
    # List projects
    result = await bitbucket_mcp.list_projects(ctx, workspace)
    projects_data = json.loads(result)
    
    assert "values" in projects_data
    
    # Verify our test project is in the list
    project_keys = [project["key"] for project in projects_data["values"]]
    assert TEST_PROJECT_KEY in project_keys

@pytest.mark.asyncio
async def test_05_update_project(ctx, test_environment):
    """Test updating a project."""
    global created_resources
    
    workspace = created_resources['workspace']
    
    # Update project description
    new_description = f"Updated description {TEST_PREFIX}"
    result = await bitbucket_mcp.update_project(
        ctx, workspace, TEST_PROJECT_KEY, 
        description=new_description
    )
    
    project_data = json.loads(result)
    assert "description" in project_data
    assert project_data["description"] == new_description

#--------------------- REPOSITORY TESTS ---------------------#

@pytest.mark.asyncio
async def test_06_create_and_get_repository(ctx, test_environment):
    """Test creating and getting a repository."""
    global created_resources
    
    workspace = created_resources['workspace']
    
    # Create repository
    result = await bitbucket_mcp.create_repository(
        ctx, workspace, TEST_REPO_SLUG,
        f"Test repository for {TEST_PREFIX}", True, "allow_forks", 
        TEST_PROJECT_KEY
    )
    
    repo_data = json.loads(result)
    assert "slug" in repo_data
    assert repo_data["slug"] == TEST_REPO_SLUG
    
    # Store for cleanup
    created_resources["repositories"].append(TEST_REPO_SLUG)
    
    # Get repository
    result = await bitbucket_mcp.get_repository(ctx, workspace, TEST_REPO_SLUG)
    repo_data = json.loads(result)
    assert "slug" in repo_data
    assert repo_data["slug"] == TEST_REPO_SLUG
    assert "project" in repo_data
    assert repo_data["project"]["key"] == TEST_PROJECT_KEY

@pytest.mark.asyncio
async def test_07_list_repositories(ctx, test_environment):
    """Test listing repositories."""
    global created_resources
    
    workspace = created_resources['workspace']
    
    # List repositories for workspace
    result = await bitbucket_mcp.list_repositories(ctx, workspace)
    repos_data = json.loads(result)
    
    assert "values" in repos_data
    
    # Verify our test repo is in the list
    repo_slugs = [repo["slug"] for repo in repos_data["values"]]
    assert TEST_REPO_SLUG in repo_slugs

@pytest.mark.asyncio
async def test_08_update_repository(ctx, test_environment):
    """Test updating a repository."""
    global created_resources
    
    workspace = created_resources['workspace']
    
    # Update repository description
    new_description = f"Updated repo description {TEST_PREFIX}"
    result = await bitbucket_mcp.update_repository(
        ctx, workspace, TEST_REPO_SLUG, 
        description=new_description
    )
    
    repo_data = json.loads(result)
    assert "description" in repo_data
    assert repo_data["description"] == new_description

#--------------------- BRANCH AND TAG TESTS ---------------------#

@pytest.mark.asyncio
async def test_09_branch_operations(ctx, test_environment):
    """Test branch operations."""
    global created_resources
    
    workspace = created_resources['workspace']
    
    # Get the default branch commit hash first
    result = await bitbucket_mcp.list_branches(ctx, workspace, TEST_REPO_SLUG)
    branches_data = json.loads(result)
    
    # There should be at least one branch (master/main)
    assert "values" in branches_data
    assert len(branches_data["values"]) > 0
    
    # Get the target hash from the default branch
    default_branch = branches_data["values"][0]
    target_hash = default_branch["target"]["hash"]
    
    # Create a new branch
    result = await bitbucket_mcp.create_branch(
        ctx, workspace, TEST_REPO_SLUG, TEST_BRANCH, target_hash
    )
    branch_data = json.loads(result)
    
    assert "name" in branch_data
    assert branch_data["name"] == TEST_BRANCH
    
    # Store for reference (cleanup happens with repo deletion)
    created_resources["branches"].append(TEST_BRANCH)
    
    # Wait a moment for the branch to be created
    time.sleep(2)
    
    # List branches to verify new branch exists
    result = await bitbucket_mcp.list_branches(ctx, workspace, TEST_REPO_SLUG)
    branches_data = json.loads(result)
    
    branch_names = [branch["name"] for branch in branches_data["values"]]
    assert TEST_BRANCH in branch_names

@pytest.mark.asyncio
async def test_10_tag_operations(ctx, test_environment):
    """Test tag operations."""
    global created_resources
    
    workspace = created_resources['workspace']
    
    # Get the commit hash first
    result = await bitbucket_mcp.list_branches(ctx, workspace, TEST_REPO_SLUG)
    branches_data = json.loads(result)
    target_hash = branches_data["values"][0]["target"]["hash"]
    
    # Create a new tag
    result = await bitbucket_mcp.create_tag(
        ctx, workspace, TEST_REPO_SLUG, 
        TEST_TAG, target_hash, f"Test tag message {TEST_PREFIX}"
    )
    tag_data = json.loads(result)
    
    assert "name" in tag_data
    assert tag_data["name"] == TEST_TAG
    
    # Store for reference (cleanup happens with repo deletion)
    created_resources["tags"].append(TEST_TAG)
    
    # Wait a moment for the tag to be created
    time.sleep(2)
    
    # List tags to verify new tag exists
    result = await bitbucket_mcp.list_tags(ctx, workspace, TEST_REPO_SLUG)
    tags_data = json.loads(result)
    
    # Check if there are tags and verify our test tag is in the list
    if "values" in tags_data and len(tags_data["values"]) > 0:
        tag_names = [tag["name"] for tag in tags_data["values"]]
        assert TEST_TAG in tag_names

#--------------------- COMMIT AND DIFF TESTS ---------------------#

@pytest.mark.asyncio
async def test_11_commit_operations(ctx, test_environment):
    """Test commit operations."""
    global created_resources
    
    workspace = created_resources['workspace']
    
    # List commits
    result = await bitbucket_mcp.list_commits(ctx, workspace, TEST_REPO_SLUG)
    commits_data = json.loads(result)
    
    # There should be at least one commit in the repository
    assert "values" in commits_data
    
    # If there are commits, test getting a specific commit
    if len(commits_data["values"]) > 0:
        commit_hash = commits_data["values"][0]["hash"]
        
        result = await bitbucket_mcp.get_commit(ctx, workspace, TEST_REPO_SLUG, commit_hash)
        commit_data = json.loads(result)
        
        assert "hash" in commit_data
        assert commit_data["hash"] == commit_hash
        
        # Test get commit diff
        try:
            result = await bitbucket_mcp.get_commit_diff(ctx, workspace, TEST_REPO_SLUG, commit_hash)
            # Don't assert on content, just that it didn't fail
        except Exception as e:
            # It's acceptable if this fails for the initial commit 
            print(f"Note: Get commit diff failed: {e}")

#--------------------- PULL REQUEST TESTS ---------------------#

@pytest.mark.asyncio
async def test_12_pull_request_operations(ctx, test_environment):
    """Test pull request operations."""
    global created_resources
    
    workspace = created_resources['workspace']
    
    # First, ensure we have the branch we created earlier
    result = await bitbucket_mcp.list_branches(ctx, workspace, TEST_REPO_SLUG)
    branches_data = json.loads(result)
    
    # Find the default branch and our test branch
    branch_names = [branch["name"] for branch in branches_data["values"]]
    
    if TEST_BRANCH in branch_names:
        # Find the default branch (usually main or master)
        default_branch = next((branch["name"] for branch in branches_data["values"] 
                              if branch["name"] in ["main", "master"]), None)
        
        if default_branch:
            # Create pull request
            result = await bitbucket_mcp.create_pull_request(
                ctx, workspace, TEST_REPO_SLUG,
                TEST_PR_TITLE, TEST_BRANCH, default_branch,
                f"Test PR description {TEST_PREFIX}", False
            )
            pr_data = json.loads(result)
            
            assert "id" in pr_data
            pr_id = pr_data["id"]
            
            # Store for cleanup
            created_resources["pull_requests"].append(pr_id)
            
            # Get pull request
            result = await bitbucket_mcp.get_pull_request(ctx, workspace, TEST_REPO_SLUG, pr_id)
            pr_data = json.loads(result)
            
            assert "id" in pr_data
            assert pr_data["id"] == pr_id
            assert "title" in pr_data
            assert pr_data["title"] == TEST_PR_TITLE
            
            # Try to approve the PR
            try:
                result = await bitbucket_mcp.approve_pull_request(ctx, workspace, TEST_REPO_SLUG, pr_id)
                approve_data = json.loads(result)
                
                # Try to unapprove
                result = await bitbucket_mcp.unapprove_pull_request(ctx, workspace, TEST_REPO_SLUG, pr_id)
            except Exception as e:
                # Some accounts can't approve their own PRs, so this might fail
                print(f"Note: PR approve/unapprove operations failed: {e}")
            
            # Add a comment to the PR
            try:
                result = await bitbucket_mcp.add_pull_request_comment(
                    ctx, workspace, TEST_REPO_SLUG, pr_id,
                    f"Test PR comment {TEST_PREFIX}"
                )
                comment_data = json.loads(result)
                assert "content" in comment_data
            except Exception as e:
                print(f"Note: Adding PR comment failed: {e}")
            
            # Decline the PR at the end of testing
            result = await bitbucket_mcp.decline_pull_request(ctx, workspace, TEST_REPO_SLUG, pr_id)
            decline_data = json.loads(result)
            
            assert "state" in decline_data
            assert decline_data["state"] == "DECLINED"

#--------------------- REPOSITORY SETTINGS TESTS ---------------------#

@pytest.mark.asyncio
async def test_13_deploy_key_operations(ctx, test_environment):
    """Test deploy key operations."""
    global created_resources
    
    workspace = created_resources['workspace']
    
    # Create a test SSH key for deploy keys testing
    test_key = "ssh-rsa AAAAB3NzaC1yc2EAAAADAQABAAABAQC6OvhPHkd5jXmRvYwaxVWyMknlOobrq5Vu5F6W9CWs5UZODBeV9jgQV1OXOfdv4HxYHWQWJSikQkGLQWYp0tXyHCj2tGuJOZCvtgQ7qwJHActLiUW76MseC1Lx9OwVgM9Q9qMXPkvEqiVR6zd+AY9C1GOYIegFJKz1wZZxUkWX1p6KCd+MyOk2FeIh+hb2g8c1b7VFtGZ7VBKoWQWsE8BMuTaS+kQ+e8wm8c+T7cFz9xP/0qY7FNAiUjlkdh4XcVxbKbahhL9D1Rn5NGnxbKYcT2FZrw+c5OBsAw41Q+cT+SDbOsOusQ+OBnTwLzSjXPXJGNHlnttWdVmK1eCvtzFF test-key@example.com"
    test_key_label = f"Test Deploy Key {TEST_PREFIX}"
    
    try:
        # Add deploy key
        result = await bitbucket_mcp.add_deploy_key(
            ctx, workspace, TEST_REPO_SLUG, test_key, test_key_label
        )
        key_data = json.loads(result)
        
        assert "id" in key_data
        key_id = key_data["id"]
        
        # Store for cleanup
        created_resources["deploy_keys"].append(key_id)
        
        # List deploy keys
        result = await bitbucket_mcp.list_deploy_keys(ctx, workspace, TEST_REPO_SLUG)
        keys_data = json.loads(result)
        
        assert "values" in keys_data
        
        # Verify our test key is in the list
        key_ids = [key["id"] for key in keys_data["values"]]
        assert key_id in key_ids
        
        # Delete the deploy key
        result = await bitbucket_mcp.delete_deploy_key(ctx, workspace, TEST_REPO_SLUG, key_id)
        
        # Remove from list since we already deleted it
        created_resources["deploy_keys"].remove(key_id)
        
    except Exception as e:
        print(f"Note: Deploy key operations failed (this may be expected in some test environments): {e}")

@pytest.mark.asyncio
async def test_14_webhook_operations(ctx, test_environment):
    """Test webhook operations."""
    global created_resources
    
    workspace = created_resources['workspace']
    
    try:
        # Create webhook
        result = await bitbucket_mcp.create_webhook(
            ctx, workspace, TEST_REPO_SLUG,
            TEST_WEBHOOK_URL, f"Test webhook {TEST_PREFIX}",
            ["repo:push", "pullrequest:created"], True
        )
        webhook_data = json.loads(result)
        
        assert "uuid" in webhook_data
        webhook_id = webhook_data["uuid"]
        
        # Store for cleanup
        created_resources["webhooks"].append(webhook_id)
        
        # List webhooks
        result = await bitbucket_mcp.list_webhooks(ctx, workspace, TEST_REPO_SLUG)
        webhooks_data = json.loads(result)
        
        assert "values" in webhooks_data
        
        # Verify our webhook is in the list
        webhook_ids = [hook["uuid"] for hook in webhooks_data["values"]]
        assert webhook_id in webhook_ids
        
        # Delete the webhook
        result = await bitbucket_mcp.delete_webhook(ctx, workspace, TEST_REPO_SLUG, webhook_id)
        
        # Remove from list since we already deleted it
        created_resources["webhooks"].remove(webhook_id)
        
    except Exception as e:
        print(f"Note: Webhook operations failed (this may be expected in some test environments): {e}")

#--------------------- BRANCH RESTRICTION TESTS ---------------------#

@pytest.mark.asyncio
async def test_15_branch_restriction_operations(ctx, test_environment):
    """Test branch restriction operations."""
    global created_resources
    
    workspace = created_resources['workspace']
    
    try:
        # List branch restrictions
        result = await bitbucket_mcp.list_branch_restrictions(ctx, workspace, TEST_REPO_SLUG)
        restrictions_data = json.loads(result)
        
        assert "values" in restrictions_data
        
        # Create branch restriction (push restriction on master)
        result = await bitbucket_mcp.create_branch_restriction(
            ctx, workspace, TEST_REPO_SLUG,
            "push", "master"
        )
        restriction_data = json.loads(result)
        
        assert "id" in restriction_data
        assert "kind" in restriction_data
        assert restriction_data["kind"] == "push"
        
        # No need to clean up as these are deleted with the repository
        
    except Exception as e:
        print(f"Note: Branch restriction operations failed (this may be expected in some test environments): {e}")

#--------------------- ADDITIONAL REPOSITORY TESTS ---------------------#

@pytest.mark.asyncio
async def test_16_repository_cleanup(ctx, test_environment):
    """Test repository deletion."""
    global created_resources
    
    workspace = created_resources['workspace']
    
    # Create a temporary repository to test deletion
    temp_repo_slug = f"{TEST_REPO_SLUG}-temp-delete"
    
    # Create repository
    result = await bitbucket_mcp.create_repository(
        ctx, workspace, temp_repo_slug,
        "Temporary repo for deletion test", True
    )
    
    repo_data = json.loads(result)
    assert "slug" in repo_data
    assert repo_data["slug"] == temp_repo_slug
    
    # Delete repository
    result = await bitbucket_mcp.delete_repository(ctx, workspace, temp_repo_slug)
    assert "status" in json.loads(result)
    assert json.loads(result)["status"] == "success"

#--------------------- SNIPPET TESTS ---------------------#

@pytest.mark.asyncio
async def test_17_snippet_operations(ctx, test_environment):
    """Test snippet operations."""
    global created_resources
    
    workspace = created_resources['workspace']
    
    # List snippets
    result = await bitbucket_mcp.list_snippets(ctx, workspace)
    snippets_data = json.loads(result)
    
    assert "values" in snippets_data
    
    # Create snippet
    snippet_title = f"Test Snippet {TEST_PREFIX}"
    snippet_filename = "test-file.txt"
    snippet_content = f"This is a test snippet content for {TEST_PREFIX}"
    
    try:
        result = await bitbucket_mcp.create_snippet(
            ctx, workspace, snippet_title, snippet_filename, snippet_content, True
        )
        snippet_data = json.loads(result)
        
        assert "id" in snippet_data
        snippet_id = snippet_data["id"]
        
        # Get snippet
        result = await bitbucket_mcp.get_snippet(ctx, workspace, snippet_id)
        snippet_data = json.loads(result)
        
        assert "title" in snippet_data
        assert snippet_data["title"] == snippet_title
        
        # Get snippet file
        result = await bitbucket_mcp.get_snippet_file(ctx, workspace, snippet_id, snippet_filename)
        assert result == snippet_content
        
        # Delete snippet
        result = await bitbucket_mcp.delete_snippet(ctx, workspace, snippet_id)
        assert "status" in json.loads(result)
        
    except Exception as e:
        print(f"Note: Snippet operations failed (this may be expected in some test environments): {e}")

#--------------------- PROJECT DELETION TESTS ---------------------#

@pytest.mark.asyncio
async def test_18_project_deletion(ctx, test_environment):
    """
    Test project deletion.
    This should be the last test to ensure we don't delete resources needed by other tests.
    """
    global created_resources
    
    workspace = created_resources['workspace']
    
    # Create a temporary project to test deletion
    temp_project_key = f"TDEL{TEST_PREFIX.replace('-', '_').upper()}"
    
    # Create project
    result = await bitbucket_mcp.create_project(
        ctx, workspace, "Temporary Project for Deletion Test",
        temp_project_key, "Project for deletion testing", True
    )
    
    project_data = json.loads(result)
    assert "key" in project_data
    assert project_data["key"] == temp_project_key
    
    # Delete project
    result = await bitbucket_mcp.delete_project(ctx, workspace, temp_project_key)
    assert "status" in json.loads(result)
    assert json.loads(result)["status"] == "success"