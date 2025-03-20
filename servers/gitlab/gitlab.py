#!/usr/bin/env python3
"""
GitLab MCP Server - Model Context Protocol server for GitLab API integration.

This server allows AI assistants to interact with GitLab repositories through
standardized MCP tools for file operations, repository management, issue tracking,
and more.

Environment variables:
    GITLAB_PERSONAL_ACCESS_TOKEN: Personal access token for GitLab API
    GITLAB_API_URL: GitLab API URL (default: https://gitlab.com/api/v4)
"""

import os
import json
from typing import Any, Dict, List, Optional, Union
import httpx
from mcp.server.fastmcp import FastMCP, Context
from dotenv import load_dotenv
load_dotenv()

# Initialize FastMCP server
mcp = FastMCP("gitlab")

# Configuration
GITLAB_API_URL = os.environ.get("GITLAB_API_URL", "https://gitlab.com/api/v4")
GITLAB_PERSONAL_ACCESS_TOKEN = os.environ.get("GITLAB_PERSONAL_ACCESS_TOKEN")

if not GITLAB_PERSONAL_ACCESS_TOKEN:
    raise ValueError("GITLAB_PERSONAL_ACCESS_TOKEN environment variable is required")

# Shared HTTP client for GitLab API calls
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

# Tool implementations

@mcp.tool()
async def create_or_update_file(
    project_id: str,
    file_path: str,
    content: str,
    commit_message: str,
    branch: str,
    previous_path: Optional[str] = None
) -> str:
    """Create or update a single file in a project.
    
    Args:
        project_id: Project ID or URL-encoded path
        file_path: Path where to create/update the file
        content: Content of the file
        commit_message: Commit message
        branch: Branch to create/update the file in
        previous_path: Path of the file to move/rename (optional)
    
    Returns:
        File content and commit details
    """
    endpoint = f"projects/{project_id}/repository/files/{httpx.utils.quote(file_path)}"
    
    # Check if the file exists
    try:
        await make_gitlab_request(
            "GET",
            f"{endpoint}?ref={branch}",
        )
        # File exists, update it
        method = "PUT"
    except ValueError:
        # File doesn't exist, create it
        method = "POST"
    
    data = {
        "branch": branch,
        "content": content,
        "commit_message": commit_message,
    }
    
    if previous_path:
        data["previous_path"] = previous_path
    
    result = await make_gitlab_request(
        method,
        endpoint,
        json_data=data
    )
    
    return json.dumps(result, indent=2)

@mcp.tool()
async def push_files(
    project_id: str,
    branch: str,
    files: List[Dict[str, str]],
    commit_message: str
) -> str:
    """Push multiple files in a single commit.
    
    Args:
        project_id: Project ID or URL-encoded path
        branch: Branch to push to
        files: List of files to push, each with 'file_path' and 'content'
        commit_message: Commit message
    
    Returns:
        Updated branch reference
    """
    endpoint = f"projects/{project_id}/repository/commits"
    
    # Format the actions for the commit
    actions = []
    for file in files:
        actions.append({
            "action": "update" if file.get("update", False) else "create",
            "file_path": file["file_path"],
            "content": file["content"]
        })
    
    data = {
        "branch": branch,
        "commit_message": commit_message,
        "actions": actions
    }
    
    result = await make_gitlab_request(
        "POST",
        endpoint,
        json_data=data
    )
    
    return json.dumps(result, indent=2)

@mcp.tool()
async def search_repositories(
    search: str,
    page: Optional[int] = 1,
    per_page: Optional[int] = 20
) -> str:
    """Search for GitLab projects.
    
    Args:
        search: Search query
        page: Page number for pagination (optional, default: 1)
        per_page: Results per page (optional, default: 20)
    
    Returns:
        Project search results
    """
    endpoint = "projects"
    
    params = {
        "search": search,
        "page": page,
        "per_page": per_page,
        "order_by": "id",
        "sort": "desc"
    }
    
    result = await make_gitlab_request(
        "GET",
        endpoint,
        params=params
    )
    
    return json.dumps(result, indent=2)

@mcp.tool()
async def create_repository(
    name: str,
    description: Optional[str] = None,
    visibility: Optional[str] = "private",
    initialize_with_readme: Optional[bool] = False
) -> str:
    """Create a new GitLab project.
    
    Args:
        name: Project name
        description: Project description (optional)
        visibility: 'private', 'internal', or 'public' (optional, default: 'private')
        initialize_with_readme: Initialize with README (optional, default: False)
    
    Returns:
        Created project details
    """
    endpoint = "projects"
    
    # Validate visibility
    if visibility not in ["private", "internal", "public"]:
        raise ValueError("Visibility must be one of: 'private', 'internal', 'public'")
    
    data = {
        "name": name,
        "visibility": visibility,
        "initialize_with_readme": initialize_with_readme
    }
    
    if description:
        data["description"] = description
    
    result = await make_gitlab_request(
        "POST",
        endpoint,
        json_data=data
    )
    
    return json.dumps(result, indent=2)

@mcp.tool()
async def get_file_contents(
    project_id: str,
    file_path: str,
    ref: Optional[str] = None
) -> str:
    """Get contents of a file or directory.
    
    Args:
        project_id: Project ID or URL-encoded path
        file_path: Path to file/directory
        ref: Branch/tag/commit to get contents from (optional)
    
    Returns:
        File/directory contents
    """
    params = {}
    if ref:
        params["ref"] = ref
    
    # Try to get file contents first
    try:
        endpoint = f"projects/{project_id}/repository/files/{httpx.utils.quote(file_path)}"
        result = await make_gitlab_request(
            "GET",
            endpoint,
            params=params
        )
        
        # Get raw file content
        if "content" in result:
            import base64
            try:
                # If it's base64 encoded, decode it
                content = base64.b64decode(result["content"]).decode("utf-8")
                result["decoded_content"] = content
            except:
                # If decoding fails, keep the original content
                pass
        
        return json.dumps(result, indent=2)
    
    except ValueError:
        # If not a file, try to get directory contents
        try:
            # Remove leading slash if present
            path = file_path.lstrip("/")
            endpoint = f"projects/{project_id}/repository/tree"
            path_params = params.copy()
            path_params["path"] = path
            
            result = await make_gitlab_request(
                "GET",
                endpoint,
                params=path_params
            )
            return json.dumps(result, indent=2)
        
        except ValueError as e:
            return f"Error: {str(e)}"

@mcp.tool()
async def create_issue(
    project_id: str,
    title: str,
    description: Optional[str] = None,
    assignee_ids: Optional[List[int]] = None,
    labels: Optional[List[str]] = None,
    milestone_id: Optional[int] = None
) -> str:
    """Create a new issue.
    
    Args:
        project_id: Project ID or URL-encoded path
        title: Issue title
        description: Issue description (optional)
        assignee_ids: User IDs to assign (optional)
        labels: Labels to add (optional)
        milestone_id: Milestone ID (optional)
    
    Returns:
        Created issue details
    """
    endpoint = f"projects/{project_id}/issues"
    
    data = {
        "title": title
    }
    
    if description:
        data["description"] = description
        
    if assignee_ids:
        data["assignee_ids"] = assignee_ids
        
    if labels:
        data["labels"] = ",".join(labels)
        
    if milestone_id:
        data["milestone_id"] = milestone_id
    
    result = await make_gitlab_request(
        "POST",
        endpoint,
        json_data=data
    )
    
    return json.dumps(result, indent=2)

@mcp.tool()
async def create_merge_request(
    project_id: str,
    title: str,
    source_branch: str,
    target_branch: str,
    description: Optional[str] = None,
    draft: Optional[bool] = False,
    allow_collaboration: Optional[bool] = False
) -> str:
    """Create a new merge request.
    
    Args:
        project_id: Project ID or URL-encoded path
        title: MR title
        source_branch: Branch containing changes
        target_branch: Branch to merge into
        description: MR description (optional)
        draft: Create as draft MR (optional, default: False)
        allow_collaboration: Allow commits from upstream members (optional, default: False)
    
    Returns:
        Created merge request details
    """
    endpoint = f"projects/{project_id}/merge_requests"
    
    data = {
        "title": title,
        "source_branch": source_branch,
        "target_branch": target_branch,
        "allow_collaboration": allow_collaboration
    }
    
    if description:
        data["description"] = description
        
    if draft:
        data["draft"] = True
    
    result = await make_gitlab_request(
        "POST",
        endpoint,
        json_data=data
    )
    
    return json.dumps(result, indent=2)

@mcp.tool()
async def fork_repository(
    project_id: str,
    namespace: Optional[str] = None
) -> str:
    """Fork a project.
    
    Args:
        project_id: Project ID or URL-encoded path
        namespace: Namespace to fork to (optional)
    
    Returns:
        Forked project details
    """
    endpoint = f"projects/{project_id}/fork"
    
    data = {}
    if namespace:
        data["namespace"] = namespace
    
    result = await make_gitlab_request(
        "POST",
        endpoint,
        json_data=data
    )
    
    return json.dumps(result, indent=2)

@mcp.tool()
async def create_branch(
    project_id: str,
    branch: str,
    ref: Optional[str] = "main"
) -> str:
    """Create a new branch.
    
    Args:
        project_id: Project ID or URL-encoded path
        branch: Name for new branch
        ref: Source branch/commit for new branch (optional, default: 'main')
    
    Returns:
        Created branch reference
    """
    endpoint = f"projects/{project_id}/repository/branches"
    
    data = {
        "branch": branch,
        "ref": ref
    }
    
    result = await make_gitlab_request(
        "POST",
        endpoint,
        json_data=data
    )
    
    return json.dumps(result, indent=2)

# Additional tools beyond the requested ones

@mcp.tool()
async def list_branches(
    project_id: str,
    search: Optional[str] = None
) -> str:
    """List branches in a project.
    
    Args:
        project_id: Project ID or URL-encoded path
        search: Filter branches by name (optional)
    
    Returns:
        List of branches
    """
    endpoint = f"projects/{project_id}/repository/branches"
    
    params = {}
    if search:
        params["search"] = search
    
    result = await make_gitlab_request(
        "GET",
        endpoint,
        params=params
    )
    
    return json.dumps(result, indent=2)

@mcp.tool()
async def list_issues(
    project_id: str,
    state: Optional[str] = "opened",
    labels: Optional[List[str]] = None,
    milestone: Optional[str] = None,
    search: Optional[str] = None,
    page: Optional[int] = 1,
    per_page: Optional[int] = 20
) -> str:
    """List issues in a project.
    
    Args:
        project_id: Project ID or URL-encoded path
        state: Filter issues by state ('opened', 'closed', or 'all') (optional, default: 'opened')
        labels: Filter issues by labels (optional)
        milestone: Filter issues by milestone (optional)
        search: Search issues by title and description (optional)
        page: Page number (optional, default: 1)
        per_page: Number of items per page (optional, default: 20)
    
    Returns:
        List of issues
    """
    endpoint = f"projects/{project_id}/issues"
    
    params = {
        "state": state,
        "page": page,
        "per_page": per_page
    }
    
    if labels:
        params["labels"] = ",".join(labels)
        
    if milestone:
        params["milestone"] = milestone
        
    if search:
        params["search"] = search
    
    result = await make_gitlab_request(
        "GET",
        endpoint,
        params=params
    )
    
    return json.dumps(result, indent=2)

@mcp.tool()
async def get_project_details(
    project_id: str
) -> str:
    """Get details of a project.
    
    Args:
        project_id: Project ID or URL-encoded path
    
    Returns:
        Project details
    """
    endpoint = f"projects/{project_id}"
    
    result = await make_gitlab_request(
        "GET",
        endpoint
    )
    
    return json.dumps(result, indent=2)

@mcp.tool()
async def list_commits(
    project_id: str,
    ref_name: Optional[str] = None,
    path: Optional[str] = None,
    page: Optional[int] = 1,
    per_page: Optional[int] = 20
) -> str:
    """List commits in a project.
    
    Args:
        project_id: Project ID or URL-encoded path
        ref_name: Branch/tag name (optional)
        path: Path to file (optional)
        page: Page number (optional, default: 1)
        per_page: Number of items per page (optional, default: 20)
    
    Returns:
        List of commits
    """
    endpoint = f"projects/{project_id}/repository/commits"
    
    params = {
        "page": page,
        "per_page": per_page
    }
    
    if ref_name:
        params["ref_name"] = ref_name
        
    if path:
        params["path"] = path
    
    result = await make_gitlab_request(
        "GET",
        endpoint,
        params=params
    )
    
    return json.dumps(result, indent=2)

@mcp.tool()
async def get_commit_details(
    project_id: str,
    sha: str
) -> str:
    """Get details of a commit.
    
    Args:
        project_id: Project ID or URL-encoded path
        sha: Commit hash
    
    Returns:
        Commit details
    """
    endpoint = f"projects/{project_id}/repository/commits/{sha}"
    
    result = await make_gitlab_request(
        "GET",
        endpoint
    )
    
    return json.dumps(result, indent=2)

@mcp.tool()
async def list_merge_requests(
    project_id: str,
    state: Optional[str] = "opened",
    target_branch: Optional[str] = None,
    source_branch: Optional[str] = None,
    page: Optional[int] = 1,
    per_page: Optional[int] = 20
) -> str:
    """List merge requests in a project.
    
    Args:
        project_id: Project ID or URL-encoded path
        state: Filter merge requests by state ('opened', 'closed', 'locked', 'merged', or 'all') (optional, default: 'opened')
        target_branch: Filter by target branch (optional)
        source_branch: Filter by source branch (optional)
        page: Page number (optional, default: 1)
        per_page: Number of items per page (optional, default: 20)
    
    Returns:
        List of merge requests
    """
    endpoint = f"projects/{project_id}/merge_requests"
    
    params = {
        "state": state,
        "page": page,
        "per_page": per_page
    }
    
    if target_branch:
        params["target_branch"] = target_branch
        
    if source_branch:
        params["source_branch"] = source_branch
    
    result = await make_gitlab_request(
        "GET",
        endpoint,
        params=params
    )
    
    return json.dumps(result, indent=2)

@mcp.tool()
async def get_user_info(
    user_id: Optional[str] = None
) -> str:
    """Get information about a user or the current authenticated user.
    
    Args:
        user_id: User ID or username (optional, defaults to current user)
    
    Returns:
        User information
    """
    if user_id:
        endpoint = f"users/{user_id}"
    else:
        endpoint = "user"
    
    result = await make_gitlab_request(
        "GET",
        endpoint
    )
    
    return json.dumps(result, indent=2)

if __name__ == "__main__":
    mcp.run()