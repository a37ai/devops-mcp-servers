#!/usr/bin/env python3
"""
Adjusted CircleCI MCP Test Script

This script tests the CircleCI MCP server's functionality using provided project slugs.
"""

import os
import asyncio
import json
import random
import string
from datetime import datetime, timedelta
from servers.circleci.circleci_mcp import *

# Use the provided project slugs
PROJECT_SLUGS = [
    "circleci/HUAxEremJuGfuD9HAg2Nti/CERU25RsxX8d1WuRFDGsMS",
    "circleci/HUAxEremJuGfuD9HAg2Nti/6DkLaTptU9ddwvCef1pGA1"
]

# Extract organization ID from the project slugs
ORG_ID = "HUAxEremJuGfuD9HAg2Nti" if PROJECT_SLUGS else None
ORG_SLUG = f"circleci/{ORG_ID}" if ORG_ID else None

class TestResult:
    def __init__(self, name, success, response=None, error=None):
        self.name = name
        self.success = success
        self.response = response
        self.error = error

async def run_test(name, func, *args, **kwargs):
    """Run a test and return the result."""
    print(f"Running test: {name}...")
    try:
        response = await func(*args, **kwargs)
        print(f"✅ Test passed: {name}")
        return TestResult(name, True, response)
    except Exception as e:
        print(f"❌ Test failed: {name}")
        print(f"Error: {str(e)}")
        return TestResult(name, False, error=str(e))

def generate_random_string(length=8):
    """Generate a random string for test resources."""
    return ''.join(random.choices(string.ascii_lowercase + string.digits, k=length))

async def test_user_endpoints():
    """Test user-related endpoints."""
    results = []
    
    # Test get_current_user
    try:
        results.append(await run_test("Get Current User", get_current_user))
    except Exception as e:
        print(f"Error in get_current_user: {str(e)}")
    
    # Test get_collaborations
    try:
        collab_result = await run_test("Get Collaborations", get_collaborations)
        results.append(collab_result)
        
        # Test get_user (if we have current user data)
        if collab_result.success and collab_result.response:
            try:
                user_id = (await get_current_user()).get('id')
                if user_id:
                    results.append(await run_test("Get User by ID", get_user, user_id))
            except Exception:
                pass
    except Exception as e:
        print(f"Error in get_collaborations: {str(e)}")
    
    return results

async def test_project_endpoints(project_slugs):
    """Test project-related endpoints using the provided project slugs."""
    results = []
    
    if not project_slugs:
        return results
    
    for project_slug in project_slugs:
        print(f"\nTesting with project slug: {project_slug}")
        
        # Get project details
        project_result = await run_test(f"Get Project ({project_slug})", get_project, project_slug)
        results.append(project_result)
        
        if not project_result.success:
            continue  # Skip further tests for this project if we can't get basic details
        
        # List project pipelines
        pipelines_result = await run_test(f"List Project Pipelines ({project_slug})", get_project_pipelines, project_slug)
        results.append(pipelines_result)
        
        # Get all branches
        results.append(await run_test(f"Get All Branches ({project_slug})", get_all_branches, project_slug))
        
        # List environment variables
        results.append(await run_test(f"List Environment Variables ({project_slug})", list_environment_variables, project_slug))
        
        # List checkout keys
        results.append(await run_test(f"List Checkout Keys ({project_slug})", get_all_checkout_keys, project_slug))
        
        # If we found pipelines, test workflow and job endpoints
        if pipelines_result.success and 'items' in pipelines_result.response and pipelines_result.response['items']:
            pipeline = pipelines_result.response['items'][0]
            pipeline_id = pipeline['id']
            
            # Get pipeline details
            results.append(await run_test(f"Get Pipeline ({pipeline_id})", get_pipeline, pipeline_id))
            
            # Get pipeline config
            results.append(await run_test(f"Get Pipeline Config ({pipeline_id})", get_pipeline_config, pipeline_id))
            
            # Get pipeline values
            results.append(await run_test(f"Get Pipeline Values ({pipeline_id})", get_pipeline_values, pipeline_id))
            
            # Get pipeline workflows
            workflows_result = await run_test(f"Get Pipeline Workflows ({pipeline_id})", get_pipeline_workflows, pipeline_id)
            results.append(workflows_result)
            
            # If we found workflows, test workflow endpoints
            if workflows_result.success and 'items' in workflows_result.response and workflows_result.response['items']:
                workflow = workflows_result.response['items'][0]
                workflow_id = workflow['id']
                
                # Get workflow details
                results.append(await run_test(f"Get Workflow ({workflow_id})", get_workflow, workflow_id))
                
                # Get workflow jobs
                jobs_result = await run_test(f"Get Workflow Jobs ({workflow_id})", get_workflow_jobs, workflow_id)
                results.append(jobs_result)
                
                # If we found jobs, test job endpoints
                if jobs_result.success and 'items' in jobs_result.response and jobs_result.response['items']:
                    for job in jobs_result.response['items']:
                        if job['status'] not in ['success', 'failed', 'canceled']:
                            continue  # Skip jobs that aren't complete
                        
                        job_number = job.get('job_number')
                        if job_number:
                            # Get job details
                            results.append(await run_test(
                                f"Get Job Details ({job_number})", 
                                get_job_details, 
                                project_slug, 
                                job_number
                            ))
                            
                            # Try to get artifacts
                            results.append(await run_test(
                                f"Get Job Artifacts ({job_number})", 
                                get_job_artifacts, 
                                project_slug, 
                                job_number
                            ))
                            
                            # Try to get test metadata
                            results.append(await run_test(
                                f"Get Test Metadata ({job_number})", 
                                get_test_metadata, 
                                project_slug, 
                                job_number
                            ))
                            
                            break  # Just test one job to keep the output manageable
    
    return results

async def test_organization_endpoints(org_id=None, org_slug=None):
    """Test organization-related endpoints."""
    results = []
    
    if not org_id and not org_slug:
        return results
    
    print(f"\nTesting organization endpoints with ID: {org_id}, slug: {org_slug}")
    
    # Only use the full organization slug format for summary metrics
    if org_slug:
        # Test organization summary metrics with the full slug
        results.append(await run_test(
            f"Get Organization Summary Metrics ({org_slug})", 
            get_org_summary_metrics, 
            org_slug, 
            reporting_window="last-90-days"
        ))
        
        # For contexts, the API might require the organization ID
        # rather than a slug component
        if org_id:
            results.append(await run_test(
                f"List Contexts (owner_id={org_id})", 
                list_contexts, 
                owner_id=org_id
            ))
    
    return results

async def test_insight_endpoints(project_slugs):
    """Test insights-related endpoints."""
    results = []
    
    if not project_slugs:
        return results
    
    for project_slug in project_slugs:
        # Get project summary metrics
        results.append(await run_test(
            f"Get Project Summary Metrics ({project_slug})", 
            get_project_summary_metrics, 
            project_slug, 
            reporting_window="last-90-days"
        ))
        
        # Get workflow summary metrics
        results.append(await run_test(
            f"Get Workflow Summary Metrics ({project_slug})", 
            get_workflow_summary_metrics, 
            project_slug, 
            reporting_window="last-90-days"
        ))
        
        # Get flaky tests
        results.append(await run_test(
            f"Get Flaky Tests ({project_slug})", 
            get_flaky_tests, 
            project_slug
        ))
    
    return results

async def test_schedule_endpoints(project_slugs):
    """Test schedule-related endpoints."""
    results = []
    
    if not project_slugs:
        return results
    
    for project_slug in project_slugs:
        # Get all schedules
        schedules_result = await run_test(f"Get All Schedules ({project_slug})", get_all_schedules, project_slug)
        results.append(schedules_result)
        
        # If we found schedules, test more endpoints
        if schedules_result.success and 'items' in schedules_result.response and schedules_result.response['items']:
            schedule = schedules_result.response['items'][0]
            schedule_id = schedule['id']
            
            # Get schedule details
            results.append(await run_test(f"Get Schedule ({schedule_id})", get_schedule, schedule_id))
    
    return results

async def test_webhook_endpoints(project_slugs):
    """Test webhook-related endpoints."""
    results = []
    
    if not project_slugs:
        return results
    
    for project_slug in project_slugs:
        # First, get project ID from the slug
        project_result = await run_test(f"Get Project ID ({project_slug})", get_project, project_slug)
        
        if project_result.success and 'id' in project_result.response:
            project_id = project_result.response['id']
            
            # List webhooks
            webhooks_result = await run_test(
                f"List Webhooks ({project_id})", 
                list_webhooks, 
                project_id, 
                "project"
            )
            results.append(webhooks_result)
            
            # If we found webhooks, test getting one
            if webhooks_result.success and 'items' in webhooks_result.response and webhooks_result.response['items']:
                webhook = webhooks_result.response['items'][0]
                webhook_id = webhook['id']
                
                # Get webhook details
                results.append(await run_test(f"Get Webhook ({webhook_id})", get_webhook, webhook_id))
    
    return results

async def run_all_tests():
    """Run all tests for the CircleCI MCP server."""
    all_results = []
    
    print(f"Using organization ID: {ORG_ID}")
    print(f"Using organization slug: {ORG_SLUG}")
    print(f"Using project slugs: {PROJECT_SLUGS}")
    
    # Test user endpoints
    print("\n=== TESTING USER ENDPOINTS ===")
    all_results.extend(await test_user_endpoints())
    
    # Test organization endpoints
    print("\n=== TESTING ORGANIZATION ENDPOINTS ===")
    all_results.extend(await test_organization_endpoints(org_id=ORG_ID, org_slug=ORG_SLUG))
    
    # Test project endpoints
    print("\n=== TESTING PROJECT ENDPOINTS ===")
    all_results.extend(await test_project_endpoints(PROJECT_SLUGS))
    
    # Test insights endpoints
    print("\n=== TESTING INSIGHTS ENDPOINTS ===")
    all_results.extend(await test_insight_endpoints(PROJECT_SLUGS))
    
    # Test schedule endpoints
    print("\n=== TESTING SCHEDULE ENDPOINTS ===")
    all_results.extend(await test_schedule_endpoints(PROJECT_SLUGS))
    
    # Test webhook endpoints
    print("\n=== TESTING WEBHOOK ENDPOINTS ===")
    all_results.extend(await test_webhook_endpoints(PROJECT_SLUGS))
    
    # Print summary
    print("\n\n========== TEST RESULTS SUMMARY ==========")
    passed = sum(1 for r in all_results if r.success)
    failed = len(all_results) - passed
    print(f"PASSED: {passed} | FAILED: {failed} | TOTAL: {len(all_results)}")
    
    print("\nDetails of passed tests:")
    for result in [r for r in all_results if r.success]:
        print(f"✅ {result.name}")
    
    print("\nDetails of failed tests:")
    for result in [r for r in all_results if not r.success]:
        print(f"❌ {result.name}")
        print(f"   Error: {result.error}")
    
    return all_results

async def main():
    """Main function to run all tests."""
    print("==========================================")
    print("   Adjusted CircleCI MCP Test Script")
    print("==========================================")
    print(f"API Key: {'*' * 8}{os.environ.get('CIRCLECI_API_KEY')[-5:] if os.environ.get('CIRCLECI_API_KEY') else 'Not set'}")
    print("==========================================\n")
    
    await run_all_tests()

if __name__ == "__main__":
    asyncio.run(main())