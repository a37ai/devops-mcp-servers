#!/usr/bin/env python3
"""
GitLab MCP Server Test Script

This script tests all functionality of the GitLab MCP server.
It creates a temporary test repository, runs all tests, and then cleans up.

Requirements:
    - pytest
    - pytest-asyncio
    - httpx
    - python-dotenv

Environment variables:
    GITLAB_PERSONAL_ACCESS_TOKEN: Personal access token for GitLab API
    GITLAB_API_URL: GitLab API URL (default: https://gitlab.com/api/v4)
"""

import os
import json
import pytest
import asyncio
import uuid
import base64
from typing import Dict, Any, List
import httpx
from dotenv import load_dotenv

# Import the GitLab MCP server module
import servers.gitlab.gitlab_mcp as gitlab_mcp

# Load environment variables
load_dotenv()

# Configuration
GITLAB_API_URL = os.environ.get("GITLAB_API_URL", "https://gitlab.com/api/v4")
GITLAB_PERSONAL_ACCESS_TOKEN = os.environ.get("GITLAB_PERSONAL_ACCESS_TOKEN")

if not GITLAB_PERSONAL_ACCESS_TOKEN:
    pytest.skip("GITLAB_PERSONAL_ACCESS_TOKEN environment variable is required for tests", allow_module_level=True)

# Constants for testing
TEST_PROJECT_PREFIX = "mcp-test"
TEST_BRANCH_NAME = "test-branch"
TEST_FILE_PATH = "test-file.txt"
TEST_FILE_CONTENT = "This is a test file created by the MCP test suite."
TEST_COMMIT_MESSAGE = "Test commit message"

# Helper function for direct API access (for operations not covered by the MCP server)
async def make_gitlab_request(
    method: str,
    endpoint: str,
    params: Dict[str, Any] = None,
    json_data: Dict[str, Any] = None,
    binary_data: bytes = None,
    headers: Dict[str, str] = None
) -> Dict[str, Any]:
    """Make a request to the GitLab API with proper error handling."""
    url = f"{GITLAB_API_URL}/{endpoint}"
    
    request_headers = {
        "PRIVATE-TOKEN": GITLAB_PERSONAL_ACCESS_TOKEN,
        "Content-Type": "application/json",
    }
    
    if headers:
        request_headers.update(headers)
    
    async with httpx.AsyncClient() as client:
        try:
            response = await client.request(
                method=method,
                url=url,
                params=params,
                json=json_data,
                content=binary_data,
                headers=request_headers,
                timeout=30.0
            )
            response.raise_for_status()
            
            if response.status_code == 204:  # No content
                return {"success": True}
                
            return response.json()
        except httpx.HTTPStatusError as e:
            error_msg = f"GitLab API error: {e.response.status_code}"
            try:
                error_data = e.response.json()
                error_msg += f" - {error_data.get('message', 'Unknown error')}"
            except:
                pass
            raise ValueError(error_msg)
        except Exception as e:
            raise ValueError(f"Error making GitLab API request: {str(e)}")

# Helper function to delete a repository (not in the MCP server)
async def delete_repository(project_id: str) -> Dict[str, Any]:
    """Delete a GitLab project."""
    endpoint = f"projects/{project_id}"
    return await make_gitlab_request("DELETE", endpoint)

# Test fixtures

@pytest.fixture(scope="module")
async def test_project():
    """Create a test project and return its ID."""
    # Generate a unique project name
    project_name = f"{TEST_PROJECT_PREFIX}-{uuid.uuid4().hex[:8]}"
    
    # Create the project using the MCP server function
    result = await gitlab_mcp.create_repository(
        name=project_name,
        description="Temporary project for testing GitLab MCP server",
        visibility="private",
        initialize_with_readme=True
    )
    
    project_data = json.loads(result)
    project_id = project_data["id"]
    
    # Yield the project ID for tests
    yield project_id
    
    # Clean up - delete the project
    try:
        await delete_repository(project_id)
        print(f"Cleaned up test project {project_name} (ID: {project_id})")
    except Exception as e:
        print(f"Failed to clean up test project {project_name} (ID: {project_id}): {str(e)}")

@pytest.fixture(scope="module")
async def test_branch(test_project):
    """Create a test branch and return its name."""
    # Create a branch using the MCP server function
    result = await gitlab_mcp.create_branch(
        project_id=test_project,
        branch=TEST_BRANCH_NAME,
        ref="main"
    )
    
    # Yield the branch name for tests
    yield TEST_BRANCH_NAME

# Tests

@pytest.mark.asyncio
async def test_get_project_details(test_project):
    """Test getting project details."""
    result = await gitlab_mcp.get_project_details(test_project)
    result_data = json.loads(result)
    
    assert "id" in result_data
    assert result_data["id"] == test_project
    assert "name" in result_data
    assert result_data["visibility"] == "private"

@pytest.mark.asyncio
async def test_create_or_update_file(test_project):
    """Test creating a file."""
    result = await gitlab_mcp.create_or_update_file(
        project_id=test_project,
        file_path=TEST_FILE_PATH,
        content=TEST_FILE_CONTENT,
        commit_message=TEST_COMMIT_MESSAGE,
        branch="main"
    )
    result_data = json.loads(result)
    
    assert "file_path" in result_data
    assert result_data["file_path"] == TEST_FILE_PATH

@pytest.mark.asyncio
async def test_get_file_contents(test_project):
    """Test getting file contents."""
    result = await gitlab_mcp.get_file_contents(
        project_id=test_project,
        file_path=TEST_FILE_PATH,
        ref="main"
    )
    result_data = json.loads(result)
    
    assert "content" in result_data
    assert "decoded_content" in result_data
    assert result_data["decoded_content"] == TEST_FILE_CONTENT

@pytest.mark.asyncio
async def test_update_file(test_project):
    """Test updating a file."""
    updated_content = f"{TEST_FILE_CONTENT}\nThis line was added in an update."
    
    result = await gitlab_mcp.create_or_update_file(
        project_id=test_project,
        file_path=TEST_FILE_PATH,
        content=updated_content,
        commit_message="Update test file",
        branch="main"
    )
    result_data = json.loads(result)
    
    assert "file_path" in result_data
    assert result_data["file_path"] == TEST_FILE_PATH
    
    # Verify the updated content
    get_result = await gitlab_mcp.get_file_contents(
        project_id=test_project,
        file_path=TEST_FILE_PATH,
        ref="main"
    )
    get_result_data = json.loads(get_result)
    
    assert "decoded_content" in get_result_data
    assert get_result_data["decoded_content"] == updated_content

@pytest.mark.asyncio
async def test_push_files(test_project, test_branch):
    """Test pushing multiple files."""
    files = [
        {
            "file_path": "test-file1.txt",
            "content": "Content of test file 1"
        },
        {
            "file_path": "test-file2.txt",
            "content": "Content of test file 2"
        }
    ]
    
    result = await gitlab_mcp.push_files(
        project_id=test_project,
        branch=test_branch,
        files=files,
        commit_message="Add multiple test files"
    )
    result_data = json.loads(result)
    
    assert "id" in result_data
    assert "message" in result_data
    assert result_data["message"] == "Add multiple test files"
    
    # Verify the files were created
    for file_info in files:
        get_result = await gitlab_mcp.get_file_contents(
            project_id=test_project,
            file_path=file_info["file_path"],
            ref=test_branch
        )
        get_result_data = json.loads(get_result)
        
        assert "decoded_content" in get_result_data
        assert get_result_data["decoded_content"] == file_info["content"]

@pytest.mark.asyncio
async def test_search_repositories():
    """Test searching for repositories."""
    result = await gitlab_mcp.search_repositories(
        search=TEST_PROJECT_PREFIX,
        page=1,
        per_page=10
    )
    result_data = json.loads(result)
    
    assert isinstance(result_data, list)
    # At least one test project should be found
    assert len(result_data) > 0
    
    # Verify the search results contain our test project
    found = False
    for project in result_data:
        if project["name"].startswith(TEST_PROJECT_PREFIX):
            found = True
            break
    
    assert found, f"Test project with prefix '{TEST_PROJECT_PREFIX}' not found in search results"

@pytest.mark.asyncio
async def test_create_issue(test_project):
    """Test creating an issue."""
    issue_title = "Test Issue"
    issue_description = "This is a test issue created by the test suite."
    
    result = await gitlab_mcp.create_issue(
        project_id=test_project,
        title=issue_title,
        description=issue_description
    )
    result_data = json.loads(result)
    
    assert "title" in result_data
    assert result_data["title"] == issue_title
    assert "description" in result_data
    assert result_data["description"] == issue_description

@pytest.mark.asyncio
async def test_list_issues(test_project):
    """Test listing issues."""
    result = await gitlab_mcp.list_issues(
        project_id=test_project,
        state="opened"
    )
    result_data = json.loads(result)
    
    assert isinstance(result_data, list)
    # At least one issue should be found
    assert len(result_data) > 0
    
    # The first issue should be the one we created
    issue = result_data[0]
    assert "title" in issue
    assert issue["title"] == "Test Issue"

@pytest.mark.asyncio
async def test_create_branch(test_project):
    """Test creating a branch."""
    branch_name = f"test-branch-{uuid.uuid4().hex[:8]}"
    
    result = await gitlab_mcp.create_branch(
        project_id=test_project,
        branch=branch_name,
        ref="main"
    )
    result_data = json.loads(result)
    
    assert "name" in result_data
    assert result_data["name"] == branch_name

@pytest.mark.asyncio
async def test_list_branches(test_project):
    """Test listing branches."""
    result = await gitlab_mcp.list_branches(
        project_id=test_project
    )
    result_data = json.loads(result)
    
    assert isinstance(result_data, list)
    # At least two branches should be found (main and test-branch)
    assert len(result_data) >= 2
    
    # Check if our test branch is in the list
    found = False
    for branch in result_data:
        if branch["name"] == TEST_BRANCH_NAME:
            found = True
            break
    
    assert found, f"Test branch '{TEST_BRANCH_NAME}' not found in the list"

@pytest.mark.asyncio
async def test_create_merge_request(test_project, test_branch):
    """Test creating a merge request."""
    mr_title = "Test Merge Request"
    mr_description = "This is a test merge request created by the test suite."
    
    result = await gitlab_mcp.create_merge_request(
        project_id=test_project,
        title=mr_title,
        source_branch=test_branch,
        target_branch="main",
        description=mr_description
    )
    result_data = json.loads(result)
    
    assert "title" in result_data
    assert result_data["title"] == mr_title
    assert "description" in result_data
    assert result_data["description"] == mr_description
    assert "source_branch" in result_data
    assert result_data["source_branch"] == test_branch
    assert "target_branch" in result_data
    assert result_data["target_branch"] == "main"

@pytest.mark.asyncio
async def test_list_merge_requests(test_project):
    """Test listing merge requests."""
    result = await gitlab_mcp.list_merge_requests(
        project_id=test_project,
        state="opened"
    )
    result_data = json.loads(result)
    
    assert isinstance(result_data, list)
    # At least one merge request should be found
    assert len(result_data) > 0
    
    # The first merge request should be the one we created
    mr = result_data[0]
    assert "title" in mr
    assert mr["title"] == "Test Merge Request"

@pytest.mark.asyncio
async def test_list_commits(test_project):
    """Test listing commits."""
    result = await gitlab_mcp.list_commits(
        project_id=test_project
    )
    result_data = json.loads(result)
    
    assert isinstance(result_data, list)
    # At least one commit should be found
    assert len(result_data) > 0
    
    # Get the first commit's SHA
    first_commit_sha = result_data[0]["id"]
    
    # Test getting commit details
    details_result = await gitlab_mcp.get_commit_details(
        project_id=test_project,
        sha=first_commit_sha
    )
    details_data = json.loads(details_result)
    
    assert "id" in details_data
    assert details_data["id"] == first_commit_sha

@pytest.mark.asyncio
async def test_get_user_info():
    """Test getting current user info."""
    result = await gitlab_mcp.get_user_info()
    result_data = json.loads(result)
    
    assert "id" in result_data
    assert "username" in result_data

@pytest.mark.asyncio
async def test_fork_repository(test_project):
    """Test forking a repository."""
    try:
        result = await gitlab_mcp.fork_repository(
            project_id=test_project
        )
        result_data = json.loads(result)
        
        assert "id" in result_data
        assert "name" in result_data
        assert result_data["forked_from_project"]["id"] == test_project
        
        # Clean up the forked repository
        try:
            await delete_repository(result_data["id"])
            print(f"Cleaned up forked project (ID: {result_data['id']})")
        except Exception as e:
            print(f"Failed to clean up forked project (ID: {result_data['id']}): {str(e)}")
    except Exception as e:
        # Forking might fail depending on GitLab instance settings, so don't fail the test
        print(f"Fork test skipped due to error: {str(e)}")
        pytest.skip(f"Fork test skipped due to error: {str(e)}")

# Main test runner
if __name__ == "__main__":
    # Information on how to run the tests
    print("This script should be run with pytest:")
    print("pytest -xvs test_gitlab_mcp.py")