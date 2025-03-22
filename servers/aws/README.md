AWS MCP Server with FastMCP
============================

Overview
--------
The AWS MCP Server is a powerful implementation built using the FastMCP framework to integrate with Amazon Web Services (AWS). This server provides a suite of tools for managing and interacting with common AWS services, such as S3, EC2, Lambda, and more. It also includes a flexible utility to execute custom Python code that interfaces with AWS, making it highly extensible and adaptable for various AWS automation tasks.

Features
--------
• S3 Management:
  - List all S3 buckets within your AWS account.
  - Retrieve detailed information about objects in a specific S3 bucket, with support for filtering by object prefix and limiting result counts.

• EC2 Instance Management:
  - List EC2 instances with detailed attributes including instance ID, name tag, type, state, IP addresses, and launch times.
  - List available Amazon Machine Images (AMIs) filtered by image ownership.
  - Start and stop EC2 instances with real-time feedback on instance state transitions.
  - Launch new EC2 instances with customizable parameters including AMI, instance type, key pair, security groups, subnet, and optional name tagging.

• Security Group Information:
  - Retrieve a detailed list of EC2 security groups, including inbound and outbound rule counts for better network configuration insights.

• Lambda Functions Management:
  - List all available Lambda functions along with key details such as runtime, handler, memory allocation, timeout settings, and more.

• Dynamic AWS Code Execution:
  - Run user-defined Python code that interacts with AWS services using boto3.
  - Dynamically import specified modules and capture standard output to provide informative results.

• AWS Resource Endpoints:
  - List AWS regions using a dedicated resource endpoint.
  - Retrieve a categorized list of common EC2 instance types available across AWS regions.

Tools & Endpoints
------------------

1. list_s3_buckets(region: Optional[str] = None)
   - Description: Lists all S3 buckets in your AWS account.
   - Parameters:
     • region (optional): Limit the listing to a specific AWS region.
   - Returns: JSON string with bucket names, creation dates, and region details.

2. list_s3_objects(bucket_name: str, prefix: Optional[str] = "", max_items: int = 100)
   - Description: Lists objects in a specified S3 bucket.
   - Parameters:
     • bucket_name (required): The S3 bucket to query.
     • prefix (optional): Filter objects by a given prefix.
     • max_items (optional): Maximum number of objects to return.
   - Returns: A JSON string with object details, including keys, sizes, last modification dates, and storage classes.

3. list_ec2_instances(region: Optional[str] = None, state: Optional[str] = None)
   - Description: Retrieves details of EC2 instances.
   - Parameters:
     • region (optional): AWS region to query.
     • state (optional): Filter instances by state (e.g., running, stopped).
   - Returns: JSON string comprising one or more instance details.

4. list_ec2_amis(owners: List[str] = ['self'], region: Optional[str] = None)
   - Description: Lists AMIs based on the provided owner filters.
   - Parameters:
     • owners (optional): List of AMI owners; defaults to 'self'.
     • region (optional): AWS region to limit the search.
   - Returns: Sorted JSON string of AMIs (newest first) with essential attributes.

5. start_ec2_instance(instance_id: str, region: Optional[str] = None)
   - Description: Starts an EC2 instance.
   - Parameters:
     • instance_id (required): The ID of the instance to be started.
     • region (optional): AWS region where the instance resides.
   - Returns: JSON string containing the success status and state transitions.

6. stop_ec2_instance(instance_id: str, region: Optional[str] = None)
   - Description: Stops an EC2 instance.
   - Parameters:
     • instance_id (required): The instance ID.
     • region (optional): AWS region of the instance.
   - Returns: JSON string with details of action status and instance state change.

7. create_ec2_instance(ami_id: str, instance_type: str = "t2.micro", key_name: Optional[str] = None, security_group_ids: Optional[List[str]] = None, subnet_id: Optional[str] = None, name: Optional[str] = None, region: Optional[str] = None)
   - Description: Launches a new EC2 instance with provided configuration.
   - Parameters:
     • ami_id (required): The AMI identifier.
     • instance_type (optional): EC2 instance type (defaults to t2.micro).
     • key_name (optional): SSH key pair name.
     • security_group_ids (optional): A list of security group IDs.
     • subnet_id (optional): Subnet identifier.
     • name (optional): Name for the instance (used as a tag).
     • region (optional): AWS region for deployment.
   - Returns: JSON string with the newly created instance details.

8. list_security_groups(region: Optional[str] = None)
   - Description: Lists all EC2 security groups.
   - Parameters:
     • region (optional): Specific AWS region.
   - Returns: JSON string with security group attributes including group ID, name, description, associated VPC, and rule counts.

9. list_lambda_functions(region: Optional[str] = None)
   - Description: Lists all AWS Lambda functions in the account.
   - Parameters:
     • region (optional): Specific region to query.
   - Returns: JSON string detailing each Lambda’s configuration.

10. run_aws_code(code: str, imports: Optional[str] = "import boto3")
    - Description: Executes arbitrary Python code that can interact with AWS services.
    - Parameters:
      • code (required): The Python code snippet to run.
      • imports (optional): Additional import statements (defaults to importing boto3).
    - Returns: Captured output from the execution, including error tracebacks if any.

Resource Endpoints
------------------
• aws://regions
  - Description: Returns a JSON list of available AWS regions.
  
• aws://ec2/instance-types
  - Description: Provides a categorized list of common EC2 instance types (General Purpose, Compute Optimized, Memory Optimized, Storage Optimized, and Accelerated Computing).

Configuration & Setup
---------------------
1. AWS Credentials:
   - Ensure that AWS credentials (access key, secret key, and region) are properly configured in your environment. The boto3 library will reference credentials from standard locations such as environment variables or AWS credential files.

2. Dependencies:
   - Python 3.x
   - boto3 library (can be installed via pip)
   - Other standard Python libraries (tempfile, json, subprocess, os)

3. Installation:
   - Install the required Python packages, for example:
     pip install boto3

4. Running the MCP Server:
   - The FastMCP framework takes care of initializing and running the server. To start, simply execute the Python script:
     python <script_name>.py
   - The MCP server will listen for requests and tools available under the defined configuration.

Usage Examples
--------------
• Listing S3 Buckets:
  Call the tool list_s3_buckets with an optional region parameter. The tool communicates with the AWS S3 API to return bucket names, creation dates, and corresponding regions in JSON format.

• Managing EC2 Instances:
  Use list_ec2_instances to obtain information about your instances. You can filter by AWS region and instance state. Similarly, start_ec2_instance and stop_ec2_instance allow you to control instance states, and create_ec2_instance provides a way to launch new instances with custom settings.

• Executing Custom AWS Code:
  The run_aws_code tool allows you to pass any Python code snippet that makes use of boto3. This tool will execute your code in a secure, temporary environment and return the captured output.

Contributing / Support
----------------------
Contributions are welcome. Please ensure that any additions remain consistent with the professional standards and design philosophy of the project. For any issues or support requests related to the AWS MCP Server, please open an issue via the repository’s issue tracker.

License
-------
Include your project's license details here (for example, MIT License), ensuring that any user-generated contributions comply with the license.

Conclusion
----------
The AWS MCP Server with FastMCP equips you with a streamlined and modular approach to administering AWS resources through a unified interface. Whether you need a quick glance at your S3 configuration, manage EC2 lifecycle, or dynamically execute AWS-related Python code, this server is tailored to boost your operational efficiency and control over AWS services.