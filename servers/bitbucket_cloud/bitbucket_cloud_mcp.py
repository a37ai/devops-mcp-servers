import os
import base64
import httpx
import json
from typing import Optional, List, Dict, Any, Union
from mcp.server.fastmcp import FastMCP, Context
from dotenv import load_dotenv
load_dotenv()

# Create the Bitbucket MCP server
mcp = FastMCP("Bitbucket Cloud")

# Base URL for Bitbucket Cloud API v2.0
API_BASE_URL = "https://api.bitbucket.org/2.0"

# Helper function to get authentication header from environment variables
def get_auth_header(ctx: Context) -> Dict[str, str]:
    """
    Get authentication header using either BITBUCKET_USERNAME and BITBUCKET_APP_PASSWORD
    from the context or environment variables.
    """
    username = ctx.get_config("BITBUCKET_USERNAME") or os.environ.get("BITBUCKET_USERNAME")
    app_password = ctx.get_config("BITBUCKET_APP_PASSWORD") or os.environ.get("BITBUCKET_APP_PASSWORD")
    
    if not username or not app_password:
        raise ValueError(
            "Authentication credentials not found. "
            "Please set BITBUCKET_USERNAME and BITBUCKET_APP_PASSWORD environment variables."
        )
    
    auth_string = f"{username}:{app_password}"
    encoded_auth = base64.b64encode(auth_string.encode()).decode()
    return {"Authorization": f"Basic {encoded_auth}"}

# Helper function to make API requests
async def make_request(
    ctx: Context,
    method: str,
    endpoint: str,
    params: Optional[Dict[str, Any]] = None,
    json_data: Optional[Dict[str, Any]] = None
) -> Dict[str, Any]:
    """Make a request to the Bitbucket API with auth headers."""
    url = f"{API_BASE_URL}/{endpoint}"
    headers = get_auth_header(ctx)
    headers["Content-Type"] = "application/json"
    
    async with httpx.AsyncClient() as client:
        response = await client.request(
            method=method,
            url=url,
            params=params,
            json=json_data,
            headers=headers,
            timeout=30.0
        )
        
        if response.status_code >= 400:
            error_msg = f"Error {response.status_code}: {response.text}"
            ctx.error(error_msg)
            raise ValueError(error_msg)
        
        # For empty responses (e.g., DELETE operations)
        if not response.text or response.status_code == 204:
            return {"status": "success", "status_code": response.status_code}
        
        return response.json()

# Helper function to format responses
def format_response(data: Dict[str, Any]) -> str:
    """Format API response for readability."""
    return json.dumps(data, indent=2)

# === USER AND WORKSPACE TOOLS ===

@mcp.tool()
async def get_current_user(ctx: Context) -> str:
    """
    Retrieve the authenticated user's profile information.
    
    Returns information about the authenticated user's Bitbucket account.
    """
    data = await make_request(ctx, "GET", "user")
    return format_response(data)

@mcp.tool()
async def get_user_profile(ctx: Context, username: str) -> str:
    """
    Fetch public profile data for a specific user account.
    
    Args:
        username: The username or UUID of the Bitbucket user.
    
    Returns:
        JSON data containing the user's public profile information.
    """
    data = await make_request(ctx, "GET", f"users/{username}")
    return format_response(data)

@mcp.tool()
async def list_workspaces(ctx: Context, role: Optional[str] = None, page: int = 1, pagelen: int = 10) -> str:
    """
    List workspaces the authenticated user has access to.
    
    Args:
        role: Optional filter by role (member, owner, collaborator)
        page: Page number for pagination
        pagelen: Number of items per page (max 100)
    
    Returns:
        JSON data containing the list of workspaces.
    """
    params = {"page": page, "pagelen": pagelen}
    if role:
        params["role"] = role
    
    data = await make_request(ctx, "GET", "workspaces", params=params)
    return format_response(data)

@mcp.tool()
async def get_workspace(ctx: Context, workspace: str) -> str:
    """
    Retrieves details of a specific workspace.
    
    Args:
        workspace: The workspace ID (slug) to retrieve.
    
    Returns:
        JSON data containing the workspace details.
    """
    data = await make_request(ctx, "GET", f"workspaces/{workspace}")
    return format_response(data)

# === PROJECT MANAGEMENT TOOLS ===

@mcp.tool()
async def list_projects(ctx: Context, workspace: str, page: int = 1, pagelen: int = 10) -> str:
    """
    List projects in a workspace.
    
    Args:
        workspace: The workspace ID (slug)
        page: Page number for pagination
        pagelen: Number of items per page (max 100)
    
    Returns:
        JSON data containing the list of projects.
    """
    params = {"page": page, "pagelen": pagelen}
    data = await make_request(ctx, "GET", f"workspaces/{workspace}/projects", params=params)
    return format_response(data)

@mcp.tool()
async def create_project(
    ctx: Context, 
    workspace: str, 
    name: str, 
    key: Optional[str] = None, 
    description: Optional[str] = None, 
    is_private: bool = True
) -> str:
    """
    Create a new project in a workspace.
    
    Args:
        workspace: The workspace ID (slug)
        name: The name of the project
        key: Optional project key (will be auto-generated if not provided)
        description: Optional project description
        is_private: Whether the project is private (default True)
    
    Returns:
        JSON data for the created project.
    """
    project_data = {
        "name": name,
        "is_private": is_private
    }
    
    if key:
        project_data["key"] = key
    
    if description:
        project_data["description"] = description
    
    data = await make_request(ctx, "POST", f"workspaces/{workspace}/projects", json_data=project_data)
    return format_response(data)

@mcp.tool()
async def get_project(ctx: Context, workspace: str, project_key: str) -> str:
    """
    Get details for a specific project.
    
    Args:
        workspace: The workspace ID (slug)
        project_key: The project key
    
    Returns:
        JSON data containing the project details.
    """
    data = await make_request(ctx, "GET", f"workspaces/{workspace}/projects/{project_key}")
    return format_response(data)

@mcp.tool()
async def update_project(
    ctx: Context,
    workspace: str,
    project_key: str,
    name: Optional[str] = None,
    description: Optional[str] = None,
    is_private: Optional[bool] = None
) -> str:
    """
    Update project information.
    
    Args:
        workspace: The workspace ID (slug)
        project_key: The project key
        name: New project name (optional)
        description: New project description (optional)
        is_private: New private status (optional)
    
    Returns:
        JSON data for the updated project.
    """
    update_data = {}
    
    if name:
        update_data["name"] = name
    
    if description:
        update_data["description"] = description
    
    if is_private is not None:
        update_data["is_private"] = is_private
    
    if not update_data:
        return "No update data provided"
    
    data = await make_request(ctx, "PUT", f"workspaces/{workspace}/projects/{project_key}", 
                            json_data=update_data)
    return format_response(data)

@mcp.tool()
async def delete_project(ctx: Context, workspace: str, project_key: str) -> str:
    """
    Delete a project.
    
    Args:
        workspace: The workspace ID (slug)
        project_key: The project key
    
    Returns:
        Status of the deletion operation.
    """
    result = await make_request(ctx, "DELETE", f"workspaces/{workspace}/projects/{project_key}")
    return format_response(result)

# === REPOSITORY MANAGEMENT TOOLS ===

@mcp.tool()
async def list_repositories(
    ctx: Context, 
    workspace: Optional[str] = None, 
    role: Optional[str] = None,
    page: int = 1, 
    pagelen: int = 10
) -> str:
    """
    List repositories.
    
    Args:
        workspace: Optional workspace ID to filter repositories by workspace
        role: Optional role filter (admin, contributor, member, owner)
        page: Page number for pagination
        pagelen: Number of items per page (max 100)
    
    Returns:
        JSON data containing the list of repositories.
    """
    params = {"page": page, "pagelen": pagelen}
    if role:
        params["role"] = role
    
    endpoint = "repositories"
    if workspace:
        endpoint = f"repositories/{workspace}"
    
    data = await make_request(ctx, "GET", endpoint, params=params)
    return format_response(data)

@mcp.tool()
async def get_repository(ctx: Context, workspace: str, repo_slug: str) -> str:
    """
    Get details for a specific repository.
    
    Args:
        workspace: The workspace ID (slug)
        repo_slug: The repository slug
    
    Returns:
        JSON data containing the repository details.
    """
    data = await make_request(ctx, "GET", f"repositories/{workspace}/{repo_slug}")
    return format_response(data)

@mcp.tool()
async def create_repository(
    ctx: Context,
    workspace: str,
    repo_slug: str,
    description: Optional[str] = None,
    is_private: bool = True,
    fork_policy: str = "allow_forks",
    project_key: Optional[str] = None
) -> str:
    """
    Create a new repository in a workspace.
    
    Args:
        workspace: The workspace ID (slug)
        repo_slug: The repository slug (name)
        description: Optional repository description
        is_private: Whether the repository is private (default True)
        fork_policy: Fork policy (allow_forks, no_public_forks, no_forks)
        project_key: Optional project key to associate the repository with
    
    Returns:
        JSON data for the created repository.
    """
    repo_data = {
        "scm": "git",
        "is_private": is_private,
        "fork_policy": fork_policy
    }
    
    if description:
        repo_data["description"] = description
    
    if project_key:
        repo_data["project"] = {"key": project_key}
    
    data = await make_request(ctx, "POST", f"repositories/{workspace}/{repo_slug}", 
                            json_data=repo_data)
    return format_response(data)

@mcp.tool()
async def update_repository(
    ctx: Context,
    workspace: str,
    repo_slug: str,
    description: Optional[str] = None,
    is_private: Optional[bool] = None,
    fork_policy: Optional[str] = None,
    project_key: Optional[str] = None,
    name: Optional[str] = None
) -> str:
    """
    Update repository settings.
    
    Args:
        workspace: The workspace ID (slug)
        repo_slug: The repository slug
        description: New repository description (optional)
        is_private: New private status (optional)
        fork_policy: New fork policy (optional)
        project_key: New project key (optional)
        name: New repository name (optional)
    
    Returns:
        JSON data for the updated repository.
    """
    update_data = {}
    
    if description:
        update_data["description"] = description
    
    if is_private is not None:
        update_data["is_private"] = is_private
    
    if fork_policy:
        update_data["fork_policy"] = fork_policy
    
    if project_key:
        update_data["project"] = {"key": project_key}
    
    if name:
        update_data["name"] = name
    
    if not update_data:
        return "No update data provided"
    
    data = await make_request(ctx, "PUT", f"repositories/{workspace}/{repo_slug}", 
                            json_data=update_data)
    return format_response(data)

@mcp.tool()
async def delete_repository(ctx: Context, workspace: str, repo_slug: str) -> str:
    """
    Delete a repository.
    
    Args:
        workspace: The workspace ID (slug)
        repo_slug: The repository slug
    
    Returns:
        Status of the deletion operation.
    """
    result = await make_request(ctx, "DELETE", f"repositories/{workspace}/{repo_slug}")
    return format_response(result)

# === BRANCH AND TAG MANAGEMENT TOOLS ===

@mcp.tool()
async def list_branches(
    ctx: Context, 
    workspace: str, 
    repo_slug: str,
    page: int = 1, 
    pagelen: int = 10
) -> str:
    """
    List branches in a repository.
    
    Args:
        workspace: The workspace ID (slug)
        repo_slug: The repository slug
        page: Page number for pagination
        pagelen: Number of items per page (max 100)
    
    Returns:
        JSON data containing the list of branches.
    """
    params = {"page": page, "pagelen": pagelen}
    data = await make_request(ctx, "GET", f"repositories/{workspace}/{repo_slug}/refs/branches", 
                            params=params)
    return format_response(data)

@mcp.tool()
async def create_branch(
    ctx: Context,
    workspace: str,
    repo_slug: str,
    name: str,
    target: str
) -> str:
    """
    Create a new branch in a repository.
    
    Args:
        workspace: The workspace ID (slug)
        repo_slug: The repository slug
        name: The name of the new branch
        target: The target commit hash or branch name
    
    Returns:
        JSON data for the created branch.
    """
    branch_data = {
        "name": name,
        "target": {
            "hash": target
        }
    }
    
    data = await make_request(ctx, "POST", f"repositories/{workspace}/{repo_slug}/refs/branches", 
                            json_data=branch_data)
    return format_response(data)

@mcp.tool()
async def list_tags(
    ctx: Context, 
    workspace: str, 
    repo_slug: str,
    page: int = 1, 
    pagelen: int = 10
) -> str:
    """
    List tags in a repository.
    
    Args:
        workspace: The workspace ID (slug)
        repo_slug: The repository slug
        page: Page number for pagination
        pagelen: Number of items per page (max 100)
    
    Returns:
        JSON data containing the list of tags.
    """
    params = {"page": page, "pagelen": pagelen}
    data = await make_request(ctx, "GET", f"repositories/{workspace}/{repo_slug}/refs/tags", 
                            params=params)
    return format_response(data)

@mcp.tool()
async def create_tag(
    ctx: Context,
    workspace: str,
    repo_slug: str,
    name: str,
    target: str,
    message: Optional[str] = None
) -> str:
    """
    Create a new tag in a repository.
    
    Args:
        workspace: The workspace ID (slug)
        repo_slug: The repository slug
        name: The name of the new tag
        target: The target commit hash
        message: Optional tag message
    
    Returns:
        JSON data for the created tag.
    """
    tag_data = {
        "name": name,
        "target": {
            "hash": target
        }
    }
    
    if message:
        tag_data["message"] = message
    
    data = await make_request(ctx, "POST", f"repositories/{workspace}/{repo_slug}/refs/tags", 
                            json_data=tag_data)
    return format_response(data)

# === COMMIT AND SOURCE CODE TOOLS ===

@mcp.tool()
async def list_commits(
    ctx: Context, 
    workspace: str, 
    repo_slug: str,
    branch: Optional[str] = None,
    page: int = 1, 
    pagelen: int = 10
) -> str:
    """
    List commits in a repository or branch.
    
    Args:
        workspace: The workspace ID (slug)
        repo_slug: The repository slug
        branch: Optional branch name to filter commits
        page: Page number for pagination
        pagelen: Number of items per page (max 100)
    
    Returns:
        JSON data containing the list of commits.
    """
    params = {"page": page, "pagelen": pagelen}
    
    endpoint = f"repositories/{workspace}/{repo_slug}/commits"
    if branch:
        endpoint = f"{endpoint}/{branch}"
    
    data = await make_request(ctx, "GET", endpoint, params=params)
    return format_response(data)

@mcp.tool()
async def get_commit(ctx: Context, workspace: str, repo_slug: str, commit: str) -> str:
    """
    Get detailed information for a single commit.
    
    Args:
        workspace: The workspace ID (slug)
        repo_slug: The repository slug
        commit: The commit hash
    
    Returns:
        JSON data containing the commit details.
    """
    data = await make_request(ctx, "GET", f"repositories/{workspace}/{repo_slug}/commit/{commit}")
    return format_response(data)

@mcp.tool()
async def get_commit_diff(
    ctx: Context, 
    workspace: str, 
    repo_slug: str,
    spec: str,
    context_lines: int = 3
) -> str:
    """
    Get the diff for a commit or comparison between commits.
    
    Args:
        workspace: The workspace ID (slug)
        repo_slug: The repository slug
        spec: The commit hash or revision spec (e.g., 'master..feature')
        context_lines: Number of context lines around each change
    
    Returns:
        Unified diff content.
    """
    params = {"context": context_lines}
    data = await make_request(ctx, "GET", f"repositories/{workspace}/{repo_slug}/diff/{spec}", 
                            params=params)
    return format_response(data)

@mcp.tool()
async def add_commit_comment(
    ctx: Context,
    workspace: str,
    repo_slug: str,
    commit: str,
    content: str,
    line: Optional[int] = None,
    file_path: Optional[str] = None
) -> str:
    """
    Add a comment to a commit.
    
    Args:
        workspace: The workspace ID (slug)
        repo_slug: The repository slug
        commit: The commit hash
        content: The comment text content
        line: Optional line number to comment on
        file_path: Optional file path to comment on
    
    Returns:
        JSON data for the created comment.
    """
    comment_data = {
        "content": {
            "raw": content
        }
    }
    
    if line and file_path:
        comment_data["inline"] = {
            "path": file_path,
            "line": line
        }
    
    data = await make_request(
        ctx, "POST", 
        f"repositories/{workspace}/{repo_slug}/commit/{commit}/comments", 
        json_data=comment_data
    )
    return format_response(data)

@mcp.tool()
async def get_file_content(
    ctx: Context, 
    workspace: str, 
    repo_slug: str,
    file_path: str,
    commit: Optional[str] = None
) -> str:
    """
    Get the content of a file in a repository.
    
    Args:
        workspace: The workspace ID (slug)
        repo_slug: The repository slug
        file_path: The path to the file
        commit: Optional commit hash or branch (defaults to the default branch)
    
    Returns:
        File content as text.
    """
    commit_ref = commit if commit else "master"
    raw_response = True
    
    # For raw content we need to use the raw endpoint and handle the response differently
    async with httpx.AsyncClient() as client:
        url = f"{API_BASE_URL}/repositories/{workspace}/{repo_slug}/src/{commit_ref}/{file_path}"
        headers = get_auth_header(ctx)
        
        response = await client.get(url, headers=headers, timeout=30.0)
        
        if response.status_code >= 400:
            error_msg = f"Error {response.status_code}: {response.text}"
            ctx.error(error_msg)
            raise ValueError(error_msg)
            
        return response.text

# === PULL REQUEST TOOLS ===

@mcp.tool()
async def list_pull_requests(
    ctx: Context, 
    workspace: str, 
    repo_slug: str,
    state: Optional[str] = "OPEN",
    page: int = 1, 
    pagelen: int = 10
) -> str:
    """
    List pull requests in a repository.
    
    Args:
        workspace: The workspace ID (slug)
        repo_slug: The repository slug
        state: Optional filter by state (OPEN, MERGED, DECLINED, SUPERSEDED)
        page: Page number for pagination
        pagelen: Number of items per page (max 100)
    
    Returns:
        JSON data containing the list of pull requests.
    """
    params = {"page": page, "pagelen": pagelen}
    if state:
        params["state"] = state
    
    data = await make_request(ctx, "GET", f"repositories/{workspace}/{repo_slug}/pullrequests", 
                            params=params)
    return format_response(data)

@mcp.tool()
async def create_pull_request(
    ctx: Context,
    workspace: str,
    repo_slug: str,
    title: str,
    source_branch: str,
    destination_branch: str,
    description: Optional[str] = None,
    close_source_branch: bool = False
) -> str:
    """
    Create a new pull request.
    
    Args:
        workspace: The workspace ID (slug)
        repo_slug: The repository slug
        title: The title of the pull request
        source_branch: The source branch name
        destination_branch: The destination branch name
        description: Optional pull request description
        close_source_branch: Whether to close the source branch after merge (default False)
    
    Returns:
        JSON data for the created pull request.
    """
    pr_data = {
        "title": title,
        "source": {
            "branch": {
                "name": source_branch
            }
        },
        "destination": {
            "branch": {
                "name": destination_branch
            }
        },
        "close_source_branch": close_source_branch
    }
    
    if description:
        pr_data["description"] = description
    
    data = await make_request(ctx, "POST", f"repositories/{workspace}/{repo_slug}/pullrequests", 
                            json_data=pr_data)
    return format_response(data)

@mcp.tool()
async def get_pull_request(ctx: Context, workspace: str, repo_slug: str, pull_request_id: int) -> str:
    """
    Get details for a specific pull request.
    
    Args:
        workspace: The workspace ID (slug)
        repo_slug: The repository slug
        pull_request_id: The pull request ID
    
    Returns:
        JSON data containing the pull request details.
    """
    data = await make_request(ctx, "GET", f"repositories/{workspace}/{repo_slug}/pullrequests/{pull_request_id}")
    return format_response(data)

@mcp.tool()
async def approve_pull_request(ctx: Context, workspace: str, repo_slug: str, pull_request_id: int) -> str:
    """
    Approve a pull request.
    
    Args:
        workspace: The workspace ID (slug)
        repo_slug: The repository slug
        pull_request_id: The pull request ID
    
    Returns:
        JSON data containing the approval status.
    """
    data = await make_request(
        ctx, "POST", 
        f"repositories/{workspace}/{repo_slug}/pullrequests/{pull_request_id}/approve"
    )
    return format_response(data)

@mcp.tool()
async def unapprove_pull_request(ctx: Context, workspace: str, repo_slug: str, pull_request_id: int) -> str:
    """
    Remove approval from a pull request.
    
    Args:
        workspace: The workspace ID (slug)
        repo_slug: The repository slug
        pull_request_id: The pull request ID
    
    Returns:
        Status of the unapproval operation.
    """
    data = await make_request(
        ctx, "DELETE", 
        f"repositories/{workspace}/{repo_slug}/pullrequests/{pull_request_id}/approve"
    )
    return format_response(data)

@mcp.tool()
async def merge_pull_request(
    ctx: Context, 
    workspace: str, 
    repo_slug: str, 
    pull_request_id: int,
    merge_strategy: str = "merge_commit",
    message: Optional[str] = None
) -> str:
    """
    Merge a pull request.
    
    Args:
        workspace: The workspace ID (slug)
        repo_slug: The repository slug
        pull_request_id: The pull request ID
        merge_strategy: Merge strategy (merge_commit, squash, or fast_forward)
        message: Optional custom merge commit message
    
    Returns:
        JSON data containing the merge status.
    """
    merge_data = {
        "merge_strategy": merge_strategy
    }
    
    if message:
        merge_data["message"] = message
    
    data = await make_request(
        ctx, "POST", 
        f"repositories/{workspace}/{repo_slug}/pullrequests/{pull_request_id}/merge",
        json_data=merge_data
    )
    return format_response(data)

@mcp.tool()
async def decline_pull_request(ctx: Context, workspace: str, repo_slug: str, pull_request_id: int) -> str:
    """
    Decline a pull request.
    
    Args:
        workspace: The workspace ID (slug)
        repo_slug: The repository slug
        pull_request_id: The pull request ID
    
    Returns:
        JSON data containing the decline status.
    """
    data = await make_request(
        ctx, "POST", 
        f"repositories/{workspace}/{repo_slug}/pullrequests/{pull_request_id}/decline"
    )
    return format_response(data)

@mcp.tool()
async def add_pull_request_comment(
    ctx: Context,
    workspace: str,
    repo_slug: str,
    pull_request_id: int,
    content: str,
    line: Optional[int] = None,
    file_path: Optional[str] = None
) -> str:
    """
    Add a comment to a pull request.
    
    Args:
        workspace: The workspace ID (slug)
        repo_slug: The repository slug
        pull_request_id: The pull request ID
        content: The comment text content
        line: Optional line number to comment on
        file_path: Optional file path to comment on
    
    Returns:
        JSON data for the created comment.
    """
    comment_data = {
        "content": {
            "raw": content
        }
    }
    
    if line and file_path:
        comment_data["inline"] = {
            "path": file_path,
            "line": line
        }
    
    data = await make_request(
        ctx, "POST", 
        f"repositories/{workspace}/{repo_slug}/pullrequests/{pull_request_id}/comments", 
        json_data=comment_data
    )
    return format_response(data)

# === REPOSITORY SETTINGS AND ADMIN TOOLS ===

@mcp.tool()
async def list_branch_restrictions(
    ctx: Context, 
    workspace: str, 
    repo_slug: str,
    page: int = 1, 
    pagelen: int = 10
) -> str:
    """
    List branch restrictions for a repository.
    
    Args:
        workspace: The workspace ID (slug)
        repo_slug: The repository slug
        page: Page number for pagination
        pagelen: Number of items per page (max 100)
    
    Returns:
        JSON data containing the list of branch restrictions.
    """
    params = {"page": page, "pagelen": pagelen}
    data = await make_request(ctx, "GET", f"repositories/{workspace}/{repo_slug}/branch-restrictions", 
                            params=params)
    return format_response(data)

@mcp.tool()
async def create_branch_restriction(
    ctx: Context,
    workspace: str,
    repo_slug: str,
    kind: str,
    pattern: str,
    users: Optional[List[str]] = None,
    groups: Optional[List[str]] = None
) -> str:
    """
    Create a new branch restriction.
    
    Args:
        workspace: The workspace ID (slug)
        repo_slug: The repository slug
        kind: Type of restriction (e.g., push, force, delete, merge)
        pattern: Branch pattern to apply restriction to (e.g., "master", "release/*")
        users: Optional list of user UUIDs allowed to perform the action
        groups: Optional list of group UUIDs allowed to perform the action
    
    Returns:
        JSON data for the created branch restriction.
    """
    restriction_data = {
        "kind": kind,
        "pattern": pattern
    }
    
    if users:
        restriction_data["users"] = [{"uuid": uuid} for uuid in users]
    
    if groups:
        restriction_data["groups"] = [{"uuid": uuid} for uuid in groups]
    
    data = await make_request(
        ctx, "POST", 
        f"repositories/{workspace}/{repo_slug}/branch-restrictions",
        json_data=restriction_data
    )
    return format_response(data)

@mcp.tool()
async def list_deploy_keys(
    ctx: Context, 
    workspace: str, 
    repo_slug: str,
    page: int = 1, 
    pagelen: int = 10
) -> str:
    """
    List deploy keys for a repository.
    
    Args:
        workspace: The workspace ID (slug)
        repo_slug: The repository slug
        page: Page number for pagination
        pagelen: Number of items per page (max 100)
    
    Returns:
        JSON data containing the list of deploy keys.
    """
    params = {"page": page, "pagelen": pagelen}
    data = await make_request(ctx, "GET", f"repositories/{workspace}/{repo_slug}/deploy-keys", 
                            params=params)
    return format_response(data)

@mcp.tool()
async def add_deploy_key(
    ctx: Context,
    workspace: str,
    repo_slug: str,
    key: str,
    label: str
) -> str:
    """
    Add a deploy key to a repository.
    
    Args:
        workspace: The workspace ID (slug)
        repo_slug: The repository slug
        key: The SSH public key content
        label: A label for the deploy key
    
    Returns:
        JSON data for the added deploy key.
    """
    key_data = {
        "key": key,
        "label": label
    }
    
    data = await make_request(
        ctx, "POST", 
        f"repositories/{workspace}/{repo_slug}/deploy-keys",
        json_data=key_data
    )
    return format_response(data)

@mcp.tool()
async def delete_deploy_key(ctx: Context, workspace: str, repo_slug: str, key_id: int) -> str:
    """
    Delete a deploy key from a repository.
    
    Args:
        workspace: The workspace ID (slug)
        repo_slug: The repository slug
        key_id: The ID of the deploy key
    
    Returns:
        Status of the deletion operation.
    """
    result = await make_request(
        ctx, "DELETE", 
        f"repositories/{workspace}/{repo_slug}/deploy-keys/{key_id}"
    )
    return format_response(result)

@mcp.tool()
async def list_webhooks(
    ctx: Context, 
    workspace: str, 
    repo_slug: str,
    page: int = 1, 
    pagelen: int = 10
) -> str:
    """
    List webhooks for a repository.
    
    Args:
        workspace: The workspace ID (slug)
        repo_slug: The repository slug
        page: Page number for pagination
        pagelen: Number of items per page (max 100)
    
    Returns:
        JSON data containing the list of webhooks.
    """
    params = {"page": page, "pagelen": pagelen}
    data = await make_request(ctx, "GET", f"repositories/{workspace}/{repo_slug}/hooks", 
                            params=params)
    return format_response(data)

@mcp.tool()
async def create_webhook(
    ctx: Context,
    workspace: str,
    repo_slug: str,
    url: str,
    description: Optional[str] = None,
    events: Optional[List[str]] = None,
    active: bool = True
) -> str:
    """
    Create a new webhook for a repository.
    
    Args:
        workspace: The workspace ID (slug)
        repo_slug: The repository slug
        url: The URL to send webhook events to
        description: Optional webhook description
        events: List of events to trigger the webhook (e.g., ["repo:push", "pullrequest:created"])
        active: Whether the webhook is active (default True)
    
    Returns:
        JSON data for the created webhook.
    """
    if events is None:
        events = ["repo:push"]
        
    webhook_data = {
        "url": url,
        "active": active,
        "events": events
    }
    
    if description:
        webhook_data["description"] = description
    
    data = await make_request(
        ctx, "POST", 
        f"repositories/{workspace}/{repo_slug}/hooks",
        json_data=webhook_data
    )
    return format_response(data)

@mcp.tool()
async def delete_webhook(ctx: Context, workspace: str, repo_slug: str, webhook_id: str) -> str:
    """
    Delete a webhook from a repository.
    
    Args:
        workspace: The workspace ID (slug)
        repo_slug: The repository slug
        webhook_id: The ID of the webhook
    
    Returns:
        Status of the deletion operation.
    """
    result = await make_request(
        ctx, "DELETE", 
        f"repositories/{workspace}/{repo_slug}/hooks/{webhook_id}"
    )
    return format_response(result)

# === ISSUE TRACKER TOOLS ===

@mcp.tool()
async def list_issues(
    ctx: Context, 
    workspace: str, 
    repo_slug: str,
    status: Optional[str] = None,
    assignee: Optional[str] = None,
    reporter: Optional[str] = None,
    page: int = 1, 
    pagelen: int = 10
) -> str:
    """
    List issues in a repository's issue tracker.
    
    Args:
        workspace: The workspace ID (slug)
        repo_slug: The repository slug
        status: Optional filter by status (new, open, resolved, etc.)
        assignee: Optional filter by assignee username
        reporter: Optional filter by reporter username
        page: Page number for pagination
        pagelen: Number of items per page (max 100)
    
    Returns:
        JSON data containing the list of issues.
    """
    params = {"page": page, "pagelen": pagelen}
    
    if status:
        params["status"] = status
    
    if assignee:
        params["assignee"] = assignee
    
    if reporter:
        params["reporter"] = reporter
    
    data = await make_request(ctx, "GET", f"repositories/{workspace}/{repo_slug}/issues", 
                            params=params)
    return format_response(data)

@mcp.tool()
async def create_issue(
    ctx: Context,
    workspace: str,
    repo_slug: str,
    title: str,
    content: Optional[str] = None,
    kind: Optional[str] = "bug",
    priority: Optional[str] = "major",
    assignee: Optional[str] = None
) -> str:
    """
    Create a new issue in the repository's issue tracker.
    
    Args:
        workspace: The workspace ID (slug)
        repo_slug: The repository slug
        title: The issue title
        content: Optional issue description content
        kind: Issue kind (bug, enhancement, proposal, task)
        priority: Issue priority (trivial, minor, major, critical, blocker)
        assignee: Optional assignee username
    
    Returns:
        JSON data for the created issue.
    """
    issue_data = {
        "title": title,
        "kind": kind,
        "priority": priority
    }
    
    if content:
        issue_data["content"] = {
            "raw": content
        }
    
    if assignee:
        issue_data["assignee"] = {
            "username": assignee
        }
    
    data = await make_request(
        ctx, "POST", 
        f"repositories/{workspace}/{repo_slug}/issues",
        json_data=issue_data
    )
    return format_response(data)

@mcp.tool()
async def get_issue(ctx: Context, workspace: str, repo_slug: str, issue_id: int) -> str:
    """
    Get details for a specific issue.
    
    Args:
        workspace: The workspace ID (slug)
        repo_slug: The repository slug
        issue_id: The issue ID
    
    Returns:
        JSON data containing the issue details.
    """
    data = await make_request(ctx, "GET", f"repositories/{workspace}/{repo_slug}/issues/{issue_id}")
    return format_response(data)

@mcp.tool()
async def update_issue(
    ctx: Context,
    workspace: str,
    repo_slug: str,
    issue_id: int,
    title: Optional[str] = None,
    content: Optional[str] = None,
    kind: Optional[str] = None,
    priority: Optional[str] = None,
    assignee: Optional[str] = None,
    status: Optional[str] = None
) -> str:
    """
    Update an existing issue.
    
    Args:
        workspace: The workspace ID (slug)
        repo_slug: The repository slug
        issue_id: The issue ID
        title: Optional new issue title
        content: Optional new issue description content
        kind: Optional new issue kind
        priority: Optional new issue priority
        assignee: Optional new assignee username
        status: Optional new status (new, open, resolved, etc.)
    
    Returns:
        JSON data for the updated issue.
    """
    update_data = {}
    
    if title:
        update_data["title"] = title
    
    if content:
        update_data["content"] = {
            "raw": content
        }
    
    if kind:
        update_data["kind"] = kind
    
    if priority:
        update_data["priority"] = priority
    
    if assignee:
        update_data["assignee"] = {
            "username": assignee
        }
    
    if status:
        update_data["state"] = status
    
    if not update_data:
        return "No update data provided"
    
    data = await make_request(
        ctx, "PUT", 
        f"repositories/{workspace}/{repo_slug}/issues/{issue_id}",
        json_data=update_data
    )
    return format_response(data)

@mcp.tool()
async def add_issue_comment(
    ctx: Context,
    workspace: str,
    repo_slug: str,
    issue_id: int,
    content: str
) -> str:
    """
    Add a comment to an issue.
    
    Args:
        workspace: The workspace ID (slug)
        repo_slug: The repository slug
        issue_id: The issue ID
        content: The comment text content
    
    Returns:
        JSON data for the created comment.
    """
    comment_data = {
        "content": {
            "raw": content
        }
    }
    
    data = await make_request(
        ctx, "POST", 
        f"repositories/{workspace}/{repo_slug}/issues/{issue_id}/comments", 
        json_data=comment_data
    )
    return format_response(data)

# === PIPELINES (CI/CD) TOOLS ===

@mcp.tool()
async def list_pipelines(
    ctx: Context, 
    workspace: str, 
    repo_slug: str,
    status: Optional[str] = None,
    page: int = 1, 
    pagelen: int = 10
) -> str:
    """
    List pipelines for a repository.
    
    Args:
        workspace: The workspace ID (slug)
        repo_slug: The repository slug
        status: Optional filter by status (PENDING, BUILDING, COMPLETED, etc.)
        page: Page number for pagination
        pagelen: Number of items per page (max 100)
    
    Returns:
        JSON data containing the list of pipelines.
    """
    params = {"page": page, "pagelen": pagelen}
    
    if status:
        params["status"] = status
    
    data = await make_request(ctx, "GET", f"repositories/{workspace}/{repo_slug}/pipelines/", 
                            params=params)
    return format_response(data)

@mcp.tool()
async def trigger_pipeline(
    ctx: Context,
    workspace: str,
    repo_slug: str,
    branch: str,
    variables: Optional[Dict[str, str]] = None
) -> str:
    """
    Trigger a new pipeline run on a specific branch.
    
    Args:
        workspace: The workspace ID (slug)
        repo_slug: The repository slug
        branch: The branch to run the pipeline on
        variables: Optional dictionary of pipeline variables
    
    Returns:
        JSON data for the triggered pipeline.
    """
    pipeline_data = {
        "target": {
            "ref_type": "branch",
            "ref_name": branch,
            "type": "pipeline_ref_target"
        }
    }
    
    if variables:
        pipeline_data["variables"] = [
            {"key": key, "value": value} for key, value in variables.items()
        ]
    
    data = await make_request(
        ctx, "POST", 
        f"repositories/{workspace}/{repo_slug}/pipelines/",
        json_data=pipeline_data
    )
    return format_response(data)

@mcp.tool()
async def get_pipeline(ctx: Context, workspace: str, repo_slug: str, pipeline_uuid: str) -> str:
    """
    Get details for a specific pipeline run.
    
    Args:
        workspace: The workspace ID (slug)
        repo_slug: The repository slug
        pipeline_uuid: The UUID of the pipeline
    
    Returns:
        JSON data containing the pipeline details.
    """
    data = await make_request(ctx, "GET", f"repositories/{workspace}/{repo_slug}/pipelines/{pipeline_uuid}")
    return format_response(data)

@mcp.tool()
async def stop_pipeline(ctx: Context, workspace: str, repo_slug: str, pipeline_uuid: str) -> str:
    """
    Stop a running pipeline.
    
    Args:
        workspace: The workspace ID (slug)
        repo_slug: The repository slug
        pipeline_uuid: The UUID of the pipeline
    
    Returns:
        JSON data containing the stop operation status.
    """
    data = await make_request(
        ctx, "POST", 
        f"repositories/{workspace}/{repo_slug}/pipelines/{pipeline_uuid}/stopPipeline"
    )
    return format_response(data)

# === SNIPPETS TOOLS ===

@mcp.tool()
async def list_snippets(
    ctx: Context,
    workspace: Optional[str] = None,
    role: Optional[str] = None,
    page: int = 1, 
    pagelen: int = 10
) -> str:
    """
    List snippets, optionally filtered by workspace.
    
    Args:
        workspace: Optional workspace ID to filter snippets
        role: Optional role filter (owner, contributor, member)
        page: Page number for pagination
        pagelen: Number of items per page (max 100)
    
    Returns:
        JSON data containing the list of snippets.
    """
    params = {"page": page, "pagelen": pagelen}
    
    if role:
        params["role"] = role
    
    endpoint = "snippets"
    if workspace:
        endpoint = f"snippets/{workspace}"
    
    data = await make_request(ctx, "GET", endpoint, params=params)
    return format_response(data)

@mcp.tool()
async def create_snippet(
    ctx: Context,
    workspace: str,
    title: str,
    filename: str,
    content: str,
    is_private: bool = True
) -> str:
    """
    Create a new snippet in a workspace.
    
    Args:
        workspace: The workspace ID (slug)
        title: The snippet title
        filename: The name of the file
        content: The content of the snippet file
        is_private: Whether the snippet is private (default True)
    
    Returns:
        JSON data for the created snippet.
    """
    snippet_data = {
        "title": title,
        "is_private": is_private,
        "files": {
            filename: {
                "content": content
            }
        }
    }
    
    data = await make_request(
        ctx, "POST", 
        f"snippets/{workspace}",
        json_data=snippet_data
    )
    return format_response(data)

@mcp.tool()
async def get_snippet(ctx: Context, workspace: str, snippet_id: str) -> str:
    """
    Get details for a specific snippet.
    
    Args:
        workspace: The workspace ID (slug)
        snippet_id: The snippet ID
    
    Returns:
        JSON data containing the snippet details.
    """
    data = await make_request(ctx, "GET", f"snippets/{workspace}/{snippet_id}")
    return format_response(data)

@mcp.tool()
async def get_snippet_file(
    ctx: Context, 
    workspace: str, 
    snippet_id: str, 
    filename: str
) -> str:
    """
    Get the content of a specific file in a snippet.
    
    Args:
        workspace: The workspace ID (slug)
        snippet_id: The snippet ID
        filename: The name of the file
    
    Returns:
        File content as text.
    """
    # For raw content we need to use the raw endpoint and handle the response differently
    async with httpx.AsyncClient() as client:
        url = f"{API_BASE_URL}/snippets/{workspace}/{snippet_id}/files/{filename}"
        headers = get_auth_header(ctx)
        
        response = await client.get(url, headers=headers, timeout=30.0)
        
        if response.status_code >= 400:
            error_msg = f"Error {response.status_code}: {response.text}"
            ctx.error(error_msg)
            raise ValueError(error_msg)
            
        return response.text

@mcp.tool()
async def delete_snippet(ctx: Context, workspace: str, snippet_id: str) -> str:
    """
    Delete a snippet.
    
    Args:
        workspace: The workspace ID (slug)
        snippet_id: The snippet ID
    
    Returns:
        Status of the deletion operation.
    """
    result = await make_request(
        ctx, "DELETE", 
        f"snippets/{workspace}/{snippet_id}"
    )
    return format_response(result)

# Run the server using stdio transport when executed directly
if __name__ == "__main__":
    mcp.run()