from mcp.server.fastmcp import FastMCP
import httpx
import os
import json
import logging
from dotenv import load_dotenv
load_dotenv()

from typing import Optional, Dict, List, Any, Union, Literal, ClassVar
from pydantic import BaseModel, Field, field_validator, model_validator, ConfigDict, ValidationError

# Base models
class BaseElasticsearchModel(BaseModel):
    """Base model for all Elasticsearch models."""
    model_config = ConfigDict(extra="forbid", populate_by_name=True)  # Prevent extra fields, allow aliases
    
class EmptyParams(BaseElasticsearchModel):
    """Empty parameter model for endpoints that don't require parameters."""
    pass

# Common parameter models
class RefreshParam(BaseModel):
    """Refresh policy parameter."""
    refresh: Optional[Literal["true", "false", "wait_for"]] = Field(
        None, 
        description="Refresh policy ('true', 'false', 'wait_for')"
    )
    
    # Constants for convenience
    TRUE: ClassVar[str] = "true"
    FALSE: ClassVar[str] = "false"
    WAIT_FOR: ClassVar[str] = "wait_for"

# Response models
class AcknowledgedResponse(BaseElasticsearchModel):
    """Common response for operations that return acknowledgement."""
    acknowledged: bool = Field(description="Whether the operation was acknowledged")

class ErrorResponse(BaseElasticsearchModel):
    """Error response model."""
    error: Dict[str, Any] = Field(description="Error details")
    status: int = Field(description="HTTP status code")

# Cluster API models
class ClusterHealthParams(BaseElasticsearchModel):
    """Parameters for cluster health API."""
    index: Optional[str] = Field(None, description="Optional specific index to check health for")
    timeout: Optional[str] = Field(None, description="Timeout for the health check (e.g., '30s')")
    level: Optional[Literal["cluster", "indices", "shards"]] = Field(
        None, 
        description="Level of health information to report"
    )

class ClusterHealthResponse(BaseElasticsearchModel):
    """Cluster health response model."""
    cluster_name: str
    status: Literal["green", "yellow", "red"]
    timed_out: bool
    number_of_nodes: int
    number_of_data_nodes: int
    active_primary_shards: int
    active_shards: int
    relocating_shards: int
    initializing_shards: int
    unassigned_shards: int
    delayed_unassigned_shards: int
    number_of_pending_tasks: int
    number_of_in_flight_fetch: int
    task_max_waiting_in_queue_millis: int
    active_shards_percent_as_number: float

class ClusterStatsParams(BaseElasticsearchModel):
    """Parameters for cluster stats API."""
    node_id: Optional[str] = Field(None, description="Optional specific node ID to get stats for")

class ClusterSettingsParams(BaseElasticsearchModel):
    """Parameters for cluster settings API."""
    action: Literal["get", "update"] = Field(description="Action to perform: 'get' or 'update'")
    settings: Optional[Dict[str, Any]] = Field(None, description="Settings to update (required for update action)")
    include_defaults: bool = Field(False, description="Whether to include default settings in the response")

# Search API models
class SearchParams(BaseElasticsearchModel):
    """Parameters for search API."""
    index_name: str = Field(description="Name of the index to search in (or comma-separated list of indices)")
    query: Dict[str, Any] = Field(description="Elasticsearch query DSL object")
    from_offset: Optional[int] = Field(None, description="Starting offset for results")
    size: Optional[int] = Field(None, description="Number of hits to return")
    sort: Optional[List[Union[str, Dict[str, Any]]]] = Field(None, description="Sort criteria")
    aggs: Optional[Dict[str, Any]] = Field(None, description="Aggregations to perform")
    source: Optional[Union[bool, List[str]]] = Field(None, description="Control which fields to include in the response")

class SearchHit(BaseElasticsearchModel):
    """Single search hit model."""
    index: str = Field(alias="_index")
    id: str = Field(alias="_id")
    score: Optional[float] = Field(None, alias="_score")
    source: Dict[str, Any] = Field(alias="_source")

class SearchResponse(BaseElasticsearchModel):
    """Search response model."""
    took: int = Field(description="Time in milliseconds for Elasticsearch to execute the search")
    timed_out: bool = Field(description="Whether the search timed out")
    shards: Dict[str, Any] = Field(description="Shard information", alias="_shards")
    hits: Dict[str, Any] = Field(description="Search hits")

    @field_validator("hits")
    def validate_hits(cls, v):
        if "total" not in v:
            raise ValueError("hits must contain total field")
        if "hits" not in v:
            raise ValueError("hits must contain hits array")
        return v

# Index API models
class CreateIndexParams(BaseElasticsearchModel):
    """Parameters for creating an index."""
    index_name: str = Field(description="Name of the index to create")
    settings: Optional[Dict[str, Any]] = Field(None, description="Optional index settings")
    mappings: Optional[Dict[str, Any]] = Field(None, description="Optional index mappings")
    aliases: Optional[Dict[str, Any]] = Field(None, description="Optional index aliases")

class GetIndexParams(BaseElasticsearchModel):
    """Parameters for getting index information."""
    index_name: str = Field(description="Name of the index to get information for")

class DeleteIndexParams(BaseElasticsearchModel):
    """Parameters for deleting an index."""
    index_name: str = Field(description="Name of the index to delete")

class GetMappingParams(BaseElasticsearchModel):
    """Parameters for getting index mapping."""
    index_name: str = Field(description="Name of the index to get mapping for")

class UpdateMappingParams(BaseElasticsearchModel):
    """Parameters for updating index mapping."""
    index_name: str = Field(description="Name of the index to update mapping for")
    properties: Dict[str, Any] = Field(description="Mapping properties to update")

class ListIndicesParams(BaseElasticsearchModel):
    """Parameters for listing indices."""
    pattern: Optional[str] = Field(None, description="Optional pattern to filter indices (e.g., 'log-*')")

# Document API models
class IndexDocumentParams(BaseElasticsearchModel, RefreshParam):
    """Parameters for indexing a document."""
    index_name: str = Field(description="Name of the index")
    document: Dict[str, Any] = Field(description="Document data")
    id: Optional[str] = Field(None, description="Optional document ID (if not provided, one will be generated)")

class GetDocumentParams(BaseElasticsearchModel):
    """Parameters for getting a document."""
    index_name: str = Field(description="Name of the index")
    id: str = Field(description="Document ID")
    source_includes: Optional[str] = Field(None, description="Comma-separated list of fields to include in the source")
    source_excludes: Optional[str] = Field(None, description="Comma-separated list of fields to exclude from the source")

class DeleteDocumentParams(BaseElasticsearchModel, RefreshParam):
    """Parameters for deleting a document."""
    index_name: str = Field(description="Name of the index")
    id: str = Field(description="Document ID")

class BulkOperationParams(BaseElasticsearchModel, RefreshParam):
    """Parameters for bulk operations."""
    operations: str = Field(description="Bulk operations in NDJSON format (each action and source doc on a new line)")
    index_name: Optional[str] = Field(None, description="Optional default index name")

# Simple search model
class SimpleSearchParams(BaseElasticsearchModel):
    """Parameters for simple search API."""
    index_name: str = Field(description="Name of the index to search in (or comma-separated list of indices)")
    keyword: str = Field(description="Search keyword or phrase")
    field: Optional[str] = Field(None, description="Field to search in (omit for full-text search across all fields)")
    size: int = Field(10, description="Number of hits to return (default: 10)")
    from_offset: int = Field(0, description="Starting offset for results (default: 0)")
    exact_match: bool = Field(False, description="Whether to perform an exact match (term query) or fuzzy match (default: False)")

class CountDocumentsParams(BaseElasticsearchModel):
    """Parameters for counting documents."""
    index_name: str = Field(description="Name of the index (or comma-separated list of indices)")
    query: Optional[Dict[str, Any]] = Field(None, description="Elasticsearch query DSL object (omit to count all documents)")

class MultiSearchParams(BaseElasticsearchModel):
    """Parameters for multi-search API."""
    searches: List[Dict[str, Any]] = Field(description="Array of search requests, each containing 'index', 'query' and optional 'from', 'size' parameters")

# Ingest API models
class CreatePipelineParams(BaseElasticsearchModel):
    """Parameters for creating an ingest pipeline."""
    pipeline_id: str = Field(description="ID of the pipeline")
    processors: List[Dict[str, Any]] = Field(description="Array of processor definitions")
    description: Optional[str] = Field(None, description="Description of the pipeline")

class GetPipelineParams(BaseElasticsearchModel):
    """Parameters for getting an ingest pipeline."""
    pipeline_id: Optional[str] = Field(None, description="ID of the pipeline (omit to get all pipelines)")

class DeletePipelineParams(BaseElasticsearchModel):
    """Parameters for deleting an ingest pipeline."""
    pipeline_id: str = Field(description="ID of the pipeline to delete")

class SimulatePipelineParams(BaseElasticsearchModel):
    """Parameters for simulating an ingest pipeline."""
    documents: List[Dict[str, Any]] = Field(description="Documents to process through the pipeline")
    pipeline_id: Optional[str] = Field(None, description="ID of an existing pipeline to simulate (omit if providing inline definition)")
    pipeline: Optional[Dict[str, Any]] = Field(None, description="Inline pipeline definition")
    verbose: bool = Field(False, description="Return verbose results")

# Info API models
class NodeInfoParams(BaseElasticsearchModel):
    """Parameters for node info API."""
    node_id: Optional[str] = Field(None, description="Optional specific node ID (omit for all nodes)")
    metrics: Optional[str] = Field(None, description="Comma-separated list of metrics to retrieve (e.g., 'jvm,os,process')")

class NodeStatsParams(BaseElasticsearchModel):
    """Parameters for node stats API."""
    node_id: Optional[str] = Field(None, description="Optional specific node ID (omit for all nodes)")
    metrics: Optional[str] = Field(None, description="Comma-separated list of metrics to retrieve (e.g., 'jvm,os,process')")
    index_metrics: Optional[str] = Field(None, description="Comma-separated list of index metrics to retrieve")

class CatIndicesParams(BaseElasticsearchModel):
    """Parameters for cat indices API."""
    format: str = Field("json", description="Output format (default: json)")
    verbose: bool = Field(True, description="Include column headers")
    headers: Optional[str] = Field(None, description="Comma-separated list of headers to include")

class CatNodesParams(BaseElasticsearchModel):
    """Parameters for cat nodes API."""
    format: str = Field("json", description="Output format (default: json)")
    verbose: bool = Field(True, description="Include column headers")
    headers: Optional[str] = Field(None, description="Comma-separated list of headers to include")

class CatAliasesParams(BaseElasticsearchModel):
    """Parameters for cat aliases API."""
    format: str = Field("json", description="Output format (default: json)")
    verbose: bool = Field(True, description="Include column headers")

# Template API models
class CreateIndexTemplateParams(BaseElasticsearchModel):
    """Parameters for creating an index template."""
    name: str = Field(description="Name of the template")
    index_patterns: List[str] = Field(description="List of index patterns this template applies to")
    template: Dict[str, Any] = Field(description="Template definition with settings, mappings, etc.")
    version: Optional[int] = Field(None, description="Optional version number")
    priority: Optional[int] = Field(None, description="Optional priority (higher takes precedence)")

class GetIndexTemplateParams(BaseElasticsearchModel):
    """Parameters for getting an index template."""
    name: Optional[str] = Field(None, description="Name of the template to get (omit for all templates)")

class DeleteIndexTemplateParams(BaseElasticsearchModel):
    """Parameters for deleting an index template."""
    name: str = Field(description="Name of the template to delete")


# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger("elk-mcp-server")

# Configuration
ELK_BASE_URL = os.getenv("ELASTICSEARCH_BASE_URL")
ELK_TOKEN = os.getenv("ELASTICSEARCH_TOKEN")

# Create MCP server instance
mcp = FastMCP("elk-mcp-server")

# Track if we're in serverless mode
is_serverless = None

# Helper function to make requests to Elasticsearch
async def make_elk_request(
    path: str,
    method: str = "GET",
    body: Any = None,
    content_type: str = "application/json"
) -> Any:
    url = f"{ELK_BASE_URL}{path}"
    
    headers = {
        "Content-Type": content_type,
    }
    
    # Add token authentication if provided
    if ELK_TOKEN:
        headers["Authorization"] = f"ApiKey {ELK_TOKEN}"
    
    try:
        async with httpx.AsyncClient(timeout=30.0) as client:
            if method == "GET":
                response = await client.get(url, headers=headers)
            elif method == "POST":
                if content_type == "application/x-ndjson":
                    response = await client.post(url, headers=headers, content=body)
                else:
                    response = await client.post(url, headers=headers, json=body if body else None)
            elif method == "PUT":
                response = await client.put(url, headers=headers, json=body if body else None)
            elif method == "DELETE":
                response = await client.delete(url, headers=headers)
            else:
                raise ValueError(f"Unsupported HTTP method: {method}")
            
            # Store status for potential error reporting
            status = response.status_code
            
            # Parse the response
            response_text = response.text
            
            try:
                response_data = response.json()
            except Exception:
                response_data = response_text
            
            # Check if response is OK (2xx status code)
            if 200 <= status < 300:
                return response_data
            else:
                error_message = f"Elasticsearch error: {status} - {response_data}"
                raise Exception(error_message)
    except Exception as error:
        logger.error(f"Error making ELK request: {error}")
        raise error

# Format and sanitize a response for the LLM
def format_response(data: Any) -> str:
    if isinstance(data, str):
        return data
    
    # Handle Pydantic models
    if hasattr(data, "model_dump"):
        data = data.model_dump()
    
    try:
        return json.dumps(data, indent=2)
    except Exception as error:
        return f"Error formatting response: {str(error)}"

# Decorator to validate function parameters using Pydantic models
def validate_params(model_class):
    """Decorator to validate function parameters using a Pydantic model.
    
    Args:
        model_class: The Pydantic model class to use for validation
    """
    def decorator(func):
        async def wrapper(*args, **kwargs):
            try:
                # Create model instance from kwargs
                params = model_class(**kwargs)
                # Update kwargs with validated values
                kwargs.update(params.model_dump())
                return await func(*args, **kwargs)
            except ValidationError as error:
                return f"Validation error: {error}"
        return wrapper
    return decorator

# Check if we're running in serverless mode
async def check_serverless_mode() -> bool:
    """Detect if the Elasticsearch instance is running in serverless mode"""
    global is_serverless
    
    if is_serverless is None:
        try:
            info = await make_elk_request("/")
            is_serverless = info.get("version", {}).get("build_flavor") == "serverless"
            logger.info(f"Detected Elasticsearch running in {'serverless' if is_serverless else 'standard'} mode")
        except Exception as error:
            logger.error(f"Error detecting serverless mode: {error}")
            is_serverless = False
    
    return is_serverless

# =============================================================================
# 1. Cluster APIs
# =============================================================================

@mcp.tool()
@validate_params(ClusterHealthParams)
async def cluster_health(
    index: Optional[str] = None,
    timeout: Optional[str] = None,
    level: Optional[str] = None
) -> str:
    """Get Elasticsearch cluster health status.
    
    Args:
        index: Optional specific index to check health for
        timeout: Timeout for the health check (e.g., '30s')
        level: Level of health information to report ("cluster", "indices", "shards")
    """
    try:
        # Check if we're in serverless mode
        serverless = await check_serverless_mode()
        if serverless:
            return "Cluster health API is not available in Elasticsearch Serverless mode"
            
        path = "/_cluster/health"
        
        if index:
            path += f"/{index}"
        
        query_params = []
        if timeout:
            query_params.append(f"timeout={timeout}")
        if level:
            query_params.append(f"level={level}")
        
        if query_params:
            path += f"?{'&'.join(query_params)}"
        
        result = await make_elk_request(path)
        
        return format_response(result)
    except Exception as error:
        if "not available when running in serverless mode" in str(error):
            return "Cluster health API is not available in Elasticsearch Serverless mode"
        return f"Error getting cluster health: {format_response(error)}"

@mcp.tool()
@validate_params(ClusterStatsParams)
async def cluster_stats(node_id: Optional[str] = None) -> str:
    """Get comprehensive statistics about the Elasticsearch cluster.
    
    Args:
        node_id: Optional specific node ID to get stats for
    """
    try:
        # Check if we're in serverless mode
        serverless = await check_serverless_mode()
        if serverless:
            return "Cluster stats API is not available in Elasticsearch Serverless mode"
            
        path = "/_cluster/stats"
        
        if node_id:
            path += f"/nodes/{node_id}"
        
        result = await make_elk_request(path)
        
        return format_response(result)
    except Exception as error:
        if "not available when running in serverless mode" in str(error):
            return "Cluster stats API is not available in Elasticsearch Serverless mode"
        return f"Error getting cluster stats: {format_response(error)}"

@mcp.tool()
@validate_params(ClusterSettingsParams)
async def cluster_settings(
    action: str,
    settings: Optional[Dict[str, Any]] = None,
    include_defaults: bool = False
) -> str:
    """Get or update cluster-wide settings.
    
    Args:
        action: Action to perform: 'get' or 'update'
        settings: Settings to update (required for update action)
        include_defaults: Whether to include default settings in the response
    """
    try:
        # Check if we're in serverless mode
        serverless = await check_serverless_mode()
        if serverless:
            return "Cluster settings API is not available in Elasticsearch Serverless mode"
            
        path = f"/_cluster/settings{'?include_defaults=true' if include_defaults else ''}"
        
        if action == "get":
            result = await make_elk_request(path)
            return format_response(result)
        elif action == "update":
            if not settings:
                return "Settings object is required for update action"
            
            result = await make_elk_request(path, "PUT", settings)
            return format_response(result)
        else:
            return f"Invalid action: {action}. Must be 'get' or 'update'."
    except Exception as error:
        if "not available when running in serverless mode" in str(error):
            return "Cluster settings API is not available in Elasticsearch Serverless mode"
        return f"Error with cluster settings: {format_response(error)}"

# =============================================================================
# 2. Index APIs
# =============================================================================

@mcp.tool()
@validate_params(CreateIndexParams)
async def create_index(
    index_name: str,
    settings: Optional[Dict[str, Any]] = None,
    mappings: Optional[Dict[str, Any]] = None,
    aliases: Optional[Dict[str, Any]] = None
) -> str:
    """Create a new Elasticsearch index.
    
    Args:
        index_name: Name of the index to create
        settings: Optional index settings
        mappings: Optional index mappings
        aliases: Optional index aliases
    """
    try:
        # Check if we're in serverless mode to remove incompatible settings
        serverless = await check_serverless_mode()
        body = {}
        
        if settings:
            # In serverless mode, remove number_of_shards and number_of_replicas
            if serverless:
                sanitized_settings = settings.copy()
                if 'number_of_shards' in sanitized_settings:
                    del sanitized_settings['number_of_shards']
                    logger.info("Removed 'number_of_shards' setting for serverless mode")
                if 'number_of_replicas' in sanitized_settings:
                    del sanitized_settings['number_of_replicas']
                    logger.info("Removed 'number_of_replicas' setting for serverless mode")
                body["settings"] = sanitized_settings
            else:
                body["settings"] = settings
                
        if mappings:
            body["mappings"] = mappings
        if aliases:
            body["aliases"] = aliases
        
        result = await make_elk_request(f"/{index_name}", "PUT", body)
        
        return format_response(result)
    except Exception as error:
        if "not available when running in serverless mode" in str(error):
            return f"Error creating index: Some settings are not available in serverless mode. Try without specifying number_of_shards and number_of_replicas."
        return f"Error creating index {index_name}: {format_response(error)}"

@mcp.tool()
@validate_params(GetIndexParams)
async def get_index(index_name: str) -> str:
    """Get information about an Elasticsearch index.
    
    Args:
        index_name: Name of the index to get information for
    """
    try:
        result = await make_elk_request(f"/{index_name}")
        
        return format_response(result)
    except Exception as error:
        return f"Error getting index {index_name}: {format_response(error)}"

@mcp.tool()
@validate_params(DeleteIndexParams)
async def delete_index(index_name: str) -> str:
    """Delete an Elasticsearch index.
    
    Args:
        index_name: Name of the index to delete
    """
    try:
        result = await make_elk_request(f"/{index_name}", "DELETE")
        
        return format_response(result)
    except Exception as error:
        return f"Error deleting index {index_name}: {format_response(error)}"

@mcp.tool()
@validate_params(GetMappingParams)
async def get_mapping(index_name: str) -> str:
    """Get the mapping for an index.
    
    Args:
        index_name: Name of the index to get mapping for
    """
    try:
        result = await make_elk_request(f"/{index_name}/_mapping")
        
        return format_response(result)
    except Exception as error:
        return f"Error getting mapping for index {index_name}: {format_response(error)}"

@mcp.tool()
@validate_params(UpdateMappingParams)
async def update_mapping(index_name: str, properties: Dict[str, Any]) -> str:
    """Update the mapping for an index.
    
    Args:
        index_name: Name of the index to update mapping for
        properties: Mapping properties to update
    """
    try:
        body = {
            "properties": properties
        }
        
        result = await make_elk_request(f"/{index_name}/_mapping", "PUT", body)
        
        return format_response(result)
    except Exception as error:
        return f"Error updating mapping for index {index_name}: {format_response(error)}"

@mcp.tool()
@validate_params(ListIndicesParams)
async def list_indices(pattern: Optional[str] = None) -> str:
    """List all indices in the Elasticsearch cluster.
    
    Args:
        pattern: Optional pattern to filter indices (e.g., 'log-*')
    """
    try:
        path = f"/_cat/indices/{pattern}" if pattern else "/_cat/indices"
        
        # Format as JSON for better readability
        result = await make_elk_request(f"{path}?format=json&v=true")
        
        return format_response(result)
    except Exception as error:
        return f"Error listing indices: {format_response(error)}"

# =============================================================================
# 3. Document APIs
# =============================================================================

@mcp.tool()
@validate_params(IndexDocumentParams)
async def index_document(
    index_name: str,
    document: Dict[str, Any],
    id: Optional[str] = None,
    refresh: Optional[str] = None
) -> str:
    """Create or update a document in an index.
    
    Args:
        index_name: Name of the index
        document: Document data
        id: Optional document ID (if not provided, one will be generated)
        refresh: Refresh policy ('true', 'false', 'wait_for')
    """
    try:
        path = f"/{index_name}/_doc"
        method = "PUT" if id else "POST"
        
        if id:
            path += f"/{id}"
        
        if refresh:
            path += f"?refresh={refresh}"
        
        result = await make_elk_request(path, method, document)
        
        return format_response(result)
    except Exception as error:
        return f"Error indexing document: {format_response(error)}"

@mcp.tool()
@validate_params(GetDocumentParams)
async def get_document(
    index_name: str,
    id: str,
    source_includes: Optional[str] = None,
    source_excludes: Optional[str] = None
) -> str:
    """Get a document by ID.
    
    Args:
        index_name: Name of the index
        id: Document ID
        source_includes: Comma-separated list of fields to include in the source
        source_excludes: Comma-separated list of fields to exclude from the source
    """
    try:
        path = f"/{index_name}/_doc/{id}"
        
        query_params = []
        if source_includes:
            query_params.append(f"_source_includes={source_includes}")
        if source_excludes:
            query_params.append(f"_source_excludes={source_excludes}")
        
        if query_params:
            path += f"?{'&'.join(query_params)}"
        
        result = await make_elk_request(path)
        
        return format_response(result)
    except Exception as error:
        return f"Error getting document: {format_response(error)}"

@mcp.tool()
@validate_params(DeleteDocumentParams)
async def delete_document(
    index_name: str,
    id: str,
    refresh: Optional[str] = None
) -> str:
    """Delete a document by ID.
    
    Args:
        index_name: Name of the index
        id: Document ID to delete
        refresh: Refresh policy ('true', 'false', 'wait_for')
    """
    try:
        path = f"/{index_name}/_doc/{id}"
        
        if refresh:
            path += f"?refresh={refresh}"
        
        result = await make_elk_request(path, "DELETE")
        
        return format_response(result)
    except Exception as error:
        return f"Error deleting document: {format_response(error)}"

@mcp.tool()
@validate_params(BulkOperationParams)
async def bulk_operations(
    operations: str,
    index_name: Optional[str] = None,
    refresh: Optional[str] = None
) -> str:
    """Perform multiple document operations in a single request.
    
    Args:
        operations: Bulk operations in NDJSON format
        index_name: Optional index name to restrict operations to
        refresh: Refresh policy ('true', 'false', 'wait_for')
    """
    try:
        path = f"/{index_name}/_bulk" if index_name else "/_bulk"
        
        if refresh:
            path += f"?refresh={refresh}"
        
        result = await make_elk_request(path, "POST", operations, "application/x-ndjson")
        
        return format_response(result)
    except Exception as error:
        return f"Error performing bulk operations: {format_response(error)}"

# =============================================================================
# 4. Search APIs
# =============================================================================

@mcp.tool()
@validate_params(SearchParams)
async def search(
    index_name: str,
    query: Dict[str, Any],
    from_offset: Optional[int] = None,
    size: Optional[int] = None,
    sort: Optional[List[Union[str, Dict[str, Any]]]] = None,
    aggs: Optional[Dict[str, Any]] = None,
    source: Optional[Union[bool, List[str]]] = None
) -> str:
    """Search for documents in an index.
    
    Args:
        index_name: Name of the index to search in (or comma-separated list of indices)
        query: Elasticsearch query DSL object
        from_offset: Starting offset for results
        size: Number of hits to return
        sort: Sort criteria
        aggs: Aggregations to perform
        source: Control which fields to include in the response
    """
    try:
        path = f"/{index_name}/_search"
        
        body = {
            "query": query
        }
        
        if from_offset is not None:
            body["from"] = from_offset
        if size is not None:
            body["size"] = size
        if sort:
            body["sort"] = sort
        if aggs:
            body["aggs"] = aggs
        if source is not None:
            body["_source"] = source
        
        result = await make_elk_request(path, "POST", body)
        
        return format_response(result)
    except Exception as error:
        return f"Error searching documents: {format_response(error)}"

@mcp.tool()
@validate_params(SimpleSearchParams)
async def simple_search(
    index_name: str,
    keyword: str,
    field: Optional[str] = None,
    size: int = 10,
    from_offset: int = 0,
    exact_match: bool = False
) -> str:
    """Simplified search interface for common search cases.
    
    Args:
        index_name: Name of the index to search in (or comma-separated list of indices)
        keyword: Search keyword or phrase
        field: Field to search in (omit for full-text search across all fields)
        size: Number of hits to return (default: 10)
        from_offset: Starting offset for results (default: 0)
        exact_match: Whether to perform an exact match (term query) or fuzzy match (default: False)
    """
    try:
        path = f"/{index_name}/_search"
        
        if field:
            if exact_match:
                query = {"term": {field: keyword}}
            else:
                query = {"match": {field: keyword}}
        else:
            if exact_match:
                query = {"multi_match": {"query": keyword, "type": "phrase"}}
            else:
                query = {"multi_match": {"query": keyword}}
        
        body = {
            "from": from_offset,
            "size": size,
            "query": query
        }
        
        result = await make_elk_request(path, "POST", body)
        
        return format_response(result)
    except Exception as error:
        return f"Error performing simple search: {format_response(error)}"

@mcp.tool()
@validate_params(CountDocumentsParams)
async def count_documents(
    index_name: str,
    query: Optional[Dict[str, Any]] = None
) -> str:
    """Count documents matching a query.
    
    Args:
        index_name: Name of the index to count documents in
        query: Elasticsearch query DSL object (defaults to match_all if not provided)
    """
    try:
        path = f"/{index_name}/_count"
        
        body = {"query": query} if query else None
        
        result = await make_elk_request(path, "POST", body)
        
        return format_response(result)
    except Exception as error:
        return f"Error counting documents: {format_response(error)}"

@mcp.tool()
@validate_params(MultiSearchParams)
async def multi_search(
    searches: List[Dict[str, Any]]
) -> str:
    """Perform multiple searches in a single request.
    
    Args:
        searches: List of search requests, each can include an 'index' key to specify the index
    """
    try:
        path = "/_msearch"
        
        # Format the request according to ndjson format required by _msearch
        ndjson_body = ""
        for search in searches:
            index = search.pop("index", None) if isinstance(search, dict) else None
            header = {"index": index} if index else {}
            ndjson_body += json.dumps(header) + "\n"
            ndjson_body += json.dumps(search) + "\n"
        
        result = await make_elk_request(path, "POST", ndjson_body, "application/x-ndjson")
        
        return format_response(result)
    except Exception as error:
        return f"Error performing multi-search: {format_response(error)}"

# =============================================================================
# 5. Ingest APIs
# =============================================================================

@mcp.tool()
@validate_params(CreatePipelineParams)
async def create_pipeline(
    pipeline_id: str,
    processors: List[Dict[str, Any]],
    description: Optional[str] = None
) -> str:
    """Create or update an ingest pipeline.
    
    Args:
        pipeline_id: ID of the pipeline
        processors: List of processor configurations
        description: Optional description of the pipeline
    """
    try:
        path = f"/_ingest/pipeline/{pipeline_id}"
        
        body = {
            "processors": processors
        }
        
        if description:
            body["description"] = description
        
        result = await make_elk_request(path, "PUT", body)
        
        return format_response(result)
    except Exception as error:
        return f"Error creating pipeline: {format_response(error)}"

@mcp.tool()
@validate_params(GetPipelineParams)
async def get_pipeline(
    pipeline_id: Optional[str] = None
) -> str:
    """Get an ingest pipeline.
    
    Args:
        pipeline_id: ID of the pipeline to retrieve (omit to get all pipelines)
    """
    try:
        path = f"/_ingest/pipeline/{pipeline_id}" if pipeline_id else "/_ingest/pipeline"
        
        result = await make_elk_request(path)
        
        return format_response(result)
    except Exception as error:
        return f"Error getting pipeline: {format_response(error)}"

@mcp.tool()
@validate_params(DeletePipelineParams)
async def delete_pipeline(
    pipeline_id: str
) -> str:
    """Delete an ingest pipeline.
    
    Args:
        pipeline_id: ID of the pipeline to delete
    """
    try:
        path = f"/_ingest/pipeline/{pipeline_id}"
        
        result = await make_elk_request(path, "DELETE")
        
        return format_response(result)
    except Exception as error:
        return f"Error deleting pipeline: {format_response(error)}"

@mcp.tool()
@validate_params(SimulatePipelineParams)
async def simulate_pipeline(
    documents: List[Dict[str, Any]],
    pipeline_id: Optional[str] = None,
    pipeline: Optional[Dict[str, Any]] = None,
    verbose: bool = False
) -> str:
    """Simulate an ingest pipeline on a set of documents.
    
    Args:
        documents: List of documents to process through the pipeline
        pipeline_id: ID of an existing pipeline to simulate
        pipeline: Pipeline definition to simulate (used if pipeline_id is not provided)
        verbose: Whether to include detailed processor results
    """
    try:
        path = "/_ingest/pipeline"
        
        if pipeline_id:
            path += f"/{pipeline_id}"
        
        path += "/_simulate"
        
        if verbose:
            path += "?verbose=true"
        
        body = {
            "docs": [{"_source": doc} for doc in documents]
        }
        
        if not pipeline_id and pipeline:
            body["pipeline"] = pipeline
        
        result = await make_elk_request(path, "POST", body)
        
        return format_response(result)
    except Exception as error:
        return f"Error simulating pipeline: {format_response(error)}"

# =============================================================================
# 6. Info APIs
# =============================================================================

@mcp.tool()
@validate_params(NodeInfoParams)
async def node_info(
    node_id: Optional[str] = None,
    metrics: Optional[str] = None
) -> str:
    """Get information about nodes in the cluster.
    
    Args:
        node_id: ID of the node to get info for (omit for all nodes)
        metrics: Specific metrics to retrieve (e.g., 'os,process')
    """
    try:
        # Check if we're in serverless mode
        serverless = await check_serverless_mode()
        if serverless:
            return "Node info API is not available in Elasticsearch Serverless mode"
            
        path = "/_nodes"
        
        if node_id:
            path += f"/{node_id}"
        
        if metrics:
            path += f"/{metrics}"
        
        result = await make_elk_request(path)
        
        return format_response(result)
    except Exception as error:
        if "not available when running in serverless mode" in str(error):
            return "Node info API is not available in Elasticsearch Serverless mode"
        return f"Error getting node info: {format_response(error)}"

@mcp.tool()
@validate_params(NodeStatsParams)
async def node_stats(
    node_id: Optional[str] = None,
    metrics: Optional[str] = None,
    index_metrics: Optional[str] = None
) -> str:
    """Get statistics about nodes in the cluster.
    
    Args:
        node_id: ID of the node to get stats for (omit for all nodes)
        metrics: Specific metrics to retrieve (e.g., 'jvm,os')
        index_metrics: Index-specific metrics to retrieve
    """
    try:
        # Check if we're in serverless mode
        serverless = await check_serverless_mode()
        if serverless:
            return "Node stats API is not available in Elasticsearch Serverless mode"
            
        path = "/_nodes"
        
        if node_id:
            path += f"/{node_id}"
        
        path += "/stats"
        
        if metrics:
            path += f"/{metrics}"
            
            if index_metrics:
                path += f"/{index_metrics}"
        
        result = await make_elk_request(path)
        
        return format_response(result)
    except Exception as error:
        if "not available when running in serverless mode" in str(error):
            return "Node stats API is not available in Elasticsearch Serverless mode"
        return f"Error getting node stats: {format_response(error)}"

@mcp.tool()
@validate_params(EmptyParams)
async def cluster_info() -> str:
    """Get basic information about the Elasticsearch cluster.
    """
    try:
        result = await make_elk_request("/")
        
        # Update our serverless detection while we're at it
        global is_serverless
        is_serverless = result.get("version", {}).get("build_flavor") == "serverless"
        
        return format_response(result)
    except Exception as error:
        return f"Error getting cluster info: {format_response(error)}"

@mcp.tool()
@validate_params(CatIndicesParams)
async def cat_indices(
    format: str = "json",
    verbose: bool = True,
    headers: Optional[str] = None
) -> str:
    """List indices in a more readable format using the _cat API.
    
    Args:
        format: Output format (default: json)
        verbose: Include column headers
        headers: Comma-separated list of headers to include
    """
    try:
        query_params = [f"format={format}"]
        
        if verbose:
            query_params.append("v=true")
        
        if headers:
            query_params.append(f"h={headers}")
        
        path = f"/_cat/indices?{'&'.join(query_params)}"
        
        result = await make_elk_request(path)
        
        return format_response(result)
    except Exception as error:
        return f"Error listing indices: {format_response(error)}"

@mcp.tool()
@validate_params(CatNodesParams)
async def cat_nodes(
    format: str = "json",
    verbose: bool = True,
    headers: Optional[str] = None
) -> str:
    """List nodes in a more readable format using the _cat API.
    
    Args:
        format: Output format (default: json)
        verbose: Include column headers
        headers: Comma-separated list of headers to include
    """
    try:
        # Check if we're in serverless mode
        serverless = await check_serverless_mode()
        if serverless:
            return "Cat nodes API is not available in Elasticsearch Serverless mode"
            
        query_params = [f"format={format}"]
        
        if verbose:
            query_params.append("v=true")
        
        if headers:
            query_params.append(f"h={headers}")
        
        path = f"/_cat/nodes?{'&'.join(query_params)}"
        
        result = await make_elk_request(path)
        
        return format_response(result)
    except Exception as error:
        if "not available when running in serverless mode" in str(error):
            return "Cat nodes API is not available in Elasticsearch Serverless mode"
        return f"Error listing nodes: {format_response(error)}"

@mcp.tool()
@validate_params(CatAliasesParams)
async def cat_aliases(
    format: str = "json",
    verbose: bool = True
) -> str:
    """List aliases in a more readable format using the _cat API.
    
    Args:
        format: Output format (default: json)
        verbose: Include column headers
    """
    try:
        query_params = [f"format={format}"]
        
        if verbose:
            query_params.append("v=true")
        
        path = f"/_cat/aliases?{'&'.join(query_params)}"
        
        result = await make_elk_request(path)
        
        return format_response(result)
    except Exception as error:
        return f"Error listing aliases: {format_response(error)}"

# =============================================================================
# 7. Additional APIs (Templates, etc.)
# =============================================================================

@mcp.tool()
@validate_params(CreateIndexTemplateParams)
async def create_index_template(
    name: str,
    index_patterns: List[str],
    template: Dict[str, Any],
    version: Optional[int] = None,
    priority: Optional[int] = None
) -> str:
    """Create or update an index template.
    
    Args:
        name: Name of the template
        index_patterns: List of index patterns this template applies to
        template: Template configuration including mappings and settings
        version: Optional version number for the template
        priority: Optional priority for the template
    """
    try:
        # Check if we're in serverless mode to remove incompatible settings
        serverless = await check_serverless_mode()
        
        if serverless and "settings" in template:
            # Remove incompatible settings
            if "number_of_shards" in template["settings"]:
                del template["settings"]["number_of_shards"]
                logger.info("Removed 'number_of_shards' from template settings for serverless mode")
            if "number_of_replicas" in template["settings"]:
                del template["settings"]["number_of_replicas"]
                logger.info("Removed 'number_of_replicas' from template settings for serverless mode")
                
        path = f"/_index_template/{name}"
        
        body = {
            "index_patterns": index_patterns,
            "template": template
        }
        
        if version is not None:
            body["version"] = version
        
        if priority is not None:
            body["priority"] = priority
        
        result = await make_elk_request(path, "PUT", body)
        
        return format_response(result)
    except Exception as error:
        if "not available when running in serverless mode" in str(error):
            return f"Error creating index template: Some settings are not available in serverless mode. Try without specifying number_of_shards and number_of_replicas."
        return f"Error creating index template: {format_response(error)}"

@mcp.tool()
@validate_params(GetIndexTemplateParams)
async def get_index_template(
    name: Optional[str] = None
) -> str:
    """Get index template(s).
    
    Args:
        name: Optional name of the template to retrieve. If not provided, all templates will be returned.
    """
    try:
        path = f"/_index_template/{name}" if name else "/_index_template"
        
        result = await make_elk_request(path)
        
        return format_response(result)
    except Exception as error:
        return f"Error getting index template: {format_response(error)}"

@mcp.tool()
@validate_params(DeleteIndexTemplateParams)
async def delete_index_template(
    name: str
) -> str:
    """Delete an index template.
    
    Args:
        name: Name of the template to delete
    """
    try:
        path = f"/_index_template/{name}"
        
        result = await make_elk_request(path, "DELETE")
        
        return format_response(result)
    except Exception as error:
        return f"Error deleting index template: {format_response(error)}"

if __name__ == "__main__":
    # Initialize and run the server
    mcp.run()