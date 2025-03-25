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
import base64
from typing import Any, Dict, List, Optional, Union, Literal
import urllib.parse
import httpx
from mcp.server.fastmcp import FastMCP, Context
from pydantic import BaseModel, Field, validator
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
    params: Optional[Dict[str, Any]] = None,
    json_data: Optional[Dict[str, Any]] = None,
    binary_data: Optional[bytes] = None,
    headers: Optional[Dict[str, str]] = None
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

# Pydantic models for validation (used internally)

# File operations models
class CreateOrUpdateFileModel(BaseModel):
    project_id: str = Field(description="Project ID or URL-encoded path")
    file_path: str = Field(description="Path where to create/update the file")
    content: str = Field(description="Content of the file")
    commit_message: str = Field(description="Commit message")
    branch: str = Field(description="Branch to create/update the file in")
    previous_path: Optional[str] = Field(None, description="Path of the file to move/rename (optional)")

class FileInfo(BaseModel):
    file_path: str = Field(description="Path of the file")
    content: str = Field(description="Content of the file")
    update: bool = Field(False, description="Whether to update an existing file")

class PushFilesModel(BaseModel):
    project_id: str = Field(description="Project ID or URL-encoded path")
    branch: str = Field(description="Branch to push to")
    files: List[FileInfo] = Field(description="List of files to push")
    commit_message: str = Field(description="Commit message")

class GetFileContentsModel(BaseModel):
    project_id: str = Field(description="Project ID or URL-encoded path")
    file_path: str = Field(description="Path to file/directory")
    ref: Optional[str] = Field(None, description="Branch/tag/commit to get contents from (optional)")

# Repository models
class SearchRepositoriesModel(BaseModel):
    search: str = Field(description="Search query")
    page: int = Field(1, description="Page number for pagination (optional, default: 1)")
    per_page: int = Field(20, description="Results per page (optional, default: 20)")

class CreateRepositoryModel(BaseModel):
    name: str = Field(description="Project name")
    description: Optional[str] = Field(None, description="Project description (optional)")
    visibility: str = Field("private", description="'private', 'internal', or 'public' (optional, default: 'private')")
    initialize_with_readme: bool = Field(False, description="Initialize with README (optional, default: False)")
    
    @validator('visibility')
    def validate_visibility(cls, v):
        if v not in ["private", "internal", "public"]:
            raise ValueError("Visibility must be one of: 'private', 'internal', 'public'")
        return v

class ForkRepositoryModel(BaseModel):
    project_id: str = Field(description="Project ID or URL-encoded path")
    namespace: Optional[str] = Field(None, description="Namespace to fork to (optional)")

class CreateBranchModel(BaseModel):
    project_id: str = Field(description="Project ID or URL-encoded path")
    branch: str = Field(description="Name for new branch")
    ref: str = Field("main", description="Source branch/commit for new branch (optional, default: 'main')")

class ListBranchesModel(BaseModel):
    project_id: str = Field(description="Project ID or URL-encoded path")
    search: Optional[str] = Field(None, description="Filter branches by name (optional)")

# Issue models
class CreateIssueModel(BaseModel):
    project_id: str = Field(description="Project ID or URL-encoded path")
    title: str = Field(description="Issue title")
    description: Optional[str] = Field(None, description="Issue description (optional)")
    assignee_ids: Optional[List[int]] = Field(None, description="User IDs to assign (optional)")
    labels: Optional[List[str]] = Field(None, description="Labels to add (optional)")
    milestone_id: Optional[int] = Field(None, description="Milestone ID (optional)")

class ListIssuesModel(BaseModel):
    project_id: str = Field(description="Project ID or URL-encoded path")
    state: str = Field("opened", description="Filter issues by state ('opened', 'closed', or 'all') (optional, default: 'opened')")
    labels: Optional[List[str]] = Field(None, description="Filter issues by labels (optional)")
    milestone: Optional[str] = Field(None, description="Filter issues by milestone (optional)")
    search: Optional[str] = Field(None, description="Search issues by title and description (optional)")
    page: int = Field(1, description="Page number (optional, default: 1)")
    per_page: int = Field(20, description="Number of items per page (optional, default: 20)")

# Merge request models
class CreateMergeRequestModel(BaseModel):
    project_id: str = Field(description="Project ID or URL-encoded path")
    title: str = Field(description="MR title")
    source_branch: str = Field(description="Branch containing changes")
    target_branch: str = Field(description="Branch to merge into")
    description: Optional[str] = Field(None, description="MR description (optional)")
    draft: bool = Field(False, description="Create as draft MR (optional, default: False)")
    allow_collaboration: bool = Field(False, description="Allow commits from upstream members (optional, default: False)")

class ListMergeRequestsModel(BaseModel):
    project_id: str = Field(description="Project ID or URL-encoded path")
    state: str = Field("opened", description="Filter merge requests by state ('opened', 'closed', 'locked', 'merged', or 'all') (optional, default: 'opened')")
    target_branch: Optional[str] = Field(None, description="Filter by target branch (optional)")
    source_branch: Optional[str] = Field(None, description="Filter by source branch (optional)")
    page: int = Field(1, description="Page number (optional, default: 1)")
    per_page: int = Field(20, description="Number of items per page (optional, default: 20)")

# Project models
class GetProjectDetailsModel(BaseModel):
    project_id: str = Field(description="Project ID or URL-encoded path")

# Commit models
class ListCommitsModel(BaseModel):
    project_id: str = Field(description="Project ID or URL-encoded path")
    ref_name: Optional[str] = Field(None, description="Branch/tag name (optional)")
    path: Optional[str] = Field(None, description="Path to file (optional)")
    page: int = Field(1, description="Page number (optional, default: 1)")
    per_page: int = Field(20, description="Number of items per page (optional, default: 20)")

class GetCommitDetailsModel(BaseModel):
    project_id: str = Field(description="Project ID or URL-encoded path")
    sha: str = Field(description="Commit hash")

# User models
class GetUserInfoModel(BaseModel):
    user_id: Optional[str] = Field(None, description="User ID or username (optional, defaults to current user)")

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
        Created/updated file details
    """
    # Validate inputs with Pydantic
    model = CreateOrUpdateFileModel(
        project_id=project_id,
        file_path=file_path,
        content=content,
        commit_message=commit_message,
        branch=branch,
        previous_path=previous_path
    )
    
    endpoint = f"projects/{model.project_id}/repository/files/{urllib.parse.quote(model.file_path, safe='')}"
    
    # Check if the file exists
    try:
        await make_gitlab_request(
            "GET",
            f"{endpoint}?ref={model.branch}",
        )
        # File exists, update it
        method = "PUT"
    except ValueError:
        # File doesn't exist, create it
        method = "POST"
    
    data = {
        "branch": model.branch,
        "content": model.content,
        "commit_message": model.commit_message,
    }
    
    if model.previous_path:
        data["previous_path"] = model.previous_path
    
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
    files: List[Dict[str, Any]],
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
    # Convert the files list to FileInfo objects
    file_info_list = []
    for file_data in files:
        update = file_data.get("update", False)
        if isinstance(update, str):
            update = update.lower() == "true"
        file_info_list.append(FileInfo(
            file_path=file_data["file_path"],
            content=file_data["content"],
            update=update
        ))
    
    # Validate inputs with Pydantic
    model = PushFilesModel(
        project_id=project_id,
        branch=branch,
        files=file_info_list,
        commit_message=commit_message
    )
    
    endpoint = f"projects/{model.project_id}/repository/commits"
    
    # Format the actions for the commit
    actions = []
    for file in model.files:
        actions.append({
            "action": "update" if file.update else "create",
            "file_path": file.file_path,
            "content": file.content
        })
    
    data = {
        "branch": model.branch,
        "commit_message": model.commit_message,
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
    page: int = 1,
    per_page: int = 20
) -> str:
    """Search for GitLab projects.
    
    Args:
        search: Search query
        page: Page number for pagination (optional, default: 1)
        per_page: Results per page (optional, default: 20)
    
    Returns:
        List of matching projects
    """
    # Validate inputs with Pydantic
    model = SearchRepositoriesModel(
        search=search,
        page=page,
        per_page=per_page
    )
    
    endpoint = "projects"
    
    params = {
        "search": model.search,
        "page": str(model.page),
        "per_page": str(model.per_page),
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
    visibility: str = "private",
    initialize_with_readme: bool = False
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
    # Validate inputs with Pydantic
    model = CreateRepositoryModel(
        name=name,
        description=description,
        visibility=visibility,
        initialize_with_readme=initialize_with_readme
    )
    
    endpoint = "projects"
    
    data = {
        "name": model.name,
        "visibility": model.visibility,
        "initialize_with_readme": model.initialize_with_readme
    }
    
    if model.description:
        data["description"] = model.description
    
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
        File content or directory listing
    """
    # Validate inputs with Pydantic
    model = GetFileContentsModel(
        project_id=project_id,
        file_path=file_path,
        ref=ref
    )
    
    params = {}
    if model.ref:
        params["ref"] = model.ref
    
    # Try to get file contents first
    try:
        endpoint = f"projects/{model.project_id}/repository/files/{urllib.parse.quote(model.file_path, safe='')}"
        result = await make_gitlab_request(
            "GET",
            endpoint,
            params=params
        )
        
        # Get raw file content
        if "content" in result:
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
            path = model.file_path.lstrip("/")
            endpoint = f"projects/{model.project_id}/repository/tree"
            path_params = params.copy()
            path_params["path"] = path
            
            result = await make_gitlab_request(
                "GET",
                endpoint,
                params=path_params
            )
            return json.dumps(result, indent=2)
        
        except ValueError as e:
            return json.dumps({"error": str(e)}, indent=2)

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
    # Validate inputs with Pydantic
    model = CreateIssueModel(
        project_id=project_id,
        title=title,
        description=description,
        assignee_ids=assignee_ids,
        labels=labels,
        milestone_id=milestone_id
    )
    
    endpoint = f"projects/{model.project_id}/issues"
    
    data = {
        "title": model.title
    }
    
    if model.description:
        data["description"] = model.description
        
    if model.assignee_ids:
        # Convert list of IDs to individual parameters for GitLab API
        for i, assignee_id in enumerate(model.assignee_ids):
            data[f"assignee_ids[{i}]"] = str(assignee_id)
        
    if model.labels:
        data["labels"] = ",".join(model.labels)
        
    if model.milestone_id:
        data["milestone_id"] = str(model.milestone_id)
    
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
    draft: bool = False,
    allow_collaboration: bool = False
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
    # Validate inputs with Pydantic
    model = CreateMergeRequestModel(
        project_id=project_id,
        title=title,
        source_branch=source_branch,
        target_branch=target_branch,
        description=description,
        draft=draft,
        allow_collaboration=allow_collaboration
    )
    
    endpoint = f"projects/{model.project_id}/merge_requests"
    
    data = {
        "title": model.title,
        "source_branch": model.source_branch,
        "target_branch": model.target_branch,
        "allow_collaboration": model.allow_collaboration
    }
    
    if model.description:
        data["description"] = model.description
        
    if model.draft:
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
    """Fork a project to the current user's namespace or a specified namespace.
    
    Args:
        project_id: Project ID or URL-encoded path
        namespace: Namespace to fork to (optional)
    
    Returns:
        Forked project details
    """
    # Validate inputs with Pydantic
    model = ForkRepositoryModel(
        project_id=project_id,
        namespace=namespace
    )
    
    endpoint = f"projects/{model.project_id}/fork"
    
    data = {}
    if model.namespace:
        data["namespace"] = model.namespace
    
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
    ref: str = "main"
) -> str:
    """Create a new branch in a project.
    
    Args:
        project_id: Project ID or URL-encoded path
        branch: Name for new branch
        ref: Source branch/commit for new branch (optional, default: 'main')
    
    Returns:
        Created branch details
    """
    # Validate inputs with Pydantic
    model = CreateBranchModel(
        project_id=project_id,
        branch=branch,
        ref=ref
    )
    
    endpoint = f"projects/{model.project_id}/repository/branches"
    
    data = {
        "branch": model.branch,
        "ref": model.ref
    }
    
    result = await make_gitlab_request(
        "POST",
        endpoint,
        json_data=data
    )
    
    return json.dumps(result, indent=2)

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
    # Validate inputs with Pydantic
    model = ListBranchesModel(
        project_id=project_id,
        search=search
    )
    
    endpoint = f"projects/{model.project_id}/repository/branches"
    
    params = {}
    if model.search:
        params["search"] = model.search
    
    result = await make_gitlab_request(
        "GET",
        endpoint,
        params=params
    )
    
    return json.dumps(result, indent=2)

@mcp.tool()
async def list_issues(
    project_id: str,
    state: str = "opened",
    labels: Optional[List[str]] = None,
    milestone: Optional[str] = None,
    search: Optional[str] = None,
    page: int = 1,
    per_page: int = 20
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
    # Validate inputs with Pydantic
    model = ListIssuesModel(
        project_id=project_id,
        state=state,
        labels=labels,
        milestone=milestone,
        search=search,
        page=page,
        per_page=per_page
    )
    
    endpoint = f"projects/{model.project_id}/issues"
    
    params = {
        "state": model.state,
        "page": str(model.page),
        "per_page": str(model.per_page)
    }
    
    if model.labels:
        params["labels"] = ",".join(model.labels)
        
    if model.milestone:
        params["milestone"] = model.milestone
        
    if model.search:
        params["search"] = model.search
    
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
    # Validate inputs with Pydantic
    model = GetProjectDetailsModel(
        project_id=project_id
    )
    
    endpoint = f"projects/{model.project_id}"
    
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
    page: int = 1,
    per_page: int = 20
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
    # Validate inputs with Pydantic
    model = ListCommitsModel(
        project_id=project_id,
        ref_name=ref_name,
        path=path,
        page=page,
        per_page=per_page
    )
    
    endpoint = f"projects/{model.project_id}/repository/commits"
    
    params = {
        "page": str(model.page),
        "per_page": str(model.per_page)
    }
    
    if model.ref_name:
        params["ref_name"] = model.ref_name
        
    if model.path:
        params["path"] = model.path
    
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
    # Validate inputs with Pydantic
    model = GetCommitDetailsModel(
        project_id=project_id,
        sha=sha
    )
    
    endpoint = f"projects/{model.project_id}/repository/commits/{model.sha}"
    
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
    # Validate inputs with Pydantic
    model = ListMergeRequestsModel(
        project_id=project_id,
        state=state,
        target_branch=target_branch,
        source_branch=source_branch,
        page=page,
        per_page=per_page
    )
    
    endpoint = f"projects/{model.project_id}/merge_requests"
    
    params = {
        "state": model.state,
        "page": str(model.page),
        "per_page": str(model.per_page)
    }
    
    if model.target_branch:
        params["target_branch"] = model.target_branch
        
    if model.source_branch:
        params["source_branch"] = model.source_branch
    
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
    # Validate inputs with Pydantic
    model = GetUserInfoModel(
        user_id=user_id
    )
    
    if model.user_id:
        endpoint = f"users/{model.user_id}"
    else:
        endpoint = "user"
    
    result = await make_gitlab_request(
        "GET",
        endpoint
    )
    
    return json.dumps(result, indent=2)
