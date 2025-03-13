from mcp.server.fastmcp import FastMCP
import httpx
import os
from typing import Optional, Dict, List, Any, Union
from dotenv import load_dotenv
import json
import logging

# Load environment variables from .env file
load_dotenv()

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger("elk-mcp-server")

# Configuration
ELK_BASE_URL = os.getenv("ELK_BASE_URL", "http://localhost:9200")
ELK_USERNAME = os.getenv("ELK_USERNAME", "")
ELK_PASSWORD = os.getenv("ELK_PASSWORD", "")

# Create MCP server instance
mcp = FastMCP("elk-mcp-server")

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
    
    # Add authentication if provided
    if ELK_USERNAME and ELK_PASSWORD:
        auth = (ELK_USERNAME, ELK_PASSWORD)
    else:
        auth = None
    
    try:
        async with httpx.AsyncClient(auth=auth, timeout=30.0) as client:
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
                raise {
                    "status": status,
                    "message": f"Elasticsearch error: {status}",
                    "details": response_data,
                }
    except Exception as error:
        logger.error(f"Error making ELK request: {error}")
        raise error

# Format and sanitize a response for the LLM
def format_response(data: Any) -> str:
    if isinstance(data, str):
        return data
    
    try:
        return json.dumps(data, indent=2)
    except Exception as error:
        return f"Error formatting response: {str(error)}"

# =============================================================================
# 1. Cluster APIs
# =============================================================================

@mcp.tool()
async def cluster_health(
    index: Optional[str] = None, 
    timeout: Optional[str] = None,
    level: Optional[str] = None
) -> str:
    """Get Elasticsearch cluster health status.
    
    Args:
        index: Optional specific index to check health for
        timeout: Timeout for the health check (e.g., '30s')
        level: Level of health information to report (cluster, indices, shards)
    """
    try:
        path = "/_cluster/health"
        
        if index:
            path += f"/{index}"
        
        params = []
        if timeout:
            params.append(f"timeout={timeout}")
        if level:
            params.append(f"level={level}")
        
        if params:
            path += f"?{'&'.join(params)}"
        
        result = await make_elk_request(path)
        
        return format_response(result)
    except Exception as error:
        return f"Error getting cluster health: {format_response(error)}"

@mcp.tool()
async def cluster_stats(node_id: Optional[str] = None) -> str:
    """Get comprehensive statistics about the Elasticsearch cluster.
    
    Args:
        node_id: Optional specific node ID to get stats for
    """
    try:
        path = "/_cluster/stats"
        
        if node_id:
            path += f"/nodes/{node_id}"
        
        result = await make_elk_request(path)
        
        return format_response(result)
    except Exception as error:
        return f"Error getting cluster stats: {format_response(error)}"

@mcp.tool()
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
        return f"Error with cluster settings: {format_response(error)}"

# =============================================================================
# 2. Index APIs
# =============================================================================

@mcp.tool()
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
        body = {}
        
        if settings:
            body["settings"] = settings
        if mappings:
            body["mappings"] = mappings
        if aliases:
            body["aliases"] = aliases
        
        result = await make_elk_request(f"/{index_name}", "PUT", body)
        
        return format_response(result)
    except Exception as error:
        return f"Error creating index {index_name}: {format_response(error)}"

@mcp.tool()
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
        
        params = []
        if source_includes:
            params.append(f"_source_includes={source_includes}")
        if source_excludes:
            params.append(f"_source_excludes={source_excludes}")
        
        if params:
            path += f"?{'&'.join(params)}"
        
        result = await make_elk_request(path)
        
        return format_response(result)
    except Exception as error:
        return f"Error getting document: {format_response(error)}"

@mcp.tool()
async def delete_document(
    index_name: str,
    id: str,
    refresh: Optional[str] = None
) -> str:
    """Delete a document by ID.
    
    Args:
        index_name: Name of the index
        id: Document ID
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
async def bulk_operations(
    operations: str,
    index_name: Optional[str] = None,
    refresh: Optional[str] = None
) -> str:
    """Perform multiple document operations in a single request.
    
    Args:
        operations: Bulk operations in NDJSON format (each action and source doc on a new line)
        index_name: Optional default index name
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
async def count_documents(
    index_name: str,
    query: Optional[Dict[str, Any]] = None
) -> str:
    """Count documents matching a query.
    
    Args:
        index_name: Name of the index (or comma-separated list of indices)
        query: Elasticsearch query DSL object (omit to count all documents)
    """
    try:
        path = f"/{index_name}/_count"
        
        body = {"query": query} if query else None
        
        result = await make_elk_request(path, "POST", body)
        
        return format_response(result)
    except Exception as error:
        return f"Error counting documents: {format_response(error)}"

@mcp.tool()
async def multi_search(
    searches: List[Dict[str, Any]]
) -> str:
    """Perform multiple searches in a single request.
    
    Args:
        searches: Array of search requests, each containing 'index', 'query' and optional 'from', 'size' parameters
    """
    try:
        path = "/_msearch"
        
        # Format the request according to ndjson format required by _msearch
        ndjson_body = ""
        for search in searches:
            index = search.pop("index", None)
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
async def create_pipeline(
    pipeline_id: str,
    processors: List[Dict[str, Any]],
    description: Optional[str] = None
) -> str:
    """Create or update an ingest pipeline.
    
    Args:
        pipeline_id: ID of the pipeline
        processors: Array of processor definitions
        description: Description of the pipeline
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
async def get_pipeline(pipeline_id: Optional[str] = None) -> str:
    """Get an ingest pipeline.
    
    Args:
        pipeline_id: ID of the pipeline (omit to get all pipelines)
    """
    try:
        path = f"/_ingest/pipeline/{pipeline_id}" if pipeline_id else "/_ingest/pipeline"
        
        result = await make_elk_request(path)
        
        return format_response(result)
    except Exception as error:
        return f"Error getting pipeline: {format_response(error)}"

@mcp.tool()
async def delete_pipeline(pipeline_id: str) -> str:
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
async def simulate_pipeline(
    documents: List[Dict[str, Any]],
    pipeline_id: Optional[str] = None,
    pipeline: Optional[Dict[str, Any]] = None,
    verbose: bool = False
) -> str:
    """Simulate an ingest pipeline on a set of documents.
    
    Args:
        documents: Documents to process through the pipeline
        pipeline_id: ID of an existing pipeline to simulate (omit if providing inline definition)
        pipeline: Inline pipeline definition
        verbose: Return verbose results
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
async def node_info(
    node_id: Optional[str] = None,
    metrics: Optional[str] = None
) -> str:
    """Get information about nodes in the cluster.
    
    Args:
        node_id: Optional specific node ID (omit for all nodes)
        metrics: Comma-separated list of metrics to retrieve (e.g., 'jvm,os,process')
    """
    try:
        path = "/_nodes"
        
        if node_id:
            path += f"/{node_id}"
        
        if metrics:
            path += f"/{metrics}"
        
        result = await make_elk_request(path)
        
        return format_response(result)
    except Exception as error:
        return f"Error getting node info: {format_response(error)}"

@mcp.tool()
async def node_stats(
    node_id: Optional[str] = None,
    metrics: Optional[str] = None,
    index_metrics: Optional[str] = None
) -> str:
    """Get statistics about nodes in the cluster.
    
    Args:
        node_id: Optional specific node ID (omit for all nodes)
        metrics: Comma-separated list of metrics to retrieve (e.g., 'jvm,os,process')
        index_metrics: Comma-separated list of index metrics to retrieve
    """
    try:
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
        return f"Error getting node stats: {format_response(error)}"

@mcp.tool()
async def cluster_info() -> str:
    """Get basic information about the Elasticsearch cluster.
    """
    try:
        result = await make_elk_request("/")
        
        return format_response(result)
    except Exception as error:
        return f"Error getting cluster info: {format_response(error)}"

@mcp.tool()
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
        params = [f"format={format}"]
        
        if verbose:
            params.append("v=true")
        
        if headers:
            params.append(f"h={headers}")
        
        path = f"/_cat/indices?{'&'.join(params)}"
        
        result = await make_elk_request(path)
        
        return format_response(result)
    except Exception as error:
        return f"Error listing indices: {format_response(error)}"

@mcp.tool()
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
        params = [f"format={format}"]
        
        if verbose:
            params.append("v=true")
        
        if headers:
            params.append(f"h={headers}")
        
        path = f"/_cat/nodes?{'&'.join(params)}"
        
        result = await make_elk_request(path)
        
        return format_response(result)
    except Exception as error:
        return f"Error listing nodes: {format_response(error)}"

@mcp.tool()
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
        params = [f"format={format}"]
        
        if verbose:
            params.append("v=true")
        
        path = f"/_cat/aliases?{'&'.join(params)}"
        
        result = await make_elk_request(path)
        
        return format_response(result)
    except Exception as error:
        return f"Error listing aliases: {format_response(error)}"

# =============================================================================
# 7. Additional APIs (Kibana, Templates, etc.)
# =============================================================================

@mcp.tool()
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
        template: Template definition with settings, mappings, etc.
        version: Optional version number
        priority: Optional priority (higher takes precedence)
    """
    try:
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
        return f"Error creating index template: {format_response(error)}"

@mcp.tool()
async def get_index_template(name: Optional[str] = None) -> str:
    """Get index template(s).
    
    Args:
        name: Name of the template to get (omit for all templates)
    """
    try:
        path = f"/_index_template/{name}" if name else "/_index_template"
        
        result = await make_elk_request(path)
        
        return format_response(result)
    except Exception as error:
        return f"Error getting index template: {format_response(error)}"

@mcp.tool()
async def delete_index_template(name: str) -> str:
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