import os
import requests
from urllib.parse import urljoin
import json
from typing import Dict, Any, List, Optional, Union
from mcp.server.fastmcp import FastMCP
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Initialize MCP server
mcp = FastMCP("jenkins-server")

# Jenkins configuration
JENKINS_URL = os.getenv("JENKINS_URL", "http://localhost:8080")
JENKINS_USER = os.getenv("JENKINS_USER", "admin")
JENKINS_API_TOKEN = os.getenv("JENKINS_API_TOKEN", "")
VERIFY_SSL = os.getenv("JENKINS_VERIFY_SSL", "true").lower() == "true"

# Jenkins API helper functions
def jenkins_request(method: str, endpoint: str, params: Dict = None, data: Any = None, headers: Dict = None) -> Dict:
    """Make a request to Jenkins API with authentication."""
    url = urljoin(JENKINS_URL, endpoint)
    auth = (JENKINS_USER, JENKINS_API_TOKEN)
    
    default_headers = {"Content-Type": "application/json"}
    if headers:
        default_headers.update(headers)
    
    response = requests.request(
        method=method,
        url=url,
        auth=auth,
        params=params,
        data=data,
        headers=default_headers,
        verify=VERIFY_SSL
    )
    
    try:
        response.raise_for_status()
        if response.content and response.headers.get('Content-Type', '').startswith('application/json'):
            return response.json()
        return {"status": "success", "statusCode": response.status_code}
    except requests.exceptions.HTTPError as e:
        try:
            error_message = response.json()
        except:
            error_message = {"error": str(e), "statusCode": response.status_code}
        return error_message

# MCP Tools for Jenkins API

@mcp.tool()
def get_jenkins_version() -> Dict:
    """Get the Jenkins server version and basic information."""
    return jenkins_request("GET", "/api/json")

@mcp.tool()
def get_job_details(job_name: str) -> Dict:
    """
    Get detailed information about a specific Jenkins job.
    
    Args:
        job_name: Name of the Jenkins job
    """
    endpoint = f"/job/{job_name}/api/json"
    return jenkins_request("GET", endpoint)

@mcp.tool()
def get_last_build_status(job_name: str) -> Dict:
    """
    Get the status of the last build for a specific job.
    
    Args:
        job_name: Name of the Jenkins job
    """
    endpoint = f"/job/{job_name}/lastBuild/api/json"
    return jenkins_request("GET", endpoint)

@mcp.tool()
def trigger_build(job_name: str, parameters: Optional[Dict] = None) -> Dict:
    """
    Trigger a build for a specific job with optional parameters.
    
    Args:
        job_name: Name of the Jenkins job
        parameters: Optional dictionary of build parameters
    """
    if parameters:
        endpoint = f"/job/{job_name}/buildWithParameters"
        return jenkins_request("POST", endpoint, params=parameters)
    else:
        endpoint = f"/job/{job_name}/build"
        return jenkins_request("POST", endpoint)

@mcp.tool()
def get_plugin_details() -> Dict:
    """Get information about all installed Jenkins plugins."""
    return jenkins_request("GET", "/pluginManager/api/json")

@mcp.tool()
def install_plugin(plugin_name: str) -> Dict:
    """
    Install a plugin in Jenkins.
    
    Args:
        plugin_name: Name of the plugin to install
    """
    endpoint = "/pluginManager/installNecessaryPlugins"
    xml_data = f'<jenkins><install plugin="{plugin_name}@latest" /></jenkins>'
    headers = {"Content-Type": "text/xml"}
    return jenkins_request("POST", endpoint, data=xml_data, headers=headers)

@mcp.tool()
def get_node_details() -> Dict:
    """Get information about all Jenkins nodes (including the master)."""
    return jenkins_request("GET", "/computer/api/json")

@mcp.tool()
def get_queue_details() -> Dict:
    """List items in the Jenkins build queue."""
    return jenkins_request("GET", "/queue/api/json")

@mcp.tool()
def create_job(job_name: str, config_xml: str) -> Dict:
    """
    Create a new Jenkins job.
    
    Args:
        job_name: Name for the new job
        config_xml: XML configuration for the job
    """
    endpoint = "/createItem"
    params = {"name": job_name}
    headers = {"Content-Type": "text/xml"}
    return jenkins_request("POST", endpoint, params=params, data=config_xml, headers=headers)

@mcp.tool()
def restart_jenkins() -> Dict:
    """Restart the Jenkins server."""
    return jenkins_request("POST", "/restart")

@mcp.tool()
def get_build_status(job_name: str, build_number: Union[int, str]) -> Dict:
    """
    Get the status of a specific build.
    
    Args:
        job_name: Name of the Jenkins job
        build_number: Build number to retrieve
    """
    endpoint = f"/job/{job_name}/{build_number}/api/json"
    return jenkins_request("GET", endpoint)

@mcp.tool()
def get_last_successful_build(job_name: str) -> Dict:
    """
    Get the status of the last successful build for a job.
    
    Args:
        job_name: Name of the Jenkins job
    """
    endpoint = f"/job/{job_name}/lastSuccessfulBuild/api/json"
    return jenkins_request("GET", endpoint)

@mcp.tool()
def get_last_failed_build(job_name: str) -> Dict:
    """
    Get the status of the last failed build for a job.
    
    Args:
        job_name: Name of the Jenkins job
    """
    endpoint = f"/job/{job_name}/lastFailedBuild/api/json"
    return jenkins_request("GET", endpoint)

@mcp.tool()
def stop_build(job_name: str, build_number: Union[int, str]) -> Dict:
    """
    Stop a running build.
    
    Args:
        job_name: Name of the Jenkins job
        build_number: Build number to stop
    """
    endpoint = f"/job/{job_name}/{build_number}/stop"
    return jenkins_request("POST", endpoint)

@mcp.tool()
def get_pipeline_description(job_name: str) -> Dict:
    """
    Get pipeline job description.
    
    Args:
        job_name: Name of the Jenkins pipeline job
    """
    endpoint = f"/job/{job_name}/wfapi"
    return jenkins_request("GET", endpoint)

@mcp.tool()
def get_builds_list(job_name: str, limit: int = 10) -> Dict:
    """
    Get a list of builds for a job.
    
    Args:
        job_name: Name of the Jenkins job
        limit: Maximum number of builds to return
    """
    endpoint = f"/job/{job_name}/api/json"
    params = {"tree": f"builds[number,result,url,timestamp,duration]{{0,{limit}}}"}
    return jenkins_request("GET", endpoint, params=params)

@mcp.tool()
def get_running_builds() -> Dict:
    """Get information about all currently running builds."""
    return jenkins_request("GET", "/computer/api/json?tree=computer[executors[currentExecutable[url,fullDisplayName]],oneOffExecutors[currentExecutable[url,fullDisplayName]]]")

@mcp.tool()
def update_build_description(job_name: str, build_number: Union[int, str], description: str) -> Dict:
    """
    Update the description of a build.
    
    Args:
        job_name: Name of the Jenkins job
        build_number: Build number to update
        description: New description text
    """
    endpoint = f"/job/{job_name}/{build_number}/submitDescription"
    params = {"description": description}
    return jenkins_request("POST", endpoint, params=params)

@mcp.tool()
def delete_job(job_name: str) -> Dict:
    """
    Delete a Jenkins job.
    
    Args:
        job_name: Name of the Jenkins job to delete
    """
    endpoint = f"/job/{job_name}/doDelete"
    return jenkins_request("POST", endpoint)

@mcp.tool()
def copy_job(source_job_name: str, target_job_name: str) -> Dict:
    """
    Copy a Jenkins job to create a new one.
    
    Args:
        source_job_name: Name of the source job
        target_job_name: Name for the new job
    """
    endpoint = "/createItem"
    params = {"name": target_job_name, "mode": "copy", "from": source_job_name}
    return jenkins_request("POST", endpoint, params=params)

@mcp.tool()
def get_job_config(job_name: str) -> Dict:
    """
    Get the XML configuration of a job.
    
    Args:
        job_name: Name of the Jenkins job
    """
    endpoint = f"/job/{job_name}/config.xml"
    response = requests.get(
        urljoin(JENKINS_URL, endpoint),
        auth=(JENKINS_USER, JENKINS_API_TOKEN),
        verify=VERIFY_SSL
    )
    try:
        response.raise_for_status()
        return {"config": response.text}
    except requests.exceptions.HTTPError as e:
        return {"error": str(e), "statusCode": response.status_code}

@mcp.tool()
def update_job_config(job_name: str, config_xml: str) -> Dict:
    """
    Update the configuration of a job.
    
    Args:
        job_name: Name of the Jenkins job
        config_xml: New XML configuration
    """
    endpoint = f"/job/{job_name}/config.xml"
    headers = {"Content-Type": "text/xml"}
    return jenkins_request("POST", endpoint, data=config_xml, headers=headers)

@mcp.tool()
def enable_job(job_name: str) -> Dict:
    """
    Enable a disabled Jenkins job.
    
    Args:
        job_name: Name of the Jenkins job
    """
    endpoint = f"/job/{job_name}/enable"
    return jenkins_request("POST", endpoint)

@mcp.tool()
def disable_job(job_name: str) -> Dict:
    """
    Disable a Jenkins job.
    
    Args:
        job_name: Name of the Jenkins job
    """
    endpoint = f"/job/{job_name}/disable"
    return jenkins_request("POST", endpoint)

@mcp.tool()
def get_build_console_output(job_name: str, build_number: Union[int, str]) -> Dict:
    """
    Get the console output of a specific build.
    
    Args:
        job_name: Name of the Jenkins job
        build_number: Build number
    """
    endpoint = f"/job/{job_name}/{build_number}/consoleText"
    response = requests.get(
        urljoin(JENKINS_URL, endpoint),
        auth=(JENKINS_USER, JENKINS_API_TOKEN),
        verify=VERIFY_SSL
    )
    try:
        response.raise_for_status()
        return {"console_output": response.text}
    except requests.exceptions.HTTPError as e:
        return {"error": str(e), "statusCode": response.status_code}

@mcp.tool()
def get_crumb() -> Dict:
    """Get a CSRF protection crumb for use with POST requests."""
    return jenkins_request("GET", "/crumbIssuer/api/json")

if __name__ == "__main__":
    print(f"Starting Jenkins MCP server, connecting to Jenkins at {JENKINS_URL}")
    mcp.run()