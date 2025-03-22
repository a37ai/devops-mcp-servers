from typing import Any, Dict, List, Optional
import os
import json
import httpx
from mcp.server.fastmcp import FastMCP, Context
from dotenv import load_dotenv
load_dotenv()

# Initialize the MCP server
mcp = FastMCP("GitHub")

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
    data: Dict[str, Any] = None, 
    params: Dict[str, Any] = None
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
    params = {
        "q": query,
        "page": page,
        "per_page": min(perPage, 100)  # Enforcing GitHub API limits
    }
    
    result = await github_request("GET", "/search/repositories", params=params)
    
    if "error" in result:
        return f"Error searching repositories: {result['error']}"
    
    total_count = result.get("total_count", 0)
    items = result.get("items", [])
    
    if not items:
        return f"No repositories found matching '{query}'."
    
    response = [f"Found {total_count} repositories matching '{query}'. Showing page {page}:"]
    
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
    if not GITHUB_TOKEN:
        return "Error: GitHub token required to create repositories."
    
    data = {
        "name": name,
        "description": description,
        "private": private,
        "auto_init": autoInit
    }
    
    result = await github_request("POST", "/user/repos", data=data)
    
    if "error" in result:
        return f"Error creating repository: {result['error']}"
    
    return f"""
Repository created successfully!
Name: {result.get('full_name', name)}
URL: {result.get('html_url', 'N/A')}
Description: {result.get('description', description)}
Private: {result.get('private', private)}
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
    endpoint = f"/repos/{owner}/{repo}/contents/{path}"
    params = {}
    if branch:
        params["ref"] = branch
    
    result = await github_request("GET", endpoint, params=params)
    
    if "error" in result:
        return f"Error getting file contents: {result['error']}"
    
    # If result is a list, it's a directory
    if isinstance(result, list):
        response = [f"Directory listing for `{path}` in {owner}/{repo}:"]
        for item in result:
            item_type = "📁 " if item.get("type") == "dir" else "📄 "
            response.append(f"{item_type}{item.get('name', 'Unknown')} - {item.get('size', 0)} bytes")
        return "\n".join(response)
    
    # It's a file
    content = result.get("content", "")
    encoding = result.get("encoding", "")
    
    if encoding == "base64":
        import base64
        try:
            decoded_content = base64.b64decode(content).decode('utf-8')
            return f"Contents of `{path}` in {owner}/{repo}:\n\n```\n{decoded_content}\n```"
        except:
            return f"Could not decode content of `{path}`. It may be a binary file."
    
    return f"Contents of `{path}` in {owner}/{repo} (not in base64 format):\n{content}"

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
    if not GITHUB_TOKEN:
        return "Error: GitHub token required to modify files."
    
    import base64
    encoded_content = base64.b64encode(content.encode()).decode()
    
    data = {
        "message": message,
        "content": encoded_content,
        "branch": branch
    }
    
    if sha:
        data["sha"] = sha
    
    endpoint = f"/repos/{owner}/{repo}/contents/{path}"
    result = await github_request("PUT", endpoint, data=data)
    
    if "error" in result:
        return f"Error creating/updating file: {result['error']}"
    
    action = "updated" if sha else "created"
    
    commit = result.get("commit", {})
    commit_url = commit.get("html_url", "Unknown")
    
    return f"""
File {action} successfully!
Path: {path}
Repository: {owner}/{repo}
Branch: {branch}
Commit message: {message}
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
    if not GITHUB_TOKEN:
        return "Error: GitHub token required to create issues."
    
    data = {
        "title": title,
        "body": body
    }
    
    if assignees:
        data["assignees"] = assignees
    
    if labels:
        data["labels"] = labels
    
    if milestone:
        data["milestone"] = milestone
    
    endpoint = f"/repos/{owner}/{repo}/issues"
    result = await github_request("POST", endpoint, data=data)
    
    if "error" in result:
        return f"Error creating issue: {result['error']}"
    
    return f"""
Issue created successfully!
Title: {result.get('title', title)}
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
    params = {
        "state": state,
        "sort": sort,
        "direction": direction,
        "page": page,
        "per_page": min(per_page, 100)  # Enforce GitHub API limits
    }
    
    if labels:
        params["labels"] = ",".join(labels)
    
    if since:
        params["since"] = since
    
    endpoint = f"/repos/{owner}/{repo}/issues"
    result = await github_request("GET", endpoint, params=params)
    
    if "error" in result:
        return f"Error listing issues: {result['error']}"
    
    if not result:
        return f"No issues found matching the criteria in {owner}/{repo}."
    
    response = [f"Issues for {owner}/{repo} (state: {state}, page: {page}):"]
    
    for issue in result:
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
        body: PR description
        head: Branch containing changes
        base: Branch to merge into
        draft: Create as draft PR
        maintainer_can_modify: Allow maintainer edits
    
    Returns:
        Pull request creation details
    """
    if not GITHUB_TOKEN:
        return "Error: GitHub token required to create pull requests."
    
    data = {
        "title": title,
        "head": head,
        "base": base,
        "body": body,
        "draft": draft,
        "maintainer_can_modify": maintainer_can_modify
    }
    
    endpoint = f"/repos/{owner}/{repo}/pulls"
    result = await github_request("POST", endpoint, data=data)
    
    if "error" in result:
        return f"Error creating pull request: {result['error']}"
    
    return f"""
Pull request created successfully!
Title: {result.get('title', title)}
Number: #{result.get('number', 'Unknown')}
URL: {result.get('html_url', 'N/A')}
Status: {result.get('state', 'Unknown')}
Draft: {'Yes' if result.get('draft', draft) else 'No'}
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
    endpoint = f"/repos/{owner}/{repo}"
    result = await github_request("GET", endpoint)
    
    if "error" in result:
        return f"Error getting repository information: {result['error']}"
    
    topics = result.get("topics", [])
    topics_str = ", ".join(topics) if topics else "None"
    
    return f"""
# Repository Information: {result.get('full_name', f'{owner}/{repo}')}

- Description: {result.get('description', 'No description')}
- URL: {result.get('html_url', 'N/A')}
- Homepage: {result.get('homepage', 'N/A')}
- Language: {result.get('language', 'Not specified')}
- Stars: {result.get('stargazers_count', 0)}
- Forks: {result.get('forks_count', 0)}
- Watchers: {result.get('watchers_count', 0)}
- Open Issues: {result.get('open_issues_count', 0)}
- License: {result.get('license', {}).get('name', 'Not specified')}
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
    if not GITHUB_TOKEN:
        return "Error: GitHub token required to fork repositories."
    
    endpoint = f"/repos/{owner}/{repo}/forks"
    data = {}
    
    if organization:
        data["organization"] = organization
    
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
    if not GITHUB_TOKEN:
        return "Error: GitHub token required to create branches."
    
    # First, get the source branch ref if not specified
    if not from_branch:
        repo_info = await github_request("GET", f"/repos/{owner}/{repo}")
        if "error" in repo_info:
            return f"Error getting repository information: {repo_info['error']}"
        from_branch = repo_info.get("default_branch", "main")
    
    # Get the SHA of the source branch's HEAD
    ref_result = await github_request("GET", f"/repos/{owner}/{repo}/git/refs/heads/{from_branch}")
    
    if "error" in ref_result:
        return f"Error getting reference for source branch: {ref_result['error']}"
    
    sha = ref_result.get("object", {}).get("sha")
    if not sha:
        return f"Could not determine SHA for source branch '{from_branch}'"
    
    # Create the new branch
    data = {
        "ref": f"refs/heads/{branch}",
        "sha": sha
    }
    
    create_result = await github_request("POST", f"/repos/{owner}/{repo}/git/refs", data=data)
    
    if "error" in create_result:
        return f"Error creating branch: {create_result['error']}"
    
    return f"""
Branch created successfully!
Name: {branch}
Based on: {from_branch}
Repository: {owner}/{repo}
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
    params = {
        "q": q,
        "sort": sort,
        "order": order,
        "per_page": min(per_page, 100),
        "page": page
    }
    
    result = await github_request("GET", "/search/code", params=params)
    
    if "error" in result:
        return f"Error searching code: {result['error']}"
    
    total_count = result.get("total_count", 0)
    items = result.get("items", [])
    
    if not items:
        return f"No code found matching '{q}'."
    
    response = [f"Found {total_count} code results matching '{q}'. Showing page {page}:"]
    
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