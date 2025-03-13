#!/usr/bin/env python3
"""
Ansible MCP Server

This server provides tools for interacting with the Ansible API through the Model Context Protocol.
"""

import asyncio
import os
import json
import httpx
from typing import Dict, List, Any, Optional, Union
from urllib.parse import urljoin
from mcp.server.fastmcp import FastMCP, Context

# Initialize FastMCP server
mcp = FastMCP("ansible")

# Configuration
ANSIBLE_BASE_URL = os.environ.get("ANSIBLE_BASE_URL", "http://localhost:8043")
ANSIBLE_USERNAME = os.environ.get("ANSIBLE_USERNAME", "admin")
ANSIBLE_PASSWORD = os.environ.get("ANSIBLE_PASSWORD", "password")
ANSIBLE_TOKEN = os.environ.get("ANSIBLE_TOKEN", "")

# API Client
class AnsibleClient:
    def __init__(self, base_url: str, username: str = None, password: str = None, token: str = None):
        self.base_url = base_url
        self.username = username
        self.password = password
        self.token = token
        self.client = httpx.AsyncClient()
    
    async def __aenter__(self):
        if not self.token and self.username and self.password:
            await self.get_token()
        return self
    
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        await self.client.aclose()
    
    async def get_token(self) -> str:
        """Authenticate and get token."""
        url = urljoin(self.base_url, "/api/v2/tokens/")
        response = await self.client.post(
            url,
            json={"username": self.username, "password": self.password, "description": "MCP Server Token"},
            auth=(self.username, self.password)
        )
        if response.status_code == 201:
            self.token = response.json().get("token")
            return self.token
        else:
            raise Exception(f"Authentication failed: {response.status_code} - {response.text}")
    
    def get_headers(self) -> Dict[str, str]:
        """Get request headers with authorization."""
        headers = {"Content-Type": "application/json"}
        if self.token:
            headers["Authorization"] = f"Bearer {self.token}"
        return headers
    
    async def request(self, method: str, endpoint: str, params: Dict = None, data: Dict = None) -> Dict:
        """Make a request to the Ansible API."""
        url = urljoin(self.base_url, endpoint)
        headers = self.get_headers()
        
        response = await self.client.request(
            method=method,
            url=url,
            headers=headers,
            params=params,
            json=data
        )
        
        if response.status_code >= 400:
            error_message = f"Ansible API error: {response.status_code} - {response.text}"
            raise Exception(error_message)
            
        if response.status_code == 204:  # No content
            return {"status": "success"}
            
        return response.json()

# Helper Functions
async def get_ansible_client() -> AnsibleClient:
    """Get an initialized Ansible API client."""
    client = AnsibleClient(
        base_url=ANSIBLE_BASE_URL,
        username=ANSIBLE_USERNAME, 
        password=ANSIBLE_PASSWORD,
        token=ANSIBLE_TOKEN
    )
    await client.__aenter__()
    return client

async def handle_pagination(client: AnsibleClient, endpoint: str, params: Dict = None) -> List[Dict]:
    """Handle paginated results from Ansible API."""
    if params is None:
        params = {}
    
    results = []
    next_url = endpoint
    
    while next_url:
        response = await client.request("GET", next_url, params=params)
        if "results" in response:
            results.extend(response["results"])
        else:
            # If the response is not paginated, return it directly
            return [response]
            
        next_url = response.get("next")
        if next_url:
            # For subsequent requests, don't use params as they're included in the next URL
            params = None
            
    return results

# MCP Tools - Inventory Management

@mcp.tool()
async def list_inventories(limit: int = 100, offset: int = 0) -> str:
    """List all inventories.
    
    Args:
        limit: Maximum number of results to return
        offset: Number of results to skip
    """
    async with await get_ansible_client() as client:
        params = {"limit": limit, "offset": offset}
        inventories = await handle_pagination(client, "/api/v2/inventories/", params)
        return json.dumps(inventories, indent=2)

@mcp.tool()
async def get_inventory(inventory_id: int) -> str:
    """Get details about a specific inventory.
    
    Args:
        inventory_id: ID of the inventory
    """
    async with await get_ansible_client() as client:
        inventory = await client.request("GET", f"/api/v2/inventories/{inventory_id}/")
        return json.dumps(inventory, indent=2)

@mcp.tool()
async def create_inventory(name: str, organization_id: int, description: str = "") -> str:
    """Create a new inventory.
    
    Args:
        name: Name of the inventory
        organization_id: ID of the organization
        description: Description of the inventory
    """
    async with await get_ansible_client() as client:
        data = {
            "name": name,
            "description": description,
            "organization": organization_id
        }
        response = await client.request("POST", "/api/v2/inventories/", data=data)
        return json.dumps(response, indent=2)

@mcp.tool()
async def update_inventory(inventory_id: int, name: str = None, description: str = None) -> str:
    """Update an existing inventory.
    
    Args:
        inventory_id: ID of the inventory
        name: New name for the inventory
        description: New description for the inventory
    """
    async with await get_ansible_client() as client:
        data = {}
        if name:
            data["name"] = name
        if description:
            data["description"] = description
            
        response = await client.request("PATCH", f"/api/v2/inventories/{inventory_id}/", data=data)
        return json.dumps(response, indent=2)

@mcp.tool()
async def delete_inventory(inventory_id: int) -> str:
    """Delete an inventory.
    
    Args:
        inventory_id: ID of the inventory
    """
    async with await get_ansible_client() as client:
        await client.request("DELETE", f"/api/v2/inventories/{inventory_id}/")
        return json.dumps({"status": "success", "message": f"Inventory {inventory_id} deleted"})

# MCP Tools - Host Management

@mcp.tool()
async def list_hosts(inventory_id: int = None, limit: int = 100, offset: int = 0) -> str:
    """List hosts, optionally filtered by inventory.
    
    Args:
        inventory_id: Optional ID of inventory to filter hosts
        limit: Maximum number of results to return
        offset: Number of results to skip
    """
    async with await get_ansible_client() as client:
        params = {"limit": limit, "offset": offset}
        
        if inventory_id:
            endpoint = f"/api/v2/inventories/{inventory_id}/hosts/"
        else:
            endpoint = "/api/v2/hosts/"
            
        hosts = await handle_pagination(client, endpoint, params)
        return json.dumps(hosts, indent=2)

@mcp.tool()
async def get_host(host_id: int) -> str:
    """Get details about a specific host.
    
    Args:
        host_id: ID of the host
    """
    async with await get_ansible_client() as client:
        host = await client.request("GET", f"/api/v2/hosts/{host_id}/")
        return json.dumps(host, indent=2)

@mcp.tool()
async def create_host(name: str, inventory_id: int, variables: str = "{}", description: str = "") -> str:
    """Create a new host in an inventory.
    
    Args:
        name: Name or IP address of the host
        inventory_id: ID of the inventory to add the host to
        variables: JSON string of host variables
        description: Description of the host
    """
    try:
        # Validate that variables is a proper JSON string
        json.loads(variables)
    except json.JSONDecodeError:
        return json.dumps({"status": "error", "message": "Invalid JSON in variables"})
    
    async with await get_ansible_client() as client:
        data = {
            "name": name,
            "inventory": inventory_id,
            "variables": variables,
            "description": description
        }
        response = await client.request("POST", "/api/v2/hosts/", data=data)
        return json.dumps(response, indent=2)

@mcp.tool()
async def update_host(host_id: int, name: str = None, variables: str = None, description: str = None) -> str:
    """Update an existing host.
    
    Args:
        host_id: ID of the host
        name: New name for the host
        variables: JSON string of host variables
        description: New description for the host
    """
    if variables:
        try:
            # Validate that variables is a proper JSON string
            json.loads(variables)
        except json.JSONDecodeError:
            return json.dumps({"status": "error", "message": "Invalid JSON in variables"})
    
    async with await get_ansible_client() as client:
        data = {}
        if name:
            data["name"] = name
        if variables:
            data["variables"] = variables
        if description:
            data["description"] = description
            
        response = await client.request("PATCH", f"/api/v2/hosts/{host_id}/", data=data)
        return json.dumps(response, indent=2)

@mcp.tool()
async def delete_host(host_id: int) -> str:
    """Delete a host.
    
    Args:
        host_id: ID of the host
    """
    async with await get_ansible_client() as client:
        await client.request("DELETE", f"/api/v2/hosts/{host_id}/")
        return json.dumps({"status": "success", "message": f"Host {host_id} deleted"})

# MCP Tools - Group Management

@mcp.tool()
async def list_groups(inventory_id: int, limit: int = 100, offset: int = 0) -> str:
    """List groups in an inventory.
    
    Args:
        inventory_id: ID of the inventory
        limit: Maximum number of results to return
        offset: Number of results to skip
    """
    async with await get_ansible_client() as client:
        params = {"limit": limit, "offset": offset}
        groups = await handle_pagination(client, f"/api/v2/inventories/{inventory_id}/groups/", params)
        return json.dumps(groups, indent=2)

@mcp.tool()
async def get_group(group_id: int) -> str:
    """Get details about a specific group.
    
    Args:
        group_id: ID of the group
    """
    async with await get_ansible_client() as client:
        group = await client.request("GET", f"/api/v2/groups/{group_id}/")
        return json.dumps(group, indent=2)

@mcp.tool()
async def create_group(name: str, inventory_id: int, variables: str = "{}", description: str = "") -> str:
    """Create a new group in an inventory.
    
    Args:
        name: Name of the group
        inventory_id: ID of the inventory to add the group to
        variables: JSON string of group variables
        description: Description of the group
    """
    try:
        # Validate that variables is a proper JSON string
        json.loads(variables)
    except json.JSONDecodeError:
        return json.dumps({"status": "error", "message": "Invalid JSON in variables"})
    
    async with await get_ansible_client() as client:
        data = {
            "name": name,
            "inventory": inventory_id,
            "variables": variables,
            "description": description
        }
        response = await client.request("POST", "/api/v2/groups/", data=data)
        return json.dumps(response, indent=2)

@mcp.tool()
async def update_group(group_id: int, name: str = None, variables: str = None, description: str = None) -> str:
    """Update an existing group.
    
    Args:
        group_id: ID of the group
        name: New name for the group
        variables: JSON string of group variables
        description: New description for the group
    """
    if variables:
        try:
            # Validate that variables is a proper JSON string
            json.loads(variables)
        except json.JSONDecodeError:
            return json.dumps({"status": "error", "message": "Invalid JSON in variables"})
    
    async with await get_ansible_client() as client:
        data = {}
        if name:
            data["name"] = name
        if variables:
            data["variables"] = variables
        if description:
            data["description"] = description
            
        response = await client.request("PATCH", f"/api/v2/groups/{group_id}/", data=data)
        return json.dumps(response, indent=2)

@mcp.tool()
async def delete_group(group_id: int) -> str:
    """Delete a group.
    
    Args:
        group_id: ID of the group
    """
    async with await get_ansible_client() as client:
        await client.request("DELETE", f"/api/v2/groups/{group_id}/")
        return json.dumps({"status": "success", "message": f"Group {group_id} deleted"})

@mcp.tool()
async def add_host_to_group(group_id: int, host_id: int) -> str:
    """Add a host to a group.
    
    Args:
        group_id: ID of the group
        host_id: ID of the host
    """
    async with await get_ansible_client() as client:
        data = {"id": host_id}
        response = await client.request("POST", f"/api/v2/groups/{group_id}/hosts/", data=data)
        return json.dumps(response, indent=2)

@mcp.tool()
async def remove_host_from_group(group_id: int, host_id: int) -> str:
    """Remove a host from a group.
    
    Args:
        group_id: ID of the group
        host_id: ID of the host
    """
    async with await get_ansible_client() as client:
        await client.request("POST", f"/api/v2/groups/{group_id}/hosts/", data={"id": host_id, "disassociate": True})
        return json.dumps({"status": "success", "message": f"Host {host_id} removed from group {group_id}"})

# MCP Tools - Job Template Management

@mcp.tool()
async def list_job_templates(limit: int = 100, offset: int = 0) -> str:
    """List all job templates.
    
    Args:
        limit: Maximum number of results to return
        offset: Number of results to skip
    """
    async with await get_ansible_client() as client:
        params = {"limit": limit, "offset": offset}
        templates = await handle_pagination(client, "/api/v2/job_templates/", params)
        return json.dumps(templates, indent=2)

@mcp.tool()
async def get_job_template(template_id: int) -> str:
    """Get details about a specific job template.
    
    Args:
        template_id: ID of the job template
    """
    async with await get_ansible_client() as client:
        template = await client.request("GET", f"/api/v2/job_templates/{template_id}/")
        return json.dumps(template, indent=2)

@mcp.tool()
async def create_job_template(
    name: str, 
    inventory_id: int,
    project_id: int,
    playbook: str,
    credential_id: int = None,
    description: str = "",
    extra_vars: str = "{}"
) -> str:
    """Create a new job template.
    
    Args:
        name: Name of the job template
        inventory_id: ID of the inventory
        project_id: ID of the project
        playbook: Name of the playbook (e.g., "playbook.yml")
        credential_id: Optional ID of the credential
        description: Description of the job template
        extra_vars: JSON string of extra variables
    """
    try:
        # Validate that extra_vars is a proper JSON string
        json.loads(extra_vars)
    except json.JSONDecodeError:
        return json.dumps({"status": "error", "message": "Invalid JSON in extra_vars"})
    
    async with await get_ansible_client() as client:
        data = {
            "name": name,
            "inventory": inventory_id,
            "project": project_id,
            "playbook": playbook,
            "description": description,
            "extra_vars": extra_vars,
            "job_type": "run",
            "verbosity": 0
        }
        
        if credential_id:
            data["credential"] = credential_id
            
        response = await client.request("POST", "/api/v2/job_templates/", data=data)
        return json.dumps(response, indent=2)

@mcp.tool()
async def update_job_template(
    template_id: int,
    name: str = None,
    inventory_id: int = None,
    playbook: str = None,
    description: str = None,
    extra_vars: str = None
) -> str:
    """Update an existing job template.
    
    Args:
        template_id: ID of the job template
        name: New name for the job template
        inventory_id: New inventory ID
        playbook: New playbook name
        description: New description
        extra_vars: JSON string of extra variables
    """
    if extra_vars:
        try:
            # Validate that extra_vars is a proper JSON string
            json.loads(extra_vars)
        except json.JSONDecodeError:
            return json.dumps({"status": "error", "message": "Invalid JSON in extra_vars"})
    
    async with await get_ansible_client() as client:
        data = {}
        if name:
            data["name"] = name
        if inventory_id:
            data["inventory"] = inventory_id
        if playbook:
            data["playbook"] = playbook
        if description:
            data["description"] = description
        if extra_vars:
            data["extra_vars"] = extra_vars
            
        response = await client.request("PATCH", f"/api/v2/job_templates/{template_id}/", data=data)
        return json.dumps(response, indent=2)

@mcp.tool()
async def delete_job_template(template_id: int) -> str:
    """Delete a job template.
    
    Args:
        template_id: ID of the job template
    """
    async with await get_ansible_client() as client:
        await client.request("DELETE", f"/api/v2/job_templates/{template_id}/")
        return json.dumps({"status": "success", "message": f"Job template {template_id} deleted"})

@mcp.tool()
async def launch_job(template_id: int, extra_vars: str = None) -> str:
    """Launch a job from a job template.
    
    Args:
        template_id: ID of the job template
        extra_vars: JSON string of extra variables to override the template's variables
    """
    if extra_vars:
        try:
            # Validate that extra_vars is a proper JSON string
            json.loads(extra_vars)
        except json.JSONDecodeError:
            return json.dumps({"status": "error", "message": "Invalid JSON in extra_vars"})
    
    async with await get_ansible_client() as client:
        data = {}
        if extra_vars:
            data["extra_vars"] = extra_vars
            
        response = await client.request("POST", f"/api/v2/job_templates/{template_id}/launch/", data=data)
        return json.dumps(response, indent=2)

# MCP Tools - Job Management

@mcp.tool()
async def list_jobs(status: str = None, limit: int = 100, offset: int = 0) -> str:
    """List all jobs, optionally filtered by status.
    
    Args:
        status: Filter by job status (pending, waiting, running, successful, failed, canceled)
        limit: Maximum number of results to return
        offset: Number of results to skip
    """
    async with await get_ansible_client() as client:
        params = {"limit": limit, "offset": offset}
        if status:
            params["status"] = status
            
        jobs = await handle_pagination(client, "/api/v2/jobs/", params)
        return json.dumps(jobs, indent=2)

@mcp.tool()
async def get_job(job_id: int) -> str:
    """Get details about a specific job.
    
    Args:
        job_id: ID of the job
    """
    async with await get_ansible_client() as client:
        job = await client.request("GET", f"/api/v2/jobs/{job_id}/")
        return json.dumps(job, indent=2)

@mcp.tool()
async def cancel_job(job_id: int) -> str:
    """Cancel a running job.
    
    Args:
        job_id: ID of the job
    """
    async with await get_ansible_client() as client:
        response = await client.request("POST", f"/api/v2/jobs/{job_id}/cancel/")
        return json.dumps(response, indent=2)

@mcp.tool()
async def get_job_events(job_id: int, limit: int = 100, offset: int = 0) -> str:
    """Get events for a specific job.
    
    Args:
        job_id: ID of the job
        limit: Maximum number of results to return
        offset: Number of results to skip
    """
    async with await get_ansible_client() as client:
        params = {"limit": limit, "offset": offset}
        events = await handle_pagination(client, f"/api/v2/jobs/{job_id}/job_events/", params)
        return json.dumps(events, indent=2)

@mcp.tool()
async def get_job_stdout(job_id: int, format: str = "txt") -> str:
    """Get the standard output of a job.
    
    Args:
        job_id: ID of the job
        format: Output format (txt, html, json, ansi)
    """
    if format not in ["txt", "html", "json", "ansi"]:
        return json.dumps({"status": "error", "message": "Invalid format. Must be one of: txt, html, json, ansi"})
    
    async with await get_ansible_client() as client:
        response = await client.request("GET", f"/api/v2/jobs/{job_id}/stdout/?format={format}")
        
        if format == "json":
            return json.dumps(response, indent=2)
        else:
            # For non-JSON responses, include the content directly
            return json.dumps({"status": "success", "stdout": response}, indent=2)

# MCP Tools - Project Management

@mcp.tool()
async def list_projects(limit: int = 100, offset: int = 0) -> str:
    """List all projects.
    
    Args:
        limit: Maximum number of results to return
        offset: Number of results to skip
    """
    async with await get_ansible_client() as client:
        params = {"limit": limit, "offset": offset}
        projects = await handle_pagination(client, "/api/v2/projects/", params)
        return json.dumps(projects, indent=2)

@mcp.tool()
async def get_project(project_id: int) -> str:
    """Get details about a specific project.
    
    Args:
        project_id: ID of the project
    """
    async with await get_ansible_client() as client:
        project = await client.request("GET", f"/api/v2/projects/{project_id}/")
        return json.dumps(project, indent=2)

@mcp.tool()
async def create_project(
    name: str,
    organization_id: int,
    scm_type: str,
    scm_url: str = None,
    scm_branch: str = None,
    credential_id: int = None,
    description: str = ""
) -> str:
    """Create a new project.
    
    Args:
        name: Name of the project
        organization_id: ID of the organization
        scm_type: SCM type (git, hg, svn, manual)
        scm_url: URL for the repository
        scm_branch: Branch/tag/commit to checkout
        credential_id: ID of the credential for SCM access
        description: Description of the project
    """
    if scm_type not in ["", "git", "hg", "svn", "manual"]:
        return json.dumps({"status": "error", "message": "Invalid SCM type. Must be one of: git, hg, svn, manual"})
    
    if scm_type != "manual" and not scm_url:
        return json.dumps({"status": "error", "message": "SCM URL is required for non-manual SCM types"})
    
    async with await get_ansible_client() as client:
        data = {
            "name": name,
            "organization": organization_id,
            "scm_type": scm_type,
            "description": description
        }
        
        if scm_url:
            data["scm_url"] = scm_url
        if scm_branch:
            data["scm_branch"] = scm_branch
        if credential_id:
            data["credential"] = credential_id
            
        response = await client.request("POST", "/api/v2/projects/", data=data)
        return json.dumps(response, indent=2)

@mcp.tool()
async def update_project(
    project_id: int,
    name: str = None,
    scm_type: str = None,
    scm_url: str = None,
    scm_branch: str = None,
    description: str = None
) -> str:
    """Update an existing project.
    
    Args:
        project_id: ID of the project
        name: New name for the project
        scm_type: New SCM type (git, hg, svn, manual)
        scm_url: New URL for the repository
        scm_branch: New branch/tag/commit to checkout
        description: New description
    """
    if scm_type and scm_type not in ["", "git", "hg", "svn", "manual"]:
        return json.dumps({"status": "error", "message": "Invalid SCM type. Must be one of: git, hg, svn, manual"})
    
    async with await get_ansible_client() as client:
        data = {}
        if name:
            data["name"] = name
        if scm_type:
            data["scm_type"] = scm_type
        if scm_url:
            data["scm_url"] = scm_url
        if scm_branch:
            data["scm_branch"] = scm_branch
        if description:
            data["description"] = description
            
        response = await client.request("PATCH", f"/api/v2/projects/{project_id}/", data=data)
        return json.dumps(response, indent=2)

@mcp.tool()
async def delete_project(project_id: int) -> str:
    """Delete a project.
    
    Args:
        project_id: ID of the project
    """
    async with await get_ansible_client() as client:
        await client.request("DELETE", f"/api/v2/projects/{project_id}/")
        return json.dumps({"status": "success", "message": f"Project {project_id} deleted"})

@mcp.tool()
async def sync_project(project_id: int) -> str:
    """Sync a project with its SCM source.
    
    Args:
        project_id: ID of the project
    """
    async with await get_ansible_client() as client:
        response = await client.request("POST", f"/api/v2/projects/{project_id}/update/")
        return json.dumps(response, indent=2)

# MCP Tools - Credential Management

@mcp.tool()
async def list_credentials(limit: int = 100, offset: int = 0) -> str:
    """List all credentials.
    
    Args:
        limit: Maximum number of results to return
        offset: Number of results to skip
    """
    async with await get_ansible_client() as client:
        params = {"limit": limit, "offset": offset}
        credentials = await handle_pagination(client, "/api/v2/credentials/", params)
        return json.dumps(credentials, indent=2)

@mcp.tool()
async def get_credential(credential_id: int) -> str:
    """Get details about a specific credential.
    
    Args:
        credential_id: ID of the credential
    """
    async with await get_ansible_client() as client:
        credential = await client.request("GET", f"/api/v2/credentials/{credential_id}/")
        return json.dumps(credential, indent=2)

@mcp.tool()
async def list_credential_types(limit: int = 100, offset: int = 0) -> str:
    """List all credential types.
    
    Args:
        limit: Maximum number of results to return
        offset: Number of results to skip
    """
    async with await get_ansible_client() as client:
        params = {"limit": limit, "offset": offset}
        credential_types = await handle_pagination(client, "/api/v2/credential_types/", params)
        return json.dumps(credential_types, indent=2)

@mcp.tool()
async def create_credential(
    name: str,
    credential_type_id: int,
    organization_id: int,
    inputs: str,
    description: str = ""
) -> str:
    """Create a new credential.
    
    Args:
        name: Name of the credential
        credential_type_id: ID of the credential type
        organization_id: ID of the organization
        inputs: JSON string of credential inputs (e.g., username, password)
        description: Description of the credential
    """
    try:
        # Validate that inputs is a proper JSON string
        json.loads(inputs)
    except json.JSONDecodeError:
        return json.dumps({"status": "error", "message": "Invalid JSON in inputs"})
    
    async with await get_ansible_client() as client:
        data = {
            "name": name,
            "credential_type": credential_type_id,
            "organization": organization_id,
            "inputs": json.loads(inputs),
            "description": description
        }
            
        response = await client.request("POST", "/api/v2/credentials/", data=data)
        return json.dumps(response, indent=2)

@mcp.tool()
async def update_credential(
    credential_id: int,
    name: str = None,
    inputs: str = None,
    description: str = None
) -> str:
    """Update an existing credential.
    
    Args:
        credential_id: ID of the credential
        name: New name for the credential
        inputs: JSON string of credential inputs
        description: New description
    """
    if inputs:
        try:
            # Validate that inputs is a proper JSON string
            json.loads(inputs)
        except json.JSONDecodeError:
            return json.dumps({"status": "error", "message": "Invalid JSON in inputs"})
    
    async with await get_ansible_client() as client:
        data = {}
        if name:
            data["name"] = name
        if inputs:
            data["inputs"] = json.loads(inputs)
        if description:
            data["description"] = description
            
        response = await client.request("PATCH", f"/api/v2/credentials/{credential_id}/", data=data)
        return json.dumps(response, indent=2)

@mcp.tool()
async def delete_credential(credential_id: int) -> str:
    """Delete a credential.
    
    Args:
        credential_id: ID of the credential
    """
    async with await get_ansible_client() as client:
        await client.request("DELETE", f"/api/v2/credentials/{credential_id}/")
        return json.dumps({"status": "success", "message": f"Credential {credential_id} deleted"})

# MCP Tools - Organization Management

@mcp.tool()
async def list_organizations(limit: int = 100, offset: int = 0) -> str:
    """List all organizations.
    
    Args:
        limit: Maximum number of results to return
        offset: Number of results to skip
    """
    async with await get_ansible_client() as client:
        params = {"limit": limit, "offset": offset}
        organizations = await handle_pagination(client, "/api/v2/organizations/", params)
        return json.dumps(organizations, indent=2)

@mcp.tool()
async def get_organization(organization_id: int) -> str:
    """Get details about a specific organization.
    
    Args:
        organization_id: ID of the organization
    """
    async with await get_ansible_client() as client:
        organization = await client.request("GET", f"/api/v2/organizations/{organization_id}/")
        return json.dumps(organization, indent=2)

@mcp.tool()
async def create_organization(name: str, description: str = "") -> str:
    """Create a new organization.
    
    Args:
        name: Name of the organization
        description: Description of the organization
    """
    async with await get_ansible_client() as client:
        data = {
            "name": name,
            "description": description
        }
        response = await client.request("POST", "/api/v2/organizations/", data=data)
        return json.dumps(response, indent=2)

@mcp.tool()
async def update_organization(organization_id: int, name: str = None, description: str = None) -> str:
    """Update an existing organization.
    
    Args:
        organization_id: ID of the organization
        name: New name for the organization
        description: New description
    """
    async with await get_ansible_client() as client:
        data = {}
        if name:
            data["name"] = name
        if description:
            data["description"] = description
            
        response = await client.request("PATCH", f"/api/v2/organizations/{organization_id}/", data=data)
        return json.dumps(response, indent=2)

@mcp.tool()
async def delete_organization(organization_id: int) -> str:
    """Delete an organization.
    
    Args:
        organization_id: ID of the organization
    """
    async with await get_ansible_client() as client:
        await client.request("DELETE", f"/api/v2/organizations/{organization_id}/")
        return json.dumps({"status": "success", "message": f"Organization {organization_id} deleted"})

# MCP Tools - Team Management

@mcp.tool()
async def list_teams(organization_id: int = None, limit: int = 100, offset: int = 0) -> str:
    """List teams, optionally filtered by organization.
    
    Args:
        organization_id: Optional ID of organization to filter teams
        limit: Maximum number of results to return
        offset: Number of results to skip
    """
    async with await get_ansible_client() as client:
        params = {"limit": limit, "offset": offset}
        
        if organization_id:
            endpoint = f"/api/v2/organizations/{organization_id}/teams/"
        else:
            endpoint = "/api/v2/teams/"
            
        teams = await handle_pagination(client, endpoint, params)
        return json.dumps(teams, indent=2)

@mcp.tool()
async def get_team(team_id: int) -> str:
    """Get details about a specific team.
    
    Args:
        team_id: ID of the team
    """
    async with await get_ansible_client() as client:
        team = await client.request("GET", f"/api/v2/teams/{team_id}/")
        return json.dumps(team, indent=2)

@mcp.tool()
async def create_team(name: str, organization_id: int, description: str = "") -> str:
    """Create a new team.
    
    Args:
        name: Name of the team
        organization_id: ID of the organization
        description: Description of the team
    """
    async with await get_ansible_client() as client:
        data = {
            "name": name,
            "organization": organization_id,
            "description": description
        }
        response = await client.request("POST", "/api/v2/teams/", data=data)
        return json.dumps(response, indent=2)

@mcp.tool()
async def update_team(team_id: int, name: str = None, description: str = None) -> str:
    """Update an existing team.
    
    Args:
        team_id: ID of the team
        name: New name for the team
        description: New description
    """
    async with await get_ansible_client() as client:
        data = {}
        if name:
            data["name"] = name
        if description:
            data["description"] = description
            
        response = await client.request("PATCH", f"/api/v2/teams/{team_id}/", data=data)
        return json.dumps(response, indent=2)

@mcp.tool()
async def delete_team(team_id: int) -> str:
    """Delete a team.
    
    Args:
        team_id: ID of the team
    """
    async with await get_ansible_client() as client:
        await client.request("DELETE", f"/api/v2/teams/{team_id}/")
        return json.dumps({"status": "success", "message": f"Team {team_id} deleted"})

# MCP Tools - User Management

@mcp.tool()
async def list_users(limit: int = 100, offset: int = 0) -> str:
    """List all users.
    
    Args:
        limit: Maximum number of results to return
        offset: Number of results to skip
    """
    async with await get_ansible_client() as client:
        params = {"limit": limit, "offset": offset}
        users = await handle_pagination(client, "/api/v2/users/", params)
        return json.dumps(users, indent=2)

@mcp.tool()
async def get_user(user_id: int) -> str:
    """Get details about a specific user.
    
    Args:
        user_id: ID of the user
    """
    async with await get_ansible_client() as client:
        user = await client.request("GET", f"/api/v2/users/{user_id}/")
        return json.dumps(user, indent=2)

@mcp.tool()
async def create_user(
    username: str,
    password: str,
    first_name: str = "",
    last_name: str = "",
    email: str = "",
    is_superuser: bool = False,
    is_system_auditor: bool = False
) -> str:
    """Create a new user.
    
    Args:
        username: Username for the new user
        password: Password for the new user
        first_name: First name of the user
        last_name: Last name of the user
        email: Email address of the user
        is_superuser: Whether the user should be a superuser
        is_system_auditor: Whether the user should be a system auditor
    """
    async with await get_ansible_client() as client:
        data = {
            "username": username,
            "password": password,
            "first_name": first_name,
            "last_name": last_name,
            "email": email,
            "is_superuser": is_superuser,
            "is_system_auditor": is_system_auditor
        }
        response = await client.request("POST", "/api/v2/users/", data=data)
        return json.dumps(response, indent=2)

@mcp.tool()
async def update_user(
    user_id: int,
    username: str = None,
    password: str = None,
    first_name: str = None,
    last_name: str = None,
    email: str = None,
    is_superuser: bool = None,
    is_system_auditor: bool = None
) -> str:
    """Update an existing user.
    
    Args:
        user_id: ID of the user
        username: New username
        password: New password
        first_name: New first name
        last_name: New last name
        email: New email address
        is_superuser: Whether the user should be a superuser
        is_system_auditor: Whether the user should be a system auditor
    """
    async with await get_ansible_client() as client:
        data = {}
        if username:
            data["username"] = username
        if password:
            data["password"] = password
        if first_name is not None:
            data["first_name"] = first_name
        if last_name is not None:
            data["last_name"] = last_name
        if email:
            data["email"] = email
        if is_superuser is not None:
            data["is_superuser"] = is_superuser
        if is_system_auditor is not None:
            data["is_system_auditor"] = is_system_auditor
            
        response = await client.request("PATCH", f"/api/v2/users/{user_id}/", data=data)
        return json.dumps(response, indent=2)

@mcp.tool()
async def delete_user(user_id: int) -> str:
    """Delete a user.
    
    Args:
        user_id: ID of the user
    """
    async with await get_ansible_client() as client:
        await client.request("DELETE", f"/api/v2/users/{user_id}/")
        return json.dumps({"status": "success", "message": f"User {user_id} deleted"})

# MCP Tools - Ad Hoc Commands

@mcp.tool()
async def run_ad_hoc_command(
    inventory_id: int,
    credential_id: int,
    module_name: str,
    module_args: str,
    limit: str = "",
    verbosity: int = 0
) -> str:
    """Run an ad hoc command.
    
    Args:
        inventory_id: ID of the inventory
        credential_id: ID of the credential
        module_name: Module name (e.g., command, shell, ping)
        module_args: Module arguments
        limit: Host pattern to target
        verbosity: Verbosity level (0-4)
    """
    if verbosity not in range(5):
        return json.dumps({"status": "error", "message": "Verbosity must be between 0 and 4"})
    
    async with await get_ansible_client() as client:
        data = {
            "inventory": inventory_id,
            "credential": credential_id,
            "module_name": module_name,
            "module_args": module_args,
            "verbosity": verbosity
        }
        
        if limit:
            data["limit"] = limit
            
        response = await client.request("POST", "/api/v2/ad_hoc_commands/", data=data)
        return json.dumps(response, indent=2)

@mcp.tool()
async def get_ad_hoc_command(command_id: int) -> str:
    """Get details about a specific ad hoc command.
    
    Args:
        command_id: ID of the ad hoc command
    """
    async with await get_ansible_client() as client:
        command = await client.request("GET", f"/api/v2/ad_hoc_commands/{command_id}/")
        return json.dumps(command, indent=2)

@mcp.tool()
async def cancel_ad_hoc_command(command_id: int) -> str:
    """Cancel a running ad hoc command.
    
    Args:
        command_id: ID of the ad hoc command
    """
    async with await get_ansible_client() as client:
        response = await client.request("POST", f"/api/v2/ad_hoc_commands/{command_id}/cancel/")
        return json.dumps(response, indent=2)

# MCP Tools - Workflow Templates

@mcp.tool()
async def list_workflow_templates(limit: int = 100, offset: int = 0) -> str:
    """List all workflow templates.
    
    Args:
        limit: Maximum number of results to return
        offset: Number of results to skip
    """
    async with await get_ansible_client() as client:
        params = {"limit": limit, "offset": offset}
        templates = await handle_pagination(client, "/api/v2/workflow_job_templates/", params)
        return json.dumps(templates, indent=2)

@mcp.tool()
async def get_workflow_template(template_id: int) -> str:
    """Get details about a specific workflow template.
    
    Args:
        template_id: ID of the workflow template
    """
    async with await get_ansible_client() as client:
        template = await client.request("GET", f"/api/v2/workflow_job_templates/{template_id}/")
        return json.dumps(template, indent=2)

@mcp.tool()
async def launch_workflow(template_id: int, extra_vars: str = None) -> str:
    """Launch a workflow from a workflow template.
    
    Args:
        template_id: ID of the workflow template
        extra_vars: JSON string of extra variables to override the template's variables
    """
    if extra_vars:
        try:
            # Validate that extra_vars is a proper JSON string
            json.loads(extra_vars)
        except json.JSONDecodeError:
            return json.dumps({"status": "error", "message": "Invalid JSON in extra_vars"})
    
    async with await get_ansible_client() as client:
        data = {}
        if extra_vars:
            data["extra_vars"] = extra_vars
            
        response = await client.request("POST", f"/api/v2/workflow_job_templates/{template_id}/launch/", data=data)
        return json.dumps(response, indent=2)

# MCP Tools - Workflow Jobs

@mcp.tool()
async def list_workflow_jobs(status: str = None, limit: int = 100, offset: int = 0) -> str:
    """List all workflow jobs, optionally filtered by status.
    
    Args:
        status: Filter by job status (pending, waiting, running, successful, failed, canceled)
        limit: Maximum number of results to return
        offset: Number of results to skip
    """
    async with await get_ansible_client() as client:
        params = {"limit": limit, "offset": offset}
        if status:
            params["status"] = status
            
        jobs = await handle_pagination(client, "/api/v2/workflow_jobs/", params)
        return json.dumps(jobs, indent=2)

@mcp.tool()
async def get_workflow_job(job_id: int) -> str:
    """Get details about a specific workflow job.
    
    Args:
        job_id: ID of the workflow job
    """
    async with await get_ansible_client() as client:
        job = await client.request("GET", f"/api/v2/workflow_jobs/{job_id}/")
        return json.dumps(job, indent=2)

@mcp.tool()
async def cancel_workflow_job(job_id: int) -> str:
    """Cancel a running workflow job.
    
    Args:
        job_id: ID of the workflow job
    """
    async with await get_ansible_client() as client:
        response = await client.request("POST", f"/api/v2/workflow_jobs/{job_id}/cancel/")
        return json.dumps(response, indent=2)

# MCP Tools - Schedule Management

@mcp.tool()
async def list_schedules(unified_job_template_id: int = None, limit: int = 100, offset: int = 0) -> str:
    """List schedules, optionally filtered by job template.
    
    Args:
        unified_job_template_id: Optional ID of job or workflow template to filter schedules
        limit: Maximum number of results to return
        offset: Number of results to skip
    """
    async with await get_ansible_client() as client:
        params = {"limit": limit, "offset": offset}
        
        if unified_job_template_id:
            params["unified_job_template"] = unified_job_template_id
            
        schedules = await handle_pagination(client, "/api/v2/schedules/", params)
        return json.dumps(schedules, indent=2)

@mcp.tool()
async def get_schedule(schedule_id: int) -> str:
    """Get details about a specific schedule.
    
    Args:
        schedule_id: ID of the schedule
    """
    async with await get_ansible_client() as client:
        schedule = await client.request("GET", f"/api/v2/schedules/{schedule_id}/")
        return json.dumps(schedule, indent=2)

@mcp.tool()
async def create_schedule(
    name: str,
    unified_job_template_id: int,
    rrule: str,
    description: str = "",
    extra_data: str = "{}"
) -> str:
    """Create a new schedule.
    
    Args:
        name: Name of the schedule
        unified_job_template_id: ID of the job or workflow template
        rrule: iCal recurrence rule (e.g., "DTSTART:20231001T120000Z RRULE:FREQ=DAILY;INTERVAL=1")
        description: Description of the schedule
        extra_data: JSON string of extra variables
    """
    try:
        # Validate that extra_data is a proper JSON string
        json.loads(extra_data)
    except json.JSONDecodeError:
        return json.dumps({"status": "error", "message": "Invalid JSON in extra_data"})
    
    async with await get_ansible_client() as client:
        data = {
            "name": name,
            "unified_job_template": unified_job_template_id,
            "rrule": rrule,
            "description": description,
            "extra_data": json.loads(extra_data)
        }
            
        response = await client.request("POST", "/api/v2/schedules/", data=data)
        return json.dumps(response, indent=2)

@mcp.tool()
async def update_schedule(
    schedule_id: int,
    name: str = None,
    rrule: str = None,
    description: str = None,
    extra_data: str = None
) -> str:
    """Update an existing schedule.
    
    Args:
        schedule_id: ID of the schedule
        name: New name for the schedule
        rrule: New iCal recurrence rule
        description: New description
        extra_data: JSON string of extra variables
    """
    if extra_data:
        try:
            # Validate that extra_data is a proper JSON string
            json.loads(extra_data)
        except json.JSONDecodeError:
            return json.dumps({"status": "error", "message": "Invalid JSON in extra_data"})
    
    async with await get_ansible_client() as client:
        data = {}
        if name:
            data["name"] = name
        if rrule:
            data["rrule"] = rrule
        if description:
            data["description"] = description
        if extra_data:
            data["extra_data"] = json.loads(extra_data)
            
        response = await client.request("PATCH", f"/api/v2/schedules/{schedule_id}/", data=data)
        return json.dumps(response, indent=2)

@mcp.tool()
async def delete_schedule(schedule_id: int) -> str:
    """Delete a schedule.
    
    Args:
        schedule_id: ID of the schedule
    """
    async with await get_ansible_client() as client:
        await client.request("DELETE", f"/api/v2/schedules/{schedule_id}/")
        return json.dumps({"status": "success", "message": f"Schedule {schedule_id} deleted"})

# MCP Tools - System Information

@mcp.tool()
async def get_ansible_version() -> str:
    """Get Ansible Tower/AWX version information."""
    async with await get_ansible_client() as client:
        info = await client.request("GET", "/api/v2/ping/")
        return json.dumps(info, indent=2)

@mcp.tool()
async def get_dashboard_stats() -> str:
    """Get dashboard statistics."""
    async with await get_ansible_client() as client:
        stats = await client.request("GET", "/api/v2/dashboard/")
        return json.dumps(stats, indent=2)

@mcp.tool()
async def get_metrics() -> str:
    """Get system metrics."""
    async with await get_ansible_client() as client:
        metrics = await client.request("GET", "/api/v2/metrics/")
        return json.dumps(metrics, indent=2)

# Main entry point
if __name__ == "__main__":
    # Initialize and run the server
    mcp.run(transport='stdio')