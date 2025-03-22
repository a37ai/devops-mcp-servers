import os
import json
import logging
import requests
from mcp.server.fastmcp import FastMCP, Context

# Set up logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger("puppet-mcp")

# Create an MCP server
mcp = FastMCP("Puppet MCP Server")

# Helper function for authenticated requests to Puppet API
def puppet_request(ctx: Context, method: str, endpoint: str, data=None, params=None, headers=None) -> dict:
    """Make an authenticated request to the Puppet API"""
    puppet_url = os.environ.get("PUPPET_URL")
    auth_token = os.environ.get("PUPPET_AUTH_TOKEN")
    
    if not auth_token:
        raise ValueError("PUPPET_AUTH_TOKEN environment variable is not set")
    
    url = f"{puppet_url}{endpoint}"
    
    if headers is None:
        headers = {}
    headers["X-Authentication"] = auth_token
    
    try:
        response = requests.request(
            method=method,
            url=url,
            json=data,
            params=params,
            headers=headers
        )
        response.raise_for_status()
        return response.json()
    except requests.exceptions.RequestException as e:
        logger.error(f"Request failed: {str(e)}")
        raise

# Resources

@mcp.resource("puppet://environments")
def list_environments(ctx: Context) -> str:
    """List all available Puppet environments"""
    result = puppet_request(ctx, "GET", "/puppet/v3/environments")
    return json.dumps(result, indent=2)

@mcp.resource("puppet://nodes/{certname}")
def get_node(certname: str, ctx: Context) -> str:
    """Get node information by certname"""
    result = puppet_request(ctx, "GET", f"/puppet/v3/nodes/{certname}")
    return json.dumps(result, indent=2)

@mcp.resource("puppet://facts/{certname}")
def get_facts(certname: str, ctx: Context) -> str:
    """Get facts for a specific node"""
    result = puppet_request(ctx, "GET", f"/puppet/v3/facts/{certname}")
    return json.dumps(result, indent=2)

# Tools

@mcp.tool()
def run_puppet(nodes: list[str], ctx: Context, environment: str = "production", noop: bool = False) -> str:
    """Run Puppet on specific nodes"""
    endpoint = "/orchestrator/v1/command/deploy"
    data = {
        "environment": environment,
        "scope": {
            "nodes": nodes
        },
        "noop": noop
    }
    
    result = puppet_request(ctx, "POST", endpoint, data=data)
    return json.dumps(result, indent=2)

@mcp.tool()
def query_puppetdb(query: str, ctx: Context) -> str:
    """Run a PuppetDB query"""
    endpoint = "/pdb/query/v4"
    params = {"query": query}
    
    result = puppet_request(ctx, "GET", endpoint, params=params)
    return json.dumps(result, indent=2)

# Main function
if __name__ == "__main__":
    if not os.environ.get("PUPPET_URL") or not os.environ.get("PUPPET_AUTH_TOKEN"):
        logger.error("Missing required environment variables: PUPPET_URL and PUPPET_AUTH_TOKEN")
        logger.error("Please set these environment variables before running the server.")
        logger.error("Example:")
        logger.error("  export PUPPET_URL=https://puppet.example.com:4433")
        logger.error("  export PUPPET_AUTH_TOKEN=your_auth_token_here")
    else:
        mcp.run()
