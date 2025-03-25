from typing import Any, Dict, List, Optional, Union, cast
import os
import json
import httpx
from mcp.server.fastmcp import FastMCP, Context
from dotenv import load_dotenv
from pydantic import BaseModel, Field
load_dotenv()

# Initialize the MCP server
mcp = FastMCP("GitHub")

# Define Pydantic models for input validation
class SearchRepositoriesInput(BaseModel):
    query: str
    page: int = 1
    perPage: int = 30

class CreateRepositoryInput(BaseModel):
    name: str
    description: str = ""
    private: bool = False
    autoInit: bool = False

class GetFileContentsInput(BaseModel):
    owner: str
    repo: str
    path: str
    branch: Optional[str] = None

class CreateOrUpdateFileInput(BaseModel):
    owner: str
    repo: str
    path: str
    content: str
    message: str
    branch: str
    sha: Optional[str] = None

class CreateIssueInput(BaseModel):
    owner: str
    repo: str
    title: str
    body: str = ""
    assignees: Optional[List[str]] = None
    labels: Optional[List[str]] = None
    milestone: Optional[int] = None

class ListIssuesInput(BaseModel):
    owner: str
    repo: str
    state: str = "open"
    labels: Optional[List[str]] = None
    sort: str = "created"
    direction: str = "desc"
    since: Optional[str] = None
    page: int = 1
    per_page: int = 30

class CreatePullRequestInput(BaseModel):
    owner: str
    repo: str
    title: str
    head: str
    base: str
    body: str = ""
    draft: bool = False
    maintainer_can_modify: bool = True

class GetRepositoryInput(BaseModel):
    owner: str
    repo: str

class ForkRepositoryInput(BaseModel):
    owner: str
    repo: str
    organization: Optional[str] = None

class CreateBranchInput(BaseModel):
    owner: str
    repo: str
    branch: str
    from_branch: Optional[str] = None

class SearchCodeInput(BaseModel):
    q: str
    sort: str = "indexed"
    order: str = "desc"
    per_page: int = 30
    page: int = 1

# Constants and configuration
GITHUB_API_BASE = "https://api.github.com"
GITHUB_TOKEN = os.environ.get("GITHUB_PERSONAL_ACCESS_TOKEN")

# Check if token is available
if not GITHUB_TOKEN:
    print("Warning: GITHUB_PERSONAL_ACCESS_TOKEN environment variable not set")
    print("Some functionality may be limited")

# Helper functions for GitHub API requests
async def github_request(
    method: str, 
    endpoint: str, 
    data: Optional[Dict[str, Any]] = None, 
    params: Optional[Dict[str, Any]] = None
) -> Dict[str, Any]:
    """Make a request to the GitHub API with proper authentication and error handling."""
    headers = {
        "Accept": "application/vnd.github.v3+json",
        "User-Agent": "MCP-GitHub-Server/1.0"
    }
    
    if GITHUB_TOKEN:
        headers["Authorization"] = f"token {GITHUB_TOKEN}"
    
    url = f"{GITHUB_API_BASE}{endpoint}"
    
    async with httpx.AsyncClient() as client:
        try:
            if method == "GET":
                response = await client.get(url, headers=headers, params=params, timeout=30.0)
            elif method == "POST":
                response = await client.post(url, headers=headers, json=data, timeout=30.0)
            elif method == "PUT":
                response = await client.put(url, headers=headers, json=data, timeout=30.0)
            elif method == "PATCH":
                response = await client.patch(url, headers=headers, json=data, timeout=30.0)
            else:
                return {"error": f"Unsupported method: {method}"}
            
            response.raise_for_status()
            return response.json() if response.text else {}
        except httpx.HTTPStatusError as e:
            error_message = f"HTTP error {e.response.status_code}"
            try:
                error_json = e.response.json()
                if "message" in error_json:
                    error_message += f": {error_json['message']}"
            except:
                pass
            return {"error": error_message}
        except Exception as e:
            return {"error": str(e)}

# GitHub API Tool implementations

@mcp.tool()
async def search_repositories(query: str, page: int = 1, perPage: int = 30) -> str:
    """Search for GitHub repositories based on a query.
    
    Args:
        query: Search query using GitHub search syntax
        page: Page number for pagination (default: 1)
        perPage: Results per page (max 100, default: 30)
    
    Returns:
        Formatted search results with repository details
    """
    # Validate inputs with Pydantic
    input_data = SearchRepositoriesInput(query=query, page=page, perPage=perPage)
    
    params = {
        "q": input_data.query,
        "page": input_data.page,
        "per_page": min(input_data.perPage, 100)  # Enforcing GitHub API limits
    }
    
    result = await github_request("GET", "/search/repositories", params=params)
    
    if "error" in result:
        return f"Error searching repositories: {result['error']}"
    
    total_count = result.get("total_count", 0)
    items = result.get("items", [])
    
    if not items:
        return f"No repositories found matching '{input_data.query}'."
    
    response = [f"Found {total_count} repositories matching '{input_data.query}'. Showing page {input_data.page}:"]
    
    for repo in items:
        description = repo.get("description", "No description")
        response.append(f"\n## {repo['full_name']}")
        response.append(f"Description: {description}")
        response.append(f"Stars: {repo.get('stargazers_count', 0)}, Forks: {repo.get('forks_count', 0)}")
        response.append(f"Language: {repo.get('language', 'Not specified')}")
        response.append(f"URL: {repo.get('html_url', 'N/A')}")
        
    return "\n".join(response)

@mcp.tool()
async def create_repository(
    name: str, 
    description: str = "", 
    private: bool = False, 
    autoInit: bool = False
) -> str:
    """Create a new GitHub repository.
    
    Args:
        name: Repository name
        description: Repository description
        private: Whether the repository should be private
        autoInit: Initialize with README
    
    Returns:
        Details of the created repository
    """
    # Validate inputs with Pydantic
    input_data = CreateRepositoryInput(
        name=name,
        description=description,
        private=private,
        autoInit=autoInit
    )
    
    if not GITHUB_TOKEN:
        return "Error: GitHub token required to create repositories."
    
    data = {
        "name": input_data.name,
        "description": input_data.description,
        "private": input_data.private,
        "auto_init": input_data.autoInit
    }
    
    result = await github_request("POST", "/user/repos", data=data)
    
    if "error" in result:
        return f"Error creating repository: {result['error']}"
    
    return f"""
Repository created successfully!
Name: {result.get('full_name', input_data.name)}
URL: {result.get('html_url', 'N/A')}
Description: {result.get('description', input_data.description)}
Private: {result.get('private', input_data.private)}
    """

@mcp.tool()
async def get_file_contents(owner: str, repo: str, path: str, branch: str = None) -> str:
    """Get contents of a file or directory from a GitHub repository.
    
    Args:
        owner: Repository owner (username or organization)
        repo: Repository name
        path: Path to file/directory
        branch: Branch to get contents from (default: repo default branch)
    
    Returns:
        File content or directory listing
    """
    # Validate inputs with Pydantic
    input_data = GetFileContentsInput(owner=owner, repo=repo, path=path, branch=branch)
    
    endpoint = f"/repos/{input_data.owner}/{input_data.repo}/contents/{input_data.path}"
    params = {}
    if input_data.branch:
        params["ref"] = input_data.branch
    
    result = await github_request("GET", endpoint, params=params)
    
    if "error" in result:
        return f"Error getting file contents: {result['error']}"
    
    # If result is a list, it's a directory
    if isinstance(result, list):
        response = [f"Directory listing for `{input_data.path}` in {input_data.owner}/{input_data.repo}:"]
        for item in result:
            if isinstance(item, dict):
                item_type = "📁 " if item.get("type") == "dir" else "📄 "
                response.append(f"{item_type}{item.get('name', 'Unknown')} - {item.get('size', 0)} bytes")
            else:
                response.append(f"📄 {item}")
        return "\n".join(response)
    
    # It's a file
    content = result.get("content", "")
    encoding = result.get("encoding", "")
    
    if encoding == "base64":
        import base64
        try:
            decoded_content = base64.b64decode(content).decode('utf-8')
            return f"Contents of `{input_data.path}` in {input_data.owner}/{input_data.repo}:\n\n```\n{decoded_content}\n```"
        except:
            return f"Could not decode content of `{input_data.path}`. It may be a binary file."
    
    return f"Contents of `{input_data.path}` in {input_data.owner}/{input_data.repo} (not in base64 format):\n{content}"

@mcp.tool()
async def create_or_update_file(
    owner: str, 
    repo: str, 
    path: str, 
    content: str, 
    message: str, 
    branch: str, 
    sha: str = None
) -> str:
    """Create or update a file in a GitHub repository.
    
    Args:
        owner: Repository owner (username or organization)
        repo: Repository name
        path: Path where to create/update the file
        content: Content of the file
        message: Commit message
        branch: Branch to create/update the file in
        sha: SHA of file being replaced (required for updates)
    
    Returns:
        Confirmation message and commit details
    """
    # Validate inputs with Pydantic
    input_data = CreateOrUpdateFileInput(
        owner=owner,
        repo=repo,
        path=path,
        content=content,
        message=message,
        branch=branch,
        sha=sha
    )
    
    if not GITHUB_TOKEN:
        return "Error: GitHub token required to modify files."
    
    import base64
    encoded_content = base64.b64encode(input_data.content.encode()).decode()
    
    data = {
        "message": input_data.message,
        "content": encoded_content,
        "branch": input_data.branch
    }
    
    if input_data.sha:
        data["sha"] = input_data.sha
    
    endpoint = f"/repos/{input_data.owner}/{input_data.repo}/contents/{input_data.path}"
    result = await github_request("PUT", endpoint, data=data)
    
    if "error" in result:
        return f"Error creating/updating file: {result['error']}"
    
    action = "updated" if input_data.sha else "created"
    
    commit = result.get("commit", {})
    commit_url = commit.get("html_url", "Unknown")
    
    return f"""
File {action} successfully!
Path: {input_data.path}
Repository: {input_data.owner}/{input_data.repo}
Branch: {input_data.branch}
Commit message: {input_data.message}
Commit URL: {commit_url}
    """

@mcp.tool()
async def create_issue(
    owner: str, 
    repo: str, 
    title: str, 
    body: str = "", 
    assignees: List[str] = None, 
    labels: List[str] = None, 
    milestone: int = None
) -> str:
    """Create a new issue in a GitHub repository.
    
    Args:
        owner: Repository owner (username or organization)
        repo: Repository name
        title: Issue title
        body: Issue description
        assignees: List of usernames to assign
        labels: List of label names
        milestone: Milestone number
    
    Returns:
        Issue creation details
    """
    # Validate inputs with Pydantic
    input_data = CreateIssueInput(
        owner=owner,
        repo=repo,
        title=title,
        body=body,
        assignees=assignees,
        labels=labels,
        milestone=milestone
    )
    
    if not GITHUB_TOKEN:
        return "Error: GitHub token required to create issues."
    
    data = {
        "title": input_data.title,
        "body": input_data.body
    }
    
    # GitHub API expects these fields as JSON arrays, not strings
    if input_data.assignees:
        # Cast to Any to avoid type errors with Dict[str, Any]
        data["assignees"] = cast(Any, input_data.assignees)
    
    if input_data.labels:
        # Cast to Any to avoid type errors with Dict[str, Any]
        data["labels"] = cast(Any, input_data.labels)
    
    if input_data.milestone:
        # Convert milestone to string if provided
        data["milestone"] = str(input_data.milestone)
    
    endpoint = f"/repos/{input_data.owner}/{input_data.repo}/issues"
    result = await github_request("POST", endpoint, data=data)
    
    if "error" in result:
        return f"Error creating issue: {result['error']}"
    
    return f"""
Issue created successfully!
Title: {result.get('title', input_data.title)}
Number: #{result.get('number', 'Unknown')}
URL: {result.get('html_url', 'N/A')}
    """

@mcp.tool()
async def list_issues(
    owner: str, 
    repo: str, 
    state: str = "open", 
    labels: List[str] = None, 
    sort: str = "created", 
    direction: str = "desc", 
    since: str = None,
    page: int = 1,
    per_page: int = 30
) -> str:
    """List and filter issues from a GitHub repository.
    
    Args:
        owner: Repository owner
        repo: Repository name
        state: Filter by state ('open', 'closed', 'all')
        labels: Filter by labels
        sort: Sort by ('created', 'updated', 'comments')
        direction: Sort direction ('asc', 'desc')
        since: Filter by date (ISO 8601 timestamp)
        page: Page number
        per_page: Results per page
    
    Returns:
        Formatted list of issues
    """
    # Validate inputs with Pydantic
    input_data = ListIssuesInput(
        owner=owner,
        repo=repo,
        state=state,
        labels=labels,
        sort=sort,
        direction=direction,
        since=since,
        page=page,
        per_page=per_page
    )
    
    params = {
        "state": input_data.state,
        "sort": input_data.sort,
        "direction": input_data.direction,
        "page": input_data.page,
        "per_page": min(input_data.per_page, 100)  # Enforce GitHub API limits
    }
    
    if input_data.labels:
        params["labels"] = ",".join(input_data.labels)
    
    if input_data.since:
        params["since"] = input_data.since
    
    endpoint = f"/repos/{input_data.owner}/{input_data.repo}/issues"
    result = await github_request("GET", endpoint, params=params)
    
    if "error" in result:
        return f"Error listing issues: {result['error']}"
    
    if not result:
        return f"No issues found matching the criteria in {input_data.owner}/{input_data.repo}."
    
    response = [f"Issues for {input_data.owner}/{input_data.repo} (state: {input_data.state}, page: {input_data.page}):"]
    
    for issue in result:
        if not isinstance(issue, dict):
            response.append(f"\n## Issue: {issue}")
            continue
            
        response.append(f"\n## #{issue.get('number', 'Unknown')} - {issue.get('title', 'Untitled')}")
        response.append(f"State: {issue.get('state', 'Unknown')}")
        response.append(f"Created: {issue.get('created_at', 'Unknown')}")
        response.append(f"Updated: {issue.get('updated_at', 'Unknown')}")
        
        if issue.get('labels'):
            label_names = [label.get('name', 'Unknown') for label in issue.get('labels', [])]
            response.append(f"Labels: {', '.join(label_names)}")
        
        if issue.get('assignees'):
            assignee_names = [assignee.get('login', 'Unknown') for assignee in issue.get('assignees', [])]
            response.append(f"Assignees: {', '.join(assignee_names)}")
        
        response.append(f"URL: {issue.get('html_url', 'N/A')}")
    
    return "\n".join(response)

@mcp.tool()
async def create_pull_request(
    owner: str, 
    repo: str, 
    title: str, 
    head: str, 
    base: str, 
    body: str = "", 
    draft: bool = False,
    maintainer_can_modify: bool = True
) -> str:
    """Create a new pull request.
    
    Args:
        owner: Repository owner
        repo: Repository name
        title: PR title
        head: Branch containing changes
        base: Branch to merge into
        body: PR description
        draft: Create as draft PR
        maintainer_can_modify: Allow maintainer edits
    
    Returns:
        Pull request creation details
    """
    # Validate inputs with Pydantic
    input_data = CreatePullRequestInput(
        owner=owner,
        repo=repo,
        title=title,
        head=head,
        base=base,
        body=body,
        draft=draft,
        maintainer_can_modify=maintainer_can_modify
    )
    
    if not GITHUB_TOKEN:
        return "Error: GitHub token required to create pull requests."
    
    data = {
        "title": input_data.title,
        "head": input_data.head,
        "base": input_data.base,
        "body": input_data.body,
        "draft": input_data.draft,
        "maintainer_can_modify": input_data.maintainer_can_modify
    }
    
    endpoint = f"/repos/{input_data.owner}/{input_data.repo}/pulls"
    result = await github_request("POST", endpoint, data=data)
    
    if "error" in result:
        return f"Error creating pull request: {result['error']}"
    
    return f"""
Pull request created successfully!
Title: {result.get('title', input_data.title)}
Number: #{result.get('number', 'Unknown')}
URL: {result.get('html_url', 'N/A')}
Status: {result.get('state', 'Unknown')}
Draft: {'Yes' if result.get('draft', input_data.draft) else 'No'}
    """

@mcp.tool()
async def get_repository(owner: str, repo: str) -> str:
    """Get information about a GitHub repository.
    
    Args:
        owner: Repository owner (username or organization)
        repo: Repository name
    
    Returns:
        Formatted repository details
    """
    # Validate inputs with Pydantic
    input_data = GetRepositoryInput(owner=owner, repo=repo)
    
    endpoint = f"/repos/{input_data.owner}/{input_data.repo}"
    result = await github_request("GET", endpoint)
    
    if "error" in result:
        return f"Error getting repository information: {result['error']}"
    
    topics = result.get("topics", [])
    topics_str = ", ".join(topics) if topics else "None"
    
    return f"""
# Repository Information: {result.get('full_name', f'{input_data.owner}/{input_data.repo}')}

- Description: {result.get('description', 'No description')}
- URL: {result.get('html_url', 'N/A')}
- Homepage: {result.get('homepage', 'N/A')}
- Language: {result.get('language', 'Not specified')}
- Stars: {result.get('stargazers_count', 0)}
- Forks: {result.get('forks_count', 0)}
- Watchers: {result.get('watchers_count', 0)}
- Open Issues: {result.get('open_issues_count', 0)}
- License: {result.get('license', {}).get('name', 'Not specified') if result.get('license') else 'Not specified'}
- Private: {'Yes' if result.get('private', False) else 'No'}
- Created: {result.get('created_at', 'Unknown')}
- Updated: {result.get('updated_at', 'Unknown')}
- Default Branch: {result.get('default_branch', 'Unknown')}
- Topics: {topics_str}
    """

@mcp.tool()
async def fork_repository(owner: str, repo: str, organization: str = None) -> str:
    """Fork a repository to your account or specified organization.
    
    Args:
        owner: Repository owner
        repo: Repository name
        organization: Organization to fork to (optional)
    
    Returns:
        Forked repository details
    """
    # Validate inputs with Pydantic
    input_data = ForkRepositoryInput(owner=owner, repo=repo, organization=organization)
    
    if not GITHUB_TOKEN:
        return "Error: GitHub token required to fork repositories."
    
    endpoint = f"/repos/{input_data.owner}/{input_data.repo}/forks"
    data = {}
    
    if input_data.organization:
        data["organization"] = input_data.organization
    
    result = await github_request("POST", endpoint, data=data)
    
    if "error" in result:
        return f"Error forking repository: {result['error']}"
    
    return f"""
Repository forked successfully!
Name: {result.get('full_name', 'Unknown')}
URL: {result.get('html_url', 'N/A')}
Default Branch: {result.get('default_branch', 'Unknown')}
    """

@mcp.tool()
async def create_branch(
    owner: str, 
    repo: str, 
    branch: str, 
    from_branch: str = None
) -> str:
    """Create a new branch in a repository.
    
    Args:
        owner: Repository owner
        repo: Repository name
        branch: Name for new branch
        from_branch: Source branch (defaults to repo default)
    
    Returns:
        Branch creation confirmation
    """
    # Validate inputs with Pydantic
    input_data = CreateBranchInput(
        owner=owner,
        repo=repo,
        branch=branch,
        from_branch=from_branch
    )
    
    if not GITHUB_TOKEN:
        return "Error: GitHub token required to create branches."
    
    # First, get the source branch ref if not specified
    if not input_data.from_branch:
        repo_info = await github_request("GET", f"/repos/{input_data.owner}/{input_data.repo}")
        if "error" in repo_info:
            return f"Error getting repository information: {repo_info['error']}"
        from_branch = repo_info.get("default_branch", "main")
    else:
        from_branch = input_data.from_branch
    
    # Get the SHA of the source branch's HEAD
    ref_result = await github_request("GET", f"/repos/{input_data.owner}/{input_data.repo}/git/refs/heads/{from_branch}")
    
    if "error" in ref_result:
        return f"Error getting reference for source branch: {ref_result['error']}"
    
    sha = ref_result.get("object", {}).get("sha")
    if not sha:
        return f"Could not determine SHA for source branch '{from_branch}'"
    
    # Create the new branch
    data = {
        "ref": f"refs/heads/{input_data.branch}",
        "sha": sha
    }
    
    create_result = await github_request("POST", f"/repos/{input_data.owner}/{input_data.repo}/git/refs", data=data)
    
    if "error" in create_result:
        return f"Error creating branch: {create_result['error']}"
    
    return f"""
Branch created successfully!
Name: {input_data.branch}
Based on: {from_branch}
Repository: {input_data.owner}/{input_data.repo}
SHA: {sha[:7]}
    """

@mcp.tool()
async def search_code(
    q: str,
    sort: str = "indexed",
    order: str = "desc",
    per_page: int = 30,
    page: int = 1
) -> str:
    """Search for code across GitHub repositories.
    
    Args:
        q: Search query using GitHub code search syntax
        sort: Sort field ('indexed' only)
        order: Sort order ('asc' or 'desc')
        per_page: Results per page (max 100)
        page: Page number
    
    Returns:
        Formatted code search results
    """
    # Validate inputs with Pydantic
    input_data = SearchCodeInput(
        q=q,
        sort=sort,
        order=order,
        per_page=per_page,
        page=page
    )
    
    params = {
        "q": input_data.q,
        "sort": input_data.sort,
        "order": input_data.order,
        "per_page": min(input_data.per_page, 100),
        "page": input_data.page
    }
    
    result = await github_request("GET", "/search/code", params=params)
    
    if "error" in result:
        return f"Error searching code: {result['error']}"
    
    total_count = result.get("total_count", 0)
    items = result.get("items", [])
    
    if not items:
        return f"No code found matching '{input_data.q}'."
    
    response = [f"Found {total_count} code results matching '{input_data.q}'. Showing page {input_data.page}:"]
    
    for item in items:
        repo = item.get("repository", {})
        repo_name = repo.get("full_name", "Unknown")
        path = item.get("path", "Unknown file")
        name = item.get("name", "Unknown")
        
        response.append(f"\n## {repo_name} - {path}")
        response.append(f"File: {name}")
        response.append(f"URL: {item.get('html_url', 'N/A')}")
    
    return "\n".join(response)

# Server entry point
if __name__ == "__main__":
    mcp.run(transport='stdio')