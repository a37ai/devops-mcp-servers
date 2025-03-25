GCP MCP Server
==============

Overview
--------
The GCP MCP Server is an implementation of an MCP (Modular Control Processor) server designed to interact seamlessly with various Google Cloud Platform (GCP) services. Built on top of the FastMCP framework, this server offers a rich suite of tools to manage and monitor different GCP resources such as Cloud Storage, Compute Engine, BigQuery, Cloud Functions, and Google Kubernetes Engine (GKE).

This server provides a convenient and programmable interface for administrators and developers to perform common cloud operations, including listing resources, managing Compute Engine instances, and executing custom GCP code. Advanced resource discovery and dynamic execution capabilities ensure that users can integrate GCP services into their workflows effortlessly.

Features
--------
• Multifaceted GCP Integration – Use the server to interact with GCP services such as:
  - Google Cloud Storage (GCS): List buckets and objects
  - Google Compute Engine (GCE): List, start, stop, and create instances; list images; and manage firewall rules
  - Cloud Functions: List functions and retrieve metadata
  - BigQuery: List datasets and tables
  - Google Kubernetes Engine (GKE): List clusters and get node pool information

• Dynamic Code Execution – Run custom Python code that leverages Google Cloud libraries. A flexible tool allows users to supply code snippets along with any necessary import statements for ad-hoc operations.

• Resource Providers – Built-in resources are available for:
  - Listing common GCP regions
  - Displaying frequently used GCE machine types categorized by use case

• Modular and Extensible – The FastMCP tool decorator approach allows for easy expansion and customization. Each tool is designed to provide JSON-formatted output for easy integration into other systems or front-ends.

Installation and Setup
----------------------
1. Environment Setup:
   - Ensure Python 3.7+ is installed.
   - Install required libraries using pip:
     pip install google-cloud-storage google-cloud-bigquery google-cloud-container google-cloud-functions google-api-python-client google-auth

2. GCP Credentials:
   - Make sure you have proper GCP authentication set up. You can use Application Default Credentials by running:
     gcloud auth application-default login
   - The server will automatically use the default project unless specified otherwise via function parameters.

3. Server Initialization:
   - The main script initializes the MCP server with the identifier "gcp-server". Tools are registered via the FastMCP decorator and can be run directly using the MCP framework’s run command.

Tools & Commands
----------------
The server provides a number of tools to interact with GCP services. Below is an overview of the main commands available:

Cloud Storage Tools
-------------------
• list_gcs_buckets(project_id: Optional[String])  
  – Lists all Google Cloud Storage buckets within the specified project.  
  – Output: JSON array with bucket names, creation dates, locations, and storage classes.

• list_gcs_objects(bucket_name: String, prefix: Optional[String], max_items: Integer)  
  – Lists objects in a given bucket with optional prefix filtering.  
  – Output: JSON containing details like object names, size, content type, and update time.

Compute Engine Tools
--------------------
• list_gce_instances(project_id: Optional[String], zone: Optional[String])  
  – Retrieves instances from one or all zones, detailing instance name, machine type, IP addresses, and status.
  
• list_gce_images(project_id: Optional[String], family: Optional[String])  
  – Lists available images from common image projects (or a specific project) and filters by family if provided.
  
• start_gce_instance(instance_name: String, zone: String, project_id: Optional[String])  
  – Starts a specified Compute Engine instance and returns operation information.
  
• stop_gce_instance(instance_name: String, zone: String, project_id: Optional[String])  
  – Stops a specified Compute Engine instance and provides corresponding operation details.
  
• create_gce_instance(instance_name: String, machine_type: String, image_project: String, image_family: String, zone: String, project_id: Optional[String], network: String, subnet: Optional[String], external_ip: Boolean)  
  – Creates a new Compute Engine virtual machine using startup scripts for initial configuration.  
  – Output: JSON response including operation ID and instance configuration details.

Firewall & Network Tools
--------------------------
• list_firewall_rules(project_id: Optional[String])  
  – Lists all firewall rules in the project including allowed and denied protocols, ports, and ranges.

Cloud Functions Tools
---------------------
• list_cloud_functions(project_id: Optional[String], region: String)  
  – Retrieves information on Cloud Functions in the specified region including runtime, status, memory, and trigger information.

BigQuery Tools
--------------
• list_bigquery_datasets(project_id: Optional[String])  
  – Lists datasets available in the project, along with creation and update details.
  
• list_bigquery_tables(dataset_id: String, project_id: Optional[String])  
  – Provides a list of tables within a specified BigQuery dataset and their metadata.

GKE Tools
---------
• list_gke_clusters(project_id: Optional[String], zone: Optional[String])  
  – Retrieves and displays cluster details including node pool configurations and endpoint information.

Dynamic Code Execution
----------------------
• run_gcp_code(code: String, imports: Optional[String])  
  – Executes user-supplied Python code which interacts with the GCP libraries.  
  – This flexible tool creates a temporary file, runs the code in a safe sandbox, and captures the output.

Resources
---------
• gcp://regions  
  – A resource function that returns a JSON list of common GCP regions.

• gcp://compute/machine-types  
  – Provides a categorized list of common Compute Engine machine types (General Purpose, Memory Optimized, Compute Optimized, etc.) in JSON format.

Usage Example
-------------
1. Listing all GCS buckets:
   - Call the list_gcs_buckets() tool with an optional project_id.
   - Example output (formatted JSON):
     [
       {
         "Name": "example-bucket",
         "CreationDate": "2023-09-15T10:20:30Z",
         "Location": "US-CENTRAL1",
         "StorageClass": "STANDARD"
       },
       ...
     ]

2. Creating a Compute Engine instance:
   - Use the create_gce_instance tool with necessary parameters (instance name, machine type, image details, zone, and network settings).
   - The tool returns operation details including operation ID and instance configuration.

Running the Server
------------------
To run the MCP server, execute the main application file:
   python your_script.py

Additional Considerations
-------------------------
• Error Handling: Each tool returns JSON responses that indicate the status (Success/Error) along with descriptive error messages if applicable.
  
• Extensibility: The modular design of this server permits additional tools, resources, or custom integrations to be added with minimal complexity.

• Security: Ensure that proper IAM roles and permissions are in place for the service account used by the server when performing actions on GCP resources.

Conclusion
----------
This GCP MCP Server offers a robust and extensible platform for managing and monitoring various GCP services through programmable tools and resources. Whether you are an administrator managing infrastructure or a developer building cloud-integrated applications, this solution provides the necessary interfaces and flexibility for a wide range of cloud operations.

For further questions or support, please refer to the Google Cloud documentation or contact your system administrator.