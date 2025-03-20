import os
import httpx
import json
from typing import Optional, Dict, List, Any, Union
from dataclasses import dataclass
from mcp.server.fastmcp import FastMCP
import uuid
from dotenv import load_dotenv
load_dotenv()

# Environment variables or defaults
JFROG_URL = os.environ.get("JFROG_URL", "")
JFROG_ACCESS_TOKEN = os.environ.get("JFROG_ACCESS_TOKEN", "")

# Initialize the MCP server
mcp = FastMCP("JFrog Artifactory")

@dataclass
class JFrogClient:
    """JFrog Artifactory REST API client."""
    base_url: str
    access_token: str
    
    async def request(
        self,
        method: str,
        endpoint: str,
        params: Optional[Dict[str, Any]] = None,
        data: Optional[Union[Dict[str, Any], str]] = None,
        files: Optional[Dict[str, Any]] = None,
    ) -> Dict[str, Any]:
        """Make a request to the JFrog Artifactory REST API."""
        # Ensure the base_url doesn't end with a slash and endpoint starts with one
        base = self.base_url.rstrip('/')
        path = endpoint if endpoint.startswith('/') else f'/{endpoint}'
        url = f"{base}{path}"
        
        # Single authentication method that worked before
        headers = {
            "Authorization": f"Bearer {self.access_token}",
        }
        
        # Add Content-Type only for JSON data
        if data and not files:
            headers["Content-Type"] = "application/json"
            
        async with httpx.AsyncClient(follow_redirects=True) as client:
            try:
                if isinstance(data, dict):
                    data = json.dumps(data)
                
                response = await client.request(
                    method=method,
                    url=url,
                    headers=headers,
                    params=params,
                    content=data,
                    files=files,
                    timeout=30.0,
                )
                response.raise_for_status()
                
                # Return empty dict for successful operations with no content
                if not response.content:
                    return {"status": "success"}
                
                try:
                    return response.json()
                except json.JSONDecodeError:
                    return {"content": response.text}
                    
            except httpx.HTTPStatusError as e:
                error_message = f"HTTP Status Error: {e.response.status_code}"
                try:
                    error_data = e.response.json()
                    error_message = f"{error_message} - {error_data.get('errors', ['Unknown error'])[0]}"
                except (json.JSONDecodeError, AttributeError, KeyError):
                    if e.response.text:
                        error_message = f"{error_message} - {e.response.text[:200]}"
                
                return {"error": error_message}
            except httpx.RequestError as e:
                return {"error": f"Request Error: {str(e)}"}
            except Exception as e:
                return {"error": f"Unexpected Error: {str(e)}"}

# Function to get JFrog client
def get_jfrog_client() -> JFrogClient:
    """Get a JFrog client instance."""
    if not JFROG_URL:
        raise ValueError("JFROG_URL environment variable is not set")
    if not JFROG_ACCESS_TOKEN:
        raise ValueError("JFROG_ACCESS_TOKEN environment variable is not set")
    
    return JFrogClient(JFROG_URL, JFROG_ACCESS_TOKEN)

# Artifact Management Tools
@mcp.tool()
async def deploy_artifact(repo_key: str, item_path: str, file_path: str) -> str:
    """Deploy an artifact to a specified repository.
    
    Args:
        repo_key: The repository key
        item_path: The path within the repository
        file_path: The local path to the file to upload
    """
    jfrog_client = get_jfrog_client()
    
    try:
        with open(file_path, "rb") as f:
            files = {"file": (os.path.basename(file_path), f)}
            endpoint = f"/artifactory/{repo_key}/{item_path}"
            result = await jfrog_client.request("PUT", endpoint, files=files)
            
        if "error" in result:
            return f"Failed to deploy artifact: {result['error']}"
        return f"Successfully deployed artifact to {repo_key}/{item_path}"
    except FileNotFoundError:
        return f"Error: File {file_path} not found"
    except Exception as e:
        return f"Error deploying artifact: {str(e)}"

@mcp.tool()
async def get_artifact_info(repo_key: str, item_path: str) -> str:
    """Retrieve information about a specific artifact.
    
    Args:
        repo_key: The repository key
        item_path: The path within the repository
    """
    jfrog_client = get_jfrog_client()
    
    endpoint = f"/artifactory/api/storage/{repo_key}/{item_path}"
    result = await jfrog_client.request("GET", endpoint)
    
    if "error" in result:
        return f"Failed to get artifact info: {result['error']}"
    
    return json.dumps(result, indent=2)

@mcp.tool()
async def delete_artifact(repo_key: str, item_path: str) -> str:
    """Delete an artifact from a repository.
    
    Args:
        repo_key: The repository key
        item_path: The path within the repository
    """
    jfrog_client = get_jfrog_client()
    
    endpoint = f"/artifactory/{repo_key}/{item_path}"
    result = await jfrog_client.request("DELETE", endpoint)
    
    if "error" in result:
        return f"Failed to delete artifact: {result['error']}"
    
    return f"Successfully deleted artifact {repo_key}/{item_path}"

@mcp.tool()
async def search_artifacts(name: Optional[str] = None, repos: Optional[str] = None, 
                          properties: Optional[str] = None) -> str:
    """Search for artifacts based on name, repository, or properties.
    
    Args:
        name: The name pattern to search for
        repos: The repositories to search in, comma-separated
        properties: The properties to filter by, format: "key1=value1;key2=value2"
    """
    jfrog_client = get_jfrog_client()
    
    params = {}
    if name:
        params["name"] = name
    if repos:
        params["repos"] = repos
    if properties:
        params["properties"] = properties
    
    endpoint = "/artifactory/api/search/artifact"
    result = await jfrog_client.request("GET", endpoint, params=params)
    
    if "error" in result:
        return f"Failed to search artifacts: {result['error']}"
    
    return json.dumps(result, indent=2)

@mcp.tool()
async def advanced_search(query: str) -> str:
    """Utilize Artifactory Query Language (AQL) for complex searches.
    
    Args:
        query: AQL query (e.g., 'items.find({"repo": "my-repo"})')
    """
    jfrog_client = get_jfrog_client()
    
    endpoint = "/artifactory/api/search/aql"
    result = await jfrog_client.request("POST", endpoint, data=query)
    
    if "error" in result:
        return f"Failed to execute AQL search: {result['error']}"
    
    return json.dumps(result, indent=2)

# Repository Management Tools
@mcp.tool()
async def create_repository(repo_key: str, repo_type: str, package_type: str) -> str:
    """Create a new repository with specified type and package type.
    
    Args:
        repo_key: The repository key
        repo_type: Repository class (local, remote, virtual, federated)
        package_type: Package type (maven, npm, docker, etc.)
    """
    jfrog_client = get_jfrog_client()
    
    data = {
        "key": repo_key,
        "rclass": repo_type,
        "packageType": package_type
    }
    
    endpoint = f"/artifactory/api/repositories/{repo_key}"
    result = await jfrog_client.request("PUT", endpoint, data=data)
    
    if "error" in result:
        return f"Failed to create repository: {result['error']}"
    
    return f"Successfully created {repo_type} repository {repo_key} for {package_type} packages"

@mcp.tool()
async def get_repository(repo_key: str) -> str:
    """Retrieve information about a specific repository.
    
    Args:
        repo_key: The repository key
    """
    jfrog_client = get_jfrog_client()
    
    endpoint = f"/artifactory/api/repositories/{repo_key}"
    result = await jfrog_client.request("GET", endpoint)
    
    if "error" in result:
        return f"Failed to get repository info: {result['error']}"
    
    return json.dumps(result, indent=2)

@mcp.tool()
async def list_repositories(repo_type: Optional[str] = None) -> str:
    """List all repositories, optionally filtered by type.
    
    Args:
        repo_type: Optional repository type filter (local, remote, virtual, federated)
    """
    jfrog_client = get_jfrog_client()
    
    params = {}
    if repo_type:
        params["type"] = repo_type
    
    endpoint = "/artifactory/api/repositories"
    result = await jfrog_client.request("GET", endpoint, params=params)
    
    if "error" in result:
        return f"Failed to list repositories: {result['error']}"
    
    return json.dumps(result, indent=2)

@mcp.tool()
async def delete_repository(repo_key: str) -> str:
    """Delete a specified repository.
    
    Args:
        repo_key: The repository key
    """
    jfrog_client = get_jfrog_client()
    
    endpoint = f"/artifactory/api/repositories/{repo_key}"
    result = await jfrog_client.request("DELETE", endpoint)
    
    if "error" in result:
        return f"Failed to delete repository: {result['error']}"
    
    return f"Successfully deleted repository {repo_key}"

@mcp.tool()
async def create_federated_repository(repo_key: str, package_type: str) -> str:
    """Manage federated repositories for distributed environments.
    
    Args:
        repo_key: The repository key
        package_type: Package type (maven, npm, docker, etc.)
    """
    jfrog_client = get_jfrog_client()
    
    data = {
        "key": repo_key,
        "rclass": "federated",
        "packageType": package_type
    }
    
    endpoint = f"/artifactory/api/repositories/{repo_key}"
    result = await jfrog_client.request("PUT", endpoint, data=data)
    
    if "error" in result:
        return f"Failed to create federated repository: {result['error']}"
    
    return f"Successfully created federated repository {repo_key} for {package_type} packages"

@mcp.tool()
async def setup_repository_replication(
    repo_key: str, target_url: str, username: str, password: str
) -> str:
    """Manage replication between repositories for redundancy.
    
    Args:
        repo_key: The source repository key
        target_url: The target repository URL
        username: Username for authentication
        password: Password for authentication
    """
    jfrog_client = get_jfrog_client()
    
    data = {
        "url": target_url,
        "username": username,
        "password": password
    }
    
    endpoint = f"/artifactory/api/replications/{repo_key}"
    result = await jfrog_client.request("POST", endpoint, data=data)
    
    if "error" in result:
        return f"Failed to setup repository replication: {result['error']}"
    
    return f"Successfully set up replication for repository {repo_key}"

# User Management Tools
@mcp.tool()
async def create_user(username: str, email: str, password: str, admin: bool = False) -> str:
    """Create a new user with specified details.
    
    Args:
        username: The username
        email: User's email address
        password: User's password
        admin: Whether the user should have admin privileges
    """
    jfrog_client = get_jfrog_client()
    
    data = {
        "name": username,
        "email": email,
        "password": password,
        "admin": admin
    }
    
    endpoint = f"/artifactory/api/security/users/{username}"
    result = await jfrog_client.request("PUT", endpoint, data=data)
    
    if "error" in result:
        return f"Failed to create user: {result['error']}"
    
    return f"Successfully created user {username}"

@mcp.tool()
async def get_user(username: str) -> str:
    """Retrieve information about a specific user.
    
    Args:
        username: The username
    """
    jfrog_client = get_jfrog_client()
    
    endpoint = f"/artifactory/api/security/users/{username}"
    result = await jfrog_client.request("GET", endpoint)
    
    if "error" in result:
        return f"Failed to get user info: {result['error']}"
    
    return json.dumps(result, indent=2)

@mcp.tool()
async def list_users() -> str:
    """List all users."""
    jfrog_client = get_jfrog_client()
    
    endpoint = "/artifactory/api/security/users"
    result = await jfrog_client.request("GET", endpoint)
    
    if "error" in result:
        return f"Failed to list users: {result['error']}"
    
    return json.dumps(result, indent=2)

@mcp.tool()
async def update_user(
    username: str, email: Optional[str] = None, 
    password: Optional[str] = None, admin: Optional[bool] = None
) -> str:
    """Update an existing user's details.
    
    Args:
        username: The username
        email: New email address (optional)
        password: New password (optional)
        admin: New admin status (optional)
    """
    jfrog_client = get_jfrog_client()
    
    # First get current user info to retain unchanged values
    endpoint = f"/artifactory/api/security/users/{username}"
    current_user = await jfrog_client.request("GET", endpoint)
    
    if "error" in current_user:
        return f"Failed to get current user info: {current_user['error']}"
    
    # Update with new values
    data = {
        "name": username,
        "email": email if email is not None else current_user.get("email", ""),
        "admin": admin if admin is not None else current_user.get("admin", False)
    }
    
    # Only include password if updating it
    if password is not None:
        data["password"] = password
    
    result = await jfrog_client.request("POST", endpoint, data=data)
    
    if "error" in result:
        return f"Failed to update user: {result['error']}"
    
    return f"Successfully updated user {username}"

@mcp.tool()
async def delete_user(username: str) -> str:
    """Delete a specified user.
    
    Args:
        username: The username
    """
    jfrog_client = get_jfrog_client()
    
    endpoint = f"/artifactory/api/security/users/{username}"
    result = await jfrog_client.request("DELETE", endpoint)
    
    if "error" in result:
        return f"Failed to delete user: {result['error']}"
    
    return f"Successfully deleted user {username}"

# System Management Tools
@mcp.tool()
async def get_system_info() -> str:
    """Retrieve general system information."""
    jfrog_client = get_jfrog_client()
    
    # Try a different API endpoint format
    endpoint = "/api/system"  # Try without the /artifactory prefix
    result = await jfrog_client.request("GET", endpoint)
    
    if "error" in result:
        # Try a simpler endpoint
        endpoint = "/artifactory/api/system/ping"
        ping_result = await jfrog_client.request("GET", endpoint)
        if "error" not in ping_result:
            return "System is responsive, but detailed system info is not available."
        return f"Failed to get system info: {result['error']}"
    
    return json.dumps(result, indent=2)

@mcp.tool()
async def get_system_health() -> str:
    """Check the health of the system."""
    jfrog_client = get_jfrog_client()
    
    # Try alternative endpoints for health check
    endpoints = [
        "/artifactory/api/system/ping",
        "/api/system/ping",  # without /artifactory prefix
        "/artifactory/api/v1/system/ping",
        "/api/v1/system/ping"
    ]
    
    for endpoint in endpoints:
        result = await jfrog_client.request("GET", endpoint)
        if "error" not in result:
            return "System is healthy"
        
    # If all endpoints failed, return the error
    return f"Failed to check system health: All health check endpoints failed"


@mcp.tool()
async def get_system_configuration() -> str:
    """Retrieve system configuration (requires admin privileges)."""
    jfrog_client = get_jfrog_client()
    
    endpoint = "/artifactory/api/system/configuration"
    result = await jfrog_client.request("GET", endpoint)
    
    if "error" in result:
        return f"Failed to get system configuration: {result['error']}"
    
    return json.dumps(result, indent=2)

@mcp.tool()
async def get_storage_info() -> str:
    """Retrieve storage information."""
    jfrog_client = get_jfrog_client()
    
    endpoint = "/artifactory/api/storageinfo"
    result = await jfrog_client.request("GET", endpoint)
    
    if "error" in result:
        return f"Failed to get storage info: {result['error']}"
    
    return json.dumps(result, indent=2)

@mcp.tool()
async def get_version() -> str:
    """Retrieve Artifactory version information."""
    jfrog_client = get_jfrog_client()
    
    # Try alternative endpoints for version info
    endpoints = [
        "/artifactory/api/system/version",
        "/api/system/version",
        "/artifactory/api/v1/system/version"
    ]
    
    for endpoint in endpoints:
        result = await jfrog_client.request("GET", endpoint)
        if "error" not in result:
            return json.dumps(result, indent=2)
    
    # If simple version lookup isn't working, try a custom approach
    try:
        # Create a simple repository to test that the system is responsive
        test_repo_key = f"version-test-{uuid.uuid4().hex[:8]}"
        create_result = await create_repository(test_repo_key, "local", "generic")
        if "Successfully created" in create_result:
            # Clean up
            await delete_repository(test_repo_key)
            return "Artifactory is operational, but version info is not accessible"
    except Exception:
        pass
    
    return "Failed to get version info: All version endpoints failed"

# Build Integration Tool
@mcp.tool()
async def integrate_build(build_name: str, build_number: str) -> str:
    """Integrate with build tools like Maven or Gradle to capture build metadata.
    
    Args:
        build_name: The name of the build
        build_number: The build number
    """
    jfrog_client = get_jfrog_client()
    
    data = {
        "buildName": build_name,
        "buildNumber": build_number
    }
    
    endpoint = "/artifactory/api/build"
    result = await jfrog_client.request("POST", endpoint, data=data)
    
    if "error" in result:
        return f"Failed to integrate build: {result['error']}"
    
    return f"Successfully integrated build {build_name} #{build_number}"

# Webhook Management
@mcp.tool()
async def create_webhook(
    name: str, url: str, events: List[str]
) -> str:
    """Manage webhooks for real-time notifications on system events.
    
    Args:
        name: The webhook name
        url: The URL to notify
        events: List of event types to trigger the webhook
    """
    jfrog_client = get_jfrog_client()
    
    data = {
        "name": name,
        "url": url,
        "events": events
    }
    
    endpoint = "/artifactory/api/webhooks"
    result = await jfrog_client.request("POST", endpoint, data=data)
    
    if "error" in result:
        return f"Failed to create webhook: {result['error']}"
    
    return f"Successfully created webhook {name}"

# Access Control
@mcp.tool()
async def manage_permissions(
    name: str, repositories: List[str], principals: List[str]
) -> str:
    """Manage roles and permissions for fine-grained access control.
    
    Args:
        name: The permission name
        repositories: List of repository keys
        principals: List of principal names
    """
    jfrog_client = get_jfrog_client()
    
    data = {
        "name": name,
        "repositories": repositories,
        "principals": principals
    }
    
    endpoint = "/artifactory/api/security/permissions"
    result = await jfrog_client.request("POST", endpoint, data=data)
    
    if "error" in result:
        return f"Failed to manage permissions: {result['error']}"
    
    return f"Successfully set up permissions {name}"

# Main execution
if __name__ == "__main__":
    mcp.run(transport="stdio")