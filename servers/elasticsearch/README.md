ELK MCP Server
==============

Overview
--------
ELK MCP Server is an implementation of an MCP (Modular Control Protocol) server designed to simplify and streamline interactions with an Elasticsearch cluster. By leveraging asynchronous operations and the FastMCP framework, this server exposes a comprehensive suite of tools and APIs for managing cluster health, indices, documents, searches, ingest pipelines, and more—all through clean and well-documented endpoints.

Key Features
------------
•  Comprehensive API Coverage – Manage cluster health, configurations, indices, documents, searches, ingest pipelines, templates, and node information.  
•  Asynchronous Operations – All endpoints are built asynchronously using httpx for efficient interaction with Elasticsearch.  
•  Flexible Query Options – Supports both advanced and simplified search interfaces, including multi-search and bulk operations.  
•  Ingest Pipeline Simulation – Test pipeline configurations with verbose feedback.  
•  Dynamic Configuration – Easily set your Elasticsearch base URL and API token via environment variables.  
•  Error Handling & Logging – Integrated logging provides clear insights and error messages for troubleshooting.

Architecture & Tools
--------------------
The server is built around the FastMCP framework to expose an array of MCP tools (endpoints), each corresponding to one or more Elasticsearch REST APIs. Major components include:

1. Cluster APIs  
   •  cluster_health – Check overall health or specific index health with optional timeout and detailed level information.  
   •  cluster_stats – Retrieve detailed cluster statistics, optionally per node.  
   •  cluster_settings – Get or update cluster settings with an option to include defaults.

2. Index APIs  
   •  create_index, get_index, delete_index – Create, retrieve, and delete indices with support for custom settings, mappings, and aliases.  
   •  get_mapping, update_mapping – Manage index mappings efficiently.  
   •  list_indices – List available indices with filtering support.

3. Document APIs  
   •  index_document, get_document, delete_document – Create/update documents or manage document retrieval and deletion with refresh policies.  
   •  bulk_operations – Execute bulk operations using NDJSON formatted requests.

4. Search APIs  
   •  search – A flexible endpoint to run custom Elasticsearch queries with support for pagination, sorting, and aggregations.  
   •  simple_search – An easy-to-use search interface for common queries with exact or fuzzy matching options.  
   •  count_documents – Count documents that match a given query.  
   •  multi_search – Perform multiple searches in a single request via the _msearch elastic API.

5. Ingest APIs  
   •  create_pipeline, get_pipeline, delete_pipeline – Manage ingest pipelines for pre-processing documents prior to indexing.  
   •  simulate_pipeline – Test pipeline configurations with sample documents and get verbose output if required.

6. Info & Additional APIs  
   •  node_info, node_stats – Retrieve node-level metrics and statistics from the cluster.  
   •  cat_indices, cat_nodes, cat_aliases – Use the _cat endpoints for human-readable listings of indices, nodes, and aliases.  
   •  create_index_template, get_index_template, delete_index_template – Manage index templates for defining default settings and mappings.

Installation
------------
1. Prerequisites:  
   •  Python 3.8 or later  
   •  An Elasticsearch cluster (version compatible with your REST endpoints)  
   •  Required Python libraries: httpx, python-dotenv, logging (standard), and mcp.

2. Install Dependencies:  
   Create a virtual environment and install the necessary packages. For example:
     
     $ python -m venv venv
     $ source venv/bin/activate
     $ pip install httpx python-dotenv fastmcp

3. Set Up Environment Variables:  
   Create a .env file in the project root with the following variables:
     
     ELASTICSEARCH_BASE_URL=https://your-elasticsearch-host:9200
     ELASTICSEARCH_TOKEN=your_api_key_or_token

Usage
-----
Start the MCP server by executing the main module. The server will initialize the registered MCP tools and start listening for requests.

     $ python path/to/your_script.py

Each endpoint can be called through the MCP interface. For example, use the "cluster_health" tool to get the current health status of your cluster, or "simple_search" to perform quick document queries.

Logging & Error Handling
------------------------
Logging is configured to capture informational messages and errors with time stamps, source names, and severity levels. In case of errors when making requests to Elasticsearch, detailed error messages with the HTTP status code and response are logged and returned.

Configuration
-------------
•  ELASTICSEARCH_BASE_URL: Base URL for your Elasticsearch cluster.  
•  ELASTICSEARCH_TOKEN: Authentication token for the Elasticsearch cluster (if required).

Additional Information
----------------------
•  The MCP server is built on an asynchronous framework, allowing for scalable and efficient handling of multiple concurrent requests.  
•  The architecture emphasizes modularity, making it straightforward to add or modify endpoints as needed.  
•  Each API endpoint sanitizes and formats responses for clarity, ensuring that both success and error messages are easy to understand.

Contributing
------------
Contributions are welcome! To contribute, please fork this repository, create a feature branch, and submit a pull request with detailed explanations of your changes.

License
-------
This project is open source. Please refer to the LICENSE file for more details about usage and distribution rights.

Contact
-------
For questions or support, please reach out to the project maintainer or submit an issue on the GitHub repository.

By integrating fast, asynchronous operations with comprehensive API support, the ELK MCP Server serves as a powerful tool for developers and administrators looking to streamline their Elasticsearch management tasks. Enjoy a simplified experience managing your Elasticsearch cluster!