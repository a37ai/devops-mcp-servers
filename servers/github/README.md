GitHub MCP Server
==================

Overview
--------
GitHub MCP Server is an asynchronous implementation of an MCP server that integrates with the GitHub API. This server exposes a suite of tools enabling users to perform a variety of GitHub operations including repository searches, repository creation, file management, issue tracking, pull request creation, branch management, and code searches. By leveraging the GitHub API, this server allows for seamless integration and automation of GitHub workflows.

Features
--------
•  Repository Search  
  - Search for GitHub repositories using custom queries with pagination support.

•  Repository Creation  
  - Create new repositories with options for descriptions, privacy settings, and README initialization.

•  File Handling  
  - Retrieve file or directory contents from a repository.  
  - Create or update files in any repository.

•  Issue Management  
  - Create new issues with labels, assignees, and milestones.  
  - List and filter issues based on various criteria like state, labels, and date.

•  Pull Request Management  
  - Create pull requests with options to set draft mode and allow maintainer modifications.

•  Branch Management  
  - Create new branches based on a specified or default branch.

•  Code Search  
  - Search for code snippets across GitHub repositories with detailed result listings.

Tools and Endpoints
-------------------
The GitHub MCP Server defines multiple tools as endpoints using asynchronous functions. Below is a summary of the available tools:

1. search_repositories(query: str, page: int = 1, perPage: int = 30)  
  Search for repositories using GitHub search syntax.  
  Returns a detailed list of repositories, including information like the repository name, description, stars, forks, language, and URL.

2. create_repository(name: str, description: str = "", private: bool = False, autoInit: bool = False)  
  Create a new repository on GitHub.  
  Requires a valid GitHub Personal Access Token.  
  Returns confirmation with repository details.

3. get_file_contents(owner: str, repo: str, path: str, branch: str = None)  
  Retrieve contents of a file or directory in a specified repository.  
  Supports directory listings and file content decoding (base64).

4. create_or_update_file(owner: str, repo: str, path: str, content: str, message: str, branch: str, sha: str = None)  
  Create or update a file in a repository.  
  Handles file encoding and commit message preparation.

5. create_issue(owner: str, repo: str, title: str, body: str = "", assignees: List[str] = None, labels: List[str] = None, milestone: int = None)  
  Create a new issue with the option to add labels, assign users, and specify milestones.  
  Requires authentication via GitHub token.

6. list_issues(owner: str, repo: str, state: str = "open", labels: List[str] = None, sort: str = "created", direction: str = "desc", since: str = None, page: int = 1, per_page: int = 30)  
  List and filter issues from a repository.  
  Supports sorting, pagination, and filtering by state, labels, and date.

7. create_pull_request(owner: str, repo: str, title: str, head: str, base: str, body: str = "", draft: bool = False, maintainer_can_modify: bool = True)  
  Create a new pull request between branches.  
  Includes options for draft status and maintainer modifications.

8. get_repository(owner: str, repo: str)  
  Retrieve comprehensive details about a repository, including description, stats, license, topics, and more.

9. fork_repository(owner: str, repo: str, organization: str = None)  
  Fork an existing repository to your account or to a specified organization.  
  Requires a valid GitHub token.

10. create_branch(owner: str, repo: str, branch: str, from_branch: str = None)  
  Create a new branch based on an existing branch (defaults to the repository’s default branch).  
  Requires GitHub token authentication.

11. search_code(q: str, sort: str = "indexed", order: str = "desc", per_page: int = 30, page: int = 1)  
  Perform a code search across GitHub repositories using code search syntax.  
  Returns formatted search results with file details and direct URLs.

Configuration and Setup
-----------------------
1. Environment Variables  
  •  Create a .env file in the project root.  
  •  Set the following environment variable:  
    GITHUB_PERSONAL_ACCESS_TOKEN=your_personal_access_token_here

  Note: Without a valid GitHub token, certain functionalities (e.g., repository creation, file modifications, and issue management) will be limited or unavailable.

2. Required Dependencies  
  •  Python 3.7+  
  •  Dependencies: mcp.server.fastmcp, httpx, python-dotenv  
    Ensure you install the necessary packages using pip:  
    pip install httpx python-dotenv mcp

3. Running the Server  
  Run the server with the following command:  
    python <filename>.py

  The server uses stdio as its transport mechanism, making it ideal for integration with other systems.

Usage
-----
Once the server is running, you can interact with the exposed tools to perform GitHub operations. Each tool is decorated using the MCP framework, meaning that input parameters and expected returns are clearly documented for integration and automation.

Example Usage:
  - Executing a repository search:
    search_repositories(query="machine learning", page=1, perPage=20)

  - Creating a new repository:
    create_repository(name="new-project", description="A new GitHub project", private=False, autoInit=True)

Support and Contributions
-------------------------
For issues, feature requests, or contributions, please refer to the project’s repository or contact the maintainers. Contributions are welcome—please ensure adherence to coding standards and provide appropriate tests for new features.

License
-------
This project is made available under [Specify License Here].

Acknowledgements
----------------
Thank you for using the GitHub MCP Server. Special thanks to GitHub for their API and to the open source community for the development tools enabling this project.

Happy Coding!