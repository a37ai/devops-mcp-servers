from mcp.server.fastmcp import FastMCP
import boto3
import json
import subprocess
import tempfile
import os
from typing import Optional, Dict, Any, List

# Initialize the MCP server
mcp = FastMCP("aws-server")

# Helper function to get an AWS client
def get_aws_client(service: str, region: Optional[str] = None):
    return boto3.client(service, region_name=region) if region else boto3.client(service)

# Core S3 Tools
@mcp.tool()
def list_s3_buckets(region: Optional[str] = None) -> str:
    """List all S3 buckets in the AWS account.
    
    Args:
        region: Optional AWS region to limit the search
    
    Returns:
        JSON string with bucket information
    """
    s3 = get_aws_client('s3', region)
    response = s3.list_buckets()
    
    buckets = []
    for bucket in response['Buckets']:
        location = s3.get_bucket_location(Bucket=bucket['Name'])
        region = location['LocationConstraint'] or 'us-east-1'
        buckets.append({
            'Name': bucket['Name'],
            'CreationDate': bucket['CreationDate'].isoformat(),
            'Region': region
        })
    
    return json.dumps(buckets, indent=2)

@mcp.tool()
def list_s3_objects(bucket_name: str, prefix: Optional[str] = "", max_items: int = 100) -> str:
    """List objects in an S3 bucket.
    
    Args:
        bucket_name: Name of the S3 bucket
        prefix: Optional prefix to filter objects
        max_items: Maximum number of items to return
    
    Returns:
        JSON string with object information
    """
    s3 = get_aws_client('s3')
    
    if prefix:
        response = s3.list_objects_v2(Bucket=bucket_name, Prefix=prefix, MaxKeys=max_items)
    else:
        response = s3.list_objects_v2(Bucket=bucket_name, MaxKeys=max_items)
    
    objects = []
    if 'Contents' in response:
        for obj in response['Contents']:
            objects.append({
                'Key': obj['Key'],
                'Size': obj['Size'],
                'LastModified': obj['LastModified'].isoformat(),
                'StorageClass': obj['StorageClass']
            })
    
    return json.dumps({
        'Objects': objects,
        'Count': len(objects),
        'IsTruncated': response.get('IsTruncated', False)
    }, indent=2)

# Core EC2 Tools
@mcp.tool()
def list_ec2_instances(region: Optional[str] = None, state: Optional[str] = None) -> str:
    """List EC2 instances with their details.
    
    Args:
        region: Optional AWS region
        state: Optional instance state filter (running, stopped, etc.)
    
    Returns:
        JSON string with EC2 instance information
    """
    ec2 = get_aws_client('ec2', region)
    
    filters = []
    if state:
        filters.append({
            'Name': 'instance-state-name',
            'Values': [state]
        })
    
    if filters:
        response = ec2.describe_instances(Filters=filters)
    else:
        response = ec2.describe_instances()
    
    instances = []
    for reservation in response['Reservations']:
        for instance in reservation['Instances']:
            name = "Unnamed"
            for tag in instance.get('Tags', []):
                if tag['Key'] == 'Name':
                    name = tag['Value']
                    break
            
            instances.append({
                'InstanceId': instance['InstanceId'],
                'Name': name,
                'InstanceType': instance['InstanceType'],
                'State': instance['State']['Name'],
                'PublicIpAddress': instance.get('PublicIpAddress', 'None'),
                'PrivateIpAddress': instance.get('PrivateIpAddress', 'None'),
                'LaunchTime': instance['LaunchTime'].isoformat()
            })
    
    return json.dumps(instances, indent=2)

@mcp.tool()
def list_ec2_amis(owners: List[str] = ['self'], region: Optional[str] = None) -> str:
    """List available AMIs (Amazon Machine Images).
    
    Args:
        owners: List of AMI owners (default: self)
        region: Optional AWS region
    
    Returns:
        JSON string with AMI information
    """
    ec2 = get_aws_client('ec2', region)
    
    response = ec2.describe_images(Owners=owners)
    
    amis = []
    for image in response['Images']:
        amis.append({
            'ImageId': image['ImageId'],
            'Name': image.get('Name', 'Unnamed'),
            'CreationDate': image.get('CreationDate', 'Unknown'),
            'State': image['State'],
            'Public': image.get('Public', False),
            'Architecture': image.get('Architecture', 'Unknown'),
            'Platform': image.get('Platform', 'Linux/UNIX'),
            'Description': image.get('Description', 'No description')
        })
    
    # Sort by creation date (newest first)
    amis.sort(key=lambda x: x['CreationDate'], reverse=True)
    
    return json.dumps(amis, indent=2)

@mcp.tool()
def start_ec2_instance(instance_id: str, region: Optional[str] = None) -> str:
    """Start an EC2 instance.
    
    Args:
        instance_id: ID of the EC2 instance
        region: Optional AWS region
    
    Returns:
        JSON string with result information
    """
    ec2 = get_aws_client('ec2', region)
    
    try:
        response = ec2.start_instances(InstanceIds=[instance_id])
        return json.dumps({
            'Status': 'Success',
            'InstanceId': instance_id,
            'CurrentState': response['StartingInstances'][0]['CurrentState']['Name'],
            'PreviousState': response['StartingInstances'][0]['PreviousState']['Name']
        }, indent=2)
    except Exception as e:
        return json.dumps({
            'Status': 'Error',
            'Message': str(e)
        }, indent=2)

@mcp.tool()
def stop_ec2_instance(instance_id: str, region: Optional[str] = None) -> str:
    """Stop an EC2 instance.
    
    Args:
        instance_id: ID of the EC2 instance
        region: Optional AWS region
    
    Returns:
        JSON string with result information
    """
    ec2 = get_aws_client('ec2', region)
    
    try:
        response = ec2.stop_instances(InstanceIds=[instance_id])
        return json.dumps({
            'Status': 'Success',
            'InstanceId': instance_id,
            'CurrentState': response['StoppingInstances'][0]['CurrentState']['Name'],
            'PreviousState': response['StoppingInstances'][0]['PreviousState']['Name']
        }, indent=2)
    except Exception as e:
        return json.dumps({
            'Status': 'Error',
            'Message': str(e)
        }, indent=2)

@mcp.tool()
def create_ec2_instance(
    ami_id: str,
    instance_type: str = "t2.micro",
    key_name: Optional[str] = None,
    security_group_ids: Optional[List[str]] = None,
    subnet_id: Optional[str] = None,
    name: Optional[str] = None,
    region: Optional[str] = None
) -> str:
    """Launch a new EC2 instance.
    
    Args:
        ami_id: ID of the AMI to use
        instance_type: EC2 instance type (default: t2.micro)
        key_name: Optional SSH key pair name
        security_group_ids: Optional list of security group IDs
        subnet_id: Optional subnet ID
        name: Optional name tag for the instance
        region: Optional AWS region
    
    Returns:
        JSON string with instance information
    """
    ec2 = get_aws_client('ec2', region)
    
    # Prepare launch parameters
    params = {
        'ImageId': ami_id,
        'InstanceType': instance_type,
        'MinCount': 1,
        'MaxCount': 1
    }
    
    if key_name:
        params['KeyName'] = key_name
    
    if security_group_ids:
        params['SecurityGroupIds'] = security_group_ids
    
    if subnet_id:
        params['SubnetId'] = subnet_id
    
    try:
        # Launch the instance
        response = ec2.run_instances(**params)
        
        instance_id = response['Instances'][0]['InstanceId']
        
        # Add name tag if provided
        if name:
            ec2.create_tags(
                Resources=[instance_id],
                Tags=[{'Key': 'Name', 'Value': name}]
            )
        
        # Return instance details
        return json.dumps({
            'Status': 'Success',
            'InstanceId': instance_id,
            'InstanceType': response['Instances'][0]['InstanceType'],
            'State': response['Instances'][0]['State']['Name'],
            'PrivateIpAddress': response['Instances'][0].get('PrivateIpAddress', 'None')
        }, indent=2)
    except Exception as e:
        return json.dumps({
            'Status': 'Error',
            'Message': str(e)
        }, indent=2)

# Security Groups
@mcp.tool()
def list_security_groups(region: Optional[str] = None) -> str:
    """List EC2 security groups.
    
    Args:
        region: Optional AWS region
    
    Returns:
        JSON string with security group information
    """
    ec2 = get_aws_client('ec2', region)
    
    try:
        response = ec2.describe_security_groups()
        
        security_groups = []
        for sg in response['SecurityGroups']:
            security_groups.append({
                'GroupId': sg['GroupId'],
                'GroupName': sg['GroupName'],
                'Description': sg['Description'],
                'VpcId': sg.get('VpcId', 'None'),
                'InboundRuleCount': len(sg.get('IpPermissions', [])),
                'OutboundRuleCount': len(sg.get('IpPermissionsEgress', []))
            })
        
        return json.dumps(security_groups, indent=2)
    except Exception as e:
        return json.dumps({
            'Status': 'Error',
            'Message': str(e)
        }, indent=2)

# Lambda Functions
@mcp.tool()
def list_lambda_functions(region: Optional[str] = None) -> str:
    """List all Lambda functions in the AWS account.
    
    Args:
        region: Optional AWS region
    
    Returns:
        JSON string with Lambda function information
    """
    lambda_client = get_aws_client('lambda', region)
    
    try:
        functions = []
        response = lambda_client.list_functions()
        
        for function in response['Functions']:
            functions.append({
                'FunctionName': function['FunctionName'],
                'Runtime': function['Runtime'],
                'Handler': function['Handler'],
                'LastModified': function['LastModified'],
                'MemorySize': function['MemorySize'],
                'Timeout': function['Timeout'],
                'Description': function.get('Description', ''),
                'Role': function['Role']
            })
        
        return json.dumps(functions, indent=2)
    except Exception as e:
        return json.dumps({"error": str(e)})

# Run AWS Code (this is the main flexible tool)
@mcp.tool()
def run_aws_code(code: str, imports: Optional[str] = "import boto3") -> str:
    """Run Python code that interacts with AWS services.
    
    Args:
        code: Python code to run (using boto3)
        imports: Optional import statements to include
    
    Returns:
        Output from the executed code
    """
    # Create a temporary file
    with tempfile.NamedTemporaryFile(suffix='.py', delete=False) as temp:
        # Write code to file with imports and print capturing
        full_code = f"""
{imports}
import sys
import json
import traceback
from io import StringIO
from datetime import datetime

# Helper function to make objects JSON serializable
def json_serializer(obj):
    if isinstance(obj, datetime):
        return obj.isoformat()
    try:
        return obj.__dict__
    except:
        return str(obj)

# Capture stdout
original_stdout = sys.stdout
captured_output = StringIO()
sys.stdout = captured_output

try:
    # Execute user code
{'\n'.join('    ' + line for line in code.split('\n'))}
    
    # If the last expression evaluates to something, capture it
    result = None
    try:
        # Get locals defined in the executed code
        result = locals().get('result')
        if result is not None:
            print("\\nResult:")
            if isinstance(result, (dict, list)):
                print(json.dumps(result, default=json_serializer, indent=2))
            else:
                print(result)
    except Exception as e:
        print(f"Error formatting result: {{str(e)}}")

except Exception as e:
    print(f"Error: {{str(e)}}")
    print(traceback.format_exc())

# Restore stdout
sys.stdout = original_stdout
output = captured_output.getvalue()

# Return captured output
with open('{temp.name}.out', 'w') as f:
    f.write(output)
"""
        temp.write(full_code.encode('utf-8'))
        temp_name = temp.name

    try:
        # Execute the code
        subprocess.run(['python', temp_name], timeout=30)
        
        # Read the output
        with open(f"{temp_name}.out", 'r') as f:
            output = f.read()
            
        return output
    except subprocess.TimeoutExpired:
        return "Execution timed out (30 seconds limit)"
    except Exception as e:
        return f"Error executing code: {str(e)}"
    finally:
        # Clean up temporary files
        if os.path.exists(temp_name):
            os.remove(temp_name)
        if os.path.exists(f"{temp_name}.out"):
            os.remove(f"{temp_name}.out")

# Resource providing a list of AWS regions
@mcp.resource("aws://regions")
def list_aws_regions() -> str:
    """Return a list of AWS regions as a resource."""
    ec2 = boto3.client('ec2')
    regions = [region['RegionName'] for region in ec2.describe_regions()['Regions']]
    return json.dumps(regions, indent=2)

# Resource providing a list of Amazon EC2 instance types
@mcp.resource("aws://ec2/instance-types")
def list_instance_types() -> str:
    """Return a list of common EC2 instance types."""
    instance_types = {
        "General Purpose": ["t2.micro", "t2.small", "t3.medium", "m5.large", "m6g.xlarge"],
        "Compute Optimized": ["c5.large", "c6g.xlarge", "c5n.2xlarge"],
        "Memory Optimized": ["r5.large", "r6g.xlarge", "x1.16xlarge"],
        "Storage Optimized": ["i3.large", "d2.xlarge", "h1.2xlarge"],
        "Accelerated Computing": ["p3.2xlarge", "g4dn.xlarge", "inf1.xlarge"]
    }
    return json.dumps(instance_types, indent=2)

if __name__ == "__main__":
    mcp.run()