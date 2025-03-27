Bitbucket Cloud MCP Server
===========================

Overview
--------
The Bitbucket Cloud MCP Server is an implementation of an MCP (Modular Command Protocol) server that integrates directly with the Bitbucket Cloud API v2.0. This server leverages the FastMCP framework along with Pydantic models for input validation and response formatting, providing a robust and scalable solution for interacting with Bitbucket Cloud. The server supports a wide range of Bitbucket functions including user and workspace management, projects and repositories handling, branch/tag operations, commit and pull request operations, issue tracking, pipelines (CI/CD), and snippet management.

Features
--------
•  Authentication Integration: Uses environment variables (BITBUCKET_USERNAME and BITBUCKET_APP_PASSWORD) for secure credentials management.
•  Extensive API Tools: Provides a comprehensive set of tools for user profiles, workspaces, projects, repositories, branches, tags, commits, pull requests, issues, webhooks, deploy keys, pipelines, and snippets.
•  Input Validation: Utilizes Pydantic models to ensure data integrity and proper formatting of API requests and responses.
•  Flexible Data Formatting: Formats all API responses as JSON with clear indentation for readability.
•  Error Handling: Implements robust error checking including HTTP error code responses and JSON validation.

Tools & Endpoints
------------------
The server registers numerous tools that wrap Bitbucket Cloud API endpoints. Some of the key tools include:

User & Workspace Tools
•  get_current_user: Retrieve information about the authenticated Bitbucket user.
•  get_user_profile: Fetch public profile details for a specific user.
•  list_workspaces: List all workspaces available to the authenticated user; supports optional role filtering and pagination.
•  get_workspace: Retrieve detailed information for a given workspace.

Project Management Tools
•  list_projects: List projects within a specified workspace.
•  create_project: Create a new project in a workspace.
•  get_project: Retrieve project details by its key.
•  update_project: Update project metadata such as name, description, and privacy settings.
•  delete_project: Remove a project from the workspace.

Repository Management Tools
•  list_repositories: List repositories globally or within a workspace with optional role filtering.
•  get_repository: Retrieve repository details.
•  create_repository: Create a new Git repository in a workspace.
•  update_repository: Update repository settings.
•  delete_repository: Delete a repository.

Branch & Tag Management Tools
•  list_branches & create_branch: Manage repository branches.
•  list_tags & create_tag: List and create repository tags.

Commit & Source Code Tools
•  list_commits & get_commit: List commits, retrieve commit details and diffs.
•  add_commit_comment: Post comments on specific commits.
•  get_file_content: Fetch raw file content from repositories.

Pull Request Tools
•  list_pull_requests: List pull requests with state and pagination support.
•  create_pull_request: Open a new pull request.
•  get_pull_request: Retrieve details for a specific pull request.
•  approve_pull_request & unapprove_pull_request: Manage pull request approvals.
•  merge_pull_request & decline_pull_request: Handle merging or declining of pull requests.
•  add_pull_request_comment: Comment on pull requests.

Repository Administration Tools
•  list_branch_restrictions & create_branch_restriction: Manage branch restrictions.
•  list_deploy_keys, add_deploy_key & delete_deploy_key: Manage SSH deploy keys.
•  list_webhooks, create_webhook & delete_webhook: Manage repository webhooks.

Issue Tracker Tools
•  list_issues, create_issue, get_issue, update_issue, add_issue_comment: Tools for issue management.

Pipeline (CI/CD) Tools
•  list_pipelines, trigger_pipeline, get_pipeline, stop_pipeline: Tools for managing Bitbucket Pipelines.

Snippet Tools
•  list_snippets: List code snippets globally or by workspace.
•  create_snippet, get_snippet, get_snippet_file, delete_snippet: Manage snippets.

Installation & Setup
--------------------
1. Prerequisites:
   •  Python 3.8+ is required.
   •  Ensure you have pip installed.

2. Clone the repository and navigate to the project directory.

3. Install the required dependencies:

   pip install -r requirements.txt

4. Create a .env file in the project root with the following environment variables:

   BITBUCKET_USERNAME=your_bitbucket_username
   BITBUCKET_APP_PASSWORD=your_bitbucket_app_password

   These credentials are used to authenticate with the Bitbucket Cloud API.

5. Run the MCP server:

   python your_script.py

   When executed directly, the server launches with the stdio transport.

Configuration
-------------
•  API Base URL: The server interacts with Bitbucket Cloud API v2.0 using the base URL https://api.bitbucket.org/2.0.
•  Authentication: The helper function get_auth_header() fetches credentials from environment variables and encodes them as required by Bitbucket using HTTP Basic Auth.
•  Pagination & Validation: All list endpoints use Pydantic models like PaginationParams to validate and control pagination parameters (page number, pagelen, etc.).

Usage
-----
Once running, the server exposes many MCP tools that allow you to interact with Bitbucket functionalities programmatically. You can call these tools from your MCP client or incorporate them into larger applications for automated Bitbucket operations.

For example:
•  Use get_current_user to quickly verify your authentication credentials.
•  Use list_workspaces to enumerate all workspaces you have access to.
•  Integrate create_project and create_repository within your CI/CD pipeline to automate part of your project setup process.

Error Handling
--------------
The server performs extensive error checking for API responses. If an HTTP error code is returned or the JSON response fails to validate against the Pydantic models, descriptive error messages are provided suggesting the potential issue, thus simplifying the debugging process.

Contributing
------------
Contributions, issues, and feature requests are welcome. Please open an issue or submit a pull request on the project repository if you would like to contribute improvements or report bugs.

License
-------
This project is licensed under the MIT License. See the LICENSE file for details.

Contact
-------
For questions or support, please create an issue in the repository or contact the maintainer directly.

This Bitbucket Cloud MCP Server offers a complete, extensible solution for integrating Bitbucket Cloud functionalities into your projects, automated workflows, and development pipelines with ease and reliability. Enjoy seamless Bitbucket automation!