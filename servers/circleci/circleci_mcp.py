"""
CircleCI MCP Server

This MCP server provides tools that map to CircleCI API endpoints,
allowing an LLM to interact with CircleCI projects, pipelines, workflows, and jobs.
"""

import os
import json
import httpx
from typing import Optional, Dict, List, Any, Union
from pydantic import BaseModel, Field
from mcp.server.fastmcp import FastMCP, Context
from dotenv import load_dotenv
load_dotenv()
# Initialize the MCP server
mcp = FastMCP("CircleCI")

# Configuration and helpers
CIRCLECI_API_BASE = os.environ.get("CIRCLECI_API_BASE", "https://circleci.com/api/v2")
CIRCLECI_API_KEY = os.environ.get("CIRCLECI_API_KEY")

if not CIRCLECI_API_KEY:
    raise ValueError("CIRCLECI_API_KEY environment variable must be set")

def get_headers():
    """Get the headers for CircleCI API requests."""
    return {
        "Circle-Token": CIRCLECI_API_KEY,
        "Content-Type": "application/json",
        "Accept": "application/json"
    }

async def make_request(method: str, endpoint: str, params: Optional[Dict] = None, data: Optional[Dict] = None) -> Dict:
    """Make a request to the CircleCI API."""
    url = f"{CIRCLECI_API_BASE}/{endpoint}"
    headers = get_headers()
    
    async with httpx.AsyncClient() as client:
        if method == "GET":
            response = await client.get(url, headers=headers, params=params)
        elif method == "POST":
            response = await client.post(url, headers=headers, json=data)
        elif method == "PUT":
            response = await client.put(url, headers=headers, json=data)
        elif method == "DELETE":
            response = await client.delete(url, headers=headers)
        elif method == "PATCH":
            response = await client.patch(url, headers=headers, json=data)
        else:
            raise ValueError(f"Unsupported HTTP method: {method}")
        
        try:
            response.raise_for_status()
            return response.json()
        except httpx.HTTPStatusError as e:
            error_message = f"HTTP Error: {e.response.status_code}"
            try:
                error_details = e.response.json()
                error_message += f" - {json.dumps(error_details)}"
            except:
                error_message += f" - {e.response.text}"
            raise Exception(error_message)

#
# Context Management Endpoints
#

@mcp.tool()
async def create_context(name: str, owner: Dict) -> Dict:
    """
    Creates a new context in CircleCI.
    
    Args:
        name: The user-defined name of the context
        owner: Object containing the owner information with 'id' and 'type' fields
              Example: {"id": "497f6eca-6276-4993-bfeb-53cbbbba6f08", "type": "organization"}
    
    Returns:
        The newly created context object
    """
    data = {
        "name": name,
        "owner": owner
    }
    return await make_request("POST", "context", data=data)

@mcp.tool()
async def list_contexts(owner_id: Optional[str] = None, owner_slug: Optional[str] = None, 
                        owner_type: Optional[str] = None, page_token: Optional[str] = None) -> Dict:
    """
    List all contexts for an owner.
    
    Args:
        owner_id: The unique ID of the owner of the context. Specify either this or owner-slug.
        owner_slug: A string that represents an organization. Specify either this or owner-id.
        owner_type: The type of the owner. Defaults to "organization". Accounts are only used as context owners in server.
        page_token: A token to retrieve the next page of results.
    
    Returns:
        A paginated list of contexts
    """
    params = {}
    if owner_id:
        params["owner-id"] = owner_id
    if owner_slug:
        params["owner-slug"] = owner_slug
    if owner_type:
        params["owner-type"] = owner_type
    if page_token:
        params["page-token"] = page_token
        
    return await make_request("GET", "context", params=params)

@mcp.tool()
async def delete_context(context_id: str) -> Dict:
    """
    Delete a context by ID.
    
    Args:
        context_id: ID of the context (UUID)
    
    Returns:
        A confirmation message
    """
    return await make_request("DELETE", f"context/{context_id}")

@mcp.tool()
async def get_context(context_id: str) -> Dict:
    """
    Returns basic information about a context.
    
    Args:
        context_id: ID of the context (UUID)
    
    Returns:
        The context details
    """
    return await make_request("GET", f"context/{context_id}")

@mcp.tool()
async def list_environment_variables(context_id: str, page_token: Optional[str] = None) -> Dict:
    """
    List information about environment variables in a context, not including their values.
    
    Args:
        context_id: ID of the context (UUID)
        page_token: A token to retrieve the next page of results.
    
    Returns:
        A paginated list of environment variables
    """
    params = {}
    if page_token:
        params["page-token"] = page_token
        
    return await make_request("GET", f"context/{context_id}/environment-variable", params=params)

@mcp.tool()
async def add_or_update_environment_variable(context_id: str, env_var_name: str, value: str) -> Dict:
    """
    Create or update an environment variable within a context.
    
    Args:
        context_id: ID of the context (UUID)
        env_var_name: The name of the environment variable
        value: The value of the environment variable
    
    Returns:
        The new environment variable information (without the value)
    """
    data = {"value": value}
    return await make_request("PUT", f"context/{context_id}/environment-variable/{env_var_name}", data=data)

@mcp.tool()
async def remove_environment_variable(context_id: str, env_var_name: str) -> Dict:
    """
    Delete an environment variable from a context.
    
    Args:
        context_id: ID of the context (UUID)
        env_var_name: The name of the environment variable
    
    Returns:
        A confirmation message
    """
    return await make_request("DELETE", f"context/{context_id}/environment-variable/{env_var_name}")

@mcp.tool()
async def get_context_restrictions(context_id: str) -> Dict:
    """
    Gets a list of project restrictions associated with a context.
    
    Args:
        context_id: An opaque identifier of a context.
    
    Returns:
        List of project restrictions
    """
    return await make_request("GET", f"context/{context_id}/restrictions")

@mcp.tool()
async def create_context_restriction(context_id: str, restriction_type: str, restriction_value: str) -> Dict:
    """
    Creates project restriction on a context.
    
    Args:
        context_id: An opaque identifier of a context.
        restriction_type: Type of restriction
        restriction_value: Value for the restriction
    
    Returns:
        The created restriction
    """
    data = {
        "restriction_type": restriction_type,
        "restriction_value": restriction_value
    }
    return await make_request("POST", f"context/{context_id}/restrictions", data=data)

@mcp.tool()
async def delete_context_restriction(context_id: str, restriction_id: str) -> Dict:
    """
    Deletes a project restriction on a context.
    
    Args:
        context_id: An opaque identifier of a context.
        restriction_id: An opaque identifier of a context restriction.
    
    Returns:
        A confirmation message
    """
    return await make_request("DELETE", f"context/{context_id}/restrictions/{restriction_id}")

#
# Insights Endpoints
#

@mcp.tool()
async def get_project_summary_metrics(project_slug: str, reporting_window: Optional[str] = None,
                                     branches: Optional[List[str]] = None, workflow_names: Optional[List[str]] = None) -> Dict:
    """
    Get summary metrics and trends for a project across its workflows and branches.
    
    Args:
        project_slug: Project slug in the form vcs-slug/org-name/repo-name.
        reporting_window: The time window used to calculate metrics (e.g., "last-90-days")
        branches: The names of VCS branches to include in branch-level workflow metrics.
        workflow_names: The names of workflows to include in workflow-level metrics.
    
    Returns:
        Aggregated summary metrics and trends by workflow and branches
    """
    params = {}
    if reporting_window:
        params["reporting-window"] = reporting_window
    if branches:
        params["branches"] = branches
    if workflow_names:
        params["workflow-names"] = workflow_names
        
    return await make_request("GET", f"insights/pages/{project_slug}/summary", params=params)

@mcp.tool()
async def get_job_timeseries_data(project_slug: str, workflow_name: str, branch: Optional[str] = None,
                                granularity: Optional[str] = None, start_date: Optional[str] = None,
                                end_date: Optional[str] = None) -> Dict:
    """
    Get timeseries data for all jobs within a workflow.
    
    Args:
        project_slug: Project slug in the form vcs-slug/org-name/repo-name.
        workflow_name: The name of the workflow.
        branch: The name of a vcs branch. If not passed scope to default branch.
        granularity: The granularity for which to query timeseries data ("daily" or "hourly").
        start_date: Include only executions that started at or after this date.
        end_date: Include only executions that started before this date.
    
    Returns:
        An array of timeseries data, one entry per job.
    """
    params = {}
    if branch:
        params["branch"] = branch
    if granularity:
        params["granularity"] = granularity
    if start_date:
        params["start-date"] = start_date
    if end_date:
        params["end-date"] = end_date
        
    return await make_request("GET", f"insights/time-series/{project_slug}/workflows/{workflow_name}/jobs", params=params)

@mcp.tool()
async def get_org_summary_metrics(org_slug: str, reporting_window: Optional[str] = None,
                                 project_names: Optional[List[str]] = None) -> Dict:
    """
    Get summary metrics with trends for the entire org, and for each project.
    
    Args:
        org_slug: Org slug in the form vcs-slug/org-name.
        reporting_window: The time window used to calculate summary metrics.
        project_names: List of project names.
    
    Returns:
        Summary metrics with trends for an entire org and its projects.
    """
    params = {}
    if reporting_window:
        params["reporting-window"] = reporting_window
    if project_names:
        params["project-names"] = project_names
        
    return await make_request("GET", f"insights/{org_slug}/summary", params=params)

@mcp.tool()
async def get_all_branches(project_slug: str, workflow_name: Optional[str] = None) -> Dict:
    """
    Get a list of all branches for a specified project.
    
    Args:
        project_slug: Project slug in the form vcs-slug/org-name/repo-name.
        workflow_name: The name of a workflow.
    
    Returns:
        A list of branches for a project
    """
    params = {}
    if workflow_name:
        params["workflow-name"] = workflow_name
        
    return await make_request("GET", f"insights/{project_slug}/branches", params=params)

@mcp.tool()
async def get_flaky_tests(project_slug: str) -> Dict:
    """
    Get a list of flaky tests for a given project.
    
    Args:
        project_slug: Project slug in the form vcs-slug/org-name/repo-name.
    
    Returns:
        A list of flaky tests for a project
    """
    return await make_request("GET", f"insights/{project_slug}/flaky-tests")

@mcp.tool()
async def get_workflow_summary_metrics(project_slug: str, page_token: Optional[str] = None,
                                     all_branches: Optional[bool] = None, branch: Optional[str] = None,
                                     reporting_window: Optional[str] = None) -> Dict:
    """
    Get summary metrics for a project's workflows.
    
    Args:
        project_slug: Project slug in the form vcs-slug/org-name/repo-name.
        page_token: A token to retrieve the next page of results.
        all_branches: Whether to retrieve data for all branches combined.
        branch: The name of a vcs branch. If not passed scope to default branch.
        reporting_window: The time window used to calculate summary metrics.
    
    Returns:
        A paginated list of summary metrics by workflow
    """
    params = {}
    if page_token:
        params["page-token"] = page_token
    if all_branches is not None:
        params["all-branches"] = all_branches
    if branch:
        params["branch"] = branch
    if reporting_window:
        params["reporting-window"] = reporting_window
        
    return await make_request("GET", f"insights/{project_slug}/workflows", params=params)

@mcp.tool()
async def get_recent_workflow_runs(project_slug: str, workflow_name: str, all_branches: Optional[bool] = None,
                                 branch: Optional[str] = None, page_token: Optional[str] = None,
                                 start_date: Optional[str] = None, end_date: Optional[str] = None) -> Dict:
    """
    Get recent runs of a workflow.
    
    Args:
        project_slug: Project slug in the form vcs-slug/org-name/repo-name.
        workflow_name: The name of the workflow.
        all_branches: Whether to retrieve data for all branches combined.
        branch: The name of a vcs branch. If not passed scope to default branch.
        page_token: A token to retrieve the next page of results.
        start_date: Include only executions that started at or after this date.
        end_date: Include only executions that started before this date.
    
    Returns:
        A paginated list of recent workflow runs
    """
    params = {}
    if all_branches is not None:
        params["all-branches"] = all_branches
    if branch:
        params["branch"] = branch
    if page_token:
        params["page-token"] = page_token
    if start_date:
        params["start-date"] = start_date
    if end_date:
        params["end-date"] = end_date
        
    return await make_request("GET", f"insights/{project_slug}/workflows/{workflow_name}", params=params)

#
# Pipeline Endpoints
#

@mcp.tool()
async def list_pipelines(org_slug: Optional[str] = None, page_token: Optional[str] = None, 
                        mine: Optional[bool] = None) -> Dict:
    """
    Returns all pipelines for the most recently built projects (max 250) you follow in an organization.
    
    Args:
        org_slug: Org slug in the form vcs-slug/org-name.
        page_token: A token to retrieve the next page of results.
        mine: Only include entries created by your user.
    
    Returns:
        A sequence of pipelines.
    """
    params = {}
    if org_slug:
        params["org-slug"] = org_slug
    if page_token:
        params["page-token"] = page_token
    if mine is not None:
        params["mine"] = mine
        
    return await make_request("GET", "pipeline", params=params)

@mcp.tool()
async def continue_pipeline(continuation_key: str, configuration: str, parameters: Optional[Dict] = None) -> Dict:
    """
    Continue a pipeline from the setup phase.
    
    Args:
        continuation_key: A pipeline continuation key.
        configuration: A configuration string for the pipeline.
        parameters: An object containing pipeline parameters and their values.
    
    Returns:
        A confirmation message.
    """
    data = {
        "continuation-key": continuation_key,
        "configuration": configuration
    }
    if parameters:
        data["parameters"] = parameters
        
    return await make_request("POST", "pipeline/continue", data=data)

@mcp.tool()
async def get_pipeline(pipeline_id: str) -> Dict:
    """
    Returns a pipeline by the pipeline ID.
    
    Args:
        pipeline_id: The unique ID of the pipeline.
    
    Returns:
        A pipeline object.
    """
    return await make_request("GET", f"pipeline/{pipeline_id}")

@mcp.tool()
async def get_pipeline_config(pipeline_id: str) -> Dict:
    """
    Returns a pipeline's configuration by ID.
    
    Args:
        pipeline_id: The unique ID of the pipeline.
    
    Returns:
        The configuration strings for the pipeline.
    """
    return await make_request("GET", f"pipeline/{pipeline_id}/config")

@mcp.tool()
async def get_pipeline_values(pipeline_id: str) -> Dict:
    """
    Returns a map of pipeline values by pipeline ID.
    
    Args:
        pipeline_id: The unique ID of the pipeline.
    
    Returns:
        A JSON object of pipeline values
    """
    return await make_request("GET", f"pipeline/{pipeline_id}/values")

@mcp.tool()
async def get_pipeline_workflows(pipeline_id: str, page_token: Optional[str] = None) -> Dict:
    """
    Returns a paginated list of workflows by pipeline ID.
    
    Args:
        pipeline_id: The unique ID of the pipeline.
        page_token: A token to retrieve the next page of results.
    
    Returns:
        A paginated list of workflow objects.
    """
    params = {}
    if page_token:
        params["page-token"] = page_token
        
    return await make_request("GET", f"pipeline/{pipeline_id}/workflow", params=params)

@mcp.tool()
async def get_project_pipelines(project_slug: str, branch: Optional[str] = None, 
                             page_token: Optional[str] = None) -> Dict:
    """
    Returns all pipelines for this project.
    
    Args:
        project_slug: Project slug in the form vcs-slug/org-name/repo-name.
        branch: The name of a vcs branch.
        page_token: A token to retrieve the next page of results.
    
    Returns:
        A sequence of pipelines.
    """
    params = {}
    if branch:
        params["branch"] = branch
    if page_token:
        params["page-token"] = page_token
        
    return await make_request("GET", f"project/{project_slug}/pipeline", params=params)

@mcp.tool()
async def trigger_pipeline(project_slug: str, branch: Optional[str] = None, tag: Optional[str] = None, 
                         parameters: Optional[Dict] = None) -> Dict:
    """
    Trigger a new pipeline on the project.
    
    Args:
        project_slug: Project slug in the form vcs-slug/org-name/repo-name.
        branch: The branch where the pipeline ran.
        tag: The tag used by the pipeline.
        parameters: An object containing pipeline parameters and their values.
    
    Returns:
        The created pipeline.
    """
    data = {}
    if branch:
        data["branch"] = branch
    if tag:
        data["tag"] = tag
    if parameters:
        data["parameters"] = parameters
        
    return await make_request("POST", f"project/{project_slug}/pipeline", data=data)

@mcp.tool()
async def get_my_pipelines(project_slug: str, page_token: Optional[str] = None) -> Dict:
    """
    Returns a sequence of all pipelines for this project triggered by the user.
    
    Args:
        project_slug: Project slug in the form vcs-slug/org-name/repo-name.
        page_token: A token to retrieve the next page of results.
    
    Returns:
        A sequence of pipelines.
    """
    params = {}
    if page_token:
        params["page-token"] = page_token
        
    return await make_request("GET", f"project/{project_slug}/pipeline/mine", params=params)

@mcp.tool()
async def get_pipeline_by_number(project_slug: str, pipeline_number: str) -> Dict:
    """
    Returns a pipeline by the pipeline number.
    
    Args:
        project_slug: Project slug in the form vcs-slug/org-name/repo-name.
        pipeline_number: The number of the pipeline.
    
    Returns:
        A pipeline object.
    """
    return await make_request("GET", f"project/{project_slug}/pipeline/{pipeline_number}")

@mcp.tool()
async def trigger_new_pipeline(provider: str, organization: str, project: str, 
                              definition_id: Optional[str] = None, config: Optional[Dict] = None,
                              checkout: Optional[Dict] = None, parameters: Optional[Dict] = None) -> Dict:
    """
    Trigger a pipeline given a pipeline definition ID.
    
    Args:
        provider: The provider segment of a project or org slug (e.g., "gh", "bitbucket").
        organization: The organization segment of a project or org slug.
        project: The project segment of a project slug.
        definition_id: The unique id for the pipeline definition.
        config: Pipeline configuration parameters.
        checkout: Checkout configuration parameters.
        parameters: Pipeline parameters.
    
    Returns:
        The created pipeline.
    """
    data = {}
    if definition_id:
        data["definition_id"] = definition_id
    if config:
        data["config"] = config
    if checkout:
        data["checkout"] = checkout
    if parameters:
        data["parameters"] = parameters
        
    return await make_request("POST", f"project/{provider}/{organization}/{project}/pipeline/run", data=data)

#
# Job Endpoints
#

@mcp.tool()
async def cancel_job(job_id: str) -> Dict:
    """
    Cancel job with a given job ID.
    
    Args:
        job_id: The unique ID of the job.
    
    Returns:
        Job cancelled successfully.
    """
    return await make_request("POST", f"jobs/{job_id}/cancel")

@mcp.tool()
async def get_job_details(project_slug: str, job_number: str) -> Dict:
    """
    Returns job details.
    
    Args:
        project_slug: Project slug in the form vcs-slug/org-name/repo-name.
        job_number: The number of the job.
    
    Returns:
        Job details.
    """
    return await make_request("GET", f"project/{project_slug}/job/{job_number}")

@mcp.tool()
async def cancel_job_by_number(project_slug: str, job_number: str) -> Dict:
    """
    Cancel job with a given job number.
    
    Args:
        project_slug: Project slug in the form vcs-slug/org-name/repo-name.
        job_number: The number of the job.
    
    Returns:
        A confirmation message.
    """
    return await make_request("POST", f"project/{project_slug}/job/{job_number}/cancel")

@mcp.tool()
async def get_job_artifacts(project_slug: str, job_number: str) -> Dict:
    """
    Returns a job's artifacts.
    
    Args:
        project_slug: Project slug in the form vcs-slug/org-name/repo-name.
        job_number: The number of the job.
    
    Returns:
        A paginated list of the job's artifacts.
    """
    return await make_request("GET", f"project/{project_slug}/{job_number}/artifacts")

@mcp.tool()
async def get_test_metadata(project_slug: str, job_number: str) -> Dict:
    """
    Get test metadata for a build.
    
    Args:
        project_slug: Project slug in the form vcs-slug/org-name/repo-name.
        job_number: The number of the job.
    
    Returns:
        A paginated list of test results.
    """
    return await make_request("GET", f"project/{project_slug}/{job_number}/tests")

#
# Workflow Endpoints
#

@mcp.tool()
async def get_workflow(workflow_id: str) -> Dict:
    """
    Returns summary fields of a workflow by ID.
    
    Args:
        workflow_id: The unique ID of the workflow.
    
    Returns:
        A workflow object.
    """
    return await make_request("GET", f"workflow/{workflow_id}")

@mcp.tool()
async def approve_job(workflow_id: str, approval_request_id: str) -> Dict:
    """
    Approves a pending approval job in a workflow.
    
    Args:
        workflow_id: The unique ID of the workflow.
        approval_request_id: The ID of the job being approved.
    
    Returns:
        A confirmation message.
    """
    return await make_request("POST", f"workflow/{workflow_id}/approve/{approval_request_id}")

@mcp.tool()
async def cancel_workflow(workflow_id: str) -> Dict:
    """
    Cancels a running workflow.
    
    Args:
        workflow_id: The unique ID of the workflow.
    
    Returns:
        A confirmation message.
    """
    return await make_request("POST", f"workflow/{workflow_id}/cancel")

@mcp.tool()
async def get_workflow_jobs(workflow_id: str) -> Dict:
    """
    Returns a sequence of jobs for a workflow.
    
    Args:
        workflow_id: The unique ID of the workflow.
    
    Returns:
        A paginated sequence of jobs.
    """
    return await make_request("GET", f"workflow/{workflow_id}/job")

@mcp.tool()
async def rerun_workflow(workflow_id: str, enable_ssh: Optional[bool] = None, from_failed: Optional[bool] = None,
                       jobs: Optional[List[str]] = None, sparse_tree: Optional[bool] = None) -> Dict:
    """
    Reruns a workflow.
    
    Args:
        workflow_id: The unique ID of the workflow.
        enable_ssh: Whether to enable SSH access for the triggering user.
        from_failed: Whether to rerun the workflow from the failed job.
        jobs: A list of job IDs to rerun.
        sparse_tree: Completes rerun using sparse trees logic.
    
    Returns:
        A confirmation message.
    """
    data = {}
    if enable_ssh is not None:
        data["enable_ssh"] = enable_ssh
    if from_failed is not None:
        data["from_failed"] = from_failed
    if jobs:
        data["jobs"] = jobs
    if sparse_tree is not None:
        data["sparse_tree"] = sparse_tree
        
    return await make_request("POST", f"workflow/{workflow_id}/rerun", data=data)

#
# Project Endpoints
#

@mcp.tool()
async def get_project(project_slug: str) -> Dict:
    """
    Retrieves a project by project slug.
    
    Args:
        project_slug: Project slug in the form vcs-slug/org-name/repo-name.
    
    Returns:
        A project object
    """
    return await make_request("GET", f"project/{project_slug}")

@mcp.tool()
async def get_all_checkout_keys(project_slug: str, digest: Optional[str] = None) -> Dict:
    """
    Returns a sequence of checkout keys for a project.
    
    Args:
        project_slug: Project slug in the form vcs-slug/org-name/repo-name.
        digest: The fingerprint digest type to return (md5 or sha256).
    
    Returns:
        A sequence of checkout keys.
    """
    params = {}
    if digest:
        params["digest"] = digest
        
    return await make_request("GET", f"project/{project_slug}/checkout-key", params=params)

@mcp.tool()
async def create_checkout_key(project_slug: str, type: str) -> Dict:
    """
    Creates a new checkout key.
    
    Args:
        project_slug: Project slug in the form vcs-slug/org-name/repo-name.
        type: The type of checkout key to create (deploy-key or user-key).
    
    Returns:
        The checkout key.
    """
    data = {"type": type}
    return await make_request("POST", f"project/{project_slug}/checkout-key", data=data)

@mcp.tool()
async def get_checkout_key(project_slug: str, fingerprint: str) -> Dict:
    """
    Returns an individual checkout key via fingerprint.
    
    Args:
        project_slug: Project slug in the form vcs-slug/org-name/repo-name.
        fingerprint: An SSH key fingerprint.
    
    Returns:
        The checkout key.
    """
    return await make_request("GET", f"project/{project_slug}/checkout-key/{fingerprint}")

@mcp.tool()
async def delete_checkout_key(project_slug: str, fingerprint: str) -> Dict:
    """
    Deletes the checkout key via fingerprint.
    
    Args:
        project_slug: Project slug in the form vcs-slug/org-name/repo-name.
        fingerprint: An SSH key fingerprint.
    
    Returns:
        A confirmation message.
    """
    return await make_request("DELETE", f"project/{project_slug}/checkout-key/{fingerprint}")

@mcp.tool()
async def create_environment_variable(project_slug: str, name: str, value: str) -> Dict:
    """
    Creates a new environment variable.
    
    Args:
        project_slug: Project slug in the form vcs-slug/org-name/repo-name.
        name: The name of the environment variable.
        value: The value of the environment variable.
    
    Returns:
        The environment variable.
    """
    data = {
        "name": name,
        "value": value
    }
    return await make_request("POST", f"project/{project_slug}/envvar", data=data)

@mcp.tool()
async def list_environment_variables(project_slug: str) -> Dict:
    """
    Returns environment variables for a project.
    
    Args:
        project_slug: Project slug in the form vcs-slug/org-name/repo-name.
    
    Returns:
        A sequence of environment variables.
    """
    return await make_request("GET", f"project/{project_slug}/envvar")

@mcp.tool()
async def get_masked_environment_variable(project_slug: str, name: str) -> Dict:
    """
    Returns the masked value of environment variable by name.
    
    Args:
        project_slug: Project slug in the form vcs-slug/org-name/repo-name.
        name: The name of the environment variable.
    
    Returns:
        The environment variable with masked value.
    """
    return await make_request("GET", f"project/{project_slug}/envvar/{name}")

@mcp.tool()
async def delete_environment_variable(project_slug: str, name: str) -> Dict:
    """
    Deletes the environment variable by name.
    
    Args:
        project_slug: Project slug in the form vcs-slug/org-name/repo-name.
        name: The name of the environment variable.
    
    Returns:
        A confirmation message.
    """
    return await make_request("DELETE", f"project/{project_slug}/envvar/{name}")

@mcp.tool()
async def create_project(provider: str, organization: str, project: str) -> Dict:
    """
    Creates a new CircleCI project.
    
    Args:
        provider: The provider segment of a project (gh, bb).
        organization: The organization segment of a project.
        project: The project segment of a project.
    
    Returns:
        The project's advanced settings.
    """
    return await make_request("POST", f"project/{provider}/{organization}/{project}")

@mcp.tool()
async def get_project_settings(provider: str, organization: str, project: str) -> Dict:
    """
    Returns a list of advanced settings for a CircleCI project.
    
    Args:
        provider: The provider segment of a project (gh, bb).
        organization: The organization segment of a project.
        project: The project segment of a project.
    
    Returns:
        The project's advanced settings.
    """
    return await make_request("GET", f"project/{provider}/{organization}/{project}/settings")

@mcp.tool()
async def update_project_settings(provider: str, organization: str, project: str, advanced: Dict) -> Dict:
    """
    Updates one or more of the advanced settings for a CircleCI project.
    
    Args:
        provider: The provider segment of a project (gh, bb).
        organization: The organization segment of a project.
        project: The project segment of a project.
        advanced: Settings to update.
    
    Returns:
        The updated project settings.
    """
    data = {"advanced": advanced}
    return await make_request("PATCH", f"project/{provider}/{organization}/{project}/settings", data=data)

#
# Schedule Endpoints
#

@mcp.tool()
async def create_schedule(project_slug: str, name: str, timetable: Dict, attribution_actor: str, 
                        parameters: Dict, description: Optional[str] = None) -> Dict:
    """
    Creates a schedule and returns the created schedule.
    
    Args:
        project_slug: Project slug in the form vcs-slug/org-name/repo-name.
        name: Name of the schedule.
        timetable: Timetable that specifies when a schedule triggers.
        attribution_actor: The attribution-actor of the scheduled pipeline ("current" or "system").
        parameters: Pipeline parameters represented as key-value pairs. Must contain branch or tag.
        description: Description of the schedule.
    
    Returns:
        A schedule object.
    """
    data = {
        "name": name,
        "timetable": timetable,
        "attribution-actor": attribution_actor,
        "parameters": parameters
    }
    if description:
        data["description"] = description
        
    return await make_request("POST", f"project/{project_slug}/schedule", data=data)

@mcp.tool()
async def get_all_schedules(project_slug: str, page_token: Optional[str] = None) -> Dict:
    """
    Returns all schedules for this project.
    
    Args:
        project_slug: Project slug in the form vcs-slug/org-name/repo-name.
        page_token: A token to retrieve the next page of results.
    
    Returns:
        A sequence of schedules.
    """
    params = {}
    if page_token:
        params["page-token"] = page_token
        
    return await make_request("GET", f"project/{project_slug}/schedule", params=params)

@mcp.tool()
async def delete_schedule(schedule_id: str) -> Dict:
    """
    Deletes the schedule by id.
    
    Args:
        schedule_id: The unique ID of the schedule.
    
    Returns:
        A confirmation message.
    """
    return await make_request("DELETE", f"schedule/{schedule_id}")

@mcp.tool()
async def update_schedule(schedule_id: str, description: Optional[str] = None, name: Optional[str] = None,
                        timetable: Optional[Dict] = None, attribution_actor: Optional[str] = None,
                        parameters: Optional[Dict] = None) -> Dict:
    """
    Updates a schedule and returns the updated schedule.
    
    Args:
        schedule_id: The unique ID of the schedule.
        description: Description of the schedule.
        name: Name of the schedule.
        timetable: Timetable that specifies when a schedule triggers.
        attribution_actor: The attribution-actor of the scheduled pipeline.
        parameters: Pipeline parameters represented as key-value pairs.
    
    Returns:
        A schedule object.
    """
    data = {}
    if description:
        data["description"] = description
    if name:
        data["name"] = name
    if timetable:
        data["timetable"] = timetable
    if attribution_actor:
        data["attribution-actor"] = attribution_actor
    if parameters:
        data["parameters"] = parameters
        
    return await make_request("PATCH", f"schedule/{schedule_id}", data=data)

@mcp.tool()
async def get_schedule(schedule_id: str) -> Dict:
    """
    Get a schedule by id.
    
    Args:
        schedule_id: The unique ID of the schedule.
    
    Returns:
        A schedule object.
    """
    return await make_request("GET", f"schedule/{schedule_id}")

#
# Webhook Endpoints
#

@mcp.tool()
async def list_webhooks(scope_id: str, scope_type: str) -> Dict:
    """
    Get a list of outbound webhooks that match the given scope-type and scope-id.
    
    Args:
        scope_id: ID of the scope being used (at the moment, only project ID is supported).
        scope_type: Type of the scope being used (currently only "project").
    
    Returns:
        A list of webhooks.
    """
    params = {
        "scope-id": scope_id,
        "scope-type": scope_type
    }
    return await make_request("GET", "webhook", params=params)

@mcp.tool()
async def create_webhook(name: str, events: List[str], url: str, verify_tls: bool, 
                       signing_secret: str, scope: Dict) -> Dict:
    """
    Creates an outbound webhook.
    
    Args:
        name: Name of the webhook.
        events: Events that will trigger the webhook.
        url: URL to deliver the webhook to (only https is supported).
        verify_tls: Whether to enforce TLS certificate verification.
        signing_secret: Secret used to build an HMAC hash.
        scope: The scope in which the relevant events will trigger webhooks.
    
    Returns:
        A webhook.
    """
    data = {
        "name": name,
        "events": events,
        "url": url,
        "verify-tls": verify_tls,
        "signing-secret": signing_secret,
        "scope": scope
    }
    return await make_request("POST", "webhook", data=data)

@mcp.tool()
async def update_webhook(webhook_id: str, name: Optional[str] = None, events: Optional[List[str]] = None, 
                      url: Optional[str] = None, signing_secret: Optional[str] = None, 
                      verify_tls: Optional[bool] = None) -> Dict:
    """
    Updates an outbound webhook.
    
    Args:
        webhook_id: ID of the webhook (UUID).
        name: Name of the webhook.
        events: Events that will trigger the webhook.
        url: URL to deliver the webhook to (only https is supported).
        signing_secret: Secret used to build an HMAC hash.
        verify_tls: Whether to enforce TLS certificate verification.
    
    Returns:
        A webhook.
    """
    data = {}
    if name:
        data["name"] = name
    if events:
        data["events"] = events
    if url:
        data["url"] = url
    if signing_secret:
        data["signing-secret"] = signing_secret
    if verify_tls is not None:
        data["verify-tls"] = verify_tls
        
    return await make_request("PUT", f"webhook/{webhook_id}", data=data)

@mcp.tool()
async def delete_webhook(webhook_id: str) -> Dict:
    """
    Deletes an outbound webhook.
    
    Args:
        webhook_id: ID of the webhook (UUID).
    
    Returns:
        A confirmation message.
    """
    return await make_request("DELETE", f"webhook/{webhook_id}")

@mcp.tool()
async def get_webhook(webhook_id: str) -> Dict:
    """
    Get an outbound webhook by id.
    
    Args:
        webhook_id: ID of the webhook (UUID).
    
    Returns:
        A webhook.
    """
    return await make_request("GET", f"webhook/{webhook_id}")

#
# OIDC Token Management Endpoints
#

@mcp.tool()
async def delete_org_level_claims(orgID: str, claims: str) -> Dict:
    """
    Deletes org-level custom claims of OIDC identity tokens.
    
    Args:
        orgID: Organization ID.
        claims: Comma separated list of claims to delete ("audience" and/or "ttl").
    
    Returns:
        The updated claims.
    """
    params = {"claims": claims}
    return await make_request("DELETE", f"org/{orgID}/oidc-custom-claims", params=params)

@mcp.tool()
async def get_org_level_claims(orgID: str) -> Dict:
    """
    Fetches org-level custom claims of OIDC identity tokens.
    
    Args:
        orgID: Organization ID.
    
    Returns:
        The organization's claims.
    """
    return await make_request("GET", f"org/{orgID}/oidc-custom-claims")

@mcp.tool()
async def patch_org_level_claims(orgID: str, audience: Optional[List[str]] = None, 
                                ttl: Optional[str] = None) -> Dict:
    """
    Creates/Updates org-level custom claims of OIDC identity tokens.
    
    Args:
        orgID: Organization ID.
        audience: List of audience claims.
        ttl: TTL claim value.
    
    Returns:
        The updated claims.
    """
    data = {}
    if audience:
        data["audience"] = audience
    if ttl:
        data["ttl"] = ttl
        
    return await make_request("PATCH", f"org/{orgID}/oidc-custom-claims", data=data)

@mcp.tool()
async def delete_project_level_claims(orgID: str, projectID: str, claims: str) -> Dict:
    """
    Deletes project-level custom claims of OIDC identity tokens.
    
    Args:
        orgID: Organization ID.
        projectID: Project ID.
        claims: Comma separated list of claims to delete ("audience" and/or "ttl").
    
    Returns:
        The updated claims.
    """
    params = {"claims": claims}
    return await make_request("DELETE", f"org/{orgID}/project/{projectID}/oidc-custom-claims", params=params)

@mcp.tool()
async def get_project_level_claims(orgID: str, projectID: str) -> Dict:
    """
    Fetches project-level custom claims of OIDC identity tokens.
    
    Args:
        orgID: Organization ID.
        projectID: Project ID.
    
    Returns:
        The project's claims.
    """
    return await make_request("GET", f"org/{orgID}/project/{projectID}/oidc-custom-claims")

@mcp.tool()
async def patch_project_level_claims(orgID: str, projectID: str, audience: Optional[List[str]] = None, 
                                   ttl: Optional[str] = None) -> Dict:
    """
    Creates/Updates project-level custom claims of OIDC identity tokens.
    
    Args:
        orgID: Organization ID.
        projectID: Project ID.
        audience: List of audience claims.
        ttl: TTL claim value.
    
    Returns:
        The updated claims.
    """
    data = {}
    if audience:
        data["audience"] = audience
    if ttl:
        data["ttl"] = ttl
        
    return await make_request("PATCH", f"org/{orgID}/project/{projectID}/oidc-custom-claims", data=data)

#
# Usage Endpoints
#

@mcp.tool()
async def create_usage_export(org_id: str, start: str, end: str, shared_org_ids: Optional[List[str]] = None) -> Dict:
    """
    Submits a request to create a usage export for an organization.
    
    Args:
        org_id: An opaque identifier of an organization.
        start: The start date & time (inclusive) of the range from which data will be pulled.
        end: The end date & time (inclusive) of the range from which data will be pulled.
        shared_org_ids: Optional list of additional organization IDs to include.
    
    Returns:
        Usage export created confirmation.
    """
    data = {
        "start": start,
        "end": end
    }
    if shared_org_ids:
        data["shared_org_ids"] = shared_org_ids
        
    return await make_request("POST", f"organizations/{org_id}/usage_export_job", data=data)

@mcp.tool()
async def get_usage_export(org_id: str, usage_export_job_id: str) -> Dict:
    """
    Gets a usage export for an organization.
    
    Args:
        org_id: An opaque identifier of an organization.
        usage_export_job_id: An opaque identifier of a usage export job.
    
    Returns:
        Usage export details.
    """
    return await make_request("GET", f"organizations/{org_id}/usage_export_job/{usage_export_job_id}")

#
# Policy Management Endpoints
#

@mcp.tool()
async def get_decision_audit_logs(ownerID: str, context: str, status: Optional[str] = None,
                               after: Optional[str] = None, before: Optional[str] = None,
                               branch: Optional[str] = None, project_id: Optional[str] = None,
                               build_number: Optional[str] = None, offset: Optional[int] = None) -> List:
    """
    Retrieves the owner's decision audit logs.
    
    Args:
        ownerID: Owner ID.
        context: Context name.
        status: Return decisions matching this decision status.
        after: Return decisions made after this date.
        before: Return decisions made before this date.
        branch: Return decisions made on this branch.
        project_id: Return decisions made for this project.
        build_number: Return decisions made for this build number.
        offset: Sets the offset when retrieving the decisions, for paging.
    
    Returns:
        List of decision logs.
    """
    params = {}
    if status:
        params["status"] = status
    if after:
        params["after"] = after
    if before:
        params["before"] = before
    if branch:
        params["branch"] = branch
    if project_id:
        params["project_id"] = project_id
    if build_number:
        params["build_number"] = build_number
    if offset is not None:
        params["offset"] = offset
        
    return await make_request("GET", f"owner/{ownerID}/context/{context}/decision", params=params)

@mcp.tool()
async def make_decision(ownerID: str, context: str, input_data: str, metadata: Optional[Dict] = None) -> Dict:
    """
    Makes a decision by evaluating input data against owner's policies.
    
    Args:
        ownerID: Owner ID.
        context: Context name.
        input_data: Input data to evaluate.
        metadata: Additional metadata.
    
    Returns:
        Decision result.
    """
    data = {"input": input_data}
    if metadata:
        data["metadata"] = metadata
        
    return await make_request("POST", f"owner/{ownerID}/context/{context}/decision", data=data)

@mcp.tool()
async def get_decision_settings(ownerID: str, context: str) -> Dict:
    """
    Retrieves the current decision settings.
    
    Args:
        ownerID: Owner ID.
        context: Context name.
    
    Returns:
        Current decision settings.
    """
    return await make_request("GET", f"owner/{ownerID}/context/{context}/decision/settings")

@mcp.tool()
async def set_decision_settings(ownerID: str, context: str, enabled: bool) -> Dict:
    """
    Sets the decision settings.
    
    Args:
        ownerID: Owner ID.
        context: Context name.
        enabled: Whether to enable policy evaluation.
    
    Returns:
        Updated decision settings.
    """
    data = {"enabled": enabled}
    return await make_request("PATCH", f"owner/{ownerID}/context/{context}/decision/settings", data=data)

@mcp.tool()
async def get_decision_log(ownerID: str, context: str, decisionID: str) -> Dict:
    """
    Retrieves a decision log by ID.
    
    Args:
        ownerID: Owner ID.
        context: Context name.
        decisionID: Decision ID.
    
    Returns:
        The requested decision log.
    """
    return await make_request("GET", f"owner/{ownerID}/context/{context}/decision/{decisionID}")

@mcp.tool()
async def get_policy_bundle_for_decision(ownerID: str, context: str, decisionID: str) -> Dict:
    """
    Retrieves a policy bundle for a given decision log ID.
    
    Args:
        ownerID: Owner ID.
        context: Context name.
        decisionID: Decision ID.
    
    Returns:
        The policy bundle for the given decision.
    """
    return await make_request("GET", f"owner/{ownerID}/context/{context}/decision/{decisionID}/policy-bundle")

@mcp.tool()
async def get_policy_bundle(ownerID: str, context: str) -> Dict:
    """
    Retrieves a policy bundle.
    
    Args:
        ownerID: Owner ID.
        context: Context name.
    
    Returns:
        The policy bundle.
    """
    return await make_request("GET", f"owner/{ownerID}/context/{context}/policy-bundle")

@mcp.tool()
async def create_policy_bundle(ownerID: str, context: str, policies: Dict, dry: Optional[bool] = None) -> Dict:
    """
    Creates policy bundle for the context.
    
    Args:
        ownerID: Owner ID.
        context: Context name.
        policies: Policy bundle content.
        dry: Whether to perform a dry run.
    
    Returns:
        Policy bundle creation result.
    """
    data = {"policies": policies}
    params = {}
    if dry is not None:
        params["dry"] = dry
        
    return await make_request("POST", f"owner/{ownerID}/context/{context}/policy-bundle", params=params, data=data)

@mcp.tool()
async def get_policy_document(ownerID: str, context: str, policyName: str) -> Dict:
    """
    Retrieves a policy document.
    
    Args:
        ownerID: Owner ID.
        context: Context name.
        policyName: The policy name set by the rego policy_name rule.
    
    Returns:
        The policy document.
    """
    return await make_request("GET", f"owner/{ownerID}/context/{context}/policy-bundle/{policyName}")

#
# User Endpoints
#

@mcp.tool()
async def get_current_user() -> Dict:
    """
    Provides information about the user that is currently signed in.
    
    Returns:
        User login information.
    """
    return await make_request("GET", "me")

@mcp.tool()
async def get_collaborations() -> List:
    """
    Provides the set of organizations of which a user is a member or a collaborator.
    
    Returns:
        List of collaborations.
    """
    return await make_request("GET", "me/collaborations")

@mcp.tool()
async def get_user(user_id: str) -> Dict:
    """
    Provides information about the user with the given ID.
    
    Args:
        user_id: The unique ID of the user.
    
    Returns:
        User login information.
    """
    return await make_request("GET", f"user/{user_id}")

# Run the server if this script is executed directly
if __name__ == "__main__":
    mcp.run()