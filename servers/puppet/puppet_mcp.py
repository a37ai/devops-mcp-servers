#!/usr/bin/env python3
"""
Puppet MCP Server

This server provides tools for interacting with the Puppet Enterprise API through the Model Context Protocol.
"""

import os
import json
import requests
import urllib3
from typing import Dict, List, Any, Optional, Union
from mcp.server.fastmcp import FastMCP, Context
from dotenv import load_dotenv
from pydantic import BaseModel, Field, field_validator

# Disable SSL warnings (for self-signed certificates)
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

# Pydantic Models for API validation
class PuppetResponse(BaseModel):
    """Base model for Puppet API responses."""
    status: str = "success"
    message: str | None = None
    
class PuppetErrorResponse(PuppetResponse):
    """Error response model."""
    status: str = "error"

class NodeGroupCreate(BaseModel):
    """Model for creating a node group."""
    name: str = Field(description="Name of the node group")
    description: str = Field(description="Description of the node group")
    parent_id: str = Field(description="ID of the parent group")
    environment: str = Field(default="production", description="Puppet environment to use")
    rule: List[Any] = Field(default=None, description="Rule for node matching")
    classes: Dict[str, Dict] = Field(default=None, description="Classes to apply to nodes in this group")

class NodeGroupUpdate(BaseModel):
    """Model for updating a node group."""
    group_id: str = Field(description="ID of the group to update")
    name: str | None = Field(default=None, description="New name for the group")
    description: str | None = Field(default=None, description="New description for the group")
    parent_id: str | None = Field(default=None, description="New parent group ID")
    environment: str | None = Field(default=None, description="New Puppet environment")
    rule: List[Any] | None = Field(default=None, description="New rule for node matching")
    classes: Dict[str, Dict] | None = Field(default=None, description="New classes to apply")

class HostPinParams(BaseModel):
    """Parameters for pinning hosts to a node group."""
    group_id: str = Field(description="ID of the group to pin nodes to")
    node_names: List[str] = Field(description="List of node names to pin")

# Initialize FastMCP server
mcp = FastMCP("puppet")

load_dotenv()

# Configuration
PUPPET_URL = os.getenv("PUPPET_URL")
PUPPET_TOKEN = os.getenv("PUPPET_TOKEN")

# PuppetClient class - simplified version of the PuppetAPI class
class PuppetClient:
    def __init__(self, base_url: str, auth_token: Optional[str] = None):
        """
        Initialize the Puppet client with base URL and authentication token.

        Args:
            base_url: Base URL of the Puppet Enterprise server without protocol
            auth_token: Authentication token for API access (optional)
        """
        self.base_url = base_url
        self.auth_token = auth_token
        self.headers = {"Content-Type": "application/json"}
        if auth_token:
            self.headers["X-Authentication"] = auth_token

    def check_status(self) -> Dict:
        """
        Check the status of Puppet Enterprise services.

        Returns:
            Dictionary containing status information or error.
        """
        url = f"https://{self.base_url}:4433/status/v1/services"
        try:
            response = requests.get(url, headers=self.headers, verify=False, timeout=10)
            response.raise_for_status()
            return {"status": "success", "data": response.json()}
        except requests.exceptions.RequestException as e:
            error_message = f"Failed to get status: {e}"
            return {"status": "error", "message": error_message}

    def get_certificate_statuses(self) -> Dict:
        """
        Get all certificate statuses from the Puppet CA.

        Returns:
            List of certificate status objects or error.
        """
        url = f"https://{self.base_url}:8140/puppet-ca/v1/certificate_statuses/any_key"
        try:
            response = requests.get(url, headers=self.headers, verify=False, timeout=15)
            response.raise_for_status()
            return {"status": "success", "data": response.json()}
        except requests.exceptions.RequestException as e:
            error_message = f"Failed to fetch certificate statuses: {e}"
            return {"status": "error", "message": error_message}

    def get_certificate(self, certname: str) -> Dict:
        """
        Get a specific certificate by name.

        Args:
            certname: Name of the certificate to retrieve

        Returns:
            Certificate content as string or error.
        """
        url = f"https://{self.base_url}:8140/puppet-ca/v1/certificate/{certname}"
        try:
            response = requests.get(url, headers=self.headers, verify=False, timeout=10)
            response.raise_for_status()
            return {"status": "success", "data": response.text}
        except requests.exceptions.RequestException as e:
            error_message = f"Failed to fetch certificate {certname}: {e}"
            return {"status": "error", "message": error_message}

    def get_node_groups(self) -> Dict:
        """
        Get all node classification groups.

        Returns:
            List of node group objects or error.
        """
        url = f"https://{self.base_url}:4433/classifier-api/v1/groups"
        try:
            response = requests.get(url, headers=self.headers, verify=False, timeout=10)
            response.raise_for_status()
            return {"status": "success", "data": response.json()}
        except requests.exceptions.RequestException as e:
            error_message = f"Failed to fetch node groups: {e}"
            return {"status": "error", "message": error_message}

    def get_node_group(self, group_id: str) -> Dict:
        """
        Get a specific node group by ID.

        Args:
            group_id: ID of the group to retrieve

        Returns:
            Node group object or error.
        """
        url = f"https://{self.base_url}:4433/classifier-api/v1/groups/{group_id}"
        try:
            response = requests.get(url, headers=self.headers, verify=False, timeout=10)
            response.raise_for_status()
            return {"status": "success", "data": response.json()}
        except requests.exceptions.RequestException as e:
            error_message = f"Failed to fetch node group {group_id}: {e}"
            return {"status": "error", "message": error_message}

    def create_node_group(self, name: str, description: str, parent_id: str,
                         environment: str = "production", rule: Optional[List] = None,
                         classes: Optional[Dict] = None) -> Dict:
        """
        Create a new node classification group.

        Args:
            name: Name of the group
            description: Description of the group
            parent_id: ID of the parent group
            environment: Puppet environment to use (default: production)
            rule: Rule for node matching
            classes: Classes to apply to nodes in this group

        Returns:
            Response data (usually includes group ID) or error.
        """
        if rule is None:
            rule = ["and", ["~", "name", ".*"]]  # Default rule matches all nodes

        if classes is None:
            classes = {}

        data = {
            "name": name,
            "description": description,
            "parent": parent_id,
            "environment": environment,
            "classes": classes,
            "rule": rule
        }

        url = f"https://{self.base_url}:4433/classifier-api/v1/groups"
        try:
            response = requests.post(url, headers=self.headers, json=data, verify=False, timeout=15)
            if response.status_code in [200, 201, 303]:
                try:
                    return {"status": "success", "data": response.json()}
                except json.JSONDecodeError:
                    if response.status_code == 303 and 'Location' in response.headers:
                        location_url = response.headers['Location']
                        group_id_from_header = location_url.split('/')[-1]
                        return {"status": "success", "data": {"id": group_id_from_header, "name": name}}
                    return {"status": "success", "message": f"Group {name} created successfully"}
            else:
                response.raise_for_status()
                return {"status": "error", "message": "Unknown error occurred"}
        except requests.exceptions.RequestException as e:
            error_message = f"Failed to create node group {name}: {e}"
            return {"status": "error", "message": error_message}

    def update_node_group(self, group_id: str, data: Dict) -> Dict:
        """
        Update an existing node group. Use POST with group ID.

        Args:
            group_id: ID of the group to update
            data: Updated group data (must include all required fields)

        Returns:
            Response data or error
        """
        url = f"https://{self.base_url}:4433/classifier-api/v1/groups/{group_id}"
        try:
            response = requests.post(url, headers=self.headers, json=data, verify=False, timeout=15)
            response.raise_for_status()
            try:
                return {"status": "success", "data": response.json()}
            except json.JSONDecodeError:
                return {"status": "success", "message": f"Group {group_id} updated successfully"}
        except requests.exceptions.RequestException as e:
            error_message = f"Failed to update node group {group_id}: {e}"
            return {"status": "error", "message": error_message}

    def delete_node_group(self, group_id: str) -> Dict:
        """
        Delete a node group.

        Args:
            group_id: ID of the group to delete

        Returns:
            Success or error message
        """
        url = f"https://{self.base_url}:4433/classifier-api/v1/groups/{group_id}"
        try:
            response = requests.delete(url, headers=self.headers, verify=False, timeout=10)
            if response.status_code in [200, 204]:
                return {"status": "success", "message": f"Group {group_id} deleted successfully"}
            else:
                response.raise_for_status()
                return {"status": "error", "message": "Unknown error occurred"}
        except requests.exceptions.RequestException as e:
            error_message = f"Failed to delete node group {group_id}: {e}"
            return {"status": "error", "message": error_message}

    def pin_nodes_to_group(self, group_id: str, node_names: List[str]) -> Dict:
        """
        Pin specific nodes to a node group.

        Args:
            group_id: ID of the group to pin nodes to
            node_names: List of node names to pin

        Returns:
            Success or error message
        """
        data = {"nodes": node_names}
        url = f"https://{self.base_url}:4433/classifier-api/v1/groups/{group_id}/pin"

        try:
            response = requests.post(url, headers=self.headers, json=data, verify=False, timeout=15)
            if response.status_code in [200, 201, 204]:
                return {"status": "success", "message": f"Successfully pinned {len(node_names)} node(s) to group {group_id}"}
            else:
                response.raise_for_status()
                return {"status": "error", "message": "Unknown error occurred"}
        except requests.exceptions.RequestException as e:
            error_message = f"Failed to pin nodes to group {group_id}: {e}"
            return {"status": "error", "message": error_message}

    def unpin_nodes_from_group(self, group_id: str, node_names: List[str]) -> Dict:
        """
        Unpin nodes from a group.

        Args:
            group_id: ID of the group to unpin nodes from
            node_names: List of node names to unpin

        Returns:
            Success or error message
        """
        data = {"nodes": node_names}
        url = f"https://{self.base_url}:4433/classifier-api/v1/groups/{group_id}/unpin"

        try:
            response = requests.post(url, headers=self.headers, json=data, verify=False, timeout=15)
            if response.status_code in [200, 201, 204]:
                return {"status": "success", "message": f"Successfully unpinned {len(node_names)} node(s) from group {group_id}"}
            else:
                response.raise_for_status()
                return {"status": "error", "message": "Unknown error occurred"}
        except requests.exceptions.RequestException as e:
            error_message = f"Failed to unpin nodes from group {group_id}: {e}"
            return {"status": "error", "message": error_message}

    def list_roles(self) -> Dict:
        """
        List all roles configured in RBAC.

        Returns:
            List of role objects or error.
        """
        url = f"https://{self.base_url}:4433/rbac-api/v1/roles"
        try:
            response = requests.get(url, headers=self.headers, verify=False, timeout=10)
            response.raise_for_status()
            return {"status": "success", "data": response.json()}
        except requests.exceptions.RequestException as e:
            error_message = f"Failed to fetch roles: {e}"
            return {"status": "error", "message": error_message}

    def list_users(self) -> Dict:
        """
        List all users configured in RBAC.

        Returns:
            List of user objects or error.
        """
        url = f"https://{self.base_url}:4433/rbac-api/v1/users"
        try:
            response = requests.get(url, headers=self.headers, verify=False, timeout=10)
            response.raise_for_status()
            return {"status": "success", "data": response.json()}
        except requests.exceptions.RequestException as e:
            error_message = f"Failed to fetch users: {e}"
            return {"status": "error", "message": error_message}

    def list_tasks(self) -> Dict:
        """
        List all available Puppet tasks from the orchestrator.

        Returns:
            List of task objects or error.
        """
        url = f"https://{self.base_url}:8143/orchestrator/v1/tasks"
        try:
            response = requests.get(url, headers=self.headers, verify=False, timeout=15)
            response.raise_for_status()
            return {"status": "success", "data": response.json().get("items", [])}
        except requests.exceptions.RequestException as e:
            error_message = f"Failed to fetch tasks list: {e}"
            return {"status": "error", "message": error_message}

# Helper Functions
def get_puppet_client() -> PuppetClient:
    """Get an initialized Puppet API client."""
    client = PuppetClient(
        base_url=PUPPET_URL,
        auth_token=PUPPET_TOKEN
    )
    return client

# MCP Tools - Status API Endpoints

@mcp.tool()
def check_status() -> str:
    """
    Check the status of Puppet Enterprise services.
    
    Returns:
        JSON string with status information for Puppet Enterprise services.
    """
    client = get_puppet_client()
    result = client.check_status()
    return json.dumps(result, indent=2)

# MCP Tools - Certificate API Endpoints

@mcp.tool()
def get_certificate_statuses() -> str:
    """
    Get all certificate statuses from the Puppet CA.
    
    Returns:
        JSON string with certificate status information.
    """
    client = get_puppet_client()
    result = client.get_certificate_statuses()
    return json.dumps(result, indent=2)

@mcp.tool()
def get_certificate(certname: str) -> str:
    """
    Get a specific certificate by name.
    
    Args:
        certname: Name of the certificate to retrieve
    
    Returns:
        JSON string with certificate content.
    """
    client = get_puppet_client()
    result = client.get_certificate(certname)
    return json.dumps(result, indent=2)

# MCP Tools - Node Group API Endpoints

@mcp.tool()
def get_node_groups() -> str:
    """
    Get all node classification groups.
    
    Returns:
        JSON string with node group information.
    """
    client = get_puppet_client()
    result = client.get_node_groups()
    return json.dumps(result, indent=2)

@mcp.tool()
def get_node_group(group_id: str) -> str:
    """
    Get a specific node group by ID.
    
    Args:
        group_id: ID of the group to retrieve
    
    Returns:
        JSON string with node group details.
    """
    client = get_puppet_client()
    result = client.get_node_group(group_id)
    return json.dumps(result, indent=2)

@mcp.tool()
def create_node_group(
    name: str, 
    description: str, 
    parent_id: str,
    environment: str = "production", 
    rule_json: str = None,
    classes_json: str = None
) -> str:
    """
    Create a new node classification group.
    
    Args:
        name: Name of the group
        description: Description of the group
        parent_id: ID of the parent group
        environment: Puppet environment to use (default: production)
        rule_json: JSON string of rule for node matching (default: match all nodes)
        classes_json: JSON string of classes to apply to nodes in this group
    
    Returns:
        JSON string with the created group information.
    """
    try:
        # Parse JSON inputs if provided
        rule = json.loads(rule_json) if rule_json else ["and", ["~", "name", ".*"]]
        classes = json.loads(classes_json) if classes_json else {}
        
        client = get_puppet_client()
        result = client.create_node_group(
            name=name,
            description=description,
            parent_id=parent_id,
            environment=environment,
            rule=rule,
            classes=classes
        )
        return json.dumps(result, indent=2)
    except json.JSONDecodeError as e:
        error = {"status": "error", "message": f"Invalid JSON: {str(e)}"}
        return json.dumps(error, indent=2)

@mcp.tool()
def update_node_group(
    group_id: str,
    data_json: str
) -> str:
    """
    Update an existing node group.
    
    Args:
        group_id: ID of the group to update
        data_json: JSON string of the complete group data to update
    
    Returns:
        JSON string with the update result.
    """
    try:
        data = json.loads(data_json)
        client = get_puppet_client()
        result = client.update_node_group(group_id, data)
        return json.dumps(result, indent=2)
    except json.JSONDecodeError as e:
        error = {"status": "error", "message": f"Invalid JSON: {str(e)}"}
        return json.dumps(error, indent=2)

@mcp.tool()
def delete_node_group(group_id: str) -> str:
    """
    Delete a node group.
    
    Args:
        group_id: ID of the group to delete
    
    Returns:
        JSON string with the deletion result.
    """
    client = get_puppet_client()
    result = client.delete_node_group(group_id)
    return json.dumps(result, indent=2)

@mcp.tool()
def pin_nodes_to_group(group_id: str, node_names_json: str) -> str:
    """
    Pin specific nodes to a node group.
    
    Args:
        group_id: ID of the group to pin nodes to
        node_names_json: JSON string array of node names to pin
    
    Returns:
        JSON string with the pinning result.
    """
    try:
        node_names = json.loads(node_names_json)
        if not isinstance(node_names, list):
            raise ValueError("node_names_json must be a JSON array of strings")
        
        client = get_puppet_client()
        result = client.pin_nodes_to_group(group_id, node_names)
        return json.dumps(result, indent=2)
    except (json.JSONDecodeError, ValueError) as e:
        error = {"status": "error", "message": f"Invalid input: {str(e)}"}
        return json.dumps(error, indent=2)

@mcp.tool()
def unpin_nodes_from_group(group_id: str, node_names_json: str) -> str:
    """
    Unpin nodes from a group.
    
    Args:
        group_id: ID of the group to unpin nodes from
        node_names_json: JSON string array of node names to unpin
    
    Returns:
        JSON string with the unpinning result.
    """
    try:
        node_names = json.loads(node_names_json)
        if not isinstance(node_names, list):
            raise ValueError("node_names_json must be a JSON array of strings")
        
        client = get_puppet_client()
        result = client.unpin_nodes_from_group(group_id, node_names)
        return json.dumps(result, indent=2)
    except (json.JSONDecodeError, ValueError) as e:
        error = {"status": "error", "message": f"Invalid input: {str(e)}"}
        return json.dumps(error, indent=2)

# MCP Tools - RBAC API Endpoints

@mcp.tool()
def list_roles() -> str:
    """
    List all roles configured in RBAC.
    
    Returns:
        JSON string with role information.
    """
    client = get_puppet_client()
    result = client.list_roles()
    return json.dumps(result, indent=2)

@mcp.tool()
def list_users() -> str:
    """
    List all users configured in RBAC.
    
    Returns:
        JSON string with user information.
    """
    client = get_puppet_client()
    result = client.list_users()
    return json.dumps(result, indent=2)

# MCP Tools - Task API Endpoints

@mcp.tool()
def list_tasks() -> str:
    """
    List all available Puppet tasks from the orchestrator.
    
    Returns:
        JSON string with task information.
    """
    client = get_puppet_client()
    result = client.list_tasks()
    return json.dumps(result, indent=2)

# The following functions had issues in the tests, so they're commented out

# MCP Tools - PuppetDB API Endpoints (Commented out due to timeout issues)
"""
@mcp.tool()
def get_nodes() -> str:
    '''
    Get a list of all nodes known to PuppetDB.
    
    Returns:
        JSON string with node information.
    '''
    client = get_puppet_client()
    result = client.get_nodes()
    return json.dumps(result, indent=2)

@mcp.tool()
def get_node_facts(node_name: str) -> str:
    '''
    Get facts for a specific node using PuppetDB PQL query.
    
    Args:
        node_name: Name of the node to get facts for
    
    Returns:
        JSON string with node facts.
    '''
    client = get_puppet_client()
    result = client.get_node_facts(node_name)
    return json.dumps(result, indent=2)

@mcp.tool()
def get_reports(node_name: str = None, limit: int = 10) -> str:
    '''
    Get recent reports for all or a specific node.
    
    Args:
        node_name: Optional name of node to filter reports
        limit: Maximum number of reports to return
    
    Returns:
        JSON string with report information.
    '''
    client = get_puppet_client()
    result = client.get_reports(node_name, limit)
    return json.dumps(result, indent=2)
"""

# MCP Tools - Environment API Endpoints (Commented out due to permission issues)
"""
@mcp.tool()
def list_environments() -> str:
    '''
    List all available Puppet environments.
    
    Returns:
        JSON string with environment information.
    '''
    client = get_puppet_client()
    result = client.list_environments()
    return json.dumps(result, indent=2)

@mcp.tool()
def get_environment(env_name: str) -> str:
    '''
    Get details for a specific environment.
    
    Args:
        env_name: Name of the environment
    
    Returns:
        JSON string with environment details.
    '''
    client = get_puppet_client()
    result = client.get_environment(env_name)
    return json.dumps(result, indent=2)
"""

# MCP Tools - Activity API Endpoints (Commented out due to Bad Request issues)
"""
@mcp.tool()
def get_activity_events(limit: int = 100, offset: int = 0) -> str:
    '''
    Get activity events from the PE Activity Service.
    
    Args:
        limit: Maximum number of events to return
        offset: Offset for pagination
    
    Returns:
        JSON string with activity events.
    '''
    client = get_puppet_client()
    result = client.get_activity_events(limit, offset)
    return json.dumps(result, indent=2)

@mcp.tool()
def get_activity_report(start_time: str = None, end_time: str = None) -> str:
    '''
    Get an activity report summarizing events for a time period.
    
    Args:
        start_time: Start time in ISO 8601 format (default: 24 hours ago)
        end_time: End time in ISO 8601 format (default: now)
    
    Returns:
        JSON string with activity report.
    '''
    client = get_puppet_client()
    result = client.get_activity_report(start_time, end_time)
    return json.dumps(result, indent=2)
"""

# RBAC Creation Functions (Commented out due to failures in tests)
"""
@mcp.tool()
def create_role(display_name: str, description: str, permissions_json: str, user_ids_json: str = None, group_ids_json: str = None) -> str:
    '''
    Create a new role in RBAC.
    
    Args:
        display_name: Display name for the role
        description: Role description
        permissions_json: JSON string of permission objects
        user_ids_json: JSON string array of user UUIDs to assign to this role
        group_ids_json: JSON string array of user group UUIDs to assign to this role
    
    Returns:
        JSON string with role creation result.
    '''
    try:
        permissions = json.loads(permissions_json)
        user_ids = json.loads(user_ids_json) if user_ids_json else []
        group_ids = json.loads(group_ids_json) if group_ids_json else []
        
        client = get_puppet_client()
        result = client.create_role(display_name, description, permissions, user_ids, group_ids)
        return json.dumps(result, indent=2)
    except json.JSONDecodeError as e:
        error = {"status": "error", "message": f"Invalid JSON: {str(e)}"}
        return json.dumps(error, indent=2)
"""

# Main entry point
if __name__ == "__main__":
    # Initialize and run the server
    mcp.run(transport='stdio')