import pytest
import json
import os
import base64
from unittest.mock import patch, MagicMock, AsyncMock

# Import the MCP server
from mcp.server.fastmcp import Context
import sys
import httpx
from copy import deepcopy

# Add the directory containing the MCP server to the path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

# Import your MCP server
import servers.bitbucket_cloud.bitbucket_cloud_mcp as bitbucket_mcp

# Test configuration
TEST_USERNAME = "test_user"
TEST_APP_PASSWORD = "test_password"
TEST_WORKSPACE = "test_workspace"
TEST_REPO_SLUG = "test_repo"
TEST_PROJECT_KEY = "TEST"
TEST_BRANCH = "test_branch"
TEST_COMMIT = "1234567890abcdef"
TEST_PR_ID = 1
TEST_ISSUE_ID = 1
TEST_PIPELINE_UUID = "test-pipeline-uuid"
TEST_SNIPPET_ID = "test-snippet-id"

# Mock response data
MOCK_USER_RESPONSE = {
    "uuid": "123e4567-e89b-12d3-a456-426614174000",
    "display_name": "Test User",
    "username": TEST_USERNAME,
    "account_id": "123456:abcdef"
}

MOCK_WORKSPACE_RESPONSE = {
    "uuid": "223e4567-e89b-12d3-a456-426614174000",
    "name": "Test Workspace",
    "slug": TEST_WORKSPACE
}

MOCK_PROJECT_RESPONSE = {
    "uuid": "323e4567-e89b-12d3-a456-426614174000",
    "name": "Test Project",
    "key": TEST_PROJECT_KEY,
    "description": "Test project description",
    "is_private": True
}

MOCK_REPOSITORY_RESPONSE = {
    "uuid": "423e4567-e89b-12d3-a456-426614174000",
    "name": "Test Repository",
    "slug": TEST_REPO_SLUG,
    "description": "Test repository description",
    "is_private": True,
    "fork_policy": "allow_forks"
}

MOCK_BRANCH_RESPONSE = {
    "name": TEST_BRANCH,
    "target": {
        "hash": TEST_COMMIT
    }
}

MOCK_TAG_RESPONSE = {
    "name": "v1.0.0",
    "target": {
        "hash": TEST_COMMIT
    }
}

MOCK_COMMIT_RESPONSE = {
    "hash": TEST_COMMIT,
    "author": {
        "raw": "Test User <test.user@example.com>"
    },
    "message": "Test commit message"
}

MOCK_PR_RESPONSE = {
    "id": TEST_PR_ID,
    "title": "Test Pull Request",
    "description": "Test PR description",
    "state": "OPEN",
    "source": {
        "branch": {
            "name": "feature/test"
        }
    },
    "destination": {
        "branch": {
            "name": "master"
        }
    }
}

MOCK_ISSUE_RESPONSE = {
    "id": TEST_ISSUE_ID,
    "title": "Test Issue",
    "content": {
        "raw": "Test issue description"
    },
    "kind": "bug",
    "priority": "major",
    "state": "new"
}

MOCK_PIPELINE_RESPONSE = {
    "uuid": TEST_PIPELINE_UUID,
    "state": {
        "name": "PENDING"
    },
    "target": {
        "ref_name": TEST_BRANCH,
        "ref_type": "branch"
    }
}

MOCK_SNIPPET_RESPONSE = {
    "id": TEST_SNIPPET_ID,
    "title": "Test Snippet",
    "is_private": True,
    "files": {
        "test.py": {
            "path": "test.py"
        }
    }
}

MOCK_EMPTY_RESPONSE = {
    "status": "success",
    "status_code": 204
}

MOCK_LIST_RESPONSE = {
    "values": [MOCK_REPOSITORY_RESPONSE],
    "page": 1,
    "size": 1,
    "pagelen": 10,
    "next": None
}

# Create a fixture for the context
@pytest.fixture
def ctx():
    mock_ctx = MagicMock(spec=Context)
    mock_ctx.get_config = MagicMock(return_value=None)
    return mock_ctx

# Create a fixture for environment variables
@pytest.fixture
def env_vars(monkeypatch):
    monkeypatch.setenv("BITBUCKET_USERNAME", TEST_USERNAME)
    monkeypatch.setenv("BITBUCKET_APP_PASSWORD", TEST_APP_PASSWORD)

# Mock the httpx.AsyncClient
@pytest.fixture
def mock_httpx_client():
    with patch("httpx.AsyncClient") as mock_client:
        mock_instance = AsyncMock()
        mock_client.return_value.__aenter__.return_value = mock_instance
        
        # Mock request method to return different responses based on URL and method
        async def mock_request(**kwargs):
            url = kwargs.get("url", "")
            method = kwargs.get("method", "")
            mock_response = MagicMock()
            
            # Define status code and JSON for different endpoints
            if "/user" in url and method == "GET":
                mock_response.status_code = 200
                mock_response.text = json.dumps(MOCK_USER_RESPONSE)
                mock_response.json.return_value = MOCK_USER_RESPONSE
            elif "/users/" in url and method == "GET":
                mock_response.status_code = 200
                mock_response.text = json.dumps(MOCK_USER_RESPONSE)
                mock_response.json.return_value = MOCK_USER_RESPONSE
            elif "/workspaces" in url and not url.endswith("workspaces") and method == "GET":
                mock_response.status_code = 200
                mock_response.text = json.dumps(MOCK_WORKSPACE_RESPONSE)
                mock_response.json.return_value = MOCK_WORKSPACE_RESPONSE
            elif url.endswith("workspaces") and method == "GET":
                mock_response.status_code = 200
                mock_list = deepcopy(MOCK_LIST_RESPONSE)
                mock_list["values"] = [MOCK_WORKSPACE_RESPONSE]
                mock_response.text = json.dumps(mock_list)
                mock_response.json.return_value = mock_list
            elif "/projects" in url and method == "GET" and not url.endswith(TEST_PROJECT_KEY):
                mock_response.status_code = 200
                mock_list = deepcopy(MOCK_LIST_RESPONSE)
                mock_list["values"] = [MOCK_PROJECT_RESPONSE]
                mock_response.text = json.dumps(mock_list)
                mock_response.json.return_value = mock_list
            elif "/projects" in url and method == "GET" and url.endswith(TEST_PROJECT_KEY):
                mock_response.status_code = 200
                mock_response.text = json.dumps(MOCK_PROJECT_RESPONSE)
                mock_response.json.return_value = MOCK_PROJECT_RESPONSE
            elif "/projects" in url and method == "POST":
                mock_response.status_code = 201
                mock_response.text = json.dumps(MOCK_PROJECT_RESPONSE)
                mock_response.json.return_value = MOCK_PROJECT_RESPONSE
            elif "/projects" in url and method == "PUT":
                mock_response.status_code = 200
                mock_response.text = json.dumps(MOCK_PROJECT_RESPONSE)
                mock_response.json.return_value = MOCK_PROJECT_RESPONSE
            elif "/projects" in url and method == "DELETE":
                mock_response.status_code = 204
                mock_response.text = ""
                mock_response.json.side_effect = ValueError("No JSON content")
            elif "/repositories" in url and method == "GET" and not "/" + TEST_REPO_SLUG in url:
                mock_response.status_code = 200
                mock_list = deepcopy(MOCK_LIST_RESPONSE)
                mock_list["values"] = [MOCK_REPOSITORY_RESPONSE]
                mock_response.text = json.dumps(mock_list)
                mock_response.json.return_value = mock_list
            elif "/repositories" in url and method == "GET" and "/" + TEST_REPO_SLUG in url and not "/refs/" in url and not "/commit/" in url and not "/pullrequests" in url:
                mock_response.status_code = 200
                mock_response.text = json.dumps(MOCK_REPOSITORY_RESPONSE)
                mock_response.json.return_value = MOCK_REPOSITORY_RESPONSE
            elif "/repositories" in url and method == "POST" and not "/refs/" in url and not "/commit/" in url and not "/pullrequests" in url:
                mock_response.status_code = 201
                mock_response.text = json.dumps(MOCK_REPOSITORY_RESPONSE)
                mock_response.json.return_value = MOCK_REPOSITORY_RESPONSE
            elif "/repositories" in url and method == "PUT":
                mock_response.status_code = 200
                mock_response.text = json.dumps(MOCK_REPOSITORY_RESPONSE)
                mock_response.json.return_value = MOCK_REPOSITORY_RESPONSE
            elif "/repositories" in url and method == "DELETE" and not "/refs/" in url:
                mock_response.status_code = 204
                mock_response.text = ""
                mock_response.json.side_effect = ValueError("No JSON content")
            elif "/refs/branches" in url and method == "GET":
                mock_response.status_code = 200
                mock_list = deepcopy(MOCK_LIST_RESPONSE)
                mock_list["values"] = [MOCK_BRANCH_RESPONSE]
                mock_response.text = json.dumps(mock_list)
                mock_response.json.return_value = mock_list
            elif "/refs/branches" in url and method == "POST":
                mock_response.status_code = 201
                mock_response.text = json.dumps(MOCK_BRANCH_RESPONSE)
                mock_response.json.return_value = MOCK_BRANCH_RESPONSE
            elif "/refs/tags" in url and method == "GET":
                mock_response.status_code = 200
                mock_list = deepcopy(MOCK_LIST_RESPONSE)
                mock_list["values"] = [MOCK_TAG_RESPONSE]
                mock_response.text = json.dumps(mock_list)
                mock_response.json.return_value = mock_list
            elif "/refs/tags" in url and method == "POST":
                mock_response.status_code = 201
                mock_response.text = json.dumps(MOCK_TAG_RESPONSE)
                mock_response.json.return_value = MOCK_TAG_RESPONSE
            elif "/commits" in url and method == "GET" and not "/" + TEST_COMMIT in url:
                mock_response.status_code = 200
                mock_list = deepcopy(MOCK_LIST_RESPONSE)
                mock_list["values"] = [MOCK_COMMIT_RESPONSE]
                mock_response.text = json.dumps(mock_list)
                mock_response.json.return_value = mock_list
            elif "/commit/" in url and method == "GET" and "/" + TEST_COMMIT in url:
                mock_response.status_code = 200
                mock_response.text = json.dumps(MOCK_COMMIT_RESPONSE)
                mock_response.json.return_value = MOCK_COMMIT_RESPONSE
            elif "/diff/" in url and method == "GET":
                mock_response.status_code = 200
                mock_response.text = "@@ -1,3 +1,5 @@\n+Line 1\n+Line 2\n Line 3\n Line 4\n Line 5"
                mock_response.json.return_value = {"content": mock_response.text}
            elif "/commit/" in url and "/comments" in url and method == "POST":
                mock_response.status_code = 201
                mock_response.text = json.dumps({"id": 1, "content": {"raw": "Test comment"}})
                mock_response.json.return_value = {"id": 1, "content": {"raw": "Test comment"}}
            elif "/src/" in url and method == "GET":
                mock_response.status_code = 200
                mock_response.text = "print('Hello, World!')"
                mock_response.json.side_effect = ValueError("No JSON content")
            elif "/pullrequests" in url and method == "GET" and not "/" + str(TEST_PR_ID) in url:
                mock_response.status_code = 200
                mock_list = deepcopy(MOCK_LIST_RESPONSE)
                mock_list["values"] = [MOCK_PR_RESPONSE]
                mock_response.text = json.dumps(mock_list)
                mock_response.json.return_value = mock_list
            elif "/pullrequests" in url and method == "GET" and "/" + str(TEST_PR_ID) in url:
                mock_response.status_code = 200
                mock_response.text = json.dumps(MOCK_PR_RESPONSE)
                mock_response.json.return_value = MOCK_PR_RESPONSE
            elif "/pullrequests" in url and method == "POST" and not "/" + str(TEST_PR_ID) in url:
                mock_response.status_code = 201
                mock_response.text = json.dumps(MOCK_PR_RESPONSE)
                mock_response.json.return_value = MOCK_PR_RESPONSE
            elif "/approve" in url and method == "POST":
                mock_response.status_code = 200
                mock_response.text = json.dumps({"approved": True})
                mock_response.json.return_value = {"approved": True}
            elif "/approve" in url and method == "DELETE":
                mock_response.status_code = 204
                mock_response.text = ""
                mock_response.json.side_effect = ValueError("No JSON content")
            elif "/merge" in url and method == "POST":
                mock_response.status_code = 200
                mock_pr_response = deepcopy(MOCK_PR_RESPONSE)
                mock_pr_response["state"] = "MERGED"
                mock_response.text = json.dumps(mock_pr_response)
                mock_response.json.return_value = mock_pr_response
            elif "/decline" in url and method == "POST":
                mock_response.status_code = 200
                mock_pr_response = deepcopy(MOCK_PR_RESPONSE)
                mock_pr_response["state"] = "DECLINED"
                mock_response.text = json.dumps(mock_pr_response)
                mock_response.json.return_value = mock_pr_response
            elif "/pullrequests/" in url and "/comments" in url and method == "POST":
                mock_response.status_code = 201
                mock_response.text = json.dumps({"id": 1, "content": {"raw": "Test comment"}})
                mock_response.json.return_value = {"id": 1, "content": {"raw": "Test comment"}}
            elif "/branch-restrictions" in url and method == "GET":
                mock_response.status_code = 200
                mock_list = deepcopy(MOCK_LIST_RESPONSE)
                mock_list["values"] = [{"id": 1, "kind": "push", "pattern": "master"}]
                mock_response.text = json.dumps(mock_list)
                mock_response.json.return_value = mock_list
            elif "/branch-restrictions" in url and method == "POST":
                mock_response.status_code = 201
                mock_response.text = json.dumps({"id": 1, "kind": "push", "pattern": "master"})
                mock_response.json.return_value = {"id": 1, "kind": "push", "pattern": "master"}
            elif "/deploy-keys" in url and method == "GET":
                mock_response.status_code = 200
                mock_list = deepcopy(MOCK_LIST_RESPONSE)
                mock_list["values"] = [{"id": 1, "key": "ssh-rsa AAAAB3...", "label": "Test Key"}]
                mock_response.text = json.dumps(mock_list)
                mock_response.json.return_value = mock_list
            elif "/deploy-keys" in url and method == "POST":
                mock_response.status_code = 201
                mock_response.text = json.dumps({"id": 1, "key": "ssh-rsa AAAAB3...", "label": "Test Key"})
                mock_response.json.return_value = {"id": 1, "key": "ssh-rsa AAAAB3...", "label": "Test Key"}
            elif "/deploy-keys/" in url and method == "DELETE":
                mock_response.status_code = 204
                mock_response.text = ""
                mock_response.json.side_effect = ValueError("No JSON content")
            elif "/hooks" in url and method == "GET":
                mock_response.status_code = 200
                mock_list = deepcopy(MOCK_LIST_RESPONSE)
                mock_list["values"] = [{"uuid": "test-uuid", "url": "https://example.com/webhook", "active": True}]
                mock_response.text = json.dumps(mock_list)
                mock_response.json.return_value = mock_list
            elif "/hooks" in url and method == "POST":
                mock_response.status_code = 201
                mock_response.text = json.dumps({"uuid": "test-uuid", "url": "https://example.com/webhook", "active": True})
                mock_response.json.return_value = {"uuid": "test-uuid", "url": "https://example.com/webhook", "active": True}
            elif "/hooks/" in url and method == "DELETE":
                mock_response.status_code = 204
                mock_response.text = ""
                mock_response.json.side_effect = ValueError("No JSON content")
            elif "/issues" in url and method == "GET" and not "/" + str(TEST_ISSUE_ID) in url:
                mock_response.status_code = 200
                mock_list = deepcopy(MOCK_LIST_RESPONSE)
                mock_list["values"] = [MOCK_ISSUE_RESPONSE]
                mock_response.text = json.dumps(mock_list)
                mock_response.json.return_value = mock_list
            elif "/issues" in url and method == "GET" and "/" + str(TEST_ISSUE_ID) in url:
                mock_response.status_code = 200
                mock_response.text = json.dumps(MOCK_ISSUE_RESPONSE)
                mock_response.json.return_value = MOCK_ISSUE_RESPONSE
            elif "/issues" in url and method == "POST" and not "/" + str(TEST_ISSUE_ID) in url:
                mock_response.status_code = 201
                mock_response.text = json.dumps(MOCK_ISSUE_RESPONSE)
                mock_response.json.return_value = MOCK_ISSUE_RESPONSE
            elif "/issues/" in url and method == "PUT":
                mock_response.status_code = 200
                mock_response.text = json.dumps(MOCK_ISSUE_RESPONSE)
                mock_response.json.return_value = MOCK_ISSUE_RESPONSE
            elif "/issues/" in url and "/comments" in url and method == "POST":
                mock_response.status_code = 201
                mock_response.text = json.dumps({"id": 1, "content": {"raw": "Test comment"}})
                mock_response.json.return_value = {"id": 1, "content": {"raw": "Test comment"}}
            elif "/pipelines/" in url and method == "GET" and not "/" + TEST_PIPELINE_UUID in url:
                mock_response.status_code = 200
                mock_list = deepcopy(MOCK_LIST_RESPONSE)
                mock_list["values"] = [MOCK_PIPELINE_RESPONSE]
                mock_response.text = json.dumps(mock_list)
                mock_response.json.return_value = mock_list
            elif "/pipelines/" in url and method == "GET" and "/" + TEST_PIPELINE_UUID in url:
                mock_response.status_code = 200
                mock_response.text = json.dumps(MOCK_PIPELINE_RESPONSE)
                mock_response.json.return_value = MOCK_PIPELINE_RESPONSE
            elif "/pipelines/" in url and method == "POST" and not "/" + TEST_PIPELINE_UUID in url:
                mock_response.status_code = 201
                mock_response.text = json.dumps(MOCK_PIPELINE_RESPONSE)
                mock_response.json.return_value = MOCK_PIPELINE_RESPONSE
            elif "/stopPipeline" in url and method == "POST":
                mock_response.status_code = 200
                mock_pipeline_response = deepcopy(MOCK_PIPELINE_RESPONSE)
                mock_pipeline_response["state"]["name"] = "STOPPED"
                mock_response.text = json.dumps(mock_pipeline_response)
                mock_response.json.return_value = mock_pipeline_response
            elif "/snippets" in url and method == "GET" and not "/" + TEST_SNIPPET_ID in url:
                mock_response.status_code = 200
                mock_list = deepcopy(MOCK_LIST_RESPONSE)
                mock_list["values"] = [MOCK_SNIPPET_RESPONSE]
                mock_response.text = json.dumps(mock_list)
                mock_response.json.return_value = mock_list
            elif "/snippets" in url and method == "GET" and "/" + TEST_SNIPPET_ID in url and not "/files/" in url:
                mock_response.status_code = 200
                mock_response.text = json.dumps(MOCK_SNIPPET_RESPONSE)
                mock_response.json.return_value = MOCK_SNIPPET_RESPONSE
            elif "/snippets" in url and method == "POST":
                mock_response.status_code = 201
                mock_response.text = json.dumps(MOCK_SNIPPET_RESPONSE)
                mock_response.json.return_value = MOCK_SNIPPET_RESPONSE
            elif "/snippets/" in url and method == "DELETE":
                mock_response.status_code = 204
                mock_response.text = ""
                mock_response.json.side_effect = ValueError("No JSON content")
            elif "/files/" in url and method == "GET":
                mock_response.status_code = 200
                mock_response.text = "print('Hello, World!')"
                mock_response.json.side_effect = ValueError("No JSON content")
            else:
                # Default case for unimplemented endpoints
                mock_response.status_code = 404
                mock_response.text = json.dumps({"error": "Endpoint not implemented in test"})
                mock_response.json.return_value = {"error": "Endpoint not implemented in test"}
                
            return mock_response
            
        mock_instance.request = mock_request
        yield mock_instance

# Test helper functions
def test_get_auth_header(ctx, env_vars):
    auth_header = bitbucket_mcp.get_auth_header(ctx)
    auth_string = f"{TEST_USERNAME}:{TEST_APP_PASSWORD}"
    encoded_auth = base64.b64encode(auth_string.encode()).decode()
    expected_header = {"Authorization": f"Basic {encoded_auth}"}
    assert auth_header == expected_header

def test_get_auth_header_from_context(ctx):
    ctx.get_config.side_effect = lambda key: TEST_USERNAME if key == "BITBUCKET_USERNAME" else TEST_APP_PASSWORD
    auth_header = bitbucket_mcp.get_auth_header(ctx)
    auth_string = f"{TEST_USERNAME}:{TEST_APP_PASSWORD}"
    encoded_auth = base64.b64encode(auth_string.encode()).decode()
    expected_header = {"Authorization": f"Basic {encoded_auth}"}
    assert auth_header == expected_header

def test_get_auth_header_missing_credentials(monkeypatch, ctx):
    # Remove environment variables
    monkeypatch.delenv("BITBUCKET_USERNAME", raising=False)
    monkeypatch.delenv("BITBUCKET_APP_PASSWORD", raising=False)
    
    # Mock context to return None for config
    ctx.get_config.return_value = None
    
    # Test that ValueError is raised
    with pytest.raises(ValueError):
        bitbucket_mcp.get_auth_header(ctx)

# Test make_request function (base functionality)
@pytest.mark.asyncio
async def test_make_request(ctx, env_vars, mock_httpx_client):
    data = await bitbucket_mcp.make_request(ctx, "GET", "user")
    assert data == MOCK_USER_RESPONSE

@pytest.mark.asyncio
async def test_make_request_error(ctx, env_vars, mock_httpx_client):
    # Override the mock to return an error
    mock_httpx_client.request.side_effect = AsyncMock(
        return_value=MagicMock(status_code=404, text="Not found")
    )
    
    with pytest.raises(ValueError):
        await bitbucket_mcp.make_request(ctx, "GET", "nonexistent")

# Test format_response function
def test_format_response():
    data = {"key": "value"}
    formatted = bitbucket_mcp.format_response(data)
    assert formatted == json.dumps(data, indent=2)

# === USER AND WORKSPACE TOOLS TESTS ===

@pytest.mark.asyncio
async def test_get_current_user(ctx, env_vars, mock_httpx_client):
    result = await bitbucket_mcp.get_current_user(ctx)
    assert "display_name" in json.loads(result)
    assert "username" in json.loads(result)
    assert json.loads(result)["username"] == TEST_USERNAME

@pytest.mark.asyncio
async def test_get_user_profile(ctx, env_vars, mock_httpx_client):
    result = await bitbucket_mcp.get_user_profile(ctx, TEST_USERNAME)
    assert "display_name" in json.loads(result)
    assert "username" in json.loads(result)
    assert json.loads(result)["username"] == TEST_USERNAME

@pytest.mark.asyncio
async def test_list_workspaces(ctx, env_vars, mock_httpx_client):
    result = await bitbucket_mcp.list_workspaces(ctx)
    result_json = json.loads(result)
    assert "values" in result_json
    assert len(result_json["values"]) > 0
    assert "slug" in result_json["values"][0]
    assert result_json["values"][0]["slug"] == TEST_WORKSPACE

@pytest.mark.asyncio
async def test_get_workspace(ctx, env_vars, mock_httpx_client):
    result = await bitbucket_mcp.get_workspace(ctx, TEST_WORKSPACE)
    assert "name" in json.loads(result)
    assert "slug" in json.loads(result)
    assert json.loads(result)["slug"] == TEST_WORKSPACE

# === PROJECT MANAGEMENT TOOLS TESTS ===

@pytest.mark.asyncio
async def test_list_projects(ctx, env_vars, mock_httpx_client):
    result = await bitbucket_mcp.list_projects(ctx, TEST_WORKSPACE)
    result_json = json.loads(result)
    assert "values" in result_json
    assert len(result_json["values"]) > 0
    assert "key" in result_json["values"][0]
    assert result_json["values"][0]["key"] == TEST_PROJECT_KEY

@pytest.mark.asyncio
async def test_create_project(ctx, env_vars, mock_httpx_client):
    result = await bitbucket_mcp.create_project(
        ctx, TEST_WORKSPACE, "Test Project", TEST_PROJECT_KEY, "Test project description", True
    )
    assert "name" in json.loads(result)
    assert "key" in json.loads(result)
    assert json.loads(result)["key"] == TEST_PROJECT_KEY

@pytest.mark.asyncio
async def test_get_project(ctx, env_vars, mock_httpx_client):
    result = await bitbucket_mcp.get_project(ctx, TEST_WORKSPACE, TEST_PROJECT_KEY)
    assert "name" in json.loads(result)
    assert "key" in json.loads(result)
    assert json.loads(result)["key"] == TEST_PROJECT_KEY

@pytest.mark.asyncio
async def test_update_project(ctx, env_vars, mock_httpx_client):
    result = await bitbucket_mcp.update_project(
        ctx, TEST_WORKSPACE, TEST_PROJECT_KEY, "Updated Project", "Updated description", False
    )
    assert "name" in json.loads(result)
    assert "key" in json.loads(result)
    assert json.loads(result)["key"] == TEST_PROJECT_KEY

@pytest.mark.asyncio
async def test_delete_project(ctx, env_vars, mock_httpx_client):
    result = await bitbucket_mcp.delete_project(ctx, TEST_WORKSPACE, TEST_PROJECT_KEY)
    assert "status" in json.loads(result)
    assert json.loads(result)["status"] == "success"

# === REPOSITORY MANAGEMENT TOOLS TESTS ===

@pytest.mark.asyncio
async def test_list_repositories(ctx, env_vars, mock_httpx_client):
    result = await bitbucket_mcp.list_repositories(ctx, TEST_WORKSPACE)
    result_json = json.loads(result)
    assert "values" in result_json
    assert len(result_json["values"]) > 0
    assert "slug" in result_json["values"][0]
    assert result_json["values"][0]["slug"] == TEST_REPO_SLUG

@pytest.mark.asyncio
async def test_get_repository(ctx, env_vars, mock_httpx_client):
    result = await bitbucket_mcp.get_repository(ctx, TEST_WORKSPACE, TEST_REPO_SLUG)
    assert "name" in json.loads(result)
    assert "slug" in json.loads(result)
    assert json.loads(result)["slug"] == TEST_REPO_SLUG

@pytest.mark.asyncio
async def test_create_repository(ctx, env_vars, mock_httpx_client):
    result = await bitbucket_mcp.create_repository(
        ctx, TEST_WORKSPACE, TEST_REPO_SLUG, "Test repository description", True, "allow_forks", TEST_PROJECT_KEY
    )
    assert "name" in json.loads(result)
    assert "slug" in json.loads(result)
    assert json.loads(result)["slug"] == TEST_REPO_SLUG

@pytest.mark.asyncio
async def test_update_repository(ctx, env_vars, mock_httpx_client):
    result = await bitbucket_mcp.update_repository(
        ctx, TEST_WORKSPACE, TEST_REPO_SLUG, "Updated description", False, "no_forks", TEST_PROJECT_KEY, "Updated Repo"
    )
    assert "name" in json.loads(result)
    assert "slug" in json.loads(result)
    assert json.loads(result)["slug"] == TEST_REPO_SLUG

@pytest.mark.asyncio
async def test_delete_repository(ctx, env_vars, mock_httpx_client):
    result = await bitbucket_mcp.delete_repository(ctx, TEST_WORKSPACE, TEST_REPO_SLUG)
    assert "status" in json.loads(result)
    assert json.loads(result)["status"] == "success"

# === BRANCH AND TAG MANAGEMENT TOOLS TESTS ===

@pytest.mark.asyncio
async def test_list_branches(ctx, env_vars, mock_httpx_client):
    result = await bitbucket_mcp.list_branches(ctx, TEST_WORKSPACE, TEST_REPO_SLUG)
    result_json = json.loads(result)
    assert "values" in result_json
    assert len(result_json["values"]) > 0
    assert "name" in result_json["values"][0]
    assert result_json["values"][0]["name"] == TEST_BRANCH

@pytest.mark.asyncio
async def test_create_branch(ctx, env_vars, mock_httpx_client):
    result = await bitbucket_mcp.create_branch(
        ctx, TEST_WORKSPACE, TEST_REPO_SLUG, TEST_BRANCH, TEST_COMMIT
    )
    assert "name" in json.loads(result)
    assert json.loads(result)["name"] == TEST_BRANCH
    assert "target" in json.loads(result)
    assert "hash" in json.loads(result)["target"]
    assert json.loads(result)["target"]["hash"] == TEST_COMMIT

@pytest.mark.asyncio
async def test_list_tags(ctx, env_vars, mock_httpx_client):
    result = await bitbucket_mcp.list_tags(ctx, TEST_WORKSPACE, TEST_REPO_SLUG)
    result_json = json.loads(result)
    assert "values" in result_json
    assert len(result_json["values"]) > 0
    assert "name" in result_json["values"][0]
    assert "target" in result_json["values"][0]

@pytest.mark.asyncio
async def test_create_tag(ctx, env_vars, mock_httpx_client):
    result = await bitbucket_mcp.create_tag(
        ctx, TEST_WORKSPACE, TEST_REPO_SLUG, "v1.0.0", TEST_COMMIT, "Test tag message"
    )
    assert "name" in json.loads(result)
    assert json.loads(result)["name"] == "v1.0.0"
    assert "target" in json.loads(result)
    assert "hash" in json.loads(result)["target"]
    assert json.loads(result)["target"]["hash"] == TEST_COMMIT

# === COMMIT AND SOURCE CODE TOOLS TESTS ===

@pytest.mark.asyncio
async def test_list_commits(ctx, env_vars, mock_httpx_client):
    result = await bitbucket_mcp.list_commits(ctx, TEST_WORKSPACE, TEST_REPO_SLUG)
    result_json = json.loads(result)
    assert "values" in result_json
    assert len(result_json["values"]) > 0
    assert "hash" in result_json["values"][0]

@pytest.mark.asyncio
async def test_get_commit(ctx, env_vars, mock_httpx_client):
    result = await bitbucket_mcp.get_commit(ctx, TEST_WORKSPACE, TEST_REPO_SLUG, TEST_COMMIT)
    assert "hash" in json.loads(result)
    assert json.loads(result)["hash"] == TEST_COMMIT

@pytest.mark.asyncio
async def test_get_commit_diff(ctx, env_vars, mock_httpx_client):
    result = await bitbucket_mcp.get_commit_diff(ctx, TEST_WORKSPACE, TEST_REPO_SLUG, TEST_COMMIT)
    assert "@@ " in result or "content" in json.loads(result)

@pytest.mark.asyncio
async def test_add_commit_comment(ctx, env_vars, mock_httpx_client):
    result = await bitbucket_mcp.add_commit_comment(
        ctx, TEST_WORKSPACE, TEST_REPO_SLUG, TEST_COMMIT, "Test comment", 1, "test.py"
    )
    assert "id" in json.loads(result)
    assert "content" in json.loads(result)
    assert "raw" in json.loads(result)["content"]
    assert json.loads(result)["content"]["raw"] == "Test comment"

@pytest.mark.asyncio
async def test_get_file_content(ctx, env_vars, mock_httpx_client):
    result = await bitbucket_mcp.get_file_content(
        ctx, TEST_WORKSPACE, TEST_REPO_SLUG, "test.py", TEST_COMMIT
    )
    assert "print" in result

# === PULL REQUEST TOOLS TESTS ===

@pytest.mark.asyncio
async def test_list_pull_requests(ctx, env_vars, mock_httpx_client):
    result = await bitbucket_mcp.list_pull_requests(ctx, TEST_WORKSPACE, TEST_REPO_SLUG)
    result_json = json.loads(result)
    assert "values" in result_json
    assert len(result_json["values"]) > 0
    assert "id" in result_json["values"][0]
    assert result_json["values"][0]["id"] == TEST_PR_ID

@pytest.mark.asyncio
async def test_create_pull_request(ctx, env_vars, mock_httpx_client):
    result = await bitbucket_mcp.create_pull_request(
        ctx, TEST_WORKSPACE, TEST_REPO_SLUG, "Test Pull Request", "feature/test", "master", 
        "Test PR description", True
    )
    assert "id" in json.loads(result)
    assert json.loads(result)["id"] == TEST_PR_ID
    assert "title" in json.loads(result)
    assert json.loads(result)["title"] == "Test Pull Request"

@pytest.mark.asyncio
async def test_get_pull_request(ctx, env_vars, mock_httpx_client):
    result = await bitbucket_mcp.get_pull_request(ctx, TEST_WORKSPACE, TEST_REPO_SLUG, TEST_PR_ID)
    assert "id" in json.loads(result)
    assert json.loads(result)["id"] == TEST_PR_ID
    assert "title" in json.loads(result)

@pytest.mark.asyncio
async def test_approve_pull_request(ctx, env_vars, mock_httpx_client):
    result = await bitbucket_mcp.approve_pull_request(ctx, TEST_WORKSPACE, TEST_REPO_SLUG, TEST_PR_ID)
    assert "approved" in json.loads(result)
    assert json.loads(result)["approved"] is True

@pytest.mark.asyncio
async def test_unapprove_pull_request(ctx, env_vars, mock_httpx_client):
    result = await bitbucket_mcp.unapprove_pull_request(ctx, TEST_WORKSPACE, TEST_REPO_SLUG, TEST_PR_ID)
    assert "status" in json.loads(result)
    assert json.loads(result)["status"] == "success"

@pytest.mark.asyncio
async def test_merge_pull_request(ctx, env_vars, mock_httpx_client):
    result = await bitbucket_mcp.merge_pull_request(
        ctx, TEST_WORKSPACE, TEST_REPO_SLUG, TEST_PR_ID, "merge_commit", "Test merge commit message"
    )
    assert "state" in json.loads(result)
    assert json.loads(result)["state"] == "MERGED"

@pytest.mark.asyncio
async def test_decline_pull_request(ctx, env_vars, mock_httpx_client):
    result = await bitbucket_mcp.decline_pull_request(ctx, TEST_WORKSPACE, TEST_REPO_SLUG, TEST_PR_ID)
    assert "state" in json.loads(result)
    assert json.loads(result)["state"] == "DECLINED"

@pytest.mark.asyncio
async def test_add_pull_request_comment(ctx, env_vars, mock_httpx_client):
    result = await bitbucket_mcp.add_pull_request_comment(
        ctx, TEST_WORKSPACE, TEST_REPO_SLUG, TEST_PR_ID, "Test comment", 1, "test.py"
    )
    assert "id" in json.loads(result)
    assert "content" in json.loads(result)
    assert "raw" in json.loads(result)["content"]
    assert json.loads(result)["content"]["raw"] == "Test comment"

# === REPOSITORY SETTINGS AND ADMIN TOOLS TESTS ===

@pytest.mark.asyncio
async def test_list_branch_restrictions(ctx, env_vars, mock_httpx_client):
    result = await bitbucket_mcp.list_branch_restrictions(ctx, TEST_WORKSPACE, TEST_REPO_SLUG)
    result_json = json.loads(result)
    assert "values" in result_json
    assert len(result_json["values"]) > 0
    assert "kind" in result_json["values"][0]
    assert "pattern" in result_json["values"][0]

@pytest.mark.asyncio
async def test_create_branch_restriction(ctx, env_vars, mock_httpx_client):
    result = await bitbucket_mcp.create_branch_restriction(
        ctx, TEST_WORKSPACE, TEST_REPO_SLUG, "push", "master", ["123e4567-e89b-12d3-a456-426614174000"]
    )
    assert "id" in json.loads(result)
    assert "kind" in json.loads(result)
    assert json.loads(result)["kind"] == "push"
    assert "pattern" in json.loads(result)
    assert json.loads(result)["pattern"] == "master"

@pytest.mark.asyncio
async def test_list_deploy_keys(ctx, env_vars, mock_httpx_client):
    result = await bitbucket_mcp.list_deploy_keys(ctx, TEST_WORKSPACE, TEST_REPO_SLUG)
    result_json = json.loads(result)
    assert "values" in result_json
    assert len(result_json["values"]) > 0
    assert "key" in result_json["values"][0]
    assert "label" in result_json["values"][0]

@pytest.mark.asyncio
async def test_add_deploy_key(ctx, env_vars, mock_httpx_client):
    result = await bitbucket_mcp.add_deploy_key(
        ctx, TEST_WORKSPACE, TEST_REPO_SLUG, "ssh-rsa AAAAB3...", "Test Key"
    )
    assert "id" in json.loads(result)
    assert "key" in json.loads(result)
    assert "label" in json.loads(result)
    assert json.loads(result)["label"] == "Test Key"

@pytest.mark.asyncio
async def test_delete_deploy_key(ctx, env_vars, mock_httpx_client):
    result = await bitbucket_mcp.delete_deploy_key(ctx, TEST_WORKSPACE, TEST_REPO_SLUG, 1)
    assert "status" in json.loads(result)
    assert json.loads(result)["status"] == "success"

@pytest.mark.asyncio
async def test_list_webhooks(ctx, env_vars, mock_httpx_client):
    result = await bitbucket_mcp.list_webhooks(ctx, TEST_WORKSPACE, TEST_REPO_SLUG)
    result_json = json.loads(result)
    assert "values" in result_json
    assert len(result_json["values"]) > 0
    assert "uuid" in result_json["values"][0]
    assert "url" in result_json["values"][0]

@pytest.mark.asyncio
async def test_create_webhook(ctx, env_vars, mock_httpx_client):
    result = await bitbucket_mcp.create_webhook(
        ctx, TEST_WORKSPACE, TEST_REPO_SLUG, "https://example.com/webhook", 
        "Test webhook", ["repo:push", "pullrequest:created"], True
    )
    assert "uuid" in json.loads(result)
    assert "url" in json.loads(result)
    assert json.loads(result)["url"] == "https://example.com/webhook"
    assert "active" in json.loads(result)
    assert json.loads(result)["active"] is True

@pytest.mark.asyncio
async def test_delete_webhook(ctx, env_vars, mock_httpx_client):
    result = await bitbucket_mcp.delete_webhook(ctx, TEST_WORKSPACE, TEST_REPO_SLUG, "test-uuid")
    assert "status" in json.loads(result)
    assert json.loads(result)["status"] == "success"

# === ISSUE TRACKER TOOLS TESTS ===

@pytest.mark.asyncio
async def test_list_issues(ctx, env_vars, mock_httpx_client):
    result = await bitbucket_mcp.list_issues(ctx, TEST_WORKSPACE, TEST_REPO_SLUG)
    result_json = json.loads(result)
    assert "values" in result_json
    assert len(result_json["values"]) > 0
    assert "id" in result_json["values"][0]
    assert result_json["values"][0]["id"] == TEST_ISSUE_ID

@pytest.mark.asyncio
async def test_create_issue(ctx, env_vars, mock_httpx_client):
    result = await bitbucket_mcp.create_issue(
        ctx, TEST_WORKSPACE, TEST_REPO_SLUG, "Test Issue", "Test issue description", 
        "bug", "major", TEST_USERNAME
    )
    assert "id" in json.loads(result)
    assert json.loads(result)["id"] == TEST_ISSUE_ID
    assert "title" in json.loads(result)
    assert json.loads(result)["title"] == "Test Issue"

@pytest.mark.asyncio
async def test_get_issue(ctx, env_vars, mock_httpx_client):
    result = await bitbucket_mcp.get_issue(ctx, TEST_WORKSPACE, TEST_REPO_SLUG, TEST_ISSUE_ID)
    assert "id" in json.loads(result)
    assert json.loads(result)["id"] == TEST_ISSUE_ID
    assert "title" in json.loads(result)
    assert json.loads(result)["title"] == "Test Issue"

@pytest.mark.asyncio
async def test_update_issue(ctx, env_vars, mock_httpx_client):
    result = await bitbucket_mcp.update_issue(
        ctx, TEST_WORKSPACE, TEST_REPO_SLUG, TEST_ISSUE_ID, "Updated Issue", 
        "Updated issue description", "enhancement", "minor", TEST_USERNAME, "resolved"
    )
    assert "id" in json.loads(result)
    assert json.loads(result)["id"] == TEST_ISSUE_ID
    assert "title" in json.loads(result)
    assert json.loads(result)["title"] == "Test Issue"  # Using mock response, the actual update isn't reflected

@pytest.mark.asyncio
async def test_add_issue_comment(ctx, env_vars, mock_httpx_client):
    result = await bitbucket_mcp.add_issue_comment(
        ctx, TEST_WORKSPACE, TEST_REPO_SLUG, TEST_ISSUE_ID, "Test comment"
    )
    assert "id" in json.loads(result)
    assert "content" in json.loads(result)
    assert "raw" in json.loads(result)["content"]
    assert json.loads(result)["content"]["raw"] == "Test comment"

# === PIPELINES (CI/CD) TOOLS TESTS ===

@pytest.mark.asyncio
async def test_list_pipelines(ctx, env_vars, mock_httpx_client):
    result = await bitbucket_mcp.list_pipelines(ctx, TEST_WORKSPACE, TEST_REPO_SLUG)
    result_json = json.loads(result)
    assert "values" in result_json
    assert len(result_json["values"]) > 0
    assert "uuid" in result_json["values"][0]
    assert result_json["values"][0]["uuid"] == TEST_PIPELINE_UUID

@pytest.mark.asyncio
async def test_trigger_pipeline(ctx, env_vars, mock_httpx_client):
    result = await bitbucket_mcp.trigger_pipeline(
        ctx, TEST_WORKSPACE, TEST_REPO_SLUG, TEST_BRANCH, {"ENV": "test"}
    )
    assert "uuid" in json.loads(result)
    assert json.loads(result)["uuid"] == TEST_PIPELINE_UUID
    assert "target" in json.loads(result)
    assert "ref_name" in json.loads(result)["target"]
    assert json.loads(result)["target"]["ref_name"] == TEST_BRANCH

@pytest.mark.asyncio
async def test_get_pipeline(ctx, env_vars, mock_httpx_client):
    result = await bitbucket_mcp.get_pipeline(ctx, TEST_WORKSPACE, TEST_REPO_SLUG, TEST_PIPELINE_UUID)
    assert "uuid" in json.loads(result)
    assert json.loads(result)["uuid"] == TEST_PIPELINE_UUID
    assert "state" in json.loads(result)
    assert "name" in json.loads(result)["state"]

@pytest.mark.asyncio
async def test_stop_pipeline(ctx, env_vars, mock_httpx_client):
    result = await bitbucket_mcp.stop_pipeline(ctx, TEST_WORKSPACE, TEST_REPO_SLUG, TEST_PIPELINE_UUID)
    assert "state" in json.loads(result)
    assert "name" in json.loads(result)["state"]
    assert json.loads(result)["state"]["name"] == "STOPPED"

# === SNIPPETS TOOLS TESTS ===

@pytest.mark.asyncio
async def test_list_snippets(ctx, env_vars, mock_httpx_client):
    result = await bitbucket_mcp.list_snippets(ctx, TEST_WORKSPACE)
    result_json = json.loads(result)
    assert "values" in result_json
    assert len(result_json["values"]) > 0
    assert "id" in result_json["values"][0]
    assert result_json["values"][0]["id"] == TEST_SNIPPET_ID

@pytest.mark.asyncio
async def test_create_snippet(ctx, env_vars, mock_httpx_client):
    result = await bitbucket_mcp.create_snippet(
        ctx, TEST_WORKSPACE, "Test Snippet", "test.py", "print('Hello, World!')", True
    )
    assert "id" in json.loads(result)
    assert json.loads(result)["id"] == TEST_SNIPPET_ID
    assert "title" in json.loads(result)
    assert json.loads(result)["title"] == "Test Snippet"

@pytest.mark.asyncio
async def test_get_snippet(ctx, env_vars, mock_httpx_client):
    result = await bitbucket_mcp.get_snippet(ctx, TEST_WORKSPACE, TEST_SNIPPET_ID)
    assert "id" in json.loads(result)
    assert json.loads(result)["id"] == TEST_SNIPPET_ID
    assert "title" in json.loads(result)
    assert json.loads(result)["title"] == "Test Snippet"

@pytest.mark.asyncio
async def test_get_snippet_file(ctx, env_vars, mock_httpx_client):
    result = await bitbucket_mcp.get_snippet_file(ctx, TEST_WORKSPACE, TEST_SNIPPET_ID, "test.py")
    assert "print" in result

@pytest.mark.asyncio
async def test_delete_snippet(ctx, env_vars, mock_httpx_client):
    result = await bitbucket_mcp.delete_snippet(ctx, TEST_WORKSPACE, TEST_SNIPPET_ID)
    assert "status" in json.loads(result)
    assert json.loads(result)["status"] == "success"