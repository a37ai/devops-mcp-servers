GitLab MCP Server
=================

Overview
--------
The GitLab MCP Server is a Model Context Protocol (MCP) implementation that allows AI assistants to interact with GitLab repositories through standardized tools. It provides functionality for file operations, repository management, issue tracking, merge requests, branches, commits, and more—enabling seamless integration with the GitLab API.

Features
--------
• File Operations – Create or update a single file, push multiple files in one commit, and retrieve file contents or directory listings.  
• Repository Management – Create projects, fork repositories, get detailed project information, and search for repositories.  
• Issue & Merge Request Handling – Create issues, list issues, and create merge requests with support for drafts and collaboration settings.  
• Branch & Commit Management – Create branches, list branches, fetch commit details, and list commits with optional pagination and filtering.  
• User Information – Retrieve details for the current authenticated user or other specified users.

Tools Overview
--------------
Each MCP tool is implemented as an asynchronous function, enabling a streamlined approach to executing GitLab API operations. Key tools include:

1. create_or_update_file  
   - Creates or updates a file in a project.  
   - Supports renaming/moving files with an optional previous path.

2. push_files  
   - Pushes multiple files as part of a single commit.  
   - Accepts a list of files with details for creation or update.

3. search_repositories  
   - Searches for GitLab projects based on a query string.  
   - Supports pagination through page number and results per page.

4. create_repository  
   - Creates a new GitLab project with options for description, visibility (private, internal, public), and README initialization.

5. get_file_contents  
   - Retrieves the contents of a file or directory.  
   - Automatically decodes content if base64 encoded.

6. create_issue  
   - Creates a new issue within a project.  
   - Allows specification of title, description, assignees, labels, and milestone.

7. create_merge_request  
   - Creates a new merge request with parameters for source and target branches, title, description, and collaboration settings.

8. fork_repository  
   - Forks an existing project into an optional specified namespace.

9. create_branch  
   - Creates a new branch from an existing reference (default is "main").

10. Additional Tools  
    - list_branches: List project branches with optional search filtering.  
    - list_issues: List issues in a project with filtering options on state, labels, milestone, and title/description search.  
    - get_project_details: Retrieves detailed information about a project.  
    - list_commits: List commits with optional filters like branch/tag and file path.  
    - get_commit_details: Get detailed information about a specific commit.  
    - list_merge_requests: List merge requests in a project, with filters like state, target branch, and source branch.  
    - get_user_info: Retrieve information on a particular user or the authenticated user when no ID is provided.

Configuration & Setup
-----------------------
1. Environment Variables  
   To configure the server, set the following environment variables:

   - GITLAB_PERSONAL_ACCESS_TOKEN  
     Your personal access token for the GitLab API. This token is required for authentication.  

   - GITLAB_API_URL (optional)  
     GitLab API URL endpoint. The default is:  
       https://gitlab.com/api/v4

2. Installation  
   - Ensure Python 3 is installed on your system.  
   - Install required dependencies (e.g., httpx, python-dotenv, and any MCP framework components).  
   - Create a .env file in the project root and define the environment variables:
     
         GITLAB_PERSONAL_ACCESS_TOKEN=your_gitlab_token
         GITLAB_API_URL=https://gitlab.com/api/v4

3. Running the Server  
   Execute the server as a standalone script:
     
         ./gitlab_mcp_server.py
     
   The MCP server will initialize and be ready to process incoming requests using its registered tools.

Usage
-----
The GitLab MCP Server exposes a variety of tools designed for seamless integration with GitLab's API. AI assistants or automated processes can call these MCP tools to:
   
   - Manage repository content (e.g., push files or update content).  
   - Operate on repository settings (e.g., creating branches, forking projects).  
   - Handle issue tracking and merge requests efficiently.

Each tool accepts specific input parameters as described in its docstring. Responses are returned as formatted JSON strings containing details from the GitLab API, including error information if applicable.

Error Handling
--------------
The server implements comprehensive error handling using the httpx library. In cases where the GitLab API returns an error or if there is an issue with the API call, the server returns descriptive error messages, ensuring that issues can be diagnosed and resolved quickly.

Conclusion
----------
The GitLab MCP Server is a powerful integration point for managing GitLab projects via standard MCP tools. With support for extensive repository operations, issue management, and collaborative development processes, this server provides a robust solution for AI-driven code and repository management tasks.

For further details, ensure to review the in-code documentation and adjust configuration settings to match your GitLab environment. Enjoy seamless GitLab integration with your AI assistant!