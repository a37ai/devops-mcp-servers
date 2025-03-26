"""
Argo CD MCP Server

This server provides tools for interacting with the Argo CD API through the Model Context Protocol.
"""

import os
import json
import requests
from typing import Dict, List, Any, Optional, Union
from urllib.parse import urljoin
from mcp.server.fastmcp import FastMCP, Context
from dotenv import load_dotenv
from pydantic import BaseModel, Field, field_validator

class ArgoResponse(BaseModel):
    """Base model for Argo CD API responses."""
    status: str = "success"
    message: str | None = None
    
class ArgoErrorResponse(ArgoResponse):
    """Error response model."""
    status: str = "error"

class PaginationParams(BaseModel):
    """Common pagination parameters."""
    limit: int = Field(default=100, description="Maximum number of results to return")
    offset: int = Field(default=0, description="Number of results to skip")

class ApplicationCreate(BaseModel):
    """Model for creating an application."""
    name: str = Field(description="Name of the application")
    project: str = Field(description="Project name")
    repo_url: str = Field(description="Repository URL")
    path: str = Field(description="Path in repository")
    dest_server: str = Field(description="Destination server")
    dest_namespace: str = Field(description="Destination namespace")
    
class ApplicationUpdate(BaseModel):
    """Model for updating an application."""
    name: str = Field(description="Name of the application")
    project: str | None = Field(default=None, description="Project name")
    repo_url: str | None = Field(default=None, description="Repository URL")
    path: str | None = Field(default=None, description="Path in repository")
    dest_server: str | None = Field(default=None, description="Destination server")
    dest_namespace: str | None = Field(default=None, description="Destination namespace")

class ProjectCreate(BaseModel):
    """Model for creating a project."""
    name: str = Field(description="Name of the project")
    description: str = Field(default="", description="Description of the project")
    source_repos: List[str] = Field(default=["*"], description="Source repositories")
    
class ProjectUpdate(BaseModel):
    """Model for updating a project."""
    name: str = Field(description="Name of the project")
    description: str | None = Field(default=None, description="Description of the project")
    source_repos: List[str] | None = Field(default=None, description="Source repositories")

class RepositoryCreate(BaseModel):
    """Model for creating a repository."""
    repo: str = Field(description="Repository URL")
    username: str | None = Field(default=None, description="Username for private repositories")
    password: str | None = Field(default=None, description="Password for private repositories")
    ssh_private_key: str | None = Field(default=None, description="SSH private key for private repositories")
    
class RepositoryUpdate(BaseModel):
    """Model for updating a repository."""
    repo: str = Field(description="Repository URL")
    username: str | None = Field(default=None, description="Username for private repositories")
    password: str | None = Field(default=None, description="Password for private repositories")
    ssh_private_key: str | None = Field(default=None, description="SSH private key for private repositories")

mcp = FastMCP("argocd")

load_dotenv()

ARGOCD_URL = os.getenv("ARGOCD_URL")
ARGOCD_USERNAME = os.getenv("ARGOCD_USERNAME")
ARGOCD_PASSWORD = os.getenv("ARGOCD_PASSWORD")
ARGOCD_TOKEN = os.getenv("ARGOCD_TOKEN")

class ArgoClient:
    def __init__(self, base_url: str = None, username: str = None, password: str = None, token: str = None):
        if base_url is None:
            raise ValueError("base_url cannot be None")
        self.base_url = base_url if base_url.endswith('/') else f"{base_url}/"
        self.username = username
        self.password = password
        self.token = token
        self.session = requests.Session()
        self.session.verify = False  # Handle SSL certificates
    
    def __enter__(self):
        if not self.token and self.username and self.password:
            self.get_token()
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        self.session.close()
    
    def get_token(self) -> str:
        """Authenticate and get token."""
        login_data = {
            "username": self.username,
            "password": self.password
        }
        
        response = self.session.post(
            f"{self.base_url}api/v1/session",
            json=login_data
        )
        
        if response.status_code == 200:
            token_data = response.json()
            self.token = token_data.get('token')
            return self.token
        else:
            raise Exception(f"Login failed: {response.status_code} - {response.text}")
    
    def get_headers(self) -> Dict[str, str]:
        """Get request headers with authorization."""
        headers = {"Content-Type": "application/json"}
        if self.token:
            headers["Authorization"] = f"Bearer {self.token}"
        return headers
    
    def request(self, method: str, endpoint: str, params: Dict = None, data: Dict = None) -> Dict:
        """Make a request to the Argo CD API."""
        url = urljoin(self.base_url, endpoint)
        headers = self.get_headers()
        
        response = self.session.request(
            method=method,
            url=url,
            headers=headers,
            params=params,
            json=data,
            verify=False  # Skip SSL verification
        )
        
        if response.status_code >= 400:
            error_message = f"Argo CD API error: {response.status_code} - {response.text}"
            raise Exception(error_message)
            
        if response.status_code == 204:  # No content
            return {"status": "success"}
        
        if not response.text.strip():
            return {"status": "success", "message": "Empty response"}
            
        try:
            return response.json()
        except json.JSONDecodeError:
            return {
                "status": "success",
                "content_type": response.headers.get("Content-Type", "unknown"),
                "text": response.text[:1000]  # Return first 1000 chars to avoid massive responses
            }

def get_argo_client() -> ArgoClient:
    """Get an initialized Argo CD API client."""
    client = ArgoClient(
        base_url=ARGOCD_URL,
        username=ARGOCD_USERNAME, 
        password=ARGOCD_PASSWORD,
        token=ARGOCD_TOKEN
    )
    return client


@mcp.tool()
def list_applications(project: str = None, limit: int = 100, offset: int = 0) -> str:
    """List all applications, optionally filtered by project.
    
    Args:
        project: Optional project name to filter applications
        limit: Maximum number of results to return
        offset: Number of results to skip
    """
    try:
        params = PaginationParams(limit=limit, offset=offset)
        params_dict = params.model_dump()
        
        if project:
            params_dict["project"] = project
            
        with get_argo_client() as client:
            response = client.request("GET", "api/v1/applications", params=params_dict)
            return json.dumps(response, indent=2)
    except ValueError as e:
        return json.dumps(ArgoErrorResponse(message=str(e)).model_dump(), indent=2)

@mcp.tool()
def get_application(name: str, project: str = None) -> str:
    """Get details about a specific application.
    
    Args:
        name: Name of the application
        project: Optional project name for the application
    """
    params = {}
    if project:
        params["project"] = project
        
    with get_argo_client() as client:
        response = client.request("GET", f"api/v1/applications/{name}", params=params)
        return json.dumps(response, indent=2)

@mcp.tool()
def create_application(
    name: str,
    project: str,
    repo_url: str,
    path: str,
    dest_server: str,
    dest_namespace: str
) -> str:
    """Create a new application.
    
    Args:
        name: Name of the application
        project: Project name
        repo_url: Repository URL
        path: Path in repository
        dest_server: Destination server
        dest_namespace: Destination namespace
    """
    try:
        app_data = ApplicationCreate(
            name=name,
            project=project,
            repo_url=repo_url,
            path=path,
            dest_server=dest_server,
            dest_namespace=dest_namespace
        )
        
        with get_argo_client() as client:
            data = {
                "application": {
                    "metadata": {
                        "name": app_data.name
                    },
                    "spec": {
                        "project": app_data.project,
                        "source": {
                            "repoURL": app_data.repo_url,
                            "path": app_data.path,
                            "targetRevision": "HEAD"
                        },
                        "destination": {
                            "server": app_data.dest_server,
                            "namespace": app_data.dest_namespace
                        }
                    }
                }
            }
            
            response = client.request("POST", "api/v1/applications", data=data)
            return json.dumps(response, indent=2)
            
    except ValueError as e:
        return json.dumps(ArgoErrorResponse(message=str(e)).model_dump(), indent=2)

@mcp.tool()
def delete_application(name: str, cascade: bool = True) -> str:
    """Delete an application.
    
    Args:
        name: Name of the application
        cascade: Whether to cascade delete resources
    """
    params = {"cascade": str(cascade).lower()}
    
    with get_argo_client() as client:
        try:
            response = client.request("DELETE", f"api/v1/applications/{name}", params=params)
            return json.dumps(response, indent=2)
        except Exception as e:
            return json.dumps({"status": "error", "message": str(e)})

@mcp.tool()
def sync_application(name: str, revision: str = None, prune: bool = False) -> str:
    """Sync an application.
    
    Args:
        name: Name of the application
        revision: Revision to sync to (defaults to HEAD)
        prune: Whether to prune resources
    """
    with get_argo_client() as client:
        data = {
            "revision": revision or "HEAD",
            "prune": prune
        }
        
        response = client.request("POST", f"api/v1/applications/{name}/sync", data=data)
        return json.dumps(response, indent=2)


@mcp.tool()
def list_projects(limit: int = 100, offset: int = 0) -> str:
    """List all projects.
    
    Args:
        limit: Maximum number of results to return
        offset: Number of results to skip
    """
    try:
        params = PaginationParams(limit=limit, offset=offset)
        
        with get_argo_client() as client:
            response = client.request("GET", "api/v1/projects", params=params.model_dump())
            return json.dumps(response, indent=2)
    except ValueError as e:
        return json.dumps(ArgoErrorResponse(message=str(e)).model_dump(), indent=2)

@mcp.tool()
def get_project(name: str) -> str:
    """Get details about a specific project.
    
    Args:
        name: Name of the project
    """
    with get_argo_client() as client:
        response = client.request("GET", f"api/v1/projects/{name}")
        return json.dumps(response, indent=2)

@mcp.tool()
def create_project(name: str, description: str = "", source_repos: List[str] = None) -> str:
    """Create a new project.
    
    Args:
        name: Name of the project
        description: Description of the project
        source_repos: List of source repositories (defaults to ["*"])
    """
    try:
        project_data = ProjectCreate(
            name=name,
            description=description,
            source_repos=source_repos or ["*"]
        )
        
        with get_argo_client() as client:
            data = {
                "project": {
                    "metadata": {
                        "name": project_data.name
                    },
                    "spec": {
                        "description": project_data.description,
                        "sourceRepos": project_data.source_repos,
                        "destinations": [
                            {
                                "server": "*",
                                "namespace": "*"
                            }
                        ]
                    }
                }
            }
            
            response = client.request("POST", "api/v1/projects", data=data)
            return json.dumps(response, indent=2)
            
    except ValueError as e:
        return json.dumps(ArgoErrorResponse(message=str(e)).model_dump(), indent=2)

@mcp.tool()
def delete_project(name: str) -> str:
    """Delete a project.
    
    Args:
        name: Name of the project
    """
    with get_argo_client() as client:
        try:
            response = client.request("DELETE", f"api/v1/projects/{name}")
            return json.dumps(response, indent=2)
        except Exception as e:
            return json.dumps({"status": "error", "message": str(e)})


@mcp.tool()
def list_repositories(limit: int = 100, offset: int = 0) -> str:
    """List all repositories.
    
    Args:
        limit: Maximum number of results to return
        offset: Number of results to skip
    """
    try:
        params = PaginationParams(limit=limit, offset=offset)
        
        with get_argo_client() as client:
            response = client.request("GET", "api/v1/repositories", params=params.model_dump())
            return json.dumps(response, indent=2)
    except ValueError as e:
        return json.dumps(ArgoErrorResponse(message=str(e)).model_dump(), indent=2)

@mcp.tool()
def get_repository(repo_url: str) -> str:
    """Get details about a specific repository.
    
    Args:
        repo_url: URL of the repository
    """
    from urllib.parse import quote
    encoded_url = quote(repo_url, safe='')
    
    with get_argo_client() as client:
        response = client.request("GET", f"api/v1/repositories/{encoded_url}")
        return json.dumps(response, indent=2)

@mcp.tool()
def create_repository(
    repo: str,
    username: str = None,
    password: str = None,
    ssh_private_key: str = None
) -> str:
    """Create a new repository.
    
    Args:
        repo: Repository URL
        username: Username for private repositories
        password: Password for private repositories
        ssh_private_key: SSH private key for private repositories
    """
    try:
        repo_data = RepositoryCreate(
            repo=repo,
            username=username,
            password=password,
            ssh_private_key=ssh_private_key
        )
        
        with get_argo_client() as client:
            data = {
                "repo": repo_data.repo,
                "type": "git"
            }
            
            if repo_data.username:
                data["username"] = repo_data.username
            if repo_data.password:
                data["password"] = repo_data.password
            if repo_data.ssh_private_key:
                data["sshPrivateKey"] = repo_data.ssh_private_key
            
            response = client.request("POST", "api/v1/repositories", data=data)
            return json.dumps(response, indent=2)
            
    except ValueError as e:
        return json.dumps(ArgoErrorResponse(message=str(e)).model_dump(), indent=2)

@mcp.tool()
def delete_repository(repo_url: str) -> str:
    """Delete a repository.
    
    Args:
        repo_url: URL of the repository
    """
    from urllib.parse import quote
    encoded_url = quote(repo_url, safe='')
    
    with get_argo_client() as client:
        try:
            response = client.request("DELETE", f"api/v1/repositories/{encoded_url}")
            return json.dumps(response, indent=2)
        except Exception as e:
            return json.dumps({"status": "error", "message": str(e)})


@mcp.tool()
def list_clusters(limit: int = 100, offset: int = 0) -> str:
    """List all clusters.
    
    Args:
        limit: Maximum number of results to return
        offset: Number of results to skip
    """
    try:
        params = PaginationParams(limit=limit, offset=offset)
        
        with get_argo_client() as client:
            response = client.request("GET", "api/v1/clusters", params=params.model_dump())
            return json.dumps(response, indent=2)
    except ValueError as e:
        return json.dumps(ArgoErrorResponse(message=str(e)).model_dump(), indent=2)

@mcp.tool()
def get_cluster(server: str) -> str:
    """Get details about a specific cluster.
    
    Args:
        server: Server URL of the cluster
    """
    from urllib.parse import quote
    encoded_server = quote(server, safe='')
    
    with get_argo_client() as client:
        response = client.request("GET", f"api/v1/clusters/{encoded_server}")
        return json.dumps(response, indent=2)


@mcp.tool()
def get_version() -> str:
    """Get Argo CD version information."""
    with get_argo_client() as client:
        response = client.request("GET", "api/version")
        return json.dumps(response, indent=2)

@mcp.tool()
def get_settings() -> str:
    """Get Argo CD settings."""
    with get_argo_client() as client:
        response = client.request("GET", "api/v1/settings")
        return json.dumps(response, indent=2)

if __name__ == "__main__":
    mcp.run(transport='stdio')
