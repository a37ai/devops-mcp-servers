import os
import base64
import httpx
import json
from typing import Optional, List, Dict, Any, Union, Generic, TypeVar
from mcp.server.fastmcp import FastMCP, Context
from dotenv import load_dotenv
from pydantic import BaseModel, Field, validator, ValidationError
load_dotenv()

# Create the Bitbucket MCP server
mcp = FastMCP("Bitbucket Cloud")

# Base URL for Bitbucket Cloud API v2.0
API_BASE_URL = "https://api.bitbucket.org/2.0"

# Base Models
class PaginationParams(BaseModel):
    page: int = Field(default=1, ge=1, description="Page number for pagination")
    pagelen: int = Field(default=10, ge=1, le=100, description="Number of items per page (max 100)")

class BitbucketErrorResponse(BaseModel):
    type: str
    error: Optional[Dict[str, Any]] = None
    
# Common Models
class UserAccount(BaseModel):
    uuid: Optional[str] = None
    username: Optional[str] = None
    display_name: Optional[str] = None
    
class ContentObject(BaseModel):
    raw: str

class Links(BaseModel):
    self: Optional[Dict[str, str]] = None
    html: Optional[Dict[str, str]] = None

# Workspace Models
class WorkspaceInput(PaginationParams):
    role: Optional[str] = Field(None, description="Filter by role (member, owner, collaborator)")

class Workspace(BaseModel):
    slug: str
    name: Optional[str] = None
    uuid: Optional[str] = None
    links: Optional[Links] = None

class WorkspaceList(BaseModel):
    size: int
    page: int
    pagelen: int
    values: List[Workspace]

# Project Models
class ProjectInput(BaseModel):
    name: str
    key: Optional[str] = None
    description: Optional[str] = None
    is_private: bool = True

class ProjectUpdateInput(BaseModel):
    name: Optional[str] = None
    description: Optional[str] = None
    is_private: Optional[bool] = None
    
class Project(BaseModel):
    name: str
    key: str
    uuid: Optional[str] = None
    description: Optional[str] = None
    is_private: bool = True
    links: Optional[Links] = None

class ProjectList(BaseModel):
    size: int
    page: int
    pagelen: int
    values: List[Project]

# Repository Models
class RepositoryInput(BaseModel):
    description: Optional[str] = None
    is_private: bool = True
    fork_policy: str = "allow_forks"
    project_key: Optional[str] = None

class RepositoryUpdateInput(BaseModel):
    name: Optional[str] = None
    description: Optional[str] = None
    is_private: Optional[bool] = None
    fork_policy: Optional[str] = None
    project_key: Optional[str] = None

class Repository(BaseModel):
    slug: str
    name: str
    uuid: Optional[str] = None
    description: Optional[str] = None
    is_private: bool
    fork_policy: str
    project: Optional[Dict[str, Any]] = None
    links: Optional[Links] = None

class RepositoryList(BaseModel):
    size: int
    page: int
    pagelen: int
    values: List[Repository]

# Branch/Tag Models
class BranchInput(BaseModel):
    name: str
    target: str

class Branch(BaseModel):
    name: str
    target: Dict[str, Any]
    
class BranchRestrictionInput(BaseModel):
    kind: str = Field(..., description="Type of restriction (e.g., push, force, delete, merge)")
    pattern: str = Field(..., description="Branch pattern to apply restriction to")
    users: Optional[List[str]] = Field(None, description="List of user UUIDs allowed to perform the action")
    groups: Optional[List[str]] = Field(None, description="List of group UUIDs allowed to perform the action")

class BranchRestriction(BaseModel):
    id: int
    kind: str
    pattern: str
    users: Optional[List[Dict[str, str]]] = None
    groups: Optional[List[Dict[str, str]]] = None

class BranchRestrictionList(BaseModel):
    size: int
    page: int
    pagelen: int
    values: List[BranchRestriction]

class BranchList(BaseModel):
    size: int
    page: int
    pagelen: int
    values: List[Branch]

class TagInput(BaseModel):
    name: str
    target: str
    message: Optional[str] = None

class Tag(BaseModel):
    name: str
    target: Dict[str, Any]
    message: Optional[str] = None

class TagList(BaseModel):
    size: int
    page: int
    pagelen: int
    values: List[Tag]

# Commit Models
class CommitParams(PaginationParams):
    branch: Optional[str] = None

class Commit(BaseModel):
    hash: str
    message: str
    date: Optional[str] = None
    author: Optional[Dict[str, Any]] = None
    
class CommitList(BaseModel):
    size: int
    page: int
    pagelen: int
    values: List[Commit]

# Pull Request Models
class PullRequestInput(BaseModel):
    title: str
    source_branch: str
    destination_branch: str
    description: Optional[str] = None
    close_source_branch: bool = False

class PullRequest(BaseModel):
    id: int
    title: str
    description: Optional[str] = None
    state: str
    source: Dict[str, Any]
    destination: Dict[str, Any]
    
class PullRequestList(BaseModel):
    size: int
    page: int
    pagelen: int
    values: List[PullRequest]

class CommentInput(BaseModel):
    content: str
    line: Optional[int] = None
    file_path: Optional[str] = None

class Comment(BaseModel):
    id: int
    content: Dict[str, str]
    created_on: Optional[str] = None
    user: Optional[Dict[str, Any]] = None
    updated_on: Optional[str] = None

# Issue Models
class IssueFilterParams(PaginationParams):
    status: Optional[str] = Field(None, description="Filter by status (new, open, resolved, etc.)")
    assignee: Optional[str] = Field(None, description="Filter by assignee username")
    reporter: Optional[str] = Field(None, description="Filter by reporter username")

class IssueInput(BaseModel):
    title: str
    content: Optional[str] = None
    kind: str = "bug"
    priority: str = "major"
    assignee: Optional[str] = None

class IssueUpdateInput(BaseModel):
    title: Optional[str] = None
    content: Optional[str] = None
    kind: Optional[str] = None
    priority: Optional[str] = None
    assignee: Optional[str] = None
    status: Optional[str] = None

class Issue(BaseModel):
    id: int
    title: str
    content: Optional[Dict[str, str]] = None
    kind: str
    priority: str
    assignee: Optional[Dict[str, str]] = None
    state: str
    
class IssueList(BaseModel):
    size: int
    page: int
    pagelen: int
    values: List[Issue]

# Webhook Models
class WebhookInput(BaseModel):
    url: str
    description: Optional[str] = None
    events: List[str] = ["repo:push"]
    active: bool = True

class Webhook(BaseModel):
    uuid: str
    url: str
    description: Optional[str] = None
    events: List[str]
    active: bool

class WebhookList(BaseModel):
    size: int
    page: int
    pagelen: int
    values: List[Webhook]

# Pipeline Models
class PipelineFilterParams(PaginationParams):
    status: Optional[str] = Field(None, description="Filter by status (PENDING, BUILDING, COMPLETED, etc.)")

class PipelineInput(BaseModel):
    branch: str
    variables: Optional[Dict[str, str]] = None

class Pipeline(BaseModel):
    uuid: str
    status: Optional[str] = None
    target: Dict[str, Any]

class PipelineList(BaseModel):
    size: int
    page: int
    pagelen: int
    values: List[Pipeline]

# Snippet Models
class SnippetInput(BaseModel):
    title: str
    filename: str
    content: str
    is_private: bool = True

class Snippet(BaseModel):
    id: str
    title: str
    is_private: bool
    files: Dict[str, Any]

class DeployKeyInput(BaseModel):
    key: str = Field(..., description="The SSH public key content")
    label: str = Field(..., description="A label for the deploy key")

class DeployKey(BaseModel):
    id: int
    key: str
    label: Optional[str] = None
    type: str
    created_on: Optional[str] = None
    last_used: Optional[str] = None

class DeployKeyList(BaseModel):
    size: int
    page: int
    pagelen: int
    values: List[DeployKey]

class SnippetList(BaseModel):
    size: int
    page: int
    pagelen: int
    values: List[Snippet]


# Helper function to get authentication header from environment variables
def get_auth_header(ctx: Context) -> Dict[str, str]:
    """
    Get authentication header using BITBUCKET_USERNAME and BITBUCKET_APP_PASSWORD
    from environment variables.
    """
    username = os.environ.get("BITBUCKET_USERNAME")
    app_password = os.environ.get("BITBUCKET_APP_PASSWORD")
    
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
            # Don't use ctx.error as it's a coroutine and needs to be awaited
            try:
                error_data = response.json()
                error_response = BitbucketErrorResponse.model_validate(error_data)
                raise ValueError(f"API Error: {error_response.model_dump_json()}")
            except (json.JSONDecodeError, ValidationError):
                raise ValueError(error_msg)
        
        # For empty responses (e.g., DELETE operations)
        if not response.text or response.status_code == 204:
            return {"status": "success", "status_code": response.status_code}
        
        return response.json()

# Helper function to format responses
def format_response(data: Union[Dict[str, Any], BaseModel]) -> str:
    """Format API response for readability."""
    if isinstance(data, BaseModel):
        return json.dumps(data.model_dump(), indent=2)
    return json.dumps(data, indent=2)

# === USER AND WORKSPACE TOOLS ===

@mcp.tool()
async def get_current_user(ctx: Context) -> str:
    """
    Retrieve the authenticated user's profile information.
    
    Returns information about the authenticated user's Bitbucket account.
    """
    data = await make_request(ctx, "GET", "user")
    # Convert to Pydantic model but still return as formatted string
    user_data = UserAccount.model_validate(data)
    return format_response(user_data)

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
    user_data = UserAccount.model_validate(data)
    return format_response(user_data)

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
    # Use Pydantic model for input validation
    input_params = WorkspaceInput(role=role, page=page, pagelen=pagelen)
    
    params = input_params.model_dump(exclude_none=True)
    
    data = await make_request(ctx, "GET", "workspaces", params=params)
    
    # Validate response data with Pydantic model
    workspaces = WorkspaceList.model_validate(data)
    return format_response(workspaces)

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
    workspace_data = Workspace.model_validate(data)
    return format_response(workspace_data)

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
    # Use Pydantic model for input validation
    input_params = PaginationParams(page=page, pagelen=pagelen)
    
    params = input_params.model_dump(exclude_none=True)
    
    data = await make_request(ctx, "GET", f"workspaces/{workspace}/projects", params=params)
    
    # Validate response data with Pydantic model
    projects = ProjectList.model_validate(data)
    return format_response(projects)

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
    # Validate inputs with Pydantic model
    project_input = ProjectInput(
        name=name,
        key=key,
        description=description,
        is_private=is_private
    )
    
    # Convert to dict for API request, excluding None values
    project_data = project_input.model_dump(exclude_none=True)
    
    data = await make_request(ctx, "POST", f"workspaces/{workspace}/projects", json_data=project_data)
    
    # Validate response with Pydantic model
    project = Project.model_validate(data)
    return format_response(project)

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
    project = Project.model_validate(data)
    return format_response(project)

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
    # Validate inputs with Pydantic model
    project_update = ProjectUpdateInput(
        name=name,
        description=description,
        is_private=is_private
    )
    
    # Convert to dict for API request, excluding None values
    update_data = project_update.model_dump(exclude_none=True)
    
    if not update_data:
        return "No update data provided"
    
    data = await make_request(ctx, "PUT", f"workspaces/{workspace}/projects/{project_key}", 
                            json_data=update_data)
    
    # Validate response with Pydantic model
    project = Project.model_validate(data)
    return format_response(project)

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
    # Use Pydantic model for input validation
    input_params = PaginationParams(page=page, pagelen=pagelen)
    
    # Convert to dict for API request
    params = input_params.model_dump(exclude_none=True)
    
    if role:
        params["role"] = role
    
    endpoint = "repositories"
    if workspace:
        endpoint = f"repositories/{workspace}"
    
    data = await make_request(ctx, "GET", endpoint, params=params)
    
    # Validate response with Pydantic model
    repositories = RepositoryList.model_validate(data)
    return format_response(repositories)

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
    
    # Validate response with Pydantic model
    repository = Repository.model_validate(data)
    return format_response(repository)

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
    # Validate inputs with Pydantic model
    repo_input = RepositoryInput(
        description=description,
        is_private=is_private,
        fork_policy=fork_policy,
        project_key=project_key
    )
    
    # Convert to dict for API request, excluding None values
    repo_data = repo_input.model_dump(exclude_none=True)
    
    # Add required SCM type
    repo_data["scm"] = "git"
    
    # Format project field as required by the API
    if project_key:
        repo_data["project"] = {"key": project_key}
        # Remove the original project_key field
        repo_data.pop("project_key", None)
    
    data = await make_request(ctx, "POST", f"repositories/{workspace}/{repo_slug}", 
                            json_data=repo_data)
    
    # Validate response with Pydantic model
    repository = Repository.model_validate(data)
    return format_response(repository)

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
    # Use Pydantic model for input validation
    input_params = PaginationParams(page=page, pagelen=pagelen)
    
    # Convert to dict for API request
    params = input_params.model_dump(exclude_none=True)
    
    data = await make_request(ctx, "GET", f"repositories/{workspace}/{repo_slug}/refs/branches", 
                            params=params)
    
    # Validate response with Pydantic model
    branches = BranchList.model_validate(data)
    return format_response(branches)

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
    # Validate inputs with Pydantic model
    branch_input = BranchInput(
        name=name,
        target=target
    )
    
    # Convert to dict for API request
    branch_data = branch_input.model_dump()
    
    # Format target field as required by the API
    branch_data["target"] = {
        "hash": target
    }
    
    data = await make_request(ctx, "POST", f"repositories/{workspace}/{repo_slug}/refs/branches", 
                            json_data=branch_data)
    
    # Validate response with Pydantic model
    branch = Branch.model_validate(data)
    return format_response(branch)

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
    # Use Pydantic model for input validation
    input_params = PaginationParams(page=page, pagelen=pagelen)
    
    # Convert to dict for API request
    params = input_params.model_dump(exclude_none=True)
    
    data = await make_request(ctx, "GET", f"repositories/{workspace}/{repo_slug}/refs/tags", 
                            params=params)
    
    # Validate response with Pydantic model
    tags = TagList.model_validate(data)
    return format_response(tags)

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
    # Validate inputs with Pydantic model
    tag_input = TagInput(
        name=name,
        target=target,
        message=message
    )
    
    # Convert to dict for API request, excluding None values
    tag_data = tag_input.model_dump(exclude_none=True)
    
    # Format target field as required by the API
    tag_data["target"] = {
        "hash": target
    }
    
    data = await make_request(ctx, "POST", f"repositories/{workspace}/{repo_slug}/refs/tags", 
                            json_data=tag_data)
    
    # Validate response with Pydantic model
    tag = Tag.model_validate(data)
    return format_response(tag)

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
    # Use Pydantic model for input validation
    input_params = CommitParams(
        page=page, 
        pagelen=pagelen,
        branch=branch
    )
    
    # Convert to dict for API request
    params = input_params.model_dump(exclude_unset=True, exclude={"branch"})
    
    endpoint = f"repositories/{workspace}/{repo_slug}/commits"
    if branch:
        endpoint = f"{endpoint}/{branch}"
    
    data = await make_request(ctx, "GET", endpoint, params=params)
    
    # Validate response with Pydantic model
    commits = CommitList.model_validate(data)
    return format_response(commits)

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
    
    # Validate response with Pydantic model
    commit_data = Commit.model_validate(data)
    return format_response(commit_data)

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
    # Use Pydantic model for input validation
    input_params = PaginationParams(page=page, pagelen=pagelen)
    
    # Convert to dict for API request
    params = input_params.model_dump(exclude_none=True)
    if state:
        params["state"] = state
    
    data = await make_request(ctx, "GET", f"repositories/{workspace}/{repo_slug}/pullrequests", 
                            params=params)
    
    # Validate response with Pydantic model
    pull_requests = PullRequestList.model_validate(data)
    return format_response(pull_requests)

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
    # Validate inputs with Pydantic model
    pr_input = PullRequestInput(
        title=title,
        source_branch=source_branch,
        destination_branch=destination_branch,
        description=description,
        close_source_branch=close_source_branch
    )
    
    # Convert to dict for API request, excluding None values
    pr_data = pr_input.model_dump(exclude_none=True)
    
    # Format branch fields as required by the API
    pr_data["source"] = {
        "branch": {
            "name": source_branch
        }
    }
    pr_data["destination"] = {
        "branch": {
            "name": destination_branch
        }
    }
    
    # Remove the original fields that might be present
    pr_data.pop("source_branch", None)
    pr_data.pop("destination_branch", None)
    
    data = await make_request(ctx, "POST", f"repositories/{workspace}/{repo_slug}/pullrequests", 
                            json_data=pr_data)
    
    # Validate response with Pydantic model
    pull_request = PullRequest.model_validate(data)
    return format_response(pull_request)

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
    
    # Validate response with Pydantic model
    pull_request = PullRequest.model_validate(data)
    return format_response(pull_request)

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
    
    # Validate response with Pydantic model
    pull_request = PullRequest.model_validate(data)
    return format_response(pull_request)

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
    
    # Validate response with Pydantic model
    pull_request = PullRequest.model_validate(data)
    return format_response(pull_request)

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
    # Use Pydantic model for input validation
    merge_input = PullRequestInput(
        title="",  # Not needed for merge
        source_branch="",  # Not needed for merge
        destination_branch="",  # Not needed for merge
        description=message,
        close_source_branch=True  # Default to closing source branch after merge
    )
    
    # Convert to dict for API request
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
    
    # Validate response with Pydantic model
    pull_request = PullRequest.model_validate(data)
    return format_response(pull_request)

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
    
    # Validate response with Pydantic model
    pull_request = PullRequest.model_validate(data)
    return format_response(pull_request)

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
    # Use Pydantic model for input validation
    comment_input = CommentInput(
        content=content,
        line=line,
        file_path=file_path
    )
    
    # Convert to dict for API request
    comment_data = comment_input.model_dump(exclude_none=True)
    # Restructure for API format
    comment_data = {
        "content": {
            "raw": comment_data.pop("content")
        }
    }
    if "line" in comment_data and "file_path" in comment_data:
        comment_data["inline"] = {
            "path": comment_data.pop("file_path"),
            "line": comment_data.pop("line")
        }
    
    data = await make_request(
        ctx, "POST", 
        f"repositories/{workspace}/{repo_slug}/pullrequests/{pull_request_id}/comments", 
        json_data=comment_data
    )
    
    # Validate response with Pydantic model
    comment = ContentObject.model_validate(data)
    return format_response(comment)

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
    # Use Pydantic model for input validation
    input_params = PaginationParams(page=page, pagelen=pagelen)
    
    # Convert to dict for API request
    params = input_params.model_dump(exclude_none=True)
    
    data = await make_request(ctx, "GET", f"repositories/{workspace}/{repo_slug}/branch-restrictions", 
                            params=params)
    
    # Validate response with Pydantic model
    restrictions = BranchRestrictionList.model_validate(data)
    return format_response(restrictions)

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
    # Use Pydantic model for input validation
    restriction_input = BranchRestrictionInput(
        kind=kind,
        pattern=pattern,
        users=users,
        groups=groups
    )
    
    # Convert to dict for API request
    restriction_data = restriction_input.model_dump(exclude_none=True)
    
    # Transform users and groups to API format if present
    if "users" in restriction_data:
        restriction_data["users"] = [{"uuid": uuid} for uuid in restriction_data["users"]]
    if "groups" in restriction_data:
        restriction_data["groups"] = [{"uuid": uuid} for uuid in restriction_data["groups"]]
    
    data = await make_request(
        ctx, "POST", 
        f"repositories/{workspace}/{repo_slug}/branch-restrictions",
        json_data=restriction_data
    )
    
    # Validate response with Pydantic model
    restriction = BranchRestriction.model_validate(data)
    return format_response(restriction)

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
    # Use Pydantic model for input validation
    input_params = PaginationParams(page=page, pagelen=pagelen)
    
    # Convert to dict for API request
    params = input_params.model_dump(exclude_none=True)
    
    data = await make_request(ctx, "GET", f"repositories/{workspace}/{repo_slug}/deploy-keys", 
                            params=params)
    
    # Validate response with Pydantic model
    deploy_keys = DeployKeyList.model_validate(data)
    return format_response(deploy_keys)

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
    # Use Pydantic model for input validation
    key_input = DeployKeyInput(
        key=key,
        label=label
    )
    
    # Convert to dict for API request
    key_data = key_input.model_dump(exclude_none=True)
    
    data = await make_request(
        ctx, "POST", 
        f"repositories/{workspace}/{repo_slug}/deploy-keys",
        json_data=key_data
    )
    
    # Validate response with Pydantic model
    deploy_key = DeployKey.model_validate(data)
    return format_response(deploy_key)

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
    
    # For DELETE operations, we might get no content back
    if result:
        # If we get content back, validate it
        deploy_key = DeployKey.model_validate(result)
        return format_response(deploy_key)
    else:
        # If no content, return empty success response
        return format_response({"success": True})

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
    # Use Pydantic model for input validation
    input_params = PaginationParams(page=page, pagelen=pagelen)
    
    # Convert to dict for API request
    params = input_params.model_dump(exclude_none=True)
    
    data = await make_request(ctx, "GET", f"repositories/{workspace}/{repo_slug}/hooks", 
                            params=params)
    
    # Validate response with Pydantic model
    webhooks = WebhookList.model_validate(data)
    return format_response(webhooks)

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
        
    # Use Pydantic model for input validation
    webhook_input = WebhookInput(
        url=url,
        description=description,
        events=events,
        active=active
    )
    
    # Convert to dict for API request
    webhook_data = webhook_input.model_dump(exclude_none=True)
    
    data = await make_request(
        ctx, "POST", 
        f"repositories/{workspace}/{repo_slug}/hooks",
        json_data=webhook_data
    )
    
    # Validate response with Pydantic model
    webhook = Webhook.model_validate(data)
    return format_response(webhook)

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
    
    # For DELETE operations, we might get no content back
    if result:
        # If we get content back, validate it
        webhook = Webhook.model_validate(result)
        return format_response(webhook)
    else:
        # If no content, return empty success response
        return format_response({"success": True})

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
    # Use Pydantic model for input validation
    input_params = IssueFilterParams(
        page=page,
        pagelen=pagelen,
        status=status,
        assignee=assignee,
        reporter=reporter
    )
    
    # Convert to dict for API request
    params = input_params.model_dump(exclude_none=True)
    
    data = await make_request(ctx, "GET", f"repositories/{workspace}/{repo_slug}/issues", 
                            params=params)
    
    # Validate response with Pydantic model
    issues = IssueList.model_validate(data)
    return format_response(issues)

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
    # Validate inputs with Pydantic model
    issue_input = IssueInput(
        title=title,
        content=content,
        kind=kind,
        priority=priority,
        assignee=assignee
    )
    
    # Convert to dict for API request, excluding None values
    issue_data = issue_input.model_dump(exclude_none=True)
    
    # Format content and assignee fields as required by the API
    if content:
        issue_data["content"] = {
            "raw": content
        }
        # Remove the original content field that might be present
        if "content" in issue_data and not isinstance(issue_data["content"], dict):
            issue_data.pop("content", None)
    
    if assignee:
        issue_data["assignee"] = {
            "username": assignee
        }
        # Remove the original assignee field that might be present
        if "assignee" in issue_data and not isinstance(issue_data["assignee"], dict):
            issue_data.pop("assignee", None)
    
    data = await make_request(
        ctx, "POST", 
        f"repositories/{workspace}/{repo_slug}/issues",
        json_data=issue_data
    )
    
    # Validate response with Pydantic model
    issue = Issue.model_validate(data)
    return format_response(issue)

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
    
    # Validate response with Pydantic model
    issue = Issue.model_validate(data)
    return format_response(issue)
    # Validate response with Pydantic model
    issue = Issue.model_validate(data)
    return format_response(issue)

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
    # Use Pydantic model for input validation
    issue_update = IssueUpdateInput(
        title=title,
        content=content,
        kind=kind,
        priority=priority,
        assignee=assignee,
        status=status
    )
    
    # Convert to dict for API request
    update_data = issue_update.model_dump(exclude_none=True)
    
    # Format content and assignee fields as required by the API
    if "content" in update_data:
        update_data["content"] = {
            "raw": update_data["content"]
        }
    
    if "assignee" in update_data:
        update_data["assignee"] = {
            "username": update_data["assignee"]
        }
    
    # Map status to state field as required by API
    if "status" in update_data:
        update_data["state"] = update_data.pop("status")
    
    if not update_data:
        return "No update data provided"
    
    data = await make_request(
        ctx, "PUT", 
        f"repositories/{workspace}/{repo_slug}/issues/{issue_id}",
        json_data=update_data
    )
    
    # Validate response with Pydantic model
    issue = Issue.model_validate(data)
    return format_response(issue)

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
    # Use Pydantic model for input validation
    comment_input = CommentInput(content=content)
    
    # Format content field as required by the API
    comment_data = {
        "content": {
            "raw": comment_input.content
        }
    }
    
    data = await make_request(
        ctx, "POST", 
        f"repositories/{workspace}/{repo_slug}/issues/{issue_id}/comments", 
        json_data=comment_data
    )
    
    # Validate response with Pydantic model
    comment = Comment.model_validate(data)
    return format_response(comment)

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
    # Use Pydantic model for input validation
    input_params = PipelineFilterParams(
        page=page,
        pagelen=pagelen,
        status=status
    )
    
    # Convert to dict for API request
    params = input_params.model_dump(exclude_none=True)
    
    data = await make_request(ctx, "GET", f"repositories/{workspace}/{repo_slug}/pipelines/", 
                            params=params)
    
    # Validate response with Pydantic model
    pipelines = PipelineList.model_validate(data)
    return format_response(pipelines)

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
    # Use Pydantic model for input validation
    pipeline_input = PipelineInput(
        branch=branch,
        variables=variables
    )
    
    # Convert to dict and format for API request
    pipeline_data = {
        "target": {
            "ref_type": "branch",
            "ref_name": pipeline_input.branch,
            "type": "pipeline_ref_target"
        }
    }
    
    if pipeline_input.variables:
        pipeline_data["variables"] = [
            {"key": key, "value": value} for key, value in pipeline_input.variables.items()
        ]
    
    data = await make_request(
        ctx, "POST", 
        f"repositories/{workspace}/{repo_slug}/pipelines/",
        json_data=pipeline_data
    )
    
    # Validate response with Pydantic model
    pipeline = Pipeline.model_validate(data)
    return format_response(pipeline)

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
    
    # Validate response with Pydantic model
    pipeline = Pipeline.model_validate(data)
    return format_response(pipeline)

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
    
    # Validate response with Pydantic model
    pipeline = Pipeline.model_validate(data)
    return format_response(pipeline)

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
