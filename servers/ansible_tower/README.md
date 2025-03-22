Ansible MCP Server
===================

Overview
--------
The Ansible MCP Server is an implementation of the Model Context Protocol (MCP) designed to interact with the Ansible (Tower/AWX) API. It provides a wide range of tools to manage inventories, hosts, groups, job templates, projects, credentials, organizations, teams, users, and ad hoc commands, along with system information endpoints. This server allows you to integrate Ansible capabilities into your applications efficiently.

Features
--------
• Comprehensive API Integration – Manage inventories, hosts, job templates, projects, credentials, and more via dedicated endpoints.  
• Pagination Support – Handle large result sets through built-in pagination.  
• Robust Error Handling – Provides useful error messages when API calls fail or return invalid responses.  
• JSON Friendly – Inputs and outputs are managed as JSON, making integration and debugging easier.  
• Secure Authentication – Supports token generation and header-based authorization for secure API access.  
• Extensible Design – Built using FastMCP, allowing for adding new tools with minimal effort.

Tools Overview
--------------
The server is organized into several tool categories that correspond directly to Ansible API resources:

Inventory Management
--------------------
• list_inventories(limit, offset): List all inventories.  
• get_inventory(inventory_id): Retrieve details for a specific inventory.  
• create_inventory(name, organization_id, description): Create a new inventory.  
• update_inventory(inventory_id, name, description): Update an existing inventory.  
• delete_inventory(inventory_id): Delete an inventory.

Host Management
---------------
• list_hosts(inventory_id, limit, offset): List hosts (optionally filtering by inventory).  
• get_host(host_id): Get details of a specific host.  
• create_host(name, inventory_id, variables, description): Create a new host in an inventory.  
• update_host(host_id, name, variables, description): Update an existing host.  
• delete_host(host_id): Delete a host.

Group Management
----------------
• list_groups(inventory_id, limit, offset): List groups within an inventory.  
• get_group(group_id): Get details about a specific group.  
• create_group(name, inventory_id, variables, description): Create a new group.  
• update_group(group_id, name, variables, description): Update an existing group.  
• delete_group(group_id): Delete a group.  
• add_host_to_group(group_id, host_id): Add an existing host to a group.  
• remove_host_from_group(group_id, host_id): Remove a host from a group.

Job Template Management
-----------------------
• list_job_templates(limit, offset): List all job templates.  
• get_job_template(template_id): Get details about a specific job template.  
• create_job_template(...): Create a new job template using provided parameters such as inventory, project, playbook, and extra variables.  
• update_job_template(template_id, ...): Update an existing job template.  
• delete_job_template(template_id): Delete a job template.  
• launch_job(template_id, extra_vars): Launch a job from a job template.

Job Management
--------------
• list_jobs(status, limit, offset): List jobs, with optional filtering by status.  
• get_job(job_id): Retrieve details of a specific job.  
• cancel_job(job_id): Cancel a running job.  
• get_job_events(job_id, limit, offset): Retrieve job events.  
• get_job_stdout(job_id, format): Retrieve job standard output in text, HTML, JSON, or ANSI formats.

Project Management
------------------
• list_projects(limit, offset): List all projects.  
• get_project(project_id): Retrieve details for a specific project.  
• create_project(...): Create a new project with SCM integration.  
• update_project(project_id, ...): Update existing project details.  
• delete_project(project_id): Delete a project.  
• sync_project(project_id): Sync a project with its SCM source.

Credential Management
---------------------
• list_credentials(limit, offset): List all credentials.  
• get_credential(credential_id): Retrieve details of a specific credential.  
• list_credential_types(limit, offset): List available credential types.  
• create_credential(...): Create a new credential.  
• update_credential(credential_id, ...): Update an existing credential.  
• delete_credential(credential_id): Delete a credential.

Organization & Team Management
-------------------------------
• list_organizations(): List all organizations.  
• get_organization(organization_id): Get details for a specific organization.  
• create_organization(name, description): Create a new organization.  
• update_organization(organization_id, name, description): Update an organization.  
• delete_organization(organization_id): Delete an organization.

• list_teams(organization_id, limit, offset): List teams, optionally filtering by organization.  
• get_team(team_id): Get details of a specific team.  
• create_team(name, organization_id, description): Create a new team.  
• update_team(team_id, name, description): Update team details.  
• delete_team(team_id): Delete a team.

User Management
---------------
• list_users(limit, offset): List all users.  
• get_user(user_id): Get details about a user.  
• create_user(...): Create a new user with options for superuser and system auditor privileges.  
• update_user(user_id, ...): Update an existing user.  
• delete_user(user_id): Delete a user.

Ad Hoc Commands
---------------
• run_ad_hoc_command(inventory_id, credential_id, module_name, module_args, limit, verbosity): Run an ad hoc command against hosts.  
• get_ad_hoc_command(command_id): Get details about a specific ad hoc command.  
• cancel_ad_hoc_command(command_id): Cancel a running ad hoc command.

Workflow Templates & Jobs
-------------------------
• list_workflow_templates(limit, offset): List all workflow templates.  
• get_workflow_template(template_id): Get details for a specific workflow template.  
• launch_workflow(template_id, extra_vars): Launch a workflow job.  
• list_workflow_jobs(status, limit, offset): List workflow jobs with optional status filtering.  
• get_workflow_job(job_id): Get details about a specific workflow job.  
• cancel_workflow_job(job_id): Cancel a running workflow job.

Schedule Management
-------------------
• list_schedules(unified_job_template_id, limit, offset): List schedules, optionally filtering by a job or workflow template.  
• get_schedule(schedule_id): Retrieve schedule details.  
• create_schedule(...): Create a new schedule using an iCal recurrence rule and extra data.  
• update_schedule(schedule_id, ...): Update an existing schedule.  
• delete_schedule(schedule_id): Delete a schedule.

System Information
------------------
• get_ansible_version(): Retrieve version information for Ansible Tower/AWX.  
• get_dashboard_stats(): Get dashboard statistics from Ansible.  
• get_metrics(): Retrieve system metrics.

Configuration
-------------
Before running the server, configure the following environment variables (typically via a .env file):

• ANSIBLE_BASE_URL – The base URL for your Ansible Tower/AWX instance.  
• ANSIBLE_USERNAME – The username used to log in (if token-based authentication is not pre-configured).  
• ANSIBLE_PASSWORD – The corresponding password for the user.  
• ANSIBLE_TOKEN – An API token for direct authentication (optional if using username/password).

Ensure that your system trusts the Ansible server’s SSL certificates or disable verification (as shown in the code).

Installation & Setup
--------------------
1. Ensure you have Python 3 installed.  
2. Install the required dependencies (e.g., requests, python-dotenv, FastMCP). This can be done via pip:
  
   pip install requests python-dotenv fastmcp

3. Create a .env file in the server directory with your Ansible API credentials:

   ANSIBLE_BASE_URL=https://your-ansible-instance.example.com  
   ANSIBLE_USERNAME=your_username  
   ANSIBLE_PASSWORD=your_password  
   # Optionally, provide a token if already generated  
   ANSIBLE_TOKEN=your_token

4. Make the script executable (if on a Unix-like system):

   chmod +x path/to/ansible_mcp_server.py

Running the Server
------------------
To start the server using stdio transport, run:

   ./ansible_mcp_server.py

This will initialize the FastMCP server and expose all defined tools through the MCP protocol.

Usage
-----
Each tool is invoked via the MCP protocol and accepts JSON-formatted input parameters. Tools are self-documented via function docstrings that detail required arguments and their purpose. For example, to list inventories you may call the list_inventories tool with optional limit and offset parameters.

Support & Contributions
-----------------------
Contributions, issues, and feature requests are welcome. If you encounter any problems or have suggestions for improvement, please open an issue or submit a pull request on the project repository.

License
-------
Distributed under the terms of your chosen open source license. See the LICENSE file for details.

Contact
-------
For any further inquiries, please contact the maintainer at [your-email@example.com].

This README provides a comprehensive overview of the Ansible MCP Server, its features, configuration, and operation. Use this guide as a reference to integrate, extend, or troubleshoot the server in your environment. Enjoy seamless integration with Ansible Tower/AWX!