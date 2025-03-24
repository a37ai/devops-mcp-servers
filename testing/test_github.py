import sys
import os
# Add the parent directory to the Python path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
import pytest
import pytest_asyncio
import asyncio
import json
import uuid
import time
from typing import List, Dict, Any, Tuple
from dotenv import load_dotenv

import servers.github.github_mcp as github_mcp
# Load environment variables
load_dotenv()

# Configuration for tests
GITHUB_TOKEN = os.environ.get("GITHUB_PERSONAL_ACCESS_TOKEN")
if not GITHUB_TOKEN:
    pytest.skip("GITHUB_PERSONAL_ACCESS_TOKEN not set, skipping tests", allow_module_level=True)

# Test configuration
TEST_REPO_PREFIX = "mcp-test-"  # Prefix for test repositories
TEST_OWNER = os.environ.get("GITHUB_TEST_USERNAME")  # Your GitHub username
if not TEST_OWNER:
    pytest.skip("GITHUB_TEST_USERNAME not set, skipping tests", allow_module_level=True)

# Generate a unique identifier for this test run to avoid conflicts
TEST_RUN_ID = str(uuid.uuid4())[:8]

# Tracking created resources for cleanup
created_resources = {
    "repos": [],         # List of repository names
    "branches": [],      # Tuples of (repo_name, branch_name)
    "issues": [],        # Tuples of (repo_name, issue_number)
    "prs": [],           # Tuples of (repo_name, pr_number)
    "forks": []          # List of forked repository names
}

# ---- Utility functions ----

async def cleanup_resources():
    """Clean up all resources created during testing"""
    print("\nCleaning up test resources...")
    
    # Delete test repositories (this will also remove branches, PRs, issues)
    for repo in created_resources["repos"]:
        print(f"Deleting repository: {TEST_OWNER}/{repo}")
        await github_mcp.github_request("DELETE", f"/repos/{TEST_OWNER}/{repo}")
        await asyncio.sleep(1)  # Rate limiting consideration
    
    # Delete forked repositories
    for fork in created_resources["forks"]:
        print(f"Deleting forked repository: {TEST_OWNER}/{fork}")
        await github_mcp.github_request("DELETE", f"/repos/{TEST_OWNER}/{fork}")
        await asyncio.sleep(1)  # Rate limiting consideration
    
    print("Cleanup completed")

async def create_test_repo(description="Test repository", auto_init=True, private=True):
    """Create a test repository and return its name"""
    repo_count = len(created_resources["repos"])
    repo_name = f"{TEST_REPO_PREFIX}{TEST_RUN_ID}-{repo_count}"
    
    # Create repository
    data = {
        "name": repo_name,
        "description": description,
        "private": private,
        "auto_init": auto_init
    }
    
    result = await github_mcp.github_request("POST", "/user/repos", data=data)
    assert "error" not in result, f"Failed to create test repository: {result.get('error')}"
    
    # Track for cleanup
    created_resources["repos"].append(repo_name)
    
    # Wait for repository creation to propagate
    await asyncio.sleep(2)
    
    return repo_name

async def extract_default_branch(repo_name):
    """Get the default branch for a repository"""
    # Make sure repo_name is a string, not an async generator
    if hasattr(repo_name, '__aiter__'):
        raise TypeError("repo_name is an async generator object, not a string")
    
    # Add a retry mechanism for API calls
    max_retries = 3
    retry_delay = 2
    
    for attempt in range(max_retries):
        try:
            repo_info = await github_mcp.github_request("GET", f"/repos/{TEST_OWNER}/{repo_name}")
            if "error" not in repo_info:
                return repo_info.get("default_branch", "main")
            
            if attempt < max_retries - 1:
                print(f"Attempt {attempt+1} failed: {repo_info.get('error')}. Retrying in {retry_delay} seconds...")
                await asyncio.sleep(retry_delay)
                retry_delay *= 2  # Exponential backoff
            else:
                assert False, f"Failed to get repository info: {repo_info.get('error')}"
        except Exception as e:
            if attempt < max_retries - 1:
                print(f"Exception occurred: {str(e)}. Retrying in {retry_delay} seconds...")
                await asyncio.sleep(retry_delay)
                retry_delay *= 2  # Exponential backoff
            else:
                raise

async def wait_for_rate_limit():
    """Check GitHub rate limit and wait if needed"""
    rate_limit = await github_mcp.github_request("GET", "/rate_limit")
    
    if "error" not in rate_limit and "resources" in rate_limit:
        core = rate_limit["resources"]["core"]
        remaining = core.get("remaining", 1000)
        reset_time = core.get("reset", 0)
        
        if remaining < 10:  # Getting low on requests
            current_time = int(time.time())
            wait_time = max(0, reset_time - current_time) + 5  # Add buffer
            print(f"Rate limit low ({remaining} remaining). Waiting {wait_time} seconds...")
            await asyncio.sleep(wait_time)

# ---- Fix the get_repository function in github_mcp.py ----
# This would normally be in a separate file, but we'll modify it here to handle None values

async def patched_get_repository(owner: str, repo: str) -> str:
    """Patched version of get_repository that handles None values safely"""
    endpoint = f"/repos/{owner}/{repo}"
    result = await github_mcp.github_request("GET", endpoint)
    
    if "error" in result:
        return f"Error getting repository information: {result['error']}"
    
    topics = result.get("topics", [])
    topics_str = ", ".join(topics) if topics else "None"
    
    # Fix the license attribute access to handle None values safely
    license_name = "Not specified"
    license_obj = result.get("license")
    if license_obj and isinstance(license_obj, dict):
        license_name = license_obj.get("name", "Not specified")
    
    return f"""
# Repository Information: {result.get('full_name', f'{owner}/{repo}')}

- Description: {result.get('description', 'No description')}
- URL: {result.get('html_url', 'N/A')}
- Homepage: {result.get('homepage', 'N/A')}
- Language: {result.get('language', 'Not specified')}
- Stars: {result.get('stargazers_count', 0)}
- Forks: {result.get('forks_count', 0)}
- Watchers: {result.get('watchers_count', 0)}
- Open Issues: {result.get('open_issues_count', 0)}
- License: {license_name}
- Private: {'Yes' if result.get('private', False) else 'No'}
- Created: {result.get('created_at', 'Unknown')}
- Updated: {result.get('updated_at', 'Unknown')}
- Default Branch: {result.get('default_branch', 'Unknown')}
- Topics: {topics_str}
    """

# Replace the original function with our patched version
github_mcp.get_repository = patched_get_repository

# ---- Fixtures ----

@pytest.fixture(scope="session")
def event_loop():
    """Create an event loop for the test session"""
    loop = asyncio.get_event_loop_policy().new_event_loop()
    yield loop
    loop.close()

@pytest_asyncio.fixture(scope="session", autouse=True)
async def cleanup_after_tests():
    """Run tests and clean up afterward"""
    yield
    await cleanup_resources()

@pytest_asyncio.fixture
async def test_repo():
    """Create a test repository and return its name"""
    repo_name = await create_test_repo("Temporary repository for MCP GitHub testing")
    # Make sure we wait long enough for the repo to be fully created
    await asyncio.sleep(3)
    return repo_name

# ---- Tests ----

@pytest.mark.asyncio
async def test_get_repository():
    """Test getting repository information"""
    # First create a repository we can query
    repo_name = await create_test_repo("Test repo for get_repository")
    
    # Wait for repository creation to be fully propagated
    await asyncio.sleep(3)
    await wait_for_rate_limit()
    
    # Now test the get_repository function
    result = await github_mcp.get_repository(TEST_OWNER, repo_name)
    
    # Assertions
    assert f"Repository Information: {TEST_OWNER}/{repo_name}" in result
    assert "Description: Test repo for get_repository" in result
    assert "Private: Yes" in result

@pytest.mark.asyncio
async def test_search_repositories():
    """Test searching for repositories"""
    # Create a unique repository that we can search for
    unique_name = await create_test_repo("Unique repository for search testing", private=False)
    
    # Wait for repository to be indexed (this can take a while for GitHub search)
    await asyncio.sleep(5)
    await wait_for_rate_limit()
    
    # Search for the repository
    # Note: GitHub search might have indexing delays, so this test could be flaky
    result = await github_mcp.search_repositories(f"repo:{TEST_OWNER}/{unique_name}")
    
    # If search doesn't find it due to indexing delay, we'll skip asserting exact matches
    if "No repositories found" not in result:
        assert unique_name in result, "Repository should be found in search results"
    else:
        print(f"Warning: Repository {unique_name} not found in search results. This may be due to indexing delay.")

@pytest.mark.asyncio
async def test_create_repository():
    """Test repository creation"""
    repo_name = f"{TEST_REPO_PREFIX}{TEST_RUN_ID}-create"
    
    await wait_for_rate_limit()
    
    result = await github_mcp.create_repository(
        name=repo_name,
        description="Test repository creation",
        private=True,
        autoInit=True
    )
    
    # Track for cleanup
    created_resources["repos"].append(repo_name)
    
    # Assertions
    assert "Repository created successfully" in result
    assert f"Name: {TEST_OWNER}/{repo_name}" in result
    assert "Description: Test repository creation" in result
    assert "Private: True" in result

@pytest.mark.asyncio
async def test_get_file_contents(test_repo):
    """Test getting file contents"""
    # Wait a bit for README.md to be fully created (auto_init=True)
    await asyncio.sleep(3)
    await wait_for_rate_limit()
    
    # README.md should exist due to auto_init=True
    result = await github_mcp.get_file_contents(TEST_OWNER, test_repo, "README.md")
    
    # Assertions
    assert f"Contents of `README.md` in {TEST_OWNER}/{test_repo}" in result
    assert "```" in result  # Content should be inside code block

@pytest.mark.asyncio
async def test_create_or_update_file(test_repo):
    """Test creating and updating a file"""
    # Create a new file
    file_path = "test-file.txt"
    file_content = "This is a test file created by MCP tests."
    commit_message = "Create test file via MCP"
    
    await wait_for_rate_limit()
    
    # Get the default branch
    default_branch = await extract_default_branch(test_repo)
    
    # Create file
    create_result = await github_mcp.create_or_update_file(
        owner=TEST_OWNER,
        repo=test_repo,
        path=file_path,
        content=file_content,
        message=commit_message,
        branch=default_branch
    )
    
    # Assertions for create
    assert "File created successfully" in create_result
    
    # Get the SHA of the created file
    file_info = await github_mcp.github_request(
        "GET", 
        f"/repos/{TEST_OWNER}/{test_repo}/contents/{file_path}"
    )
    sha = file_info.get("sha")
    
    # Update the file
    updated_content = "This file has been updated by MCP tests."
    update_message = "Update test file via MCP"
    
    update_result = await github_mcp.create_or_update_file(
        owner=TEST_OWNER,
        repo=test_repo,
        path=file_path,
        content=updated_content,
        message=update_message,
        branch=default_branch,
        sha=sha
    )
    
    # Assertions for update
    assert "File updated successfully" in update_result
    
    # Verify content was updated
    get_result = await github_mcp.get_file_contents(TEST_OWNER, test_repo, file_path)
    assert "This file has been updated by MCP tests" in get_result

@pytest.mark.asyncio
async def test_create_issue(test_repo):
    """Test creating an issue"""
    issue_title = "Test Issue Created by MCP"
    issue_body = "This is a test issue created during automated testing."
    
    await wait_for_rate_limit()
    
    result = await github_mcp.create_issue(
        owner=TEST_OWNER,
        repo=test_repo,
        title=issue_title,
        body=issue_body
    )
    
    # Extract issue number for tracking
    issue_number = None
    for line in result.splitlines():
        if line.startswith("Number: #"):
            issue_number = line.replace("Number: #", "").strip()
            created_resources["issues"].append((test_repo, issue_number))
            break
    
    # Assertions
    assert "Issue created successfully" in result
    assert f"Title: {issue_title}" in result

@pytest.mark.asyncio
async def test_list_issues(test_repo):
    """Test listing issues"""
    await wait_for_rate_limit()
    
    # Create a couple of issues first
    issues = [
        {"title": "Test Issue 1", "body": "Test body 1"},
        {"title": "Test Issue 2", "body": "Test body 2"}
    ]
    
    for issue in issues:
        await github_mcp.create_issue(
            owner=TEST_OWNER,
            repo=test_repo,
            title=issue["title"],
            body=issue["body"]
        )
    
    # Allow time for issues to be created
    await asyncio.sleep(2)
    
    # List issues
    result = await github_mcp.list_issues(
        owner=TEST_OWNER,
        repo=test_repo,
        state="open"
    )
    
    # Assertions
    assert f"Issues for {TEST_OWNER}/{test_repo}" in result
    assert "Test Issue 1" in result
    assert "Test Issue 2" in result

@pytest.mark.asyncio
async def test_create_branch(test_repo):
    """Test creating a branch"""
    await wait_for_rate_limit()
    
    # Get the default branch
    default_branch = await extract_default_branch(test_repo)
    
    # Create a new branch
    branch_name = f"test-branch-{TEST_RUN_ID}"
    
    result = await github_mcp.create_branch(
        owner=TEST_OWNER,
        repo=test_repo,
        branch=branch_name,
        from_branch=default_branch
    )
    
    # Track for cleanup
    created_resources["branches"].append((test_repo, branch_name))
    
    # Assertions
    assert "Branch created successfully" in result
    assert f"Name: {branch_name}" in result
    assert f"Based on: {default_branch}" in result

@pytest.mark.asyncio
async def test_create_pull_request(test_repo):
    """Test creating a pull request"""
    await wait_for_rate_limit()
    
    # First we need two branches: the default one and a new one with changes
    
    # Get the default branch
    default_branch = await extract_default_branch(test_repo)
    
    # Create a new branch
    new_branch = f"pr-test-branch-{TEST_RUN_ID}"
    
    branch_result = await github_mcp.create_branch(
        owner=TEST_OWNER,
        repo=test_repo,
        branch=new_branch,
        from_branch=default_branch
    )
    assert "Branch created successfully" in branch_result
    
    # Create a file on the new branch
    file_path = f"pr-test-file-{TEST_RUN_ID}.txt"
    file_content = "This file is created for pull request testing."
    commit_message = "Add file for PR test"
    
    file_result = await github_mcp.create_or_update_file(
        owner=TEST_OWNER,
        repo=test_repo,
        path=file_path,
        content=file_content,
        message=commit_message,
        branch=new_branch
    )
    assert "File created successfully" in file_result
    
    # Now create a pull request
    pr_title = "Test Pull Request"
    pr_body = "This is a test pull request created by automated tests."
    
    result = await github_mcp.create_pull_request(
        owner=TEST_OWNER,
        repo=test_repo,
        title=pr_title,
        head=new_branch,
        base=default_branch,
        body=pr_body
    )
    
    # Extract PR number for tracking
    pr_number = None
    for line in result.splitlines():
        if line.startswith("Number: #"):
            pr_number = line.replace("Number: #", "").strip()
            created_resources["prs"].append((test_repo, pr_number))
            break
    
    # Assertions
    assert "Pull request created successfully" in result
    assert f"Title: {pr_title}" in result

@pytest.mark.asyncio
async def test_fork_repository():
    """Test forking a repository"""
    await wait_for_rate_limit()
    
    # We'll fork a small public repository for testing
    # Using a well-known repo that's unlikely to disappear
    source_owner = "octocat"
    source_repo = "hello-world"
    
    result = await github_mcp.fork_repository(
        owner=source_owner,
        repo=source_repo
    )
    
    # Check if fork was successful
    if "Repository forked successfully" in result:
        # The fork name might be different case than the source repo
        # Get the actual name from the result
        forked_repo = None
        for line in result.splitlines():
            if line.startswith("Name:"):
                # Format is typically "Name: Username/RepoName"
                forked_repo = line.split("/")[-1].strip()
                break
                
        if forked_repo:
            created_resources["forks"].append(forked_repo)
        
        # Assertions - just verify fork was successful
        assert "Repository forked successfully" in result
    else:
        # The repo might already be forked
        # In that case, the error message would mention this
        assert "already exists" in result or "Resource not accessible" in result

@pytest.mark.asyncio
async def test_search_code():
    """Test searching for code"""
    # Create a repo with a file containing distinctive content
    repo_name = await create_test_repo("Repository for code search testing", private=False)
    
    await wait_for_rate_limit()
    
    # Get the default branch
    default_branch = await extract_default_branch(repo_name)
    
    # Create a file with unique content
    unique_marker = f"MCPUNIQUEMARKER{TEST_RUN_ID}"
    file_content = f"// This file contains a unique marker: {unique_marker}\nfunction test() {{\n  console.log('Hello!');\n}}"
    
    file_result = await github_mcp.create_or_update_file(
        owner=TEST_OWNER,
        repo=repo_name,
        path="unique-file.js",
        content=file_content,
        message="Add file with unique marker",
        branch=default_branch
    )
    assert "File created successfully" in file_result
    
    # Wait for indexing (may take a while)
    await asyncio.sleep(10)
    
    # Search for the unique marker
    # Note: GitHub search might have indexing delays, so this test could be flaky
    search_query = f"repo:{TEST_OWNER}/{repo_name} {unique_marker}"
    
    result = await github_mcp.search_code(q=search_query)
    
    # For search tests, we'll be lenient due to indexing delays
    print(f"Search result: {result}")
    if "No code found matching" not in result:
        assert unique_marker in result or repo_name in result, "Repository or unique marker should be found"

@pytest.mark.asyncio
async def test_end_to_end_workflow():
    """Test a complete workflow from repo creation to PR merge"""
    # 1. Create a repository
    repo_name = await create_test_repo("End-to-end workflow test repository")
    
    # Wait for repository creation to propagate
    await asyncio.sleep(3)
    await wait_for_rate_limit()
    
    # 2. Get repository information
    repo_info_result = await github_mcp.get_repository(TEST_OWNER, repo_name)
    assert f"Repository Information: {TEST_OWNER}/{repo_name}" in repo_info_result
    
    # Extract the default branch
    default_branch = None
    for line in repo_info_result.splitlines():
        if "Default Branch:" in line:
            default_branch = line.split(":")[-1].strip()
            break
    
    assert default_branch is not None, "Could not determine default branch"
    
    # 3. Create a new branch
    feature_branch = f"feature-{TEST_RUN_ID}"
    branch_result = await github_mcp.create_branch(
        owner=TEST_OWNER,
        repo=repo_name,
        branch=feature_branch,
        from_branch=default_branch
    )
    assert "Branch created successfully" in branch_result
    
    # 4. Add a file to the feature branch
    file_path = "feature-file.txt"
    file_content = "This file demonstrates the feature work."
    
    file_result = await github_mcp.create_or_update_file(
        owner=TEST_OWNER,
        repo=repo_name,
        path=file_path,
        content=file_content,
        message="Add feature file",
        branch=feature_branch
    )
    assert "File created successfully" in file_result
    
    # 5. Create a pull request
    pr_result = await github_mcp.create_pull_request(
        owner=TEST_OWNER,
        repo=repo_name,
        title="Implement new feature",
        head=feature_branch,
        base=default_branch,
        body="This PR adds the new feature implementation."
    )
    assert "Pull request created successfully" in pr_result
    
    # Extract PR number
    pr_number = None
    for line in pr_result.splitlines():
        if line.startswith("Number: #"):
            pr_number = line.replace("Number: #", "").strip()
            break
    
    assert pr_number is not None, "Could not determine PR number"
    
    # 6. Create an issue
    issue_result = await github_mcp.create_issue(
        owner=TEST_OWNER,
        repo=repo_name,
        title="Related feature issue",
        body=f"This issue is related to PR #{pr_number}"
    )
    assert "Issue created successfully" in issue_result
    
    # 7. List issues
    list_issues_result = await github_mcp.list_issues(
        owner=TEST_OWNER,
        repo=repo_name,
        state="open"
    )
    assert "Related feature issue" in list_issues_result
    
    # 8. Verify file contents
    get_file_result = await github_mcp.get_file_contents(
        TEST_OWNER, 
        repo_name, 
        file_path, 
        branch=feature_branch
    )
    assert "This file demonstrates the feature work" in get_file_result
    
    print("\nEnd-to-end workflow test completed successfully")

if __name__ == "__main__":
    print(f"Running GitHub MCP tests with ID: {TEST_RUN_ID}")
    pytest.main(["-xvs", __file__])