"""
Consul MCP Server

A Model Context Protocol server that exposes Consul API functionality as tools for LLMs.
"""

import os
import json
import httpx
from typing import Dict, List, Optional, Union, Any
from mcp.server.fastmcp import FastMCP
from dotenv import load_dotenv
load_dotenv()

# Initialize the MCP server
mcp = FastMCP("consul-server")

# Consul client configuration
CONSUL_URL = os.environ.get("CONSUL_URL")
CONSUL_TOKEN = os.environ.get("CONSUL_TOKEN")

# Common headers for Consul API requests
def get_headers():
    headers = {"Content-Type": "application/json"}
    if CONSUL_TOKEN:
        headers["X-Consul-Token"] = CONSUL_TOKEN
    return headers

# Helper function for HTTP requests
async def make_request(method, endpoint, params=None, json_data=None):
    url = f"{CONSUL_URL}{endpoint}"
    async with httpx.AsyncClient() as client:
        response = await client.request(
            method=method,
            url=url,
            params=params,
            json=json_data,
            headers=get_headers(),
            timeout=30.0
        )
        try:
            response.raise_for_status()
            if response.status_code == 204:  # No content
                return {"success": True}
            return response.json()
        except httpx.HTTPStatusError as e:
            return {
                "error": True,
                "status_code": e.response.status_code,
                "message": str(e),
                "details": e.response.text
            }

# 1. List Datacenters
@mcp.tool()
async def list_datacenters() -> str:
    """
    Returns a list of all known datacenters sorted by estimated median round trip time.
    
    This tool doesn't require any parameters.
    """
    data = await make_request("GET", "/v1/catalog/datacenters")
    return json.dumps(data, indent=2)

# 2. List Nodes
@mcp.tool()
async def list_nodes(dc: Optional[str] = None, near: Optional[str] = None, filter: Optional[str] = None) -> str:
    """
    Returns the nodes registered in a given datacenter.
    
    Args:
        dc: Specifies the datacenter to query
        near: Sorts nodes by round trip time from a specified node
        filter: Filters results based on a query expression
    """
    params = {}
    if dc:
        params["dc"] = dc
    if near:
        params["near"] = near
    if filter:
        params["filter"] = filter
    
    data = await make_request("GET", "/v1/catalog/nodes", params=params)
    return json.dumps(data, indent=2)

# 3. List Services
@mcp.tool()
async def list_services(dc: Optional[str] = None) -> str:
    """
    Returns a list of services registered in the catalog.
    
    Args:
        dc: Specifies the datacenter to query
    """
    params = {}
    if dc:
        params["dc"] = dc
    
    data = await make_request("GET", "/v1/catalog/services", params=params)
    return json.dumps(data, indent=2)

# 4. Register Service
@mcp.tool()
async def register_service(
    name: str,
    id: Optional[str] = None,
    address: Optional[str] = None,
    port: Optional[int] = None,
    tags: Optional[str] = None,
    meta: Optional[str] = None,
    dc: Optional[str] = None
) -> str:
    """
    Registers a new service with the catalog.
    
    Args:
        name: Service name
        id: Service ID (if not provided, defaults to name)
        address: Service address (defaults to node address)
        port: Service port
        tags: Comma-separated list of tags for the service
        meta: JSON string with metadata key-value pairs
        dc: Datacenter to register in
    """
    service_def = {
        "Name": name
    }
    
    if id:
        service_def["ID"] = id
    if address:
        service_def["Address"] = address
    if port:
        service_def["Port"] = port
    if tags:
        service_def["Tags"] = [tag.strip() for tag in tags.split(",")]
    if meta:
        try:
            service_def["Meta"] = json.loads(meta)
        except json.JSONDecodeError:
            return json.dumps({"error": "Invalid JSON in meta parameter"})
    
    data = {
        "Service": service_def
    }
    
    if dc:
        data["Datacenter"] = dc
    
    result = await make_request("PUT", "/v1/catalog/register", json_data=data)
    return json.dumps(result, indent=2)

# 5. Deregister Service
@mcp.tool()
async def deregister_service(
    service_id: str,
    node: Optional[str] = None, 
    dc: Optional[str] = None
) -> str:
    """
    Deregisters a service from the catalog.
    
    Args:
        service_id: ID of the service to deregister
        node: Node the service is registered on (required)
        dc: Datacenter the service is registered in
    """
    if not node:
        return json.dumps({"error": "Node parameter is required for deregistration"})
    
    data = {
        "ServiceID": service_id,
        "Node": node
    }
    
    if dc:
        data["Datacenter"] = dc
    
    result = await make_request("PUT", "/v1/catalog/deregister", json_data=data)
    return json.dumps(result, indent=2)

# 6. Health Checking
@mcp.tool()
async def health_service(
    service: str,
    dc: Optional[str] = None,
    passing: bool = False,
    near: Optional[str] = None,
    filter: Optional[str] = None
) -> str:
    """
    Returns health information for a service.
    
    Args:
        service: Service name
        dc: Datacenter to query
        passing: If true, only return passing services
        near: Sorts results by round trip time from specified node
        filter: Filters results based on a query expression
    """
    params = {}
    if dc:
        params["dc"] = dc
    if passing:
        params["passing"] = "true"
    if near:
        params["near"] = near
    if filter:
        params["filter"] = filter
    
    data = await make_request("GET", f"/v1/health/service/{service}", params=params)
    return json.dumps(data, indent=2)

# 7. Create ACL Token
@mcp.tool()
async def create_acl_token(
    description: Optional[str] = None,
    policies: Optional[str] = None,
    roles: Optional[str] = None,
    service_identities: Optional[str] = None,
    expires_after: Optional[str] = None
) -> str:
    """
    Creates a new ACL token.
    
    Args:
        description: Human readable description of the token
        policies: Comma-separated list of policy names to associate with the token
        roles: Comma-separated list of role names to associate with the token
        service_identities: JSON string with service identity definitions
        expires_after: Duration after which the token expires (e.g., "24h")
    """
    token_def = {}
    
    if description:
        token_def["Description"] = description
    
    if policies:
        token_def["Policies"] = [{"Name": policy.strip()} for policy in policies.split(",")]
    
    if roles:
        token_def["Roles"] = [{"Name": role.strip()} for role in roles.split(",")]
    
    if service_identities:
        try:
            token_def["ServiceIdentities"] = json.loads(service_identities)
        except json.JSONDecodeError:
            return json.dumps({"error": "Invalid JSON in service_identities parameter"})
    
    if expires_after:
        token_def["ExpirationTTL"] = expires_after
    
    result = await make_request("PUT", "/v1/acl/token", json_data=token_def)
    return json.dumps(result, indent=2)

# 8. Query Prepared Queries
@mcp.tool()
async def execute_prepared_query(
    query_id: str,
    dc: Optional[str] = None
) -> str:
    """
    Executes a prepared query.
    
    Args:
        query_id: ID of the prepared query to execute
        dc: Datacenter to query
    """
    params = {}
    if dc:
        params["dc"] = dc
    
    data = await make_request("GET", f"/v1/query/{query_id}/execute", params=params)
    return json.dumps(data, indent=2)

# 9. Service Mesh Intention
@mcp.tool()
async def create_intention(
    source_name: str,
    destination_name: str,
    action: str,
    description: Optional[str] = None,
    meta: Optional[str] = None
) -> str:
    """
    Creates or updates a service intention.
    
    Args:
        source_name: Source service name
        destination_name: Destination service name
        action: Can be "allow" or "deny"
        description: Human readable description
        meta: JSON string with metadata key-value pairs
    """
    if action not in ["allow", "deny"]:
        return json.dumps({"error": "Action must be either 'allow' or 'deny'"})
    
    intention_def = {
        "SourceName": source_name,
        "DestinationName": destination_name,
        "Action": action
    }
    
    if description:
        intention_def["Description"] = description
    
    if meta:
        try:
            intention_def["Meta"] = json.loads(meta)
        except json.JSONDecodeError:
            return json.dumps({"error": "Invalid JSON in meta parameter"})
    
    result = await make_request("POST", "/v1/connect/intentions", json_data=intention_def)
    return json.dumps(result, indent=2)

# 10. KV Store Operations - Get
@mcp.tool()
async def kv_get(
    key: str,
    dc: Optional[str] = None,
    recurse: bool = False,
    raw: bool = False
) -> str:
    """
    Retrieves a key-value pair from the KV store.
    
    Args:
        key: Key to retrieve
        dc: Datacenter to query
        recurse: If true, retrieves all keys with the given prefix
        raw: If true, returns just the raw value without metadata
    """
    params = {}
    if dc:
        params["dc"] = dc
    if recurse:
        params["recurse"] = "true"
    if raw:
        params["raw"] = "true"
    
    data = await make_request("GET", f"/v1/kv/{key}", params=params)
    return json.dumps(data, indent=2)

# KV Store Operations - Put
@mcp.tool()
async def kv_put(
    key: str,
    value: str,
    dc: Optional[str] = None,
    flags: Optional[int] = None,
    cas: Optional[int] = None
) -> str:
    """
    Stores a key-value pair in the KV store.
    
    Args:
        key: Key to store
        value: Value to store
        dc: Datacenter to store in
        flags: Unsigned integer value to assign to the key
        cas: Check-and-set value for optimistic locking
    """
    params = {}
    if dc:
        params["dc"] = dc
    if flags is not None:
        params["flags"] = str(flags)
    if cas is not None:
        params["cas"] = str(cas)
    
    # The value is sent as the request body, not as JSON
    async with httpx.AsyncClient() as client:
        response = await client.put(
            f"{CONSUL_URL}/v1/kv/{key}",
            params=params,
            headers=get_headers(),
            content=value,
            timeout=30.0
        )
        try:
            response.raise_for_status()
            return json.dumps({"success": response.json()}, indent=2)
        except httpx.HTTPStatusError as e:
            return json.dumps({
                "error": True,
                "status_code": e.response.status_code,
                "message": str(e),
                "details": e.response.text
            }, indent=2)

# KV Store Operations - Delete
@mcp.tool()
async def kv_delete(
    key: str,
    dc: Optional[str] = None,
    recurse: bool = False
) -> str:
    """
    Deletes a key-value pair from the KV store.
    
    Args:
        key: Key to delete
        dc: Datacenter to delete from
        recurse: If true, deletes all keys with the given prefix
    """
    params = {}
    if dc:
        params["dc"] = dc
    if recurse:
        params["recurse"] = "true"
    
    data = await make_request("DELETE", f"/v1/kv/{key}", params=params)
    return json.dumps(data, indent=2)

# Main entry point
if __name__ == "__main__":
    # Run the MCP server
    mcp.run()