#!/usr/bin/env python3
"""
Test script for JFrog Artifactory MCP Tools
"""

import os
import asyncio
import tempfile
from pathlib import Path
import sys

# Import the improved MCP implementation
# (assuming both files are in the same directory or the improved version is in the Python path)
try:
    from gotta_complete_still.artifactory_improved_mcp import (
        get_system_health, get_version, get_storage_info, get_system_info, 
        create_repository, get_repository, list_repositories, delete_repository,
        deploy_artifact, get_artifact_info, search_artifacts, delete_artifact, advanced_search,
        create_user, get_user, update_user, delete_user, list_users,
        integrate_build, create_webhook, manage_permissions, run_tests
    )
except ImportError:
    print("Error: Could not import the improved artifactory_mcp_improved module.")
    print("Make sure you've saved the improved implementation to 'artifactory_mcp_improved.py'")
    sys.exit(1)

async def main():
    # Setup environment variables
    print("Checking environment variables...")
    if not os.environ.get("JFROG_URL"):
        print("JFROG_URL environment variable is not set")
        print("Using default value from previous script: INSERT")
        os.environ["JFROG_URL"] = "INSERT"
    
    if not os.environ.get("JFROG_ACCESS_TOKEN"):
        print("JFROG_ACCESS_TOKEN environment variable is not set")
        print("Using default value from previous script")
        os.environ["JFROG_ACCESS_TOKEN"] = "INSERT"
    
    # Parse command line arguments
    import argparse
    parser = argparse.ArgumentParser(description="Test JFrog Artifactory MCP")
    parser.add_argument("--debug", action="store_true", help="Enable debug output")
    parser.add_argument("--specific-test", help="Run a specific test instead of all tests")
    args = parser.parse_args()
    
    debug = args.debug
    
    if args.specific_test:
        # Run a specific test
        test_name = args.specific_test.lower()
        print(f"Running specific test: {test_name}")
        
        if test_name == "system":
            print("\n=== Testing System Information ===")
            print(await get_system_health(debug=debug))
            print(await get_version(debug=debug))
            print(await get_system_info(debug=debug))
        
        elif test_name == "repository":
            print("\n=== Testing Repository Management ===")
            repo_key = f"test-repo-{os.urandom(4).hex()}"
            print(f"Creating repository {repo_key}...")
            print(await create_repository(repo_key, "local", "generic", debug=debug))
            print(f"Getting repository {repo_key}...")
            print(await get_repository(repo_key, debug=debug))
            print("Listing repositories...")
            print(await list_repositories(debug=debug))
            print(f"Deleting repository {repo_key}...")
            print(await delete_repository(repo_key, debug=debug))
        
        elif test_name == "artifact":
            print("\n=== Testing Artifact Management ===")
            repo_key = f"test-repo-{os.urandom(4).hex()}"
            print(f"Creating repository {repo_key}...")
            await create_repository(repo_key, "local", "generic", debug=debug)
            
            # Create a test file
            with tempfile.NamedTemporaryFile(delete=False, suffix=".txt") as temp:
                temp.write(b"Test artifact content")
                temp_path = temp.name
            
            artifact_path = f"test-artifact-{os.urandom(4).hex()}.txt"
            print(f"Deploying artifact to {repo_key}/{artifact_path}...")
            print(await deploy_artifact(repo_key, artifact_path, temp_path, debug=debug))
            print(f"Getting artifact info for {repo_key}/{artifact_path}...")
            print(await get_artifact_info(repo_key, artifact_path, debug=debug))
            print(f"Searching artifacts in {repo_key}...")
            print(await search_artifacts(repos=repo_key, debug=debug))
            print(f"Deleting artifact {repo_key}/{artifact_path}...")
            print(await delete_artifact(repo_key, artifact_path, debug=debug))
            
            # Cleanup
            os.unlink(temp_path)
            await delete_repository(repo_key, debug=debug)
        
        elif test_name == "user":
            print("\n=== Testing User Management ===")
            username = f"test-user-{os.urandom(4).hex()}"
            email = f"{username}@example.com"
            password = "Test1234!"
            
            print(f"Creating user {username}...")
            print(await create_user(username, email, password, debug=debug))
            print(f"Getting user {username}...")
            print(await get_user(username, debug=debug))
            print(f"Updating user {username}...")
            print(await update_user(username, email=f"updated-{email}", debug=debug))
            print("Listing users...")
            print(await list_users(debug=debug))
            print(f"Deleting user {username}...")
            print(await delete_user(username, debug=debug))
        
        else:
            print(f"Unknown test: {test_name}")
            print("Available tests: system, repository, artifact, user")
    else:
        # Run all tests
        await run_tests(debug=debug)

if __name__ == "__main__":
    asyncio.run(main())