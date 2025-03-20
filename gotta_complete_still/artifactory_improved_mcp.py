import os
import httpx
import json
from typing import Optional, Dict, List, Any, Union
import asyncio
import uuid
from pathlib import Path

# Environment variables or defaults
JFROG_URL = os.environ.get("JFROG_URL")
JFROG_ACCESS_TOKEN = os.environ.get("JFROG_ACCESS_TOKEN")

class JFrogClient:
    """JFrog Artifactory REST API client."""
    def __init__(self, base_url: str, access_token: str):
        self.base_url = base_url
        self.access_token = access_token
    
    async def request(
        self,
        method: str,
        endpoint: str,
        params: Optional[Dict[str, Any]] = None,
        data: Optional[Union[Dict[str, Any], str]] = None,
        files: Optional[Dict[str, Any]] = None,
        debug: bool = False,
    ) -> Dict[str, Any]:
        """Make a request to the JFrog Artifactory REST API."""
        # Ensure the base_url doesn't end with a slash and endpoint starts with one
        base = self.base_url.rstrip('/')
        path = endpoint if endpoint.startswith('/') else f'/{endpoint}'
        url = f"{base}{path}"
        
        headers = {
            "Authorization": f"Bearer {self.access_token}",
        }
        
        # Add Content-Type only for JSON data
        if data and not files and isinstance(data, (dict, str)):
            headers["Content-Type"] = "application/json"
        
        if debug:
            print(f"DEBUG: Making {method} request to {url}")
            print(f"DEBUG: Headers: {headers}")
            if params:
                print(f"DEBUG: Params: {params}")
            if data:
                print(f"DEBUG: Data: {data}")
            
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
                
                if debug:
                    print(f"DEBUG: Response status: {response.status_code}")
                    print(f"DEBUG: Response headers: {response.headers}")
                    content_preview = response.content[:200] if response.content else "Empty content"
                    print(f"DEBUG: Response content preview: {content_preview}")
                
                # For successful responses with content
                if 200 <= response.status_code < 300:
                    if not response.content:
                        return {"status": "success"}
                    
                    # Try to parse as JSON first
                    try:
                        return response.json()
                    except json.JSONDecodeError:
                        # Return text content as is
                        return {"content": response.text}
                
                # For error responses
                error_message = f"HTTP Status Error: {response.status_code}"
                try:
                    if "application/json" in response.headers.get("content-type", ""):
                        error_data = response.json()
                        error_message = f"{error_message} - {error_data.get('errors', ['Unknown error'])[0]}"
                    else:
                        error_message = f"{error_message} - {response.text[:200]}"
                except (json.JSONDecodeError, AttributeError, KeyError):
                    if response.text:
                        error_message = f"{error_message} - {response.text[:200]}"
                    
                # For 409 conflicts, return a specific error type to handle differently
                if response.status_code == 409:
                    return {"error": error_message, "error_type": "conflict", "status_code": 409}
                    
                return {"error": error_message, "status_code": response.status_code}
                
            except httpx.HTTPStatusError as e:
                return {"error": f"HTTP Status Error: {e.response.status_code} - {e.response.text[:200]}"}
            except httpx.RequestError as e:
                return {"error": f"Request Error: {str(e)}"}
            except Exception as e:
                return {"error": f"Unexpected Error: {str(e)}"}

# Function to get JFrog client
def get_jfrog_client(debug: bool = False) -> JFrogClient:
    """Get a JFrog client instance."""
    if not JFROG_URL:
        raise ValueError("JFROG_URL environment variable is not set")
    if not JFROG_ACCESS_TOKEN:
        raise ValueError("JFROG_ACCESS_TOKEN environment variable is not set")
    
    if debug:
        print(f"DEBUG: Using JFROG_URL: {JFROG_URL}")
        print(f"DEBUG: Using token: {JFROG_ACCESS_TOKEN[:5]}...{JFROG_ACCESS_TOKEN[-5:]}")
    
    return JFrogClient(JFROG_URL, JFROG_ACCESS_TOKEN)

# System Management Tools
async def get_system_health(debug: bool = False) -> str:
    """Check the health of the system."""
    jfrog_client = get_jfrog_client(debug)
    
    # Try different endpoints with and without the artifactory prefix
    endpoints = [
        "/artifactory/api/system/ping",
        "/artifactory/api/system/health",
        "/api/system/ping",
        "/api/system/health",
        "/api/v1/system/ping",
        "/artifactory/api/v1/system/ping"
    ]
    
    for endpoint in endpoints:
        if debug:
            print(f"DEBUG: Trying health check endpoint: {endpoint}")
        result = await jfrog_client.request("GET", endpoint, debug=debug)
        if "error" not in result:
            return f"System is healthy (endpoint: {endpoint})"
        
    # Try a simpler approach - just checking if we can create and delete a repo
    try:
        test_repo_key = f"health-test-{uuid.uuid4().hex[:8]}"
        if debug:
            print(f"DEBUG: Testing system health with repo creation: {test_repo_key}")
        
        create_result = await create_repository(test_repo_key, "local", "generic", debug=debug)
        if "Successfully created" in create_result:
            # Clean up
            if debug:
                print(f"DEBUG: Cleaning up test repository: {test_repo_key}")
            await delete_repository(test_repo_key, debug=debug)
            return "System is responsive (verified by repository creation test)"
    except Exception as e:
        if debug:
            print(f"DEBUG: Error during health check repo test: {str(e)}")
    
    return "Failed to verify system health: All health check methods failed"

async def get_version(debug: bool = False) -> str:
    """Retrieve Artifactory version information."""
    jfrog_client = get_jfrog_client(debug)
    
    # Try alternative endpoints for version info
    endpoints = [
        "/artifactory/api/system/version",
        "/api/system/version",
        "/artifactory/api/v1/system/version",
        "/api/v1/system/version"
    ]
    
    for endpoint in endpoints:
        if debug:
            print(f"DEBUG: Trying version endpoint: {endpoint}")
        result = await jfrog_client.request("GET", endpoint, debug=debug)
        if "error" not in result:
            return json.dumps(result, indent=2)
    
    # If simple version lookup isn't working, try a custom approach
    try:
        # Try to get server info through another endpoint
        if debug:
            print("DEBUG: Trying system info endpoint for version")
        info_result = await get_system_info(debug=debug)
        if "version" in info_result.lower():
            return info_result
    except Exception:
        pass
    
    return "Artifactory version information is not accessible"

async def get_system_info(debug: bool = False) -> str:
    """Retrieve general system information."""
    jfrog_client = get_jfrog_client(debug)
    
    # Try different endpoints
    endpoints = [
        "/artifactory/api/system/info",
        "/api/system/info",
        "/artifactory/api/system",
        "/api/system"
    ]
    
    for endpoint in endpoints:
        if debug:
            print(f"DEBUG: Trying system info endpoint: {endpoint}")
        result = await jfrog_client.request("GET", endpoint, debug=debug)
        if "error" not in result:
            return json.dumps(result, indent=2)
    
    # Try a more generic endpoint
    health_result = await get_system_health(debug=debug)
    if "System is" in health_result:
        return f"{health_result}. Detailed system info is not available."
    
    return "Failed to retrieve system information"

async def get_storage_info(debug: bool = False) -> str:
    """Retrieve storage information."""
    jfrog_client = get_jfrog_client(debug)
    
    # Try different endpoints
    endpoints = [
        "/artifactory/api/storageinfo",
        "/api/storageinfo",
        "/artifactory/api/storage/info",
        "/api/storage/info"
    ]
    
    for endpoint in endpoints:
        if debug:
            print(f"DEBUG: Trying storage info endpoint: {endpoint}")
        result = await jfrog_client.request("GET", endpoint, debug=debug)
        if "error" not in result:
            return json.dumps(result, indent=2)
    
    return "Failed to retrieve storage information"

# Repository Management Tools
async def create_repository(repo_key: str, repo_type: str, package_type: str, debug: bool = False) -> str:
    """Create a new repository with specified type and package type."""
    jfrog_client = get_jfrog_client(debug)
    
    # Check if repository already exists
    if debug:
        print(f"DEBUG: Checking if repository {repo_key} already exists")
    
    get_result = await get_repository(repo_key, debug=debug)
    if "error" not in get_result or ("error_type" in get_result and get_result.get("error_type") != "conflict"):
        return f"Repository {repo_key} already exists"
    
    data = {
        "key": repo_key,
        "rclass": repo_type,
        "packageType": package_type
    }
    
    endpoints = [
        f"/artifactory/api/repositories/{repo_key}",
        f"/api/repositories/{repo_key}"
    ]
    
    for endpoint in endpoints:
        if debug:
            print(f"DEBUG: Trying to create repository with endpoint: {endpoint}")
        result = await jfrog_client.request("PUT", endpoint, data=data, debug=debug)
        if "error" not in result:
            return f"Successfully created {repo_type} repository {repo_key} for {package_type} packages"
    
    return f"Failed to create repository: {result.get('error', 'Unknown error')}"

async def get_repository(repo_key: str, debug: bool = False) -> str:
    """Retrieve information about a specific repository."""
    jfrog_client = get_jfrog_client(debug)
    
    endpoints = [
        f"/artifactory/api/repositories/{repo_key}",
        f"/api/repositories/{repo_key}"
    ]
    
    for endpoint in endpoints:
        if debug:
            print(f"DEBUG: Trying to get repository info with endpoint: {endpoint}")
        result = await jfrog_client.request("GET", endpoint, debug=debug)
        if "error" not in result:
            return json.dumps(result, indent=2)
    
    return f"Failed to get repository info: {result.get('error', 'Unknown error')}"

async def list_repositories(repo_type: Optional[str] = None, debug: bool = False) -> str:
    """List all repositories, optionally filtered by type."""
    jfrog_client = get_jfrog_client(debug)
    
    params = {}
    if repo_type:
        params["type"] = repo_type
    
    endpoints = [
        "/artifactory/api/repositories",
        "/api/repositories"
    ]
    
    for endpoint in endpoints:
        if debug:
            print(f"DEBUG: Trying to list repositories with endpoint: {endpoint}")
        result = await jfrog_client.request("GET", endpoint, params=params, debug=debug)
        if "error" not in result:
            return json.dumps(result, indent=2)
    
    # Try an alternative approach - list storage info which might include repos
    if debug:
        print("DEBUG: Trying to get repositories through storage info")
    try:
        storage_info = await get_storage_info(debug=debug)
        if "error" not in storage_info and "repositories" in storage_info:
            return storage_info
    except Exception:
        pass
    
    return f"Failed to list repositories: {result.get('error', 'Unknown error')}"

async def delete_repository(repo_key: str, debug: bool = False) -> str:
    """Delete a specified repository."""
    jfrog_client = get_jfrog_client(debug)
    
    endpoints = [
        f"/artifactory/api/repositories/{repo_key}",
        f"/api/repositories/{repo_key}"
    ]
    
    for endpoint in endpoints:
        if debug:
            print(f"DEBUG: Trying to delete repository with endpoint: {endpoint}")
        result = await jfrog_client.request("DELETE", endpoint, debug=debug)
        if "error" not in result:
            return f"Successfully deleted repository {repo_key}"
        
    # Check if the repo is already gone (404)
    if "status_code" in result and result["status_code"] == 404:
        return f"Repository {repo_key} does not exist or was already deleted"
    
    return f"Failed to delete repository: {result.get('error', 'Unknown error')}"

# User Management Tools
async def create_user(username: str, email: str, password: str, admin: bool = False, debug: bool = False) -> str:
    """Create a new user with specified details."""
    jfrog_client = get_jfrog_client(debug)
    
    # First check if user already exists
    user_exists = await get_user(username, check_only=True, debug=debug)
    if user_exists:
        return f"User {username} already exists"
    
    data = {
        "name": username,
        "email": email,
        "password": password,
        "admin": admin
    }
    
    endpoints = [
        f"/artifactory/api/security/users/{username}",
        f"/api/security/users/{username}"
    ]
    
    for endpoint in endpoints:
        if debug:
            print(f"DEBUG: Trying to create user with endpoint: {endpoint}")
        result = await jfrog_client.request("PUT", endpoint, data=data, debug=debug)
        if "error" not in result:
            return f"Successfully created user {username}"
    
    return f"Failed to create user: {result.get('error', 'Unknown error')}"

async def get_user(username: str, check_only: bool = False, debug: bool = False) -> Union[str, bool]:
    """Retrieve information about a specific user."""
    jfrog_client = get_jfrog_client(debug)
    
    endpoints = [
        f"/artifactory/api/security/users/{username}",
        f"/api/security/users/{username}"
    ]
    
    for endpoint in endpoints:
        if debug:
            print(f"DEBUG: Trying to get user info with endpoint: {endpoint}")
        result = await jfrog_client.request("GET", endpoint, debug=debug)
        if "error" not in result:
            return True if check_only else json.dumps(result, indent=2)
    
    return False if check_only else f"Failed to get user info: {result.get('error', 'Unknown error')}"

async def update_user(
    username: str, email: Optional[str] = None, 
    password: Optional[str] = None, admin: Optional[bool] = None,
    debug: bool = False
) -> str:
    """Update an existing user's details."""
    jfrog_client = get_jfrog_client(debug)
    
    # Check if user exists
    user_exists = await get_user(username, check_only=True, debug=debug)
    if not user_exists:
        return f"User {username} does not exist"
    
    # Prepare minimal data for update
    data = {"name": username}
    if email is not None:
        data["email"] = email
    if password is not None:
        data["password"] = password
    if admin is not None:
        data["admin"] = admin
    
    endpoints = [
        f"/artifactory/api/security/users/{username}",
        f"/api/security/users/{username}"
    ]
    
    for endpoint in endpoints:
        if debug:
            print(f"DEBUG: Trying to update user with endpoint: {endpoint}")
        result = await jfrog_client.request("POST", endpoint, data=data, debug=debug)
        if "error" not in result:
            return f"Successfully updated user {username}"
    
    return f"Failed to update user: {result.get('error', 'Unknown error')}"

async def delete_user(username: str, debug: bool = False) -> str:
    """Delete a specified user."""
    jfrog_client = get_jfrog_client(debug)
    
    endpoints = [
        f"/artifactory/api/security/users/{username}",
        f"/api/security/users/{username}"
    ]
    
    for endpoint in endpoints:
        if debug:
            print(f"DEBUG: Trying to delete user with endpoint: {endpoint}")
        result = await jfrog_client.request("DELETE", endpoint, debug=debug)
        if "error" not in result:
            return f"Successfully deleted user {username}"
        
    # Check if user doesn't exist (404)
    if "status_code" in result and result["status_code"] == 404:
        return f"User {username} does not exist or was already deleted"
    
    return f"Failed to delete user: {result.get('error', 'Unknown error')}"

# Artifact Management Tools
async def deploy_artifact(repo_key: str, item_path: str, file_path: str, debug: bool = False) -> str:
    """Deploy an artifact to a specified repository."""
    jfrog_client = get_jfrog_client(debug)
    
    try:
        with open(file_path, "rb") as f:
            files = {"file": (os.path.basename(file_path), f)}
            
            endpoints = [
                f"/artifactory/{repo_key}/{item_path}",
                f"/{repo_key}/{item_path}"
            ]
            
            for endpoint in endpoints:
                if debug:
                    print(f"DEBUG: Trying to deploy artifact with endpoint: {endpoint}")
                result = await jfrog_client.request("PUT", endpoint, files=files, debug=debug)
                if "error" not in result:
                    return f"Successfully deployed artifact to {repo_key}/{item_path}"
            
        return f"Failed to deploy artifact: {result.get('error', 'Unknown error')}"
    except FileNotFoundError:
        return f"Error: File {file_path} not found"
    except Exception as e:
        return f"Error deploying artifact: {str(e)}"

async def get_artifact_info(repo_key: str, item_path: str, debug: bool = False) -> str:
    """Retrieve information about a specific artifact."""
    jfrog_client = get_jfrog_client(debug)
    
    endpoints = [
        f"/artifactory/api/storage/{repo_key}/{item_path}",
        f"/api/storage/{repo_key}/{item_path}"
    ]
    
    for endpoint in endpoints:
        if debug:
            print(f"DEBUG: Trying to get artifact info with endpoint: {endpoint}")
        result = await jfrog_client.request("GET", endpoint, debug=debug)
        if "error" not in result:
            return json.dumps(result, indent=2)
    
    return f"Failed to get artifact info: {result.get('error', 'Unknown error')}"

async def delete_artifact(repo_key: str, item_path: str, debug: bool = False) -> str:
    """Delete an artifact from a repository."""
    jfrog_client = get_jfrog_client(debug)
    
    endpoints = [
        f"/artifactory/{repo_key}/{item_path}",
        f"/{repo_key}/{item_path}"
    ]
    
    for endpoint in endpoints:
        if debug:
            print(f"DEBUG: Trying to delete artifact with endpoint: {endpoint}")
        result = await jfrog_client.request("DELETE", endpoint, debug=debug)
        if "error" not in result:
            return f"Successfully deleted artifact {repo_key}/{item_path}"
    
    # Check if artifact doesn't exist (404)
    if "status_code" in result and result["status_code"] == 404:
        return f"Artifact {repo_key}/{item_path} does not exist or was already deleted"
    
    return f"Failed to delete artifact: {result.get('error', 'Unknown error')}"

async def search_artifacts(name: Optional[str] = None, repos: Optional[str] = None, 
                           properties: Optional[str] = None, debug: bool = False) -> str:
    """Search for artifacts based on name, repository, or properties."""
    jfrog_client = get_jfrog_client(debug)
    
    params = {}
    if name:
        params["name"] = name
    if repos:
        params["repos"] = repos
    if properties:
        params["properties"] = properties
    
    endpoints = [
        "/artifactory/api/search/artifact",
        "/api/search/artifact"
    ]
    
    for endpoint in endpoints:
        if debug:
            print(f"DEBUG: Trying to search artifacts with endpoint: {endpoint}")
        result = await jfrog_client.request("GET", endpoint, params=params, debug=debug)
        if "error" not in result:
            return json.dumps(result, indent=2)
    
    # Try AQL search as fallback
    if debug:
        print("DEBUG: Trying AQL search as fallback")
    aql_query = "items.find("
    query_parts = []
    if repos:
        query_parts.append(f'"repo":"{repos}"')
    if name:
        query_parts.append(f'"name":"{name}"')
    
    aql_query += "{" + ",".join(query_parts) + "})"
    
    try:
        aql_result = await advanced_search(aql_query, debug=debug)
        if "error" not in aql_result:
            return aql_result
    except Exception:
        pass
    
    return f"Failed to search artifacts: {result.get('error', 'Unknown error')}"

async def advanced_search(query: str, debug: bool = False) -> str:
    """Utilize Artifactory Query Language (AQL) for complex searches."""
    jfrog_client = get_jfrog_client(debug)
    
    endpoints = [
        "/artifactory/api/search/aql",
        "/api/search/aql"
    ]
    
    for endpoint in endpoints:
        if debug:
            print(f"DEBUG: Trying AQL search with endpoint: {endpoint}")
        result = await jfrog_client.request("POST", endpoint, data=query, debug=debug)
        if "error" not in result:
            return json.dumps(result, indent=2)
    
    return f"Failed to execute AQL search: {result.get('error', 'Unknown error')}"

# Other Tools - keeping the same since they appear to work
async def integrate_build(build_name: str, build_number: str, debug: bool = False) -> str:
    """Integrate with build tools to capture build metadata."""
    jfrog_client = get_jfrog_client(debug)
    
    data = {
        "buildName": build_name,
        "buildNumber": build_number
    }
    
    endpoints = [
        "/artifactory/api/build",
        "/api/build"
    ]
    
    for endpoint in endpoints:
        if debug:
            print(f"DEBUG: Trying to integrate build with endpoint: {endpoint}")
        result = await jfrog_client.request("POST", endpoint, data=data, debug=debug)
        if "error" not in result:
            return f"Successfully integrated build {build_name} #{build_number}"
    
    return f"Failed to integrate build: {result.get('error', 'Unknown error')}"

async def create_webhook(name: str, url: str, events: List[str], debug: bool = False) -> str:
    """Manage webhooks for real-time notifications on system events."""
    jfrog_client = get_jfrog_client(debug)
    
    data = {
        "name": name,
        "url": url,
        "events": events
    }
    
    endpoints = [
        "/artifactory/api/webhooks",
        "/api/webhooks"
    ]
    
    for endpoint in endpoints:
        if debug:
            print(f"DEBUG: Trying to create webhook with endpoint: {endpoint}")
        result = await jfrog_client.request("POST", endpoint, data=data, debug=debug)
        if "error" not in result:
            return f"Successfully created webhook {name}"
    
    return f"Failed to create webhook: {result.get('error', 'Unknown error')}"

async def manage_permissions(name: str, repositories: List[str], principals: List[str], debug: bool = False) -> str:
    """Manage roles and permissions for fine-grained access control."""
    jfrog_client = get_jfrog_client(debug)
    
    data = {
        "name": name,
        "repositories": repositories,
        "principals": principals
    }
    
    endpoints = [
        "/artifactory/api/security/permissions",
        "/api/security/permissions"
    ]
    
    for endpoint in endpoints:
        if debug:
            print(f"DEBUG: Trying to manage permissions with endpoint: {endpoint}")
        result = await jfrog_client.request("POST", endpoint, data=data, debug=debug)
        if "error" not in result:
            return f"Successfully set up permissions {name}"
    
    return f"Failed to manage permissions: {result.get('error', 'Unknown error')}"

# Test function
async def run_tests(debug: bool = False):
    """Run tests for all MCP tools with improved debugging."""
    print("Starting JFrog Artifactory MCP tests with improved client...")
    
    # Generate unique identifiers for test resources
    test_id = str(uuid.uuid4())[:8]
    test_repo_key = f"test-repo-{test_id}"
    test_user = f"test-user-{test_id}"
    
    # Create a temporary test file
    temp_file = Path("test_artifact.txt")
    temp_file.write_text("This is a test artifact for JFrog Artifactory MCP testing.")
    
    try:
        print("\n--- Testing System Information Tools ---")
        
        print("Testing get_system_health...")
        result = await get_system_health(debug=debug)
        print(f"  Result: {result}")
        
        print("Testing get_version...")
        result = await get_version(debug=debug)
        print(f"  Result: {result}")
        
        print("Testing get_storage_info...")
        result = await get_storage_info(debug=debug)
        print(f"  Result: {result}")
        
        print("Testing get_system_info...")
        result = await get_system_info(debug=debug)
        result_preview = result[:100] + "..." if len(result) > 100 else result
        print(f"  Result: {result_preview}")
        
        print("\n--- Testing Repository Management Tools ---")
        
        print("Testing list_repositories...")
        result = await list_repositories(debug=debug)
        result_preview = result[:100] + "..." if len(result) > 100 else result
        print(f"  Result: {result_preview}")
        
        print(f"Testing create_repository ({test_repo_key})...")
        result = await create_repository(test_repo_key, "local", "generic", debug=debug)
        print(f"  Result: {result}")
        
        print(f"Testing get_repository ({test_repo_key})...")
        result = await get_repository(test_repo_key, debug=debug)
        print(f"  Result: {result}")
        
        print("\n--- Testing Artifact Management Tools ---")
        
        artifact_path = f"test-artifact-{uuid.uuid4()}.txt"
        
        print(f"Testing deploy_artifact to {test_repo_key}/{artifact_path}...")
        result = await deploy_artifact(test_repo_key, artifact_path, str(temp_file), debug=debug)
        print(f"  Result: {result}")
        
        print(f"Testing get_artifact_info for {test_repo_key}/{artifact_path}...")
        result = await get_artifact_info(test_repo_key, artifact_path, debug=debug)
        print(f"  Result: {result}")
        
        print(f"Testing search_artifacts...")
        result = await search_artifacts(name="*.txt", repos=test_repo_key, debug=debug)
        result_preview = result[:100] + "..." if len(result) > 100 else result
        print(f"  Result: {result_preview}")
        
        print(f"Testing delete_artifact for {test_repo_key}/{artifact_path}...")
        result = await delete_artifact(test_repo_key, artifact_path, debug=debug)
        print(f"  Result: {result}")
        
        print("\n--- Testing User Management Tools ---")
        
        test_email = f"{test_user}@example.com"
        test_password = "Password123!"
        
        print(f"Testing create_user ({test_user})...")
        result = await create_user(test_user, test_email, test_password, admin=False, debug=debug)
        print(f"  Result: {result}")
        
        print(f"Testing get_user ({test_user})...")
        result = await get_user(test_user, debug=debug)
        print(f"  Result: {result}")
        
        print(f"Testing update_user ({test_user})...")
        result = await update_user(test_user, email=f"updated-{test_email}", debug=debug)
        print(f"  Result: {result}")
        
        print("Testing list_users...")
        result = await list_users(debug=debug)
        result_preview = result[:100] + "..." if len(result) > 100 else result
        print(f"  Result: {result_preview}")
        
        print("\n--- Testing Search Tools ---")
        
        print("Testing advanced_search with AQL...")
        aql_query = f'items.find({{"repo":"{test_repo_key}","type":"file"}})'
        result = await advanced_search(aql_query, debug=debug)
        result_preview = result[:100] + "..." if len(result) > 100 else result
        print(f"  Result: {result_preview}")
        
        print("\n--- Testing Other MCP Tools ---")
        
        # Test build integration
        build_name = f"test-build-{uuid.uuid4()}"
        build_number = "1.0.0"
        
        print(f"Testing integrate_build ({build_name})...")
        result = await integrate_build(build_name, build_number, debug=debug)
        print(f"  Result: {result}")
        
        # Test webhook creation
        webhook_name = f"test-webhook-{uuid.uuid4()}"
        
        print(f"Testing create_webhook ({webhook_name})...")
        result = await create_webhook(
            webhook_name, 
            "https://example.com/webhook", 
            ["artifact.create", "artifact.delete"],
            debug=debug
        )
        print(f"  Result: {result}")
        
        # Test permission management
        permission_name = f"test-permission-{uuid.uuid4()}"
        
        print(f"Testing manage_permissions ({permission_name})...")
        result = await manage_permissions(
            permission_name,
            [test_repo_key],
            ["users/admin"],
            debug=debug
        )
        print(f"  Result: {result}")
        
        print("\nAll tests completed! 🎉")
        
    except Exception as e:
        print(f"\n❌ Tests failed: {str(e)}")
        
    finally:
        # Cleanup resources
        print("\nCleaning up test resources...")
        try:
            await delete_repository(test_repo_key, debug=debug)
            await delete_user(test_user, debug=debug)
            temp_file.unlink(missing_ok=True)
        except Exception as e:
            print(f"Cleanup error: {str(e)}")

# Function to list users (which was missing in the first part)
async def list_users(debug: bool = False) -> str:
    """List all users."""
    jfrog_client = get_jfrog_client(debug)
    
    endpoints = [
        "/artifactory/api/security/users",
        "/api/security/users"
    ]
    
    for endpoint in endpoints:
        if debug:
            print(f"DEBUG: Trying to list users with endpoint: {endpoint}")
        result = await jfrog_client.request("GET", endpoint, debug=debug)
        if "error" not in result:
            return json.dumps(result, indent=2)
    
    return f"Failed to list users: {result.get('error', 'Unknown error')}"

# Main execution
if __name__ == "__main__":
    import argparse
    
    parser = argparse.ArgumentParser(description="JFrog Artifactory MCP Test Runner")
    parser.add_argument("--debug", action="store_true", help="Enable debug output")
    args = parser.parse_args()
    
    asyncio.run(run_tests(debug=args.debug))