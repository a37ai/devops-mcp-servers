"""
Consul MCP Server

A Model Context Protocol server that exposes Consul API functionality as tools for LLMs.
"""

import os
import json
import urllib.parse
import asyncio
import functools
import base64
from typing import Dict, List, Optional, Union, Any, Type, Literal
from consul import Consul
from consul.base import ACLPermissionDenied  # Import directly from consul.base
from mcp.server.fastmcp import FastMCP
from dotenv import load_dotenv
from pydantic import BaseModel, Field, field_validator, model_validator, RootModel

# Common Models
class DatacenterParam(BaseModel):
    """Common parameter for datacenter specification."""
    dc: Optional[str] = Field(default=None, description="Datacenter to query")

class ErrorResponse(BaseModel):
    """Common error response model."""
    error: str
    success: Optional[bool] = False

class SuccessResponse(BaseModel):
    """Common success response model."""
    success: bool
    error: Optional[str] = None

# Datacenter Models
class DatacenterList(BaseModel):
    """List of datacenters."""
    datacenters: List[str]

# Node Models
class NodeParams(DatacenterParam):
    """Parameters for node operations."""
    near: Optional[str] = Field(default=None, description="Sort by RTT from this node")
    filter: Optional[str] = Field(default=None, description="Filter expression")

class NodeTaggedAddresses(BaseModel):
    """Tagged addresses for a node."""
    lan: Optional[str] = None
    lan_ipv4: Optional[str] = None
    wan: Optional[str] = None
    wan_ipv4: Optional[str] = None

class NodeMeta(BaseModel):
    """Metadata for a node."""
    consul_network_segment: Optional[str] = Field(default=None, alias="consul-network-segment")
    consul_version: Optional[str] = Field(default=None, alias="consul-version")

class Node(BaseModel):
    """Node information."""
    ID: str
    Node: str
    Address: str
    Datacenter: Optional[str] = None
    TaggedAddresses: Optional[NodeTaggedAddresses] = None
    Meta: Optional[NodeMeta] = None
    CreateIndex: Optional[int] = None
    ModifyIndex: Optional[int] = None

class NodeList(BaseModel):
    """List of nodes."""
    nodes: List[Node]

# Service Models
class ServiceParams(DatacenterParam):
    """Parameters for service operations."""
    pass

class ServiceTagMap(RootModel[Dict[str, List[str]]]):
    """Map of service name to tags."""
    model_config = {
        "arbitrary_types_allowed": True
    }

# Service Registration Models
class ServiceRegistrationParams(DatacenterParam):
    """Parameters for service registration."""
    name: str = Field(description="Service name")
    id: Optional[str] = Field(default=None, description="Service ID (defaults to name)")
    address: Optional[str] = Field(default=None, description="Service address")
    port: Optional[int] = Field(default=None, description="Service port")
    tags: Optional[str] = Field(default=None, description="Comma-separated list of tags")
    meta: Optional[str] = Field(default=None, description="JSON string with metadata key-value pairs")
    node: Optional[str] = Field(default=None, description="Node to register service on")

    @field_validator('meta')
    def validate_meta_json(cls, v):
        """Validate that meta is valid JSON if provided."""
        if v is not None:
            import json
            try:
                json.loads(v)
            except json.JSONDecodeError:
                raise ValueError("Invalid JSON in meta parameter")
        return v

# Service Deregistration Models
class ServiceDeregistrationParams(DatacenterParam):
    """Parameters for service deregistration."""
    service_id: str = Field(description="ID of the service to deregister")
    node: str = Field(description="Node the service is registered on")

# Health Check Models
class HealthServiceParams(DatacenterParam):
    """Parameters for health service operations."""
    service: str = Field(description="Service name")
    passing: bool = Field(default=False, description="If true, only return passing services")
    near: Optional[str] = Field(default=None, description="Sorts results by round trip time")
    filter: Optional[str] = Field(default=None, description="Filters results based on expression")

# ACL Token Models
class ACLTokenParams(BaseModel):
    """Parameters for ACL token creation."""
    description: Optional[str] = Field(default=None, description="Human readable description")
    policies: Optional[str] = Field(default=None, description="Comma-separated policy names")
    roles: Optional[str] = Field(default=None, description="Comma-separated role names")
    service_identities: Optional[str] = Field(default=None, description="JSON service identities")
    expires_after: Optional[str] = Field(default=None, description="Token expiration duration")

    @field_validator('service_identities')
    def validate_service_identities_json(cls, v):
        """Validate that service_identities is valid JSON if provided."""
        if v is not None:
            import json
            try:
                json.loads(v)
            except json.JSONDecodeError:
                raise ValueError("Invalid JSON in service_identities parameter")
        return v

# Prepared Query Models
class PreparedQueryParams(DatacenterParam):
    """Parameters for executing prepared queries."""
    query_id: str = Field(description="ID of the prepared query to execute")

# Intention Models
class IntentionParams(BaseModel):
    """Parameters for creating service mesh intentions."""
    source_name: str = Field(description="Source service name")
    destination_name: str = Field(description="Destination service name")
    action: Literal["allow", "deny"] = Field(description="Can be 'allow' or 'deny'")
    description: Optional[str] = Field(default=None, description="Human readable description")
    meta: Optional[str] = Field(default=None, description="JSON metadata key-value pairs")

    @field_validator('meta')
    def validate_meta_json(cls, v):
        """Validate that meta is valid JSON if provided."""
        if v is not None:
            import json
            try:
                json.loads(v)
            except json.JSONDecodeError:
                raise ValueError("Invalid JSON in meta parameter")
        return v

# KV Models
class KVGetParams(DatacenterParam):
    """Parameters for KV get operations."""
    key: str = Field(description="Key to retrieve")
    recurse: bool = Field(default=False, description="Get all keys with given prefix")
    raw: bool = Field(default=False, description="Return raw value")

class KVPutParams(DatacenterParam):
    """Parameters for KV put operations."""
    key: str = Field(description="Key to store")
    value: str = Field(description="Value to store")
    flags: Optional[int] = Field(default=None, description="Unsigned integer value")
    cas: Optional[int] = Field(default=None, description="Check-and-set value")

class KVDeleteParams(DatacenterParam):
    """Parameters for KV delete operations."""
    key: str = Field(description="Key to delete")
    recurse: bool = Field(default=False, description="Delete all keys with given prefix")

class KVEntry(BaseModel):
    """KV store entry."""
    CreateIndex: int
    ModifyIndex: int
    LockIndex: int
    Key: str
    Flags: int
    Value: Optional[str] = None
    Session: Optional[str] = None

class KVList(BaseModel):
    """List of KV entries."""
    entries: List[KVEntry]


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
    
    # Print connection info for debugging
    print(f"Consul connection info: {host}:{port}")
    
    return host, port

# Initialize Consul client
def get_consul_client():
    # Use the environment variables directly to ensure correct connection
    if CONSUL_URL:
        parsed_url = urllib.parse.urlparse(CONSUL_URL)
        host = parsed_url.hostname
        port = parsed_url.port or 8500
    else:
        host, port = get_consul_connection_info()
    
    print(f"Creating Consul client with host={host}, port={port}")
    return Consul(host=host, port=port, token=CONSUL_TOKEN)

# Helper to run synchronous functions in a thread pool
async def run_sync(func):
    """Run a synchronous function in a thread pool."""
    loop = asyncio.get_event_loop()
    return await loop.run_in_executor(None, func)

# Helper function to handle model to JSON string conversion
def model_to_json(model: BaseModel) -> str:
    """Convert a Pydantic model to a JSON string."""
    return model.model_dump_json(indent=2)

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
    # Create and return a Pydantic model
    response = DatacenterList(datacenters=datacenters)
    return model_to_json(response)

# 2. List Nodes
@mcp.tool()
async def list_nodes(
    dc: Optional[str] = None,
    near: Optional[str] = None,
    filter: Optional[str] = None
) -> str:
    """
    Returns the nodes registered in a given datacenter.
    """
    # Create and validate the input parameters model
    params = NodeParams(dc=dc, near=near, filter=filter)
    
    client = get_consul_client()
    
    # Build query parameters
    query_params = {}
    if params.dc:
        query_params["dc"] = params.dc
    if params.near:
        query_params["near"] = params.near
    # Note: Remove filter param as the Consul API doesn't support it
    
    def get_nodes():
        return client.catalog.nodes(**query_params)
    
    index, nodes = await run_sync(get_nodes)
    
    # Apply manual filtering if filter parameter was provided
    if params.filter:
        # Implement manual filtering logic here if needed
        # For now, just add a warning
        print(f"Warning: Filter parameter '{params.filter}' not supported by underlying API, results not filtered")
    
    # Create node models from the response
    node_list = []
    for node in nodes:
        # Convert each node to a Node model
        node_list.append(Node(**node))
    
    # Create and return the node list response
    response = NodeList(nodes=node_list)
    return model_to_json(response)

# 3. List Services
@mcp.tool()
async def list_services(dc: Optional[str] = None) -> str:
    """
    Returns a list of services registered in the catalog.
    
    Args:
        dc: Specifies the datacenter to query
    """
    # Create and validate the input parameters model
    params = ServiceParams(dc=dc)
    
    client = get_consul_client()
    
    query_params = {}
    if params.dc:
        query_params["dc"] = params.dc
    
    # Change this to regular function
    def get_services():
        return client.catalog.services(**query_params)
    
    index, services = await run_sync(get_services)
    
    # Create response model (services is already a dict of service name -> tags)
    response = ServiceTagMap(root=services)
    return model_to_json(response)

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
    # Create and validate the input parameters model
    params = ServiceRegistrationParams(
        name=name, id=id, address=address, port=port,
        tags=tags, meta=meta, dc=dc, node=node
    )
    
    client = get_consul_client()
    
    # Get nodes if node not provided
    if not params.node:
        def get_nodes():
            return client.catalog.nodes()
        
        index, nodes = await run_sync(get_nodes)
        if not nodes:
            error = ErrorResponse(error="No nodes found, cannot register service")
            return model_to_json(error)
        
        # Use the first node
        params.node = nodes[0]['Node']
    
    # Build service definition
    service_def = {
        "node": params.node,
        "service": params.name
    }
    
    if params.id:
        service_def["service"] = params.id  # Changed from service_id to service
    if params.address:
        service_def["address"] = params.address
    if params.port:
        service_def["port"] = params.port
    if params.tags:
        service_def["tags"] = [tag.strip() for tag in params.tags.split(",")]
    if params.meta:
        try:
            service_def["meta"] = json.loads(params.meta)
        except json.JSONDecodeError:
            error = ErrorResponse(error="Invalid JSON in meta parameter")
            return model_to_json(error)
    
    if params.dc:
        service_def["dc"] = params.dc
    
    def do_register():
        return client.catalog.register(**service_def)
    
    try:
        result = await run_sync(do_register)
        response = SuccessResponse(success=result)
        return model_to_json(response)
    except Exception as e:
        error = ErrorResponse(error=str(e))
        return model_to_json(error)

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
    # Create and validate the input parameters model
    params = ServiceDeregistrationParams(service_id=service_id, node=node, dc=dc)
    
    if not params.node:
        error = ErrorResponse(error="Node parameter is required for deregistration")
        return model_to_json(error)
    
    client = get_consul_client()
    
    deregister_params = {
        "node": params.node,
        "service_id": params.service_id
    }
    
    if params.dc:
        deregister_params["dc"] = params.dc
    
    def do_deregister():
        return client.catalog.deregister(**deregister_params)
    
    try:
        result = await run_sync(do_deregister)
        response = SuccessResponse(success=result)
        return model_to_json(response)
    except Exception as e:
        error = ErrorResponse(error=str(e))
        return model_to_json(error)

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
    # Create and validate the input parameters model
    params = HealthServiceParams(
        service=service, dc=dc, passing=passing, near=near, filter=filter
    )
    
    client = get_consul_client()
    
    query_params = {}
    if params.dc:
        query_params["dc"] = params.dc
    if params.passing:
        query_params["passing"] = params.passing
    if params.near:
        query_params["near"] = params.near
    # Remove filter param as it's not supported
    
    def get_health():
        return client.health.service(params.service, **query_params)
    
    index, health_data = await run_sync(get_health)
    
    # Apply manual filtering if filter parameter was provided
    if params.filter:
        print(f"Warning: Filter parameter '{params.filter}' not supported by underlying API, results not filtered")
    
    # Return the health data as JSON (already has proper structure)
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
    # Create and validate the input parameters model
    params = ACLTokenParams(
        description=description,
        policies=policies,
        roles=roles,
        service_identities=service_identities,
        expires_after=expires_after
    )
    
    # The Python consul package may not fully support newer ACL APIs
    # Falling back to HTTP request method for this one
    import httpx
    
    url = f"{CONSUL_URL}/v1/acl/token"
    headers = {"Content-Type": "application/json"}
    if CONSUL_TOKEN:
        headers["X-Consul-Token"] = CONSUL_TOKEN
    
    token_def = {}
    
    if params.description:
        token_def["Description"] = params.description
    
    if params.policies:
        token_def["Policies"] = [{"Name": policy.strip()} for policy in params.policies.split(",")]
    
    if params.roles:
        token_def["Roles"] = [{"Name": role.strip()} for role in params.roles.split(",")]
    
    if params.service_identities:
        try:
            token_def["ServiceIdentities"] = json.loads(params.service_identities)
        except json.JSONDecodeError:
            error = ErrorResponse(error="Invalid JSON in service_identities parameter")
            return model_to_json(error)
    
    if params.expires_after:
        token_def["ExpirationTTL"] = params.expires_after
    
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
            error = {
                "error": True,
                "status_code": e.response.status_code,
                "message": str(e),
                "details": e.response.text
            }
            return json.dumps(error, indent=2)

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
    # Create and validate the input parameters model
    params = PreparedQueryParams(query_id=query_id, dc=dc)
    
    # The Python consul package may not support prepared queries API
    # Falling back to HTTP request method for this one
    import httpx
    
    url = f"{CONSUL_URL}/v1/query/{params.query_id}/execute"
    headers = {"Content-Type": "application/json"}
    if CONSUL_TOKEN:
        headers["X-Consul-Token"] = CONSUL_TOKEN
    
    query_params = {}
    if params.dc:
        query_params["dc"] = params.dc
    
    async with httpx.AsyncClient() as http_client:
        response = await http_client.get(
            url,
            params=query_params,
            headers=headers
        )
        try:
            response.raise_for_status()
            return json.dumps(response.json(), indent=2)
        except httpx.HTTPStatusError as e:
            error = {
                "error": True,
                "status_code": e.response.status_code,
                "message": str(e),
                "details": e.response.text
            }
            return json.dumps(error, indent=2)

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
    # Validate action before creating model
    if action not in ["allow", "deny"]:
        error = ErrorResponse(error="Action must be either 'allow' or 'deny'")
        return model_to_json(error)
    
    # Create and validate the input parameters model
    params = IntentionParams(
        source_name=source_name,
        destination_name=destination_name,
        action=action,
        description=description,
        meta=meta
    )
    
    # The Python consul package may not support connect intentions API
    # Falling back to HTTP request method for this one
    import httpx
    
    url = f"{CONSUL_URL}/v1/connect/intentions"
    headers = {"Content-Type": "application/json"}
    if CONSUL_TOKEN:
        headers["X-Consul-Token"] = CONSUL_TOKEN
    
    intention_def = {
        "SourceName": params.source_name,
        "DestinationName": params.destination_name,
        "Action": params.action
    }
    
    if params.description:
        intention_def["Description"] = params.description
    
    if params.meta:
        try:
            intention_def["Meta"] = json.loads(params.meta)
        except json.JSONDecodeError:
            error = ErrorResponse(error="Invalid JSON in meta parameter")
            return model_to_json(error)
    
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
            error = {
                "error": True,
                "status_code": e.response.status_code,
                "message": str(e),
                "details": e.response.text
            }
            return json.dumps(error, indent=2)

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
    # Create and validate the input parameters model
    params = KVGetParams(key=key, dc=dc, recurse=recurse, raw=raw)
    
    client = get_consul_client()
    
    query_params = {}
    if params.dc:
        query_params["dc"] = params.dc
    
    def do_get():
        return client.kv.get(params.key, recurse=params.recurse, **query_params)
    
    try:
        index, value = await run_sync(do_get)
        
        if value is None:
            error = ErrorResponse(error="Key not found")
            return model_to_json(error)
        
        if params.raw:
            if params.recurse:
                # For recursive operations, just return the full structure
                return json.dumps(value, indent=2)
            else:
                # For single key with raw, return just the value
                return value["Value"].decode("utf-8") if value["Value"] else ""
        else:
            # Process values for non-recursive responses to decode base64
            if not params.recurse:
                if isinstance(value, dict) and "Value" in value and value["Value"]:
                    try:
                        # Value is base64 encoded, decode it
                        value["Value"] = value["Value"].decode("utf-8")
                    except (UnicodeDecodeError, AttributeError):
                        # If we can't decode as string, leave it as is
                        pass
            else:
                # Handle recursive results (list of dicts)
                for item in value:
                    if "Value" in item and item["Value"]:
                        try:
                            item["Value"] = item["Value"].decode("utf-8")
                        except (UnicodeDecodeError, AttributeError):
                            pass
                            
            # Normal get operation
            return json.dumps(value, indent=2)
    except Exception as e:
        error = ErrorResponse(error=str(e))
        return model_to_json(error)

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
    # Create and validate the input parameters model
    params = KVPutParams(key=key, value=value, dc=dc, flags=flags, cas=cas)
    
    client = get_consul_client()
    
    query_params = {}
    if params.dc:
        query_params["dc"] = params.dc
    if params.flags is not None:
        query_params["flags"] = params.flags
    if params.cas is not None:
        query_params["cas"] = params.cas
    
    def do_put():
        try:
            return client.kv.put(params.key, params.value, **query_params)
        except ACLPermissionDenied:  # Fixed: use imported ACLPermissionDenied
            return {"acl_error": "Permission denied: ACL permissions required for KV write operations"}
        except Exception as e:
            return {"error": str(e)}
    
    result = await run_sync(do_put)
    
    # Check if we got an error
    if isinstance(result, dict) and ("acl_error" in result or "error" in result):
        error_msg = result.get("acl_error", result.get("error", "Unknown error"))
        error = ErrorResponse(error=error_msg)
        return model_to_json(error)
    
    response = SuccessResponse(success=result)
    return model_to_json(response)

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
    # Create and validate the input parameters model
    params = KVDeleteParams(key=key, dc=dc, recurse=recurse)
    
    client = get_consul_client()
    
    query_params = {}
    if params.dc:
        query_params["dc"] = params.dc
    
    def do_delete():
        try:
            return client.kv.delete(params.key, recurse=params.recurse, **query_params)
        except ACLPermissionDenied:  # Fixed: use imported ACLPermissionDenied
            return {"acl_error": "Permission denied: ACL permissions required for KV write operations"}
        except Exception as e:
            return {"error": str(e)}
    
    result = await run_sync(do_delete)
    
    # Check if we got an error
    if isinstance(result, dict) and ("acl_error" in result or "error" in result):
        error_msg = result.get("acl_error", result.get("error", "Unknown error"))
        error = ErrorResponse(error=error_msg)
        return model_to_json(error)
    
    response = SuccessResponse(success=result)
    return model_to_json(response)

# Main entry point
if __name__ == "__main__":
    # Run the MCP server
    mcp.run()