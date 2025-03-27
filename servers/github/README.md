GitHub MCP Server
==================

Overview
--------
GitHub MCP Server is an MCP (Multi-Channel Protocol) server implementation built using FastMCP that integrates with the GitHub API. It provides a seamless interface to interact with GitHub resources such as repositories, files, issues, pull requests, and more. With input validation powered by Pydantic and asynchronous HTTP handling via httpx, this server is designed for robust and efficient GitHub integrations.

Features
--------
• Search Repositories – Execute complex repository searches based on GitHub search syntax, with pagination support.  
• Create Repositories – Easily create new repositories with configuration options (description, privacy, and initialization).  
• File Management – Retrieve file contents (with base64 decoding for text-based files), create new files, or update existing ones.  
• Issue Management – Create new issues or list existing issues with filters (state, labels, sort, and more).  
• Pull Request Creation – Open new pull requests by specifying base and head branches alongside other details.  
• Repository Details – Retrieve detailed information about repositories including stats, topics, and license information.  
• Forking & Branching – Fork repositories and create new branches based on existing branch references.  
• Code Search – Search across GitHub repositories for code snippets using specialized search parameters.

Tools and Endpoints
-------------------
The server currently exposes the following tools as MCP endpoints:

1. search_repositories  
   - Inputs:  
     • query (str): The search query using GitHub syntax  
     • page (int, default 1): Pagination page number  
     • perPage (int, default 30): Number of results per page (max 100 enforced)  
   - Description: Returns a formatted list of repositories matching the search criteria.

2. create_repository  
   - Inputs:  
     • name (str): The intended repository name  
     • description (str, default ""): Optional repository description  
     • private (bool, default False): Whether repository is private  
     • autoInit (bool, default False): Initialize repository with a README  
   - Description: Creates a new repository and returns its details.

3. get_file_contents  
   - Inputs:  
     • owner (str): Repository owner (user or organization)  
     • repo (str): Repository name  
     • path (str): File or directory path  
     • branch (Optional[str]): Specific branch (defaults to repo’s default)  
   - Description: Retrieves file contents or directory listings with proper formatting.

4. create_or_update_file  
   - Inputs:  
     • owner (str), repo (str), path (str)  
     • content (str): New file content  
     • message (str): Commit message  
     • branch (str): Target branch name  
     • sha (Optional[str]): SHA for file update (if applicable)  
   - Description: Creates or updates a file; performs base64 encoding and handles commit creation.

5. create_issue  
   - Inputs:  
     • owner (str), repo (str)  
     • title (str), body (str, default "")  
     • assignees (Optional[List[str]]), labels (Optional[List[str]])  
     • milestone (Optional[int])  
   - Description: Creates an issue in a GitHub repository with detailed configuration options.

6. list_issues  
   - Inputs:  
     • owner (str), repo (str)  
     • state (str, default "open"), labels (Optional[List[str]])  
     • sort (str, default "created"), direction (str, default "desc")  
     • since (Optional[str]), page (int, default 1), per_page (int, default 30)  
   - Description: Retrieves a formatted list of issues based on filters.

7. create_pull_request  
   - Inputs:  
     • owner (str), repo (str)  
     • title (str), head (str), base (str)  
     • body (str, default ""), draft (bool, default False)  
     • maintainer_can_modify (bool, default True)  
   - Description: Opens a new pull request with the specified details.

8. get_repository  
   - Inputs:  
     • owner (str), repo (str)  
   - Description: Returns detailed repository information including stats, topics, and license.

9. fork_repository  
   - Inputs:  
     • owner (str), repo (str)  
     • organization (Optional[str])  
   - Description: Forks the specified repository to the authenticated user’s account or given organization.

10. create_branch  
    - Inputs:  
      • owner (str), repo (str)  
      • branch (str), from_branch (Optional[str])  
    - Description: Creates a new branch based on the provided source branch (or defaults to the repository’s main branch).

11. search_code  
    - Inputs:  
      • q (str): Code search query using GitHub syntax  
      • sort (str, default "indexed"), order (str, default "desc")  
      • per_page (int, default 30), page (int, default 1)  
    - Description: Searches across code repositories and returns matching code fragments along with associated metadata.

Installation & Configuration
------------------------------
1. Environment Setup:  
   • Ensure Python 3.7+ is installed.  
   • Install required packages using pip:
     
     pip install httpx python-dotenv pydantic fastapi mcp-server

2. Environment Variables:  
   • Create a .env file in your project root.  
   • Set the GitHub Personal Access Token required for operations that modify GitHub state:
     
     GITHUB_PERSONAL_ACCESS_TOKEN=your_github_token_here

   Note: Some functionalities (e.g., creating repositories, issues, etc.) require a valid GitHub token.

Running the Server
------------------
Launch the MCP server via the command line. By default, the server uses standard I/O for transport:

  python path/to/your_server_file.py

The server will initialize and expose all available GitHub tools as MCP endpoints. Integration clients can then call these endpoints with the appropriate parameters.

Error Handling & Fallbacks
---------------------------
• All GitHub API interactions are wrapped in robust error handling.  
• In cases of HTTP errors, the tools return informative error messages that include status codes and messages from GitHub.  
• The server validates all inputs using Pydantic models to ensure reliable execution.

Conclusion
----------
The GitHub MCP Server provides a comprehensive suite of tools that simplify interacting with GitHub via a unified multi-channel protocol interface. Its modular design and use of asynchronous operations make it ideal for integrating GitHub functionality into broader systems or automation pipelines.

For further customization and enhancements, refer to the inline documentation within the source code.

Happy Coding!