#!/usr/bin/env python
"""
JFrog Artifactory MCP Server

This server exposes JFrog Artifactory REST API functionality as MCP tools,
allowing LLMs to interact with Artifactory for artifact, repository, and user management.
"""

import os
import json
import base64
import httpx
from typing import Optional, Dict, Any, List, Union
from dataclasses import dataclass
from contextlib import asynccontextmanager
from mcp.server.fastmcp import FastMCP, Context

# Initialize FastMCP server
mcp = FastMCP("JFrog Artifactory")

@dataclass
class ArtifactoryClient:
    """Class for handling JFrog Artifactory API requests"""
    base_url: str
    api_key: Optional[str] = None
    username: Optional[str] = None
    password: Optional[str] = None
    access_token: Optional[str] = None

    async def request(
        self, 
        method: str, 
        path: str, 
        json_data: Optional[Dict[str, Any]] = None, 
        params: Optional[Dict[str, Any]] = None,
        files: Optional[Dict[str, Any]] = None,
        binary_data: Optional[bytes] = None,
        content_type: Optional[str] = None
    ) -> Dict[str, Any]:
        """Make a request to the Artifactory API with appropriate authentication"""
        url = f"{self.base_url.rstrip('/')}/{path.lstrip('/')}"
        headers = {}
        
        # Add authentication
        if self.api_key:
            headers["X-JFrog-Art-Api"] = self.api_key
        elif self.access_token:
            headers["Authorization"] = f"Bearer {self.access_token}"
        elif self.username and self.password:
            auth_str = f"{self.username}:{self.password}"
            encoded_auth = base64.b64encode(auth_str.encode()).decode()
            headers["Authorization"] = f"Basic {encoded_auth}"
            
        if content_type:
            headers["Content-Type"] = content_type
            
        async with httpx.AsyncClient() as client:
            if method.upper() == "GET":
                response = await client.get(url, headers=headers, params=params)
            elif method.upper() == "POST":
                if files:
                    response = await client.post(url, headers=headers, data=json_data, files=files)
                elif binary_data:
                    response = await client.post(url, headers=headers, content=binary_data)
                else:
                    response = await client.post(url, headers=headers, json=json_data)
            elif method.upper() == "PUT":
                if binary_data:
                    response = await client.put(url, headers=headers, content=binary_data)
                else:
                    response = await client.put(url, headers=headers, json=json_data)
            elif method.upper() == "DELETE":
                response = await client.delete(url, headers=headers)
            else:
                raise ValueError(f"Unsupported HTTP method: {method}")
                
            response.raise_for_status()
            
            if response.headers.get("content-type", "").startswith("application/json"):
                return response.json()
            else:
                return {"status": "success", "status_code": response.status_code, "text": response.text}

@asynccontextmanager
async def artifactory_lifespan(server: FastMCP):
    """Initialize and manage JFrog Artifactory connection"""
    # Get connection details from environment variables
    base_url = os.environ.get("JFROG_URL")
    api_key = os.environ.get("JFROG_API_KEY")
    username = os.environ.get("JFROG_USERNAME")
    password = os.environ.get("JFROG_PASSWORD")
    access_token = os.environ.get("JFROG_ACCESS_TOKEN")
    
    if not base_url:
        raise ValueError("JFROG_URL environment variable must be set")
    
    # Create Artifactory client
    client = ArtifactoryClient(
        base_url=base_url,
        api_key=api_key,
        username=username,
        password=password,
        access_token=access_token
    )
    
    try:
        # Test connection
        server.log_info("Initializing JFrog Artifactory client...")
        try:
            await client.request("GET", "/artifactory/api/system/ping")
            server.log_info("Successfully connected to JFrog Artifactory")
        except Exception as e:
            server.log_error(f"Failed to connect to JFrog Artifactory: {str(e)}")
            # Continue anyway as credentials might be provided in tool calls
            
        yield {"client": client}
    finally:
        server.log_info("Shutting down JFrog Artifactory client...")

# Set lifespan handler
mcp.set_lifespan(artifactory_lifespan)

#
# Artifact Management Tools
#

@mcp.tool()
async def deploy_artifact(repo_key: str, item_path: str, artifact_content: str, content_type: str = "application/octet-stream", ctx: Context = None) -> str:
    """
    Deploy an artifact to a repository.
    
    Args:
        repo_key: The repository key.
        item_path: The path to the artifact in the repository.
        artifact_content: The artifact content encoded as base64 string.
        content_type: The content type of the artifact (default: application/octet-stream).
    
    Returns:
        A success message or error details.
    """
    client = ctx.request_context.lifespan_context["client"]
    path = f"/artifactory/{repo_key}/{item_path}"
    
    try:
        # Decode base64 content
        try:
            binary_data = base64.b64decode(artifact_content)
        except Exception as e:
            return f"Error decoding artifact content: {str(e)}. Make sure content is base64 encoded."
        
        result = await client.request("PUT", path, binary_data=binary_data, content_type=content_type)
        return f"Successfully deployed artifact to {repo_key}/{item_path}"
    except Exception as e:
        return f"Error deploying artifact: {str(e)}"

@mcp.tool()
async def get_artifact_info(repo_key: str, item_path: str, ctx: Context = None) -> str:
    """
    Get information about an artifact.
    
    Args:
        repo_key: The repository key.
        item_path: The path to the artifact in the repository.
    
    Returns:
        The artifact information as JSON string.
    """
    client = ctx.request_context.lifespan_context["client"]
    path = f"/artifactory/api/storage/{repo_key}/{item_path}"
    
    try:
        result = await client.request("GET", path)
        return json.dumps(result, indent=2)
    except Exception as e:
        return f"Error getting artifact info: {str(e)}"

@mcp.tool()
async def delete_artifact(repo_key: str, item_path: str, ctx: Context = None) -> str:
    """
    Delete an artifact from a repository.
    
    Args:
        repo_key: The repository key.
        item_path: The path to the artifact in the repository.
    
    Returns:
        A success message or error details.
    """
    client = ctx.request_context.lifespan_context["client"]
    path = f"/artifactory/{repo_key}/{item_path}"
    
    try:
        result = await client.request("DELETE", path)
        return f"Successfully deleted artifact {repo_key}/{item_path}"
    except Exception as e:
        return f"Error deleting artifact: {str(e)}"

@mcp.tool()
async def search_artifacts(name: str = None, repo: str = None, properties: str = None, ctx: Context = None) -> str:
    """
    Search for artifacts based on various criteria.
    
    Args:
        name: Optional pattern to search artifact names.
        repo: Optional repository to limit search.
        properties: Optional properties to search for (format: "key1=value1;key2=value2").
    
    Returns:
        The search results as JSON string.
    """
    client = ctx.request_context.lifespan_context["client"]
    path = "/artifactory/api/search/artifact"
    params = {}
    
    if name:
        params["name"] = name
    if repo:
        params["repos"] = repo
    if properties:
        params["properties"] = properties
        
    try:
        result = await client.request("GET", path, params=params)
        return json.dumps(result, indent=2)
    except Exception as e:
        return f"Error searching artifacts: {str(e)}"

#
# Repository Management Tools
#

@mcp.tool()
async def create_repository(repo_key: str, repo_type: str, package_type: str, description: str = None, ctx: Context = None) -> str:
    """
    Create a new repository.
    
    Args:
        repo_key: The key of the repository.
        repo_type: The type of repository (local, remote, virtual, federated, distribution).
        package_type: The package type (e.g., maven, npm, docker, etc.).
        description: Optional description of the repository.
    
    Returns:
        A success message or error details.
    """
    client = ctx.request_context.lifespan_context["client"]
    path = "/artifactory/api/repositories"
    
    valid_repo_types = ["local", "remote", "virtual", "federated", "distribution"]
    if repo_type not in valid_repo_types:
        return f"Invalid repository type. Must be one of: {', '.join(valid_repo_types)}"
    
    data = {
        "key": repo_key,
        "rclass": repo_type,
        "packageType": package_type
    }
    
    if description:
        data["description"] = description
    
    try:
        result = await client.request("PUT", f"{path}/{repo_key}", json_data=data)
        return f"Successfully created {repo_type} repository '{repo_key}'"
    except Exception as e:
        return f"Error creating repository: {str(e)}"

@mcp.tool()
async def get_repository(repo_key: str, ctx: Context = None) -> str:
    """
    Get information about a repository.
    
    Args:
        repo_key: The key of the repository.
    
    Returns:
        The repository information as JSON string.
    """
    client = ctx.request_context.lifespan_context["client"]
    path = f"/artifactory/api/repositories/{repo_key}"
    
    try:
        result = await client.request("GET", path)
        return json.dumps(result, indent=2)
    except Exception as e:
        return f"Error getting repository information: {str(e)}"

@mcp.tool()
async def list_repositories(type: str = None, ctx: Context = None) -> str:
    """
    List repositories.
    
    Args:
        type: Optional repository type filter (local, remote, virtual, federated, distribution).
    
    Returns:
        The list of repositories as JSON string.
    """
    client = ctx.request_context.lifespan_context["client"]
    path = "/artifactory/api/repositories"
    params = {}
    
    if type:
        params["type"] = type
    
    try:
        result = await client.request("GET", path, params=params)
        return json.dumps(result, indent=2)
    except Exception as e:
        return f"Error listing repositories: {str(e)}"

@mcp.tool()
async def delete_repository(repo_key: str, ctx: Context = None) -> str:
    """
    Delete a repository.
    
    Args:
        repo_key: The key of the repository.
    
    Returns:
        A success message or error details.
    """
    client = ctx.request_context.lifespan_context["client"]
    path = f"/artifactory/api/repositories/{repo_key}"
    
    try:
        result = await client.request("DELETE", path)
        return f"Successfully deleted repository '{repo_key}'"
    except Exception as e:
        return f"Error deleting repository: {str(e)}"

#
# User Management Tools
#

@mcp.tool()
async def create_user(username: str, password: str, email: str, admin: bool = False, ctx: Context = None) -> str:
    """
    Create a new user.
    
    Args:
        username: The username of the new user.
        password: The password for the new user.
        email: The email address of the new user.
        admin: Whether the user should have admin privileges.
    
    Returns:
        A success message or error details.
    """
    client = ctx.request_context.lifespan_context["client"]
    path = "/artifactory/api/security/users"
    
    data = {
        "name": username,
        "password": password,
        "email": email,
        "admin": admin,
        "profileUpdatable": True,
        "disableUIAccess": False,
        "internalPasswordDisabled": False
    }
    
    try:
        result = await client.request("PUT", f"{path}/{username}", json_data=data)
        return f"Successfully created user '{username}'"
    except Exception as e:
        return f"Error creating user: {str(e)}"

@mcp.tool()
async def get_user(username: str, ctx: Context = None) -> str:
    """
    Get information about a user.
    
    Args:
        username: The username of the user.
    
    Returns:
        The user information as JSON string.
    """
    client = ctx.request_context.lifespan_context["client"]
    path = f"/artifactory/api/security/users/{username}"
    
    try:
        result = await client.request("GET", path)
        # Remove sensitive information
        if "password" in result:
            del result["password"]
        return json.dumps(result, indent=2)
    except Exception as e:
        return f"Error getting user information: {str(e)}"

@mcp.tool()
async def list_users(ctx: Context = None) -> str:
    """
    List all users.
    
    Returns:
        The list of users as JSON string.
    """
    client = ctx.request_context.lifespan_context["client"]
    path = "/artifactory/api/security/users"
    
    try:
        result = await client.request("GET", path)
        # Remove sensitive information
        for user in result:
            if "password" in user:
                del user["password"]
        return json.dumps(result, indent=2)
    except Exception as e:
        return f"Error listing users: {str(e)}"

@mcp.tool()
async def update_user(username: str, email: str = None, password: str = None, admin: bool = None, ctx: Context = None) -> str:
    """
    Update an existing user.
    
    Args:
        username: The username of the user.
        email: Optional new email address for the user.
        password: Optional new password for the user.
        admin: Optional admin status for the user.
    
    Returns:
        A success message or error details.
    """
    client = ctx.request_context.lifespan_context["client"]
    path = f"/artifactory/api/security/users/{username}"
    
    try:
        # First get current user data
        current_user = await client.request("GET", path)
        
        # Update fields if provided
        if email:
            current_user["email"] = email
        if password:
            current_user["password"] = password
        if admin is not None:
            current_user["admin"] = admin
            
        # Remove unnecessary fields
        if "lastLoggedIn" in current_user:
            del current_user["lastLoggedIn"]
        if "lastLoginClientIp" in current_user:
            del current_user["lastLoginClientIp"]
            
        result = await client.request("POST", path, json_data=current_user)
        return f"Successfully updated user '{username}'"
    except Exception as e:
        return f"Error updating user: {str(e)}"

@mcp.tool()
async def delete_user(username: str, ctx: Context = None) -> str:
    """
    Delete a user.
    
    Args:
        username: The username of the user.
    
    Returns:
        A success message or error details.
    """
    client = ctx.request_context.lifespan_context["client"]
    path = f"/artifactory/api/security/users/{username}"
    
    try:
        result = await client.request("DELETE", path)
        return f"Successfully deleted user '{username}'"
    except Exception as e:
        return f"Error deleting user: {str(e)}"

#
# Authentication and Access Token Tools
#

@mcp.tool()
async def generate_api_key(ctx: Context = None) -> str:
    """
    Generate an API key for the current user.
    
    Returns:
        The generated API key or error details.
    """
    client = ctx.request_context.lifespan_context["client"]
    path = "/artifactory/api/security/apiKey"
    
    try:
        result = await client.request("POST", path)
        return json.dumps(result, indent=2)
    except Exception as e:
        return f"Error generating API key: {str(e)}"

@mcp.tool()
async def regenerate_api_key(ctx: Context = None) -> str:
    """
    Regenerate an API key for the current user.
    
    Returns:
        The regenerated API key or error details.
    """
    client = ctx.request_context.lifespan_context["client"]
    path = "/artifactory/api/security/apiKey"
    
    try:
        # First delete the existing key
        try:
            await client.request("DELETE", path)
        except Exception:
            pass  # Ignore if no key exists
            
        # Generate a new key
        result = await client.request("POST", path)
        return json.dumps(result, indent=2)
    except Exception as e:
        return f"Error regenerating API key: {str(e)}"

@mcp.tool()
async def get_access_token(username: str, password: str, expires_in: int = 3600, scope: str = "api:*", audience: str = "jfrt@*", ctx: Context = None) -> str:
    """
    Get an access token for JFrog Platform authentication.
    
    Args:
        username: The username.
        password: The password.
        expires_in: The token expiration time in seconds (default: 3600).
        scope: The token scope (default: "api:*").
        audience: The token audience (default: "jfrt@*").
    
    Returns:
        The access token information or error details.
    """
    client = ctx.request_context.lifespan_context["client"]
    path = "/access/api/v1/oauth/token"
    
    data = {
        "username": username,
        "password": password,
        "grant_type": "password",
        "expires_in": expires_in,
        "scope": scope,
        "audience": audience
    }
    
    try:
        result = await client.request("POST", path, json_data=data)
        return json.dumps(result, indent=2)
    except Exception as e:
        return f"Error getting access token: {str(e)}"

#
# System Configuration Tools
#

@mcp.tool()
async def get_system_info(ctx: Context = None) -> str:
    """
    Get system information.
    
    Returns:
        The system information as JSON string.
    """
    client = ctx.request_context.lifespan_context["client"]
    path = "/artifactory/api/system"
    
    try:
        result = await client.request("GET", path)
        return json.dumps(result, indent=2)
    except Exception as e:
        return f"Error getting system information: {str(e)}"

@mcp.tool()
async def get_system_health(ctx: Context = None) -> str:
    """
    Get system health information.
    
    Returns:
        The system health information as JSON string.
    """
    client = ctx.request_context.lifespan_context["client"]
    path = "/artifactory/api/system/ping"
    
    try:
        result = await client.request("GET", path)
        return "System is healthy: " + result.get("text", "OK")
    except Exception as e:
        return f"System health check failed: {str(e)}"

@mcp.tool()
async def get_system_configuration(ctx: Context = None) -> str:
    """
    Get system configuration (requires admin privileges).
    
    Returns:
        The system configuration or error details.
    """
    client = ctx.request_context.lifespan_context["client"]
    path = "/artifactory/api/system/configuration"
    
    try:
        result = await client.request("GET", path)
        return result.get("text", "")
    except Exception as e:
        return f"Error getting system configuration: {str(e)}"

@mcp.tool()
async def get_storage_info(ctx: Context = None) -> str:
    """
    Get storage information.
    
    Returns:
        The storage information as JSON string.
    """
    client = ctx.request_context.lifespan_context["client"]
    path = "/artifactory/api/storageinfo"
    
    try:
        result = await client.request("GET", path)
        return json.dumps(result, indent=2)
    except Exception as e:
        return f"Error getting storage information: {str(e)}"

@mcp.tool()
async def get_version(ctx: Context = None) -> str:
    """
    Get Artifactory version information.
    
    Returns:
        The version information as JSON string.
    """
    client = ctx.request_context.lifespan_context["client"]
    path = "/artifactory/api/system/version"
    
    try:
        result = await client.request("GET", path)
        return json.dumps(result, indent=2)
    except Exception as e:
        return f"Error getting version information: {str(e)}"

# Main entry point
if __name__ == "__main__":
    mcp.run()