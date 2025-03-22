Jenkins MCP Server
===================

Overview
--------
The Jenkins MCP Server is an implementation of an MCP (Microservice Control Protocol) server that provides a comprehensive set of tools to interact with a Jenkins instance. Built on top of FastMCP, this server integrates with the Jenkins API to offer functionalities for monitoring, building, and managing Jenkins jobs, builds, plugins, nodes, and configurations. It streamlines common Jenkins operations and simplifies automation by exposing them as callable MCP tools.

Features
--------
• Comprehensive Jenkins API Integration  
  – Retrieve Jenkins server details, version, and basic configuration  
  – Manage jobs: get details, trigger builds, stop builds, enable/disable, and delete jobs

• Build and Pipeline Management  
  – Fetch build statuses including the last build, last successful/failed builds  
  – Get build lists and console outputs for detailed analysis  
  – Update build descriptions and configurations

• Plugin and Node Management  
  – Retrieve details on installed plugins  
  – Install new plugins on demand  
  – Monitor node details and track running builds

• CSRF Protection Support  
  – Retrieve a security crumb for safe POST requests

Configuration
-------------
Before running the server, ensure you have set up the necessary Jenkins environment variables. Create a .env file in the project root or configure your environment with the following:

• JENKINS_URL  
  The base URL of your Jenkins server (e.g., https://jenkins.example.com)

• JENKINS_USER  
  Your Jenkins username for API access

• JENKINS_API_TOKEN  
  Your Jenkins API token for authentication

• JENKINS_VERIFY_SSL  
  (Optional) Specify whether to verify SSL certificates (default is "false")

Installation and Setup
----------------------
1. Install required dependencies:
   • Python 3.x
   • requests
   • python-dotenv
   • FastMCP (provided by the mcp.server package)

   You can install dependencies via pip:
   
      pip install requests python-dotenv

2. Configure your environment:
   • Create a .env file in your project directory with the required Jenkins configuration variables.

3. Run the server:
   • Execute the Python script:
     
         python <script_name>.py

   The server will start and print a confirmation message indicating the Jenkins URL to which it is connected.

Tools and Endpoints
-------------------
Each function decorated with @mcp.tool() exposes an MCP tool to interact with the Jenkins API. Below is an overview of the available tools along with a brief description and required parameters where applicable:

1. get_jenkins_version
   • Description: Returns Jenkins server version and basic information.
   • HTTP Method: GET

2. get_job_details
   • Description: Retrieves detailed information about a specific Jenkins job.
   • Inputs:
     - job_name (string): Name of the Jenkins job

3. get_last_build_status
   • Description: Fetches the status of the last build for a given job.
   • Inputs:
     - job_name (string): Name of the Jenkins job

4. trigger_build
   • Description: Triggers a build for a specified job, with support for optional build parameters.
   • Inputs:
     - job_name (string): Name of the Jenkins job
     - parameters (optional, dictionary): Build parameters

5. get_plugin_details
   • Description: Retrieves information about all installed Jenkins plugins.

6. install_plugin
   • Description: Installs a specified plugin in the Jenkins server.
   • Inputs:
     - plugin_name (string): The name of the plugin to install

7. get_node_details
   • Description: Retrieves information about all Jenkins nodes (including the master).

8. get_queue_details
   • Description: Lists current items in the Jenkins build queue.

9. create_job
   • Description: Creates a new Jenkins job using the supplied XML configuration.
   • Inputs:
     - job_name (string): New job name
     - config_xml (string): XML configuration for the job

10. restart_jenkins
    • Description: Initiates a restart of the Jenkins server.

11. get_build_status
    • Description: Retrieves the status of a specific build.
    • Inputs:
      - job_name (string): Name of the Jenkins job
      - build_number (number/string): Build number to retrieve

12. get_last_successful_build
    • Description: Gets the details of the last successful build for a job.
    • Inputs:
      - job_name (string): Name of the Jenkins job

13. get_last_failed_build
    • Description: Gets the details of the last failed build for a job.
    • Inputs:
      - job_name (string): Name of the Jenkins job

14. stop_build
    • Description: Stops a running build.
    • Inputs:
      - job_name (string): Name of the Jenkins job
      - build_number (number/string): Build number to stop

15. get_pipeline_description
    • Description: Retrieves the description of a Jenkins pipeline job.
    • Inputs:
      - job_name (string): Name of the pipeline job

16. get_builds_list
    • Description: Retrieves a list of recent builds for a job.
    • Inputs:
      - job_name (string): Name of the Jenkins job
      - limit (number): Maximum number of builds to return (default is 10)

17. get_running_builds
    • Description: Retrieves information about all currently running builds.

18. update_build_description
    • Description: Updates the description for a specific build.
    • Inputs:
      - job_name (string): Name of the Jenkins job
      - build_number (number/string): Build number to update
      - description (string): New description text

19. delete_job
    • Description: Deletes a specified Jenkins job.
    • Inputs:
      - job_name (string): Name of the job to delete

20. copy_job
    • Description: Copies an existing job to create a new one.
    • Inputs:
      - source_job_name (string): Source job name
      - target_job_name (string): New job name

21. get_job_config
    • Description: Retrieves the XML configuration of a job.
    • Inputs:
      - job_name (string): Name of the Jenkins job

22. update_job_config
    • Description: Updates a job's configuration with new XML data.
    • Inputs:
      - job_name (string): Name of the Jenkins job
      - config_xml (string): New XML configuration

23. enable_job
    • Description: Enables a disabled Jenkins job.
    • Inputs:
      - job_name (string): Name of the Jenkins job

24. disable_job
    • Description: Disables an active Jenkins job.
    • Inputs:
      - job_name (string): Name of the Jenkins job

25. get_build_console_output
    • Description: Retrieves the console output for a specific build.
    • Inputs:
      - job_name (string): Name of the Jenkins job
      - build_number (number/string): Build number

26. get_crumb
    • Description: Retrieves a CSRF protection crumb for safe POST requests.

Jenkins API Helper Functions
----------------------------
The script includes a helper function, jenkins_request, to facilitate authenticated HTTP requests to the Jenkins API. This function:
• Constructs the URL using the Jenkins base URL and endpoint.
• Handles authentication with the provided user credentials and API token.
• Manages headers (including content-type) and SSL verification.
• Returns JSON responses or error details as appropriate.

Running the Server
------------------
To launch the Jenkins MCP Server, simply run the script. Upon starting, the server will connect to your Jenkins instance using the configuration provided via environment variables. It exposes all defined MCP tools and is ready to receive RPC or API calls through the FastMCP framework.

Final Notes
-----------
This Jenkins MCP Server facilitates seamless integration with Jenkins, enabling flexible automation and management of CI/CD tasks. Customize and extend these tools as needed to fit your specific automation workflows and infrastructure requirements.

For any questions or contributions, please consult the project documentation or reach out to the project maintainers. Enjoy automating your Jenkins operations!