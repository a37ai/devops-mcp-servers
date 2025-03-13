import os
import json
import httpx
from typing import Dict, List, Optional, Any, Union
from mcp.server.fastmcp import FastMCP

# Initialize MCP server
mcp = FastMCP("nexus-api")

# Configuration
NEXUS_URL = os.environ.get("NEXUS_URL", "http://localhost:8081")
NEXUS_USERNAME = os.environ.get("NEXUS_USERNAME", "admin")
NEXUS_PASSWORD = os.environ.get("NEXUS_PASSWORD", "admin123")

# Base URL for API calls
BASE_API_URL = f"{NEXUS_URL}/service/rest/v1"

# Create a client session with authentication
async def get_client_session():
    """Create an authenticated HTTP client session."""
    return httpx.AsyncClient(
        auth=(NEXUS_USERNAME, NEXUS_PASSWORD),
        headers={"Content-Type": "application/json"}
    )

# Helper functions
async def make_request(method: str, endpoint: str, data: Optional[Dict] = None) -> Dict:
    """Make a request to the Nexus API with proper error handling."""
    url = f"{BASE_API_URL}/{endpoint}"
    async with await get_client_session() as client:
        try:
            if method == "GET":
                response = await client.get(url)
            elif method == "POST":
                response = await client.post(url, json=data)
            elif method == "PUT":
                response = await client.put(url, json=data)
            elif method == "DELETE":
                response = await client.delete(url)
            else:
                return {"error": f"Unsupported method: {method}"}
            
            response.raise_for_status()
            
            if response.status_code == 204:  # No content
                return {"message": "Operation successful"}
            
            try:
                return response.json()
            except:
                return {"message": f"Operation successful. Status code: {response.status_code}"}
                
        except httpx.HTTPStatusError as e:
            try:
                error_content = e.response.json()
                return {"error": f"HTTP Error {e.response.status_code}: {error_content}"}
            except:
                return {"error": f"HTTP Error {e.response.status_code}: {e.response.text}"}
        except Exception as e:
            return {"error": f"Error: {str(e)}"}

# ========== 1. Repository Management Endpoints ==========

@mcp.tool()
async def get_all_repositories() -> str:
    """
    Retrieves a list of all repositories in Nexus.
    
    Returns:
        A JSON string containing repository details.
    """
    result = await make_request("GET", "repositories")
    return json.dumps(result, indent=2)

@mcp.tool()
async def create_repository(repository_type: str, repository_format: str, repository_name: str, blob_store_name: str, online: bool = True, write_policy: str = "ALLOW") -> str:
    """
    Creates a new repository in Nexus.
    
    Args:
        repository_type: The type of repository (hosted, proxy, or group)
        repository_format: Format of the repository (maven2, npm, docker, etc.)
        repository_name: Name for the new repository
        blob_store_name: Name of the blob store to use
        online: Whether the repository should be online (default: True)
        write_policy: Write policy for hosted repositories (ALLOW, ALLOW_ONCE, DENY) - default: ALLOW
        
    Returns:
        A JSON string with the result of the operation.
    """
    # This is a simplified payload - actual payload varies by repository type and format
    data = {
        "name": repository_name,
        "online": online,
        "storage": {
            "blobStoreName": blob_store_name,
            "strictContentTypeValidation": True,
            "writePolicy": write_policy
        }
    }
    
    endpoint = f"repositories/{repository_format}/{repository_type}"
    result = await make_request("POST", endpoint, data)
    return json.dumps(result, indent=2)

@mcp.tool()
async def update_repository(repository_name: str, repository_type: str, repository_format: str, repository_data: str) -> str:
    """
    Updates an existing repository with new configuration.
    
    Args:
        repository_name: Name of the repository to update
        repository_type: Type of the repository (hosted, proxy, or group)
        repository_format: Format of the repository (maven2, npm, docker, etc.)
        repository_data: JSON string containing the updated repository configuration
        
    Returns:
        A JSON string with the result of the operation.
    """
    try:
        data = json.loads(repository_data)
        endpoint = f"repositories/{repository_format}/{repository_type}/{repository_name}"
        result = await make_request("PUT", endpoint, data)
        return json.dumps(result, indent=2)
    except json.JSONDecodeError:
        return json.dumps({"error": "Invalid JSON format for repository_data"}, indent=2)

@mcp.tool()
async def delete_repository(repository_name: str) -> str:
    """
    Deletes a repository.
    
    Args:
        repository_name: Name of the repository to delete
        
    Returns:
        A JSON string with the result of the operation.
    """
    endpoint = f"repositories/{repository_name}"
    result = await make_request("DELETE", endpoint)
    return json.dumps(result, indent=2)

# ========== 2. User and Role Management Endpoints ==========

@mcp.tool()
async def get_all_users() -> str:
    """
    Retrieves a list of all users.
    
    Returns:
        A JSON string containing user details.
    """
    result = await make_request("GET", "users")
    return json.dumps(result, indent=2)

@mcp.tool()
async def create_user(user_id: str, first_name: str, last_name: str, email: str, password: str, status: str = "active", roles: Optional[List[str]] = None) -> str:
    """
    Creates a new user in Nexus.
    
    Args:
        user_id: Unique identifier for the user
        first_name: User's first name
        last_name: User's last name
        email: User's email address
        password: User's password
        status: User status (active or disabled) - default: active
        roles: List of role IDs to assign to the user
        
    Returns:
        A JSON string with the result of the operation.
    """
    data = {
        "userId": user_id,
        "firstName": first_name,
        "lastName": last_name,
        "emailAddress": email,
        "password": password,
        "status": status,
        "roles": roles or []
    }
    
    result = await make_request("POST", "users", data)
    return json.dumps(result, indent=2)

@mcp.tool()
async def update_user(user_id: str, first_name: str, last_name: str, email: str, status: str = "active", roles: Optional[List[str]] = None) -> str:
    """
    Updates an existing user in Nexus.
    
    Args:
        user_id: ID of the user to update
        first_name: User's first name
        last_name: User's last name
        email: User's email address
        status: User status (active or disabled) - default: active
        roles: List of role IDs to assign to the user
        
    Returns:
        A JSON string with the result of the operation.
    """
    data = {
        "userId": user_id,
        "firstName": first_name,
        "lastName": last_name,
        "emailAddress": email,
        "status": status,
        "roles": roles or []
    }
    
    result = await make_request("PUT", f"users/{user_id}", data)
    return json.dumps(result, indent=2)

@mcp.tool()
async def delete_user(user_id: str) -> str:
    """
    Deletes a user from Nexus.
    
    Args:
        user_id: ID of the user to delete
        
    Returns:
        A JSON string with the result of the operation.
    """
    result = await make_request("DELETE", f"users/{user_id}")
    return json.dumps(result, indent=2)

@mcp.tool()
async def list_roles() -> str:
    """
    Lists all roles defined in Nexus.
    
    Returns:
        A JSON string containing role details.
    """
    result = await make_request("GET", "roles")
    return json.dumps(result, indent=2)

@mcp.tool()
async def create_role(role_id: str, name: str, description: str, privileges: List[str], roles: Optional[List[str]] = None) -> str:
    """
    Creates a new role in Nexus.
    
    Args:
        role_id: Unique identifier for the role
        name: Display name for the role
        description: Description of the role
        privileges: List of privilege IDs to assign to the role
        roles: List of nested role IDs
        
    Returns:
        A JSON string with the result of the operation.
    """
    data = {
        "id": role_id,
        "name": name,
        "description": description,
        "privileges": privileges,
        "roles": roles or []
    }
    
    result = await make_request("POST", "roles", data)
    return json.dumps(result, indent=2)

# ========== 3. Content Management Endpoints ==========

@mcp.tool()
async def search_components(repository: Optional[str] = None, keyword: Optional[str] = None, format: Optional[str] = None) -> str:
    """
    Searches for components or assets in Nexus repositories.
    
    Args:
        repository: Optional repository name to search in
        keyword: Optional keyword to search for
        format: Optional format to filter by (maven2, npm, etc.)
        
    Returns:
        A JSON string containing search results.
    """
    # Build query parameters
    params = []
    if repository:
        params.append(f"repository={repository}")
    if keyword:
        params.append(f"keyword={keyword}")
    if format:
        params.append(f"format={format}")
    
    endpoint = f"search/assets/download" + (f"?{'&'.join(params)}" if params else "")
    result = await make_request("GET", endpoint)
    return json.dumps(result, indent=2)

@mcp.tool()
async def upload_component(repository: str, component_format: str, component_data: str) -> str:
    """
    Uploads a new component to a Nexus repository.
    
    Args:
        repository: Name of the repository to upload to
        component_format: Format of the component (maven2, npm, etc.)
        component_data: JSON string containing the component details
        
    Returns:
        A JSON string with the result of the operation.
    """
    try:
        data = json.loads(component_data)
        endpoint = f"components?repository={repository}"
        result = await make_request("POST", endpoint, data)
        return json.dumps(result, indent=2)
    except json.JSONDecodeError:
        return json.dumps({"error": "Invalid JSON format for component_data"}, indent=2)

# ========== 4. LDAP and External Authentication Endpoints ==========

@mcp.tool()
async def list_ldap_servers() -> str:
    """
    Lists all LDAP servers configured in Nexus.
    
    Returns:
        A JSON string containing LDAP server details.
    """
    result = await make_request("GET", "ldap/servers")
    return json.dumps(result, indent=2)

@mcp.tool()
async def create_ldap_server(
    name: str, 
    protocol: str, 
    host: str, 
    port: int, 
    search_base: str,
    authentication_scheme: str = "simple",
    connection_timeout_seconds: int = 30,
    retry_delay_seconds: int = 300,
    max_incidents: int = 3
) -> str:
    """
    Creates a new LDAP server configuration in Nexus.
    
    Args:
        name: Unique name for the LDAP server
        protocol: Protocol to use (ldap or ldaps)
        host: LDAP server hostname
        port: LDAP server port
        search_base: LDAP search base
        authentication_scheme: Authentication scheme (simple, etc.)
        connection_timeout_seconds: Connection timeout in seconds
        retry_delay_seconds: Retry delay in seconds
        max_incidents: Maximum number of connection incidents
        
    Returns:
        A JSON string with the result of the operation.
    """
    data = {
        "name": name,
        "protocol": protocol,
        "host": host,
        "port": port,
        "searchBase": search_base,
        "authScheme": authentication_scheme,
        "connectionTimeoutSeconds": connection_timeout_seconds,
        "retryDelaySeconds": retry_delay_seconds,
        "maxIncidents": max_incidents
    }
    
    result = await make_request("POST", "ldap/servers", data)
    return json.dumps(result, indent=2)

@mcp.tool()
async def delete_ldap_server(server_id: str) -> str:
    """
    Deletes an LDAP server configuration from Nexus.
    
    Args:
        server_id: ID of the LDAP server to delete
        
    Returns:
        A JSON string with the result of the operation.
    """
    result = await make_request("DELETE", f"ldap/servers/{server_id}")
    return json.dumps(result, indent=2)

# ========== 5. Content Selectors Endpoints ==========

@mcp.tool()
async def list_content_selectors() -> str:
    """
    Lists all content selectors configured in Nexus.
    
    Returns:
        A JSON string containing content selector details.
    """
    result = await make_request("GET", "content-selectors")
    return json.dumps(result, indent=2)

@mcp.tool()
async def create_content_selector(name: str, description: str, expression: str) -> str:
    """
    Creates a new content selector in Nexus.
    
    Args:
        name: Unique name for the content selector
        description: Description of the content selector
        expression: CSEL expression for the content selector
        
    Returns:
        A JSON string with the result of the operation.
    """
    data = {
        "name": name,
        "description": description,
        "expression": expression
    }
    
    result = await make_request("POST", "content-selectors", data)
    return json.dumps(result, indent=2)

# ========== 6. Privileges Management Endpoints ==========

@mcp.tool()
async def list_privileges() -> str:
    """
    Lists all privileges configured in Nexus.
    
    Returns:
        A JSON string containing privilege details.
    """
    result = await make_request("GET", "privileges")
    return json.dumps(result, indent=2)

@mcp.tool()
async def create_privilege(name: str, description: str, privilege_type: str, privilege_properties: str) -> str:
    """
    Creates a new privilege in Nexus.
    
    Args:
        name: Unique name for the privilege
        description: Description of the privilege
        privilege_type: Type of privilege (e.g., repository-view, application, etc.)
        privilege_properties: JSON string containing privilege-specific properties
        
    Returns:
        A JSON string with the result of the operation.
    """
    try:
        properties = json.loads(privilege_properties)
        data = {
            "name": name,
            "description": description,
            "type": privilege_type,
            "properties": properties
        }
        
        result = await make_request("POST", "privileges", data)
        return json.dumps(result, indent=2)
    except json.JSONDecodeError:
        return json.dumps({"error": "Invalid JSON format for privilege_properties"}, indent=2)

# ========== 7. Repository Firewall Configuration Endpoints ==========

@mcp.tool()
async def get_firewall_config() -> str:
    """
    Retrieves the Repository Firewall configuration from Nexus.
    
    Returns:
        A JSON string containing firewall configuration details.
    """
    result = await make_request("GET", "iq")
    return json.dumps(result, indent=2)

@mcp.tool()
async def update_firewall_config(enabled: bool, url: str, authentication_type: str, username: Optional[str] = None, password: Optional[str] = None) -> str:
    """
    Updates the Repository Firewall configuration in Nexus.
    
    Args:
        enabled: Whether the firewall is enabled
        url: URL of the IQ server
        authentication_type: Type of authentication (USER or TOKEN)
        username: Username for authentication (when using USER type)
        password: Password for authentication
        
    Returns:
        A JSON string with the result of the operation.
    """
    data = {
        "enabled": enabled,
        "url": url,
        "authenticationType": authentication_type
    }
    
    if username:
        data["username"] = username
    if password:
        data["password"] = password
    
    result = await make_request("PUT", "iq", data)
    return json.dumps(result, indent=2)

# ========== 8. IQ Server Features Endpoints ==========

@mcp.tool()
async def update_sbom_scanning(enabled: bool) -> str:
    """
    Enables or disables SBOM binary scanning in Nexus.
    
    Args:
        enabled: Whether to enable SBOM binary scanning
        
    Returns:
        A JSON string with the result of the operation.
    """
    data = {
        "enabled": enabled
    }
    
    result = await make_request("PUT", "features/sbomBinaryScanning", data)
    return json.dumps(result, indent=2)

# ========== 9. Webhooks and Automation Endpoints ==========

@mcp.tool()
async def list_webhooks() -> str:
    """
    Lists all webhooks configured in Nexus.
    
    Returns:
        A JSON string containing webhook details.
    """
    result = await make_request("GET", "webhooks")
    return json.dumps(result, indent=2)

@mcp.tool()
async def create_webhook(name: str, url: str, webhook_type: str, secret: Optional[str] = None, webhook_config: Optional[str] = None) -> str:
    """
    Creates a new webhook in Nexus.
    
    Args:
        name: Unique name for the webhook
        url: URL to send webhook notifications to
        webhook_type: Type of webhook event to listen for
        secret: Optional secret for webhook authentication
        webhook_config: Optional JSON string containing additional webhook configuration
        
    Returns:
        A JSON string with the result of the operation.
    """
    data = {
        "name": name,
        "url": url,
        "eventTypes": [webhook_type]
    }
    
    if secret:
        data["secret"] = secret
    
    if webhook_config:
        try:
            config = json.loads(webhook_config)
            data.update(config)
        except json.JSONDecodeError:
            return json.dumps({"error": "Invalid JSON format for webhook_config"}, indent=2)
    
    result = await make_request("POST", "webhooks", data)
    return json.dumps(result, indent=2)

# Run the server
if __name__ == "__main__":
    mcp.run()