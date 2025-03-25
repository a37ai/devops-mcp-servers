import os
import requests
from urllib.parse import urljoin
import json
from typing import Dict, Any, List, Optional, Union
from mcp.server.fastmcp import FastMCP
from dotenv import load_dotenv
from pydantic import BaseModel, Field, HttpUrl

# Base response models
class JenkinsErrorResponse(BaseModel):
    error: Optional[str] = None
    statusCode: Optional[int] = None

class JenkinsSuccessResponse(BaseModel):
    status: Optional[str] = None
    statusCode: Optional[int] = None

# Jenkins Server Models
class JenkinsLabel(BaseModel):
    name: str

class JenkinsView(BaseModel):
    _class: str
    name: str
    url: str

class JenkinsJob(BaseModel):
    _class: str
    name: str
    url: str
    color: Optional[str] = None

class JenkinsLoadStatistics(BaseModel):
    _class: Optional[str] = None

class JenkinsServerInfo(BaseModel):
    _class: str
    assignedLabels: List[JenkinsLabel]
    mode: str
    nodeDescription: str
    nodeName: str
    numExecutors: int
    description: Optional[str] = None
    jobs: List[JenkinsJob]
    overallLoad: Dict[str, Any] = Field(default_factory=dict)
    primaryView: JenkinsView
    quietDownReason: Optional[str] = None
    quietingDown: bool
    slaveAgentPort: int
    unlabeledLoad: JenkinsLoadStatistics
    url: str
    useCrumbs: bool
    useSecurity: bool
    views: List[JenkinsView]

# Job Related Models
class JenkinsAction(BaseModel):
    _class: Optional[str] = None

class JenkinsSCM(BaseModel):
    _class: str

class JenkinsJobDetails(BaseModel):
    _class: str
    actions: List[JenkinsAction]
    description: Optional[str] = None
    displayName: str
    displayNameOrNull: Optional[str] = None
    fullDisplayName: str
    fullName: str
    name: str
    url: str
    buildable: bool
    builds: List[Dict[str, Any]] = Field(default_factory=list)
    color: str
    firstBuild: Optional[Dict[str, Any]] = None
    healthReport: List[Dict[str, Any]] = Field(default_factory=list)
    inQueue: bool
    keepDependencies: bool
    lastBuild: Optional[Dict[str, Any]] = None
    lastCompletedBuild: Optional[Dict[str, Any]] = None
    lastFailedBuild: Optional[Dict[str, Any]] = None
    lastStableBuild: Optional[Dict[str, Any]] = None
    lastSuccessfulBuild: Optional[Dict[str, Any]] = None
    lastUnstableBuild: Optional[Dict[str, Any]] = None
    lastUnsuccessfulBuild: Optional[Dict[str, Any]] = None
    nextBuildNumber: int
    property: List[Dict[str, Any]] = Field(default_factory=list)
    queueItem: Optional[Dict[str, Any]] = None
    concurrentBuild: bool
    disabled: bool
    downstreamProjects: List[Dict[str, Any]] = Field(default_factory=list)
    labelExpression: Optional[str] = None
    scm: JenkinsSCM
    upstreamProjects: List[Dict[str, Any]] = Field(default_factory=list)

# Build Models
class JenkinsBuildInfo(BaseModel):
    number: int
    result: Optional[str] = None
    url: str
    timestamp: int
    duration: int

class JenkinsBuildsListResponse(BaseModel):
    _class: str
    builds: List[JenkinsBuildInfo] = Field(default_factory=list)

# Plugin Models
class JenkinsPlugin(BaseModel):
    _class: Optional[str] = None

class JenkinsPluginDetails(BaseModel):
    _class: str
    plugins: List[JenkinsPlugin] = Field(default_factory=list)

# Node Models
class JenkinsExecutor(BaseModel):
    currentExecutable: Optional[Dict[str, Any]] = None

class JenkinsComputer(BaseModel):
    executors: List[JenkinsExecutor] = Field(default_factory=list)
    oneOffExecutors: List[JenkinsExecutor] = Field(default_factory=list)

class JenkinsNodeDetails(BaseModel):
    _class: str
    computer: List[JenkinsComputer] = Field(default_factory=list)

# Queue Models
class JenkinsQueueDetails(BaseModel):
    _class: str
    items: List[Dict[str, Any]] = Field(default_factory=list)

# Console Output
class JenkinsConsoleOutput(BaseModel):
    console_output: str

# Job Config
class JenkinsJobConfig(BaseModel):
    config: str

# Generic Response Type
JenkinsResponse = Union[
    JenkinsServerInfo, 
    JenkinsJobDetails, 
    JenkinsPluginDetails, 
    JenkinsNodeDetails, 
    JenkinsQueueDetails, 
    JenkinsBuildsListResponse,
    JenkinsConsoleOutput,
    JenkinsJobConfig,
    JenkinsSuccessResponse, 
    JenkinsErrorResponse
]

# Input Models for tool functions
class TriggerBuildInput(BaseModel):
    job_name: str
    parameters: Optional[Dict[str, Any]] = None

class JobNameInput(BaseModel):
    job_name: str

class BuildStatusInput(BaseModel):
    job_name: str
    build_number: Union[int, str]

class BuildsListInput(BaseModel):
    job_name: str
    limit: int = 10

class UpdateBuildDescriptionInput(BaseModel):
    job_name: str
    build_number: Union[int, str]
    description: str

class CopyJobInput(BaseModel):
    source_job_name: str
    target_job_name: str

class CreateJobInput(BaseModel):
    job_name: str
    config_xml: str

class UpdateJobConfigInput(BaseModel):
    job_name: str
    config_xml: str

class InstallPluginInput(BaseModel):
    plugin_name: str


load_dotenv()

# Initialize MCP server
mcp = FastMCP("jenkins-server")

# Jenkins configuration
JENKINS_URL = os.getenv("JENKINS_URL")
JENKINS_USER = os.getenv("JENKINS_USER")
JENKINS_API_TOKEN = os.getenv("JENKINS_API_TOKEN")
VERIFY_SSL = os.getenv("JENKINS_VERIFY_SSL", "false").lower()

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
def get_jenkins_version() -> JenkinsServerInfo:
    """Get the Jenkins server version and basic information."""
    return JenkinsServerInfo.model_validate(jenkins_request("GET", "/api/json"))

@mcp.tool()
def get_job_details(job_name: str) -> JenkinsJobDetails:
    """
    Get detailed information about a specific Jenkins job.
    
    Args:
        job_name: Name of the Jenkins job
    """
    endpoint = f"/job/{job_name}/api/json"
    return JenkinsJobDetails.model_validate(jenkins_request("GET", endpoint))

@mcp.tool()
def get_last_build_status(job_name_input: JobNameInput) -> Union[JenkinsJobDetails, JenkinsErrorResponse]:
    """
    Get the status of the last build for a specific job.
    
    Args:
        job_name_input: Job name input model
    """
    job_name = job_name_input.job_name
    endpoint = f"/job/{job_name}/lastBuild/api/json"
    result = jenkins_request("GET", endpoint)
    return JenkinsJobDetails.model_validate(result) if '_class' in result else JenkinsErrorResponse.model_validate(result)

@mcp.tool()
def trigger_build(input_data: TriggerBuildInput) -> JenkinsSuccessResponse:
    """
    Trigger a build for a specific job with optional parameters.
    
    Args:
        input_data: Build trigger input model
    """
    job_name = input_data.job_name
    parameters = input_data.parameters
    
    if parameters:
        endpoint = f"/job/{job_name}/buildWithParameters"
        return JenkinsSuccessResponse.model_validate(jenkins_request("POST", endpoint, params=parameters))
    else:
        endpoint = f"/job/{job_name}/build"
        return JenkinsSuccessResponse.model_validate(jenkins_request("POST", endpoint))

@mcp.tool()
def get_plugin_details() -> JenkinsPluginDetails:
    """Get information about all installed Jenkins plugins."""
    return JenkinsPluginDetails.model_validate(jenkins_request("GET", "/pluginManager/api/json"))

@mcp.tool()
def install_plugin(input_data: InstallPluginInput) -> JenkinsSuccessResponse:
    """
    Install a plugin in Jenkins.
    
    Args:
        input_data: Plugin installation input model
    """
    plugin_name = input_data.plugin_name
    endpoint = "/pluginManager/installNecessaryPlugins"
    xml_data = f'<jenkins><install plugin="{plugin_name}@latest" /></jenkins>'
    headers = {"Content-Type": "text/xml"}
    return JenkinsSuccessResponse.model_validate(jenkins_request("POST", endpoint, data=xml_data, headers=headers))

@mcp.tool()
def get_node_details() -> JenkinsNodeDetails:
    """Get information about all Jenkins nodes (including the master)."""
    return JenkinsNodeDetails.model_validate(jenkins_request("GET", "/computer/api/json"))

@mcp.tool()
def get_queue_details() -> JenkinsQueueDetails:
    """List items in the Jenkins build queue."""
    return JenkinsQueueDetails.model_validate(jenkins_request("GET", "/queue/api/json"))

@mcp.tool()
def create_job(input_data: CreateJobInput) -> JenkinsSuccessResponse:
    """
    Create a new Jenkins job.
    
    Args:
        input_data: Job creation input model
    """
    job_name = input_data.job_name
    config_xml = input_data.config_xml
    endpoint = "/createItem"
    params = {"name": job_name}
    headers = {"Content-Type": "text/xml"}
    return JenkinsSuccessResponse.model_validate(jenkins_request("POST", endpoint, params=params, data=config_xml, headers=headers))

@mcp.tool()
def restart_jenkins() -> JenkinsSuccessResponse:
    """Restart the Jenkins server."""
    return JenkinsSuccessResponse.model_validate(jenkins_request("POST", "/restart"))

@mcp.tool()
def get_build_status(input_data: BuildStatusInput) -> Union[JenkinsBuildInfo, JenkinsErrorResponse]:
    """
    Get the status of a specific build.
    
    Args:
        input_data: Build status input model
    """
    job_name = input_data.job_name
    build_number = input_data.build_number
    endpoint = f"/job/{job_name}/{build_number}/api/json"
    result = jenkins_request("GET", endpoint)
    return JenkinsBuildInfo.model_validate(result) if '_class' in result else JenkinsErrorResponse.model_validate(result)

@mcp.tool()
def get_last_successful_build(job_name_input: JobNameInput) -> Union[JenkinsBuildInfo, JenkinsErrorResponse]:
    """
    Get the status of the last successful build for a job.
    
    Args:
        job_name_input: Job name input model
    """
    job_name = job_name_input.job_name
    endpoint = f"/job/{job_name}/lastSuccessfulBuild/api/json"
    result = jenkins_request("GET", endpoint)
    return JenkinsBuildInfo.model_validate(result) if '_class' in result else JenkinsErrorResponse.model_validate(result)

@mcp.tool()
def get_last_failed_build(job_name_input: JobNameInput) -> Union[JenkinsBuildInfo, JenkinsErrorResponse]:
    """
    Get the status of the last failed build for a job.
    
    Args:
        job_name_input: Job name input model
    """
    job_name = job_name_input.job_name
    endpoint = f"/job/{job_name}/lastFailedBuild/api/json"
    result = jenkins_request("GET", endpoint)
    return JenkinsBuildInfo.model_validate(result) if '_class' in result else JenkinsErrorResponse.model_validate(result)

@mcp.tool()
def stop_build(input_data: BuildStatusInput) -> JenkinsSuccessResponse:
    """
    Stop a running build.
    
    Args:
        input_data: Build status input model
    """
    job_name = input_data.job_name
    build_number = input_data.build_number
    endpoint = f"/job/{job_name}/{build_number}/stop"
    return JenkinsSuccessResponse.model_validate(jenkins_request("POST", endpoint))

@mcp.tool()
def get_pipeline_description(job_name_input: JobNameInput) -> Union[Dict[str, Any], JenkinsErrorResponse]:
    """
    Get pipeline job description.
    
    Args:
        job_name_input: Job name input model
    """
    job_name = job_name_input.job_name
    endpoint = f"/job/{job_name}/wfapi"
    result = jenkins_request("GET", endpoint)
    return result if not isinstance(result, dict) or 'error' not in result else JenkinsErrorResponse.model_validate(result)

@mcp.tool()
def get_builds_list(input_data: BuildsListInput) -> JenkinsBuildsListResponse:
    """
    Get a list of builds for a job.
    
    Args:
        input_data: Builds list input model
    """
    job_name = input_data.job_name
    limit = input_data.limit
    endpoint = f"/job/{job_name}/api/json"
    params = {"tree": f"builds[number,result,url,timestamp,duration]{{0,{limit}}}"}
    return JenkinsBuildsListResponse.model_validate(jenkins_request("GET", endpoint, params=params))

@mcp.tool()
def get_running_builds() -> JenkinsNodeDetails:
    """Get information about all currently running builds."""
    return JenkinsNodeDetails.model_validate(jenkins_request("GET", "/computer/api/json?tree=computer[executors[currentExecutable[url,fullDisplayName]],oneOffExecutors[currentExecutable[url,fullDisplayName]]]"))

@mcp.tool()
def update_build_description(input_data: UpdateBuildDescriptionInput) -> JenkinsSuccessResponse:
    """
    Update the description of a build.
    
    Args:
        input_data: Update build description input model
    """
    job_name = input_data.job_name
    build_number = input_data.build_number
    description = input_data.description
    endpoint = f"/job/{job_name}/{build_number}/submitDescription"
    params = {"description": description}
    return JenkinsSuccessResponse.model_validate(jenkins_request("POST", endpoint, params=params))

@mcp.tool()
def delete_job(job_name_input: JobNameInput) -> JenkinsSuccessResponse:
    """
    Delete a Jenkins job.
    
    Args:
        job_name_input: Job name input model
    """
    job_name = job_name_input.job_name
    endpoint = f"/job/{job_name}/doDelete"
    return JenkinsSuccessResponse.model_validate(jenkins_request("POST", endpoint))

@mcp.tool()
def copy_job(input_data: CopyJobInput) -> JenkinsSuccessResponse:
    """
    Copy a Jenkins job to create a new one.
    
    Args:
        input_data: Copy job input model
    """
    source_job_name = input_data.source_job_name
    target_job_name = input_data.target_job_name
    endpoint = "/createItem"
    params = {"name": target_job_name, "mode": "copy", "from": source_job_name}
    return JenkinsSuccessResponse.model_validate(jenkins_request("POST", endpoint, params=params))

@mcp.tool()
def get_job_config(job_name_input: JobNameInput) -> Union[JenkinsJobConfig, JenkinsErrorResponse]:
    """
    Get the XML configuration of a job.
    
    Args:
        job_name_input: Job name input model
    """
    job_name = job_name_input.job_name
    endpoint = f"/job/{job_name}/config.xml"
    response = requests.get(
        urljoin(JENKINS_URL, endpoint),
        auth=(JENKINS_USER, JENKINS_API_TOKEN),
        verify=VERIFY_SSL
    )
    try:
        response.raise_for_status()
        return JenkinsJobConfig(config=response.text)
    except requests.exceptions.HTTPError as e:
        return JenkinsErrorResponse(error=str(e), statusCode=response.status_code)

@mcp.tool()
def update_job_config(input_data: UpdateJobConfigInput) -> JenkinsSuccessResponse:
    """
    Update the configuration of a job.
    
    Args:
        input_data: Update job config input model
    """
    job_name = input_data.job_name
    config_xml = input_data.config_xml
    endpoint = f"/job/{job_name}/config.xml"
    headers = {"Content-Type": "text/xml"}
    return JenkinsSuccessResponse.model_validate(jenkins_request("POST", endpoint, data=config_xml, headers=headers))

@mcp.tool()
def enable_job(job_name_input: JobNameInput) -> JenkinsSuccessResponse:
    """
    Enable a disabled Jenkins job.
    
    Args:
        job_name_input: Job name input model
    """
    job_name = job_name_input.job_name
    endpoint = f"/job/{job_name}/enable"
    return JenkinsSuccessResponse.model_validate(jenkins_request("POST", endpoint))

@mcp.tool()
def disable_job(job_name_input: JobNameInput) -> JenkinsSuccessResponse:
    """
    Disable a Jenkins job.
    
    Args:
        job_name_input: Job name input model
    """
    job_name = job_name_input.job_name
    endpoint = f"/job/{job_name}/disable"
    return JenkinsSuccessResponse.model_validate(jenkins_request("POST", endpoint))

@mcp.tool()
def get_build_console_output(input_data: BuildStatusInput) -> Union[JenkinsConsoleOutput, JenkinsErrorResponse]:
    """
    Get the console output of a specific build.
    
    Args:
        input_data: Build status input model
    """
    job_name = input_data.job_name
    build_number = input_data.build_number
    endpoint = f"/job/{job_name}/{build_number}/consoleText"
    response = requests.get(
        urljoin(JENKINS_URL, endpoint),
        auth=(JENKINS_USER, JENKINS_API_TOKEN),
        verify=VERIFY_SSL
    )
    try:
        response.raise_for_status()
        return JenkinsConsoleOutput(console_output=response.text)
    except requests.exceptions.HTTPError as e:
        return JenkinsErrorResponse(error=str(e), statusCode=response.status_code)

@mcp.tool()
def get_crumb() -> Union[Dict[str, Any], JenkinsErrorResponse]:
    """Get a CSRF protection crumb for use with POST requests."""
    result = jenkins_request("GET", "/crumbIssuer/api/json")
    return result if not isinstance(result, dict) or 'error' not in result else JenkinsErrorResponse.model_validate(result)

if __name__ == "__main__":
    print(f"Starting Jenkins MCP server, connecting to Jenkins at {JENKINS_URL}")
    mcp.run()