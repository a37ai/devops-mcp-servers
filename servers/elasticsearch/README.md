Elasticsearch MCP Server
==========================

Overview
--------
Elasticsearch MCP Server is an MCP (Multi-Channel Protocol) server implementation built using FastMCP that provides a suite of tools to interact with an Elasticsearch instance. This server leverages modern Python libraries such as httpx for asynchronous HTTP requests, pydantic for robust data validation, and python-dotenv for environment configuration. With a modular design supporting a wide range of Elasticsearch operations—from cluster health and stats to document indexing and multi-search—the server aims to simplify integration and management of Elasticsearch clusters.

Features
--------
• Comprehensive API Support – Provides endpoints for Elasticsearch Cluster, Index, Document, Search, Ingest, Info, and Additional Template APIs.  
• Robust Parameter Validation – Uses Pydantic models to enforce strict validation and sanitation of input parameters for each endpoint.  
• Asynchronous Operations – Built with asynchronous programming patterns using httpx, ensuring efficient I/O operations under a heavy load.  
• Serverless Mode Awareness – Detects Elasticsearch Serverless mode and adjusts behavior accordingly, preventing incompatible operations.  
• Flexible Request Building – Supports multiple HTTP methods (GET, POST, PUT, DELETE) and content types, including NDJSON for bulk data operations.

Installation
------------
1. Requirements  
   • Python 3.8 (or higher)  
   • Dependencies listed in requirements.txt (FastMCP, httpx, python-dotenv, pydantic)

2. Setup  
   • Clone the repository and navigate to the project directory.  
   • Install dependencies using pip:  
     
         pip install -r requirements.txt

Configuration
-------------
The MCP server requires configuration of essential environment variables to communicate with your Elasticsearch instance. Create a .env file in the project root and define the following variables:

   • ELASTICSEARCH_BASE_URL – Base URL of your Elasticsearch instance (e.g., "http://localhost:9200").  
   • ELASTICSEARCH_TOKEN – (Optional) API token for authenticating requests with Elasticsearch.

Example .env file:

   ELASTICSEARCH_BASE_URL=http://localhost:9200
   ELASTICSEARCH_TOKEN=your_api_token_here

Usage
-----
The Elasticsearch MCP Server organizes its functionality into modular API tools. Each tool is decorated with a validation wrapper ensuring that the passed parameters adhere to the expected schema. Below is an overview of the API groups:

1. Cluster APIs  
   • cluster_health – Retrieve the health status of the Elasticsearch cluster.  
   • cluster_stats – Get comprehensive cluster statistics.  
   • cluster_settings – Retrieve or update cluster-wide settings (with serverless mode support).

2. Index APIs  
   • create_index – Create a new index with optional settings, mappings, and aliases.  
   • get_index – Retrieve detailed index information.  
   • delete_index – Delete a specified index.  
   • get_mapping & update_mapping – Fetch or update index mapping definitions.  
   • list_indices – List all indices with optional filtering based on a pattern.

3. Document APIs  
   • index_document – Create or update a document within an index.  
   • get_document – Retrieve a document by its ID including selective source filtering.  
   • delete_document – Remove a document, with refresh support.  
   • bulk_operations – Execute multiple document operations in a single NDJSON formatted request.

4. Search APIs  
   • search – Execute searches with full control over query DSL, pagination, sorting, aggregations, and source filtering.  
   • simple_search – Simplified search interface using basic keyword queries with optional field targeting.  
   • count_documents – Count documents matching a specific query.  
   • multi_search – Perform multiple searches in one request using NDJSON formatting.

5. Ingest APIs  
   • create_pipeline – Create or update an ingest pipeline with an array of processors.  
   • get_pipeline – Retrieve a specific or all ingest pipelines.  
   • delete_pipeline – Remove an ingest pipeline by ID.  
   • simulate_pipeline – Simulate an ingest pipeline on provided documents for testing.

6. Info APIs  
   • node_info – Retrieve information about cluster nodes (adjusts for serverless mode).  
   • node_stats – Get detailed node statistics with optional index metric filtering.  
   • cluster_info – Fetch basic cluster information.  
   • cat_indices, cat_nodes, cat_aliases – Retrieve human-readable status and details using Elasticsearch Cat APIs.

7. Additional APIs (Templates and more)  
   • create_index_template – Create or update index templates with support for custom settings and mappings.  
   • get_index_template – Retrieve one or all index templates.  
   • delete_index_template – Delete a specified index template.

Running the Server
------------------
Once configured, you can run the MCP server directly from the command line:

   python your_main_script.py

The server initialization code will set up FastMCP, configure logging, and listen for incoming requests. Detailed log messages will help you trace operations and easily diagnose errors.

Logging
-------
The server is configured to use Python’s built-in logging module. Logging is set at the INFO level by default, and each significant operation (such as API calls or validation errors) is logged with timestamps and details. You can adjust the logging configuration as needed.

Error Handling
--------------
Each API tool includes comprehensive error-handling. Elasticsearch responses are parsed and, in case of non-successful HTTP status codes, descriptive error messages are returned. Validation errors from Pydantic are caught by the decorator, ensuring that clients receive clear feedback on bad input parameters.

Conclusion
----------
The Elasticsearch MCP Server provides a powerful and flexible foundation for integrating with Elasticsearch clusters. Its modular design, emphasis on validation, and serverless compatibility make it an excellent choice for developers looking to manage Elasticsearch operations in a scalable and modern Python environment.

For further details, please refer to the inline documentation within the code and the API tool decorators, which offer additional insights into each endpoint’s parameters and behaviors.