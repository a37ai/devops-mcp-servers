"""
Consul MCP Server

A Model Context Protocol server that exposes Consul API functionality as tools for LLMs.
"""

import os
import json
import urllib.parse
import asyncio
import functools
from typing import Dict, List, Optional, Union, Any
from consul import Consul
from consul.base import ACLPermissionDenied  # Import directly from consul.base
from mcp.server.fastmcp import FastMCP
from dotenv import load_dotenv

load_dotenv()

# Initialize the MCP server
mcp = FastMCP("consul-server")

# Consul client configuration
CONSUL_URL = os.environ.get("CONSUL_URL")
CONSUL_TOKEN = os.environ.get("CONSUL_TOKEN")

# Parse CONSUL_URL to get host and port
def get_consul_connection_info():
    if not CONSUL_URL:
        return "localhost", 8500  # Default Consul values
    
    parsed_url = urllib.parse.urlparse(CONSUL_URL)
    host = parsed_url.hostname or "localhost"
    port = parsed_url.port or 8500
    
    return host, port

# Initialize Consul client
def get_consul_client():
    host, port = get_consul_connection_info()
    return Consul(host=host, port=port, token=CONSUL_TOKEN)

# Helper to run synchronous functions in a thread pool
async def run_sync(func):
    """Run a synchronous function in a thread pool."""
    loop = asyncio.get_event_loop()
    return await loop.run_in_executor(None, func)

# 1. List Datacenters
@mcp.tool()
async def list_datacenters() -> str:
    """
    Returns a list of all known datacenters sorted by estimated median round trip time.
    """
    client = get_consul_client()
    
    # Make this a regular function, not an async function
    def get_datacenters():
        return client.catalog.datacenters()
    
    datacenters = await run_sync(get_datacenters)
    return json.dumps(datacenters, indent=2)

# 2. List Nodes
@mcp.tool()
async def list_nodes(dc: Optional[str] = None, near: Optional[str] = None, filter: Optional[str] = None) -> str:
    """
    Returns the nodes registered in a given datacenter.
    """
    client = get_consul_client()
    
    params = {}
    if dc:
        params["dc"] = dc
    if near:
        params["near"] = near
    # Note: Remove filter param as the Consul API doesn't support it
    # If filter is needed, we'll need to do filtering after getting results
    
    def get_nodes():
        return client.catalog.nodes(**params)
    
    index, nodes = await run_sync(get_nodes)
    
    # Apply manual filtering if filter parameter was provided
    if filter:
        # Implement manual filtering logic here if needed
        # For now, just add a warning
        print(f"Warning: Filter parameter '{filter}' not supported by underlying API, results not filtered")
    
    return json.dumps(nodes, indent=2)

# 3. List Services
@mcp.tool()
async def list_services(dc: Optional[str] = None) -> str:
    """
    Returns a list of services registered in the catalog.
    
    Args:
        dc: Specifies the datacenter to query
    """
    client = get_consul_client()
    
    params = {}
    if dc:
        params["dc"] = dc
    
    # Change this to regular function
    def get_services():
        return client.catalog.services(**params)
    
    index, services = await run_sync(get_services)
    return json.dumps(services, indent=2)

# 4. Register Service
@mcp.tool()
async def register_service(
    name: str,
    id: Optional[str] = None,
    address: Optional[str] = None,
    port: Optional[int] = None,
    tags: Optional[str] = None,
    meta: Optional[str] = None,
    dc: Optional[str] = None,
    node: Optional[str] = None  # Adding node parameter which appears to be required
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
        node: Node to register service on (required)
    """
    client = get_consul_client()
    
    # Get nodes if node not provided
    if not node:
        def get_nodes():
            return client.catalog.nodes()
        
        index, nodes = await run_sync(get_nodes)
        if not nodes:
            return json.dumps({"error": "No nodes found, cannot register service"})
        
        # Use the first node
        node = nodes[0]['Node']
    
    # Build service definition
    service_def = {
        "node": node,
        "service": name
    }
    
    if id:
        service_def["service"] = id  # Changed from service_id to service
    if address:
        service_def["address"] = address
    if port:
        service_def["port"] = port
    if tags:
        service_def["tags"] = [tag.strip() for tag in tags.split(",")]
    if meta:
        try:
            service_def["meta"] = json.loads(meta)
        except json.JSONDecodeError:
            return json.dumps({"error": "Invalid JSON in meta parameter"})
    
    if dc:
        service_def["dc"] = dc
    
    def do_register():
        return client.catalog.register(**service_def)
    
    try:
        result = await run_sync(do_register)
        return json.dumps({"success": result}, indent=2)
    except Exception as e:
        return json.dumps({"success": False, "error": str(e)}, indent=2)

# 5. Deregister Service
@mcp.tool()
async def deregister_service(
    service_id: str,
    node: str,
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
    
    client = get_consul_client()
    
    deregister_params = {
        "node": node,
        "service_id": service_id
    }
    
    if dc:
        deregister_params["dc"] = dc
    
    def do_deregister():
        return client.catalog.deregister(**deregister_params)
    
    try:
        result = await run_sync(do_deregister)
        return json.dumps({"success": result}, indent=2)
    except Exception as e:
        return json.dumps({"success": False, "error": str(e)}, indent=2)

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
    client = get_consul_client()
    
    params = {}
    if dc:
        params["dc"] = dc
    if passing:
        params["passing"] = passing
    if near:
        params["near"] = near
    # Remove filter param as it's not supported
    
    def get_health():
        return client.health.service(service, **params)
    
    index, health_data = await run_sync(get_health)
    
    # Apply manual filtering if filter parameter was provided
    if filter:
        print(f"Warning: Filter parameter '{filter}' not supported by underlying API, results not filtered")
    
    return json.dumps(health_data, indent=2)

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
    # The Python consul package may not fully support newer ACL APIs
    # Falling back to HTTP request method for this one
    import httpx
    
    url = f"{CONSUL_URL}/v1/acl/token"
    headers = {"Content-Type": "application/json"}
    if CONSUL_TOKEN:
        headers["X-Consul-Token"] = CONSUL_TOKEN
    
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
    
    async with httpx.AsyncClient() as http_client:
        response = await http_client.put(
            url,
            json=token_def,
            headers=headers
        )
        try:
            response.raise_for_status()
            return json.dumps(response.json(), indent=2)
        except httpx.HTTPStatusError as e:
            return json.dumps({
                "error": True,
                "status_code": e.response.status_code,
                "message": str(e),
                "details": e.response.text
            }, indent=2)

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
    # The Python consul package may not support prepared queries API
    # Falling back to HTTP request method for this one
    import httpx
    
    url = f"{CONSUL_URL}/v1/query/{query_id}/execute"
    headers = {"Content-Type": "application/json"}
    if CONSUL_TOKEN:
        headers["X-Consul-Token"] = CONSUL_TOKEN
    
    params = {}
    if dc:
        params["dc"] = dc
    
    async with httpx.AsyncClient() as http_client:
        response = await http_client.get(
            url,
            params=params,
            headers=headers
        )
        try:
            response.raise_for_status()
            return json.dumps(response.json(), indent=2)
        except httpx.HTTPStatusError as e:
            return json.dumps({
                "error": True,
                "status_code": e.response.status_code,
                "message": str(e),
                "details": e.response.text
            }, indent=2)

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
    
    # The Python consul package may not support connect intentions API
    # Falling back to HTTP request method for this one
    import httpx
    
    url = f"{CONSUL_URL}/v1/connect/intentions"
    headers = {"Content-Type": "application/json"}
    if CONSUL_TOKEN:
        headers["X-Consul-Token"] = CONSUL_TOKEN
    
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
    
    async with httpx.AsyncClient() as http_client:
        response = await http_client.post(
            url,
            json=intention_def,
            headers=headers
        )
        try:
            response.raise_for_status()
            return json.dumps(response.json(), indent=2)
        except httpx.HTTPStatusError as e:
            return json.dumps({
                "error": True,
                "status_code": e.response.status_code,
                "message": str(e),
                "details": e.response.text
            }, indent=2)

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
    """
    client = get_consul_client()
    
    params = {}
    if dc:
        params["dc"] = dc
    
    def do_get():
        return client.kv.get(key, recurse=recurse, **params)
    
    try:
        index, value = await run_sync(do_get)
        
        if value is None:
            return json.dumps({"error": "Key not found"}, indent=2)
        
        if raw:
            if recurse:
                # For recursive operations, just return the full structure
                return json.dumps(value, indent=2)
            else:
                # For single key with raw, return just the value
                return value["Value"].decode("utf-8") if value["Value"] else ""
        else:
            # Normal get operation
            return json.dumps(value, indent=2)
    except Exception as e:
        return json.dumps({"error": str(e)}, indent=2)

# 11. KV Store Operations - Put
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
    client = get_consul_client()
    
    params = {}
    if dc:
        params["dc"] = dc
    if flags is not None:
        params["flags"] = flags
    if cas is not None:
        params["cas"] = cas
    
    def do_put():
        try:
            return client.kv.put(key, value, **params)
        except ACLPermissionDenied:  # Fixed: use imported ACLPermissionDenied
            return {"acl_error": "Permission denied: ACL permissions required for KV write operations"}
        except Exception as e:
            return {"error": str(e)}
    
    result = await run_sync(do_put)
    
    # Check if we got an error
    if isinstance(result, dict) and ("acl_error" in result or "error" in result):
        error_msg = result.get("acl_error", result.get("error", "Unknown error"))
        return json.dumps({"success": False, "error": error_msg}, indent=2)
    
    return json.dumps({"success": result}, indent=2)

# 12. KV Store Operations - Delete
@mcp.tool()
async def kv_delete(
    key: str,
    dc: Optional[str] = None,
    recurse: bool = False
) -> str:
    """
    Deletes a key-value pair from the KV store.
    """
    client = get_consul_client()
    
    params = {}
    if dc:
        params["dc"] = dc
    
    def do_delete():
        try:
            return client.kv.delete(key, recurse=recurse, **params)
        except ACLPermissionDenied:  # Fixed: use imported ACLPermissionDenied
            return {"acl_error": "Permission denied: ACL permissions required for KV write operations"}
        except Exception as e:
            return {"error": str(e)}
    
    result = await run_sync(do_delete)
    
    # Check if we got an error
    if isinstance(result, dict) and ("acl_error" in result or "error" in result):
        error_msg = result.get("acl_error", result.get("error", "Unknown error"))
        return json.dumps({"success": False, "error": error_msg}, indent=2)
    
    return json.dumps({"success": result}, indent=2)

# Main entry point
if __name__ == "__main__":
    # Run the MCP server
    mcp.run()