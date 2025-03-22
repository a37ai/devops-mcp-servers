Bitbucket Cloud MCP Server
============================

Overview
--------
The Bitbucket Cloud MCP Server is an implementation built on top of the FastMCP framework, integrating Bitbucket Cloud’s REST API v2.0. It provides a rich suite of tools for managing Bitbucket resources, including user profiles, workspaces, projects, repositories, pull requests, branches, pipelines, snippets, and more. This server enables seamless automation and integration with Bitbucket Cloud using simple function calls.

Features
--------
• Secure Authentication:  
  Uses Basic Authentication with BITBUCKET_USERNAME and BITBUCKET_APP_PASSWORD set via environment variables or context configuration.

• Comprehensive API Toolset:  
  Access user and workspace information, manage projects and repositories, manage branches and tags, work with commits and pull requests, and operate on issues and pipelines.

• Repository Administration:  
  Tools for handling deployment keys, webhooks, branch restrictions, and repository settings.

• Pipelines & Snippets Support:  
  List, trigger, and manage pipelines as well as create and retrieve code snippets through dedicated tools.

• Readable Responses:  
  API responses are formatted as readable JSON, simplifying debugging and integration.

Installation & Setup
----------------------
1. Requirements:
   - Python 3.7 or higher.
   - Required Python packages: httpx, python-dotenv, and any dependencies included in the FastMCP framework.
   - A valid Bitbucket Cloud account with an App Password.

2. Clone or download the repository containing the Bitbucket Cloud MCP Server code.

3. Install the necessary dependencies (for example, using pip):
   pip install httpx python-dotenv fastmcp

4. Environment Configuration:
   Create a .env file in the project root and set your Bitbucket credentials:
  
      BITBUCKET_USERNAME=your_bitbucket_username
      BITBUCKET_APP_PASSWORD=your_bitbucket_app_password

   Alternatively, you can set these values in your system’s environment variables.

Usage
-----
To run the MCP server using the stdio transport, execute the module directly:

   python <filename>.py

Once running, the server provides multiple tool endpoints which can be called via the MCP protocol. The tools include, but are not limited to:

User & Workspace Tools:
  • get_current_user – Retrieves the authenticated user’s profile.
  • get_user_profile – Fetches public profile data for any specified user.
  • list_workspaces – Lists accessible workspaces with optional role filtering.
  • get_workspace – Retrieves details of a specific workspace.

Project & Repository Management:
  • list_projects, create_project, get_project, update_project, delete_project – Manage projects within workspaces.
  • list_repositories, get_repository, create_repository, update_repository, delete_repository – Manage repositories.

Branch & Tag Tools:
  • list_branches, create_branch – Manage branch operations.
  • list_tags, create_tag – Manage tags.

Commit & Source Code Tools:
  • list_commits, get_commit, get_commit_diff – Retrieve commit details and diffs.
  • add_commit_comment – Add comments to commits.
  • get_file_content – Retrieve the contents of a file from a repository.

Pull Request Tools:
  • list_pull_requests, create_pull_request, get_pull_request – Manage pull requests.
  • approve_pull_request, unapprove_pull_request, merge_pull_request, decline_pull_request – Handle PR lifecycle events.
  • add_pull_request_comment – Add comments within pull requests.

Repository Settings & Administration:
  • list_branch_restrictions, create_branch_restriction – Configure branch restrictions.
  • list_deploy_keys, add_deploy_key, delete_deploy_key – Manage deployment keys.
  • list_webhooks, create_webhook, delete_webhook – Manage webhooks.

Issue Tracker:
  • list_issues, create_issue, get_issue, update_issue – Work with Bitbucket issue tracker.
  • add_issue_comment – Add comments to issues.

Pipelines (CI/CD):
  • list_pipelines, trigger_pipeline, get_pipeline, stop_pipeline – Manage pipelines and trigger builds.

Snippets:
  • list_snippets, create_snippet, get_snippet, get_snippet_file, delete_snippet – Manage code snippets.

Customization
-------------
The server leverages helper functions such as get_auth_header and make_request to authenticate and make API calls. The response formatting is handled by format_response, which outputs well-indented JSON responses for ease of debugging and integration.

If additional functionality is needed, custom tools can be added using the @mcp.tool() decorator, extending the server’s capabilities.

Support & Contributing
------------------------
For additional support or to report issues, please contact the repository maintainer. Contributions, bug reports, and feature requests are welcome.

License
-------
[Include your project license here.]

Conclusion
----------
This Bitbucket Cloud MCP Server provides a professional and robust integration with Bitbucket’s API. It is ideal for teams looking to automate repository management, streamline project workflows, and integrate Bitbucket with other systems seamlessly. Enjoy managing your Bitbucket resources programmatically with clarity and efficiency!