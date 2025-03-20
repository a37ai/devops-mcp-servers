#!/usr/bin/env python3
"""
CircleCI MCP Test Script (Simple Version)

A simplified script to test the CircleCI MCP server functionality with hardcoded project values
in case the automatic discovery fails.
"""

import os
import asyncio
import json
from servers.circleci.circleci_mcp import *

async def main():
    """Main function to test essential CircleCI API endpoints."""
    print("CircleCI MCP Server Test Script (Simple Version)")
    print("===============================================")
    
    # Test user endpoints
    print("\nTesting user information...")
    try:
        user = await get_current_user()
        print(f"✅ User information: {user.get('name', 'Unknown')}")
    except Exception as e:
        print(f"❌ Failed to get user information: {str(e)}")
    
    # Test collaborations
    print("\nTesting collaborations...")
    try:
        collabs = await get_collaborations()
        print(f"✅ Found {len(collabs)} collaborations")
        
        # Use the first collaboration to get org information if not set manually
        if not ORG_SLUG and collabs:
            org = collabs[0]
            vcs_type = org.get('vcs_type', 'gh')
            org_name = org.get('name')
            if org_name:
                detected_org_slug = f"{vcs_type}/{org_name}"
                print(f"Detected organization slug: {detected_org_slug}")
    except Exception as e:
        print(f"❌ Failed to get collaborations: {str(e)}")
    
    # Try to test a simple pipeline listing
    print("\nTesting pipeline listing...")
    try:
        pipelines = await list_pipelines()
        print(f"✅ Found {len(pipelines.get('items', []))} recent pipelines")
        
        # Try to find a project slug if not set manually
        if not PROJECT_SLUG and 'items' in pipelines and pipelines['items']:
            for pipeline in pipelines['items']:
                if 'project_slug' in pipeline:
                    detected_project_slug = pipeline['project_slug']
                    print(f"Detected project slug: {detected_project_slug}")
                    break
    except Exception as e:
        print(f"❌ Failed to list pipelines: {str(e)}")
    
    print("\nTest complete. For more comprehensive testing, run the main test script.")

if __name__ == "__main__":
    asyncio.run(main())