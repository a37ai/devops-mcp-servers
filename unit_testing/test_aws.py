import pytest
import json
import boto3
import time
import os
import uuid
import tempfile
from datetime import datetime

# Import the module to test
from servers.aws.aws_mcp import *

# Generate unique identifiers for resources to avoid conflicts
test_uuid = str(uuid.uuid4())[:8]
TEST_PREFIX = f"mcp-test-{test_uuid}"

# Configure test settings
TEST_REGION = "us-east-1"  # Change this to your preferred test region
TEST_BUCKET_NAME = f"{TEST_PREFIX}-bucket"
TEST_EC2_INSTANCE_NAME = f"{TEST_PREFIX}-instance"

# Teardown resources after tests
test_resources = {
    "s3_buckets": [],
    "ec2_instances": []
}

# Fixture for cleanup after all tests
@pytest.fixture(scope="session", autouse=True)
def cleanup_resources():
    yield
    print("\nCleaning up test resources...")
    
    # Clean up EC2 instances
    if test_resources["ec2_instances"]:
        ec2 = boto3.client('ec2', region_name=TEST_REGION)
        try:
            print(f"Terminating EC2 instances: {test_resources['ec2_instances']}")
            ec2.terminate_instances(InstanceIds=test_resources["ec2_instances"])
            
            # Wait for instances to terminate
            waiter = ec2.get_waiter('instance_terminated')
            waiter.wait(InstanceIds=test_resources["ec2_instances"])
            print("EC2 instances terminated successfully")
        except Exception as e:
            print(f"Error cleaning up EC2 instances: {str(e)}")
    
    # Clean up S3 buckets
    for bucket_name in test_resources["s3_buckets"]:
        try:
            print(f"Deleting S3 bucket: {bucket_name}")
            s3 = boto3.resource('s3')
            bucket = s3.Bucket(bucket_name)
            bucket.objects.all().delete()
            bucket.delete()
            print(f"S3 bucket {bucket_name} deleted successfully")
        except Exception as e:
            print(f"Error cleaning up S3 bucket {bucket_name}: {str(e)}")


# Optional marker to skip tests that create AWS resources
skip_resource_creation = pytest.mark.skipif(
    os.environ.get("SKIP_RESOURCE_CREATION") == "true",
    reason="Skipping tests that create AWS resources"
)


# Test AWS Client Factory
def test_get_aws_client():
    """Test that the AWS client factory works"""
    s3_client = get_aws_client('s3')
    assert s3_client is not None
    
    # Test with region
    ec2_client = get_aws_client('ec2', 'us-west-2')
    assert ec2_client is not None
    assert ec2_client.meta.region_name == 'us-west-2'


# Test listing S3 buckets
def test_list_s3_buckets():
    """Test listing S3 buckets"""
    result = list_s3_buckets(region=TEST_REGION)
    buckets = json.loads(result)
    
    # Verify the result is a list
    assert isinstance(buckets, list)
    
    # Verify structure of bucket data if any buckets exist
    if buckets:
        assert 'Name' in buckets[0]
        assert 'CreationDate' in buckets[0]
        assert 'Region' in buckets[0]


# Create an S3 bucket for testing
@skip_resource_creation
def test_create_s3_bucket():
    """Create an S3 bucket for subsequent tests"""
    s3 = boto3.client('s3', region_name=TEST_REGION)
    
    try:
        # Create the test bucket
        s3.create_bucket(Bucket=TEST_BUCKET_NAME)
        
        # Add bucket to resources for cleanup
        test_resources["s3_buckets"].append(TEST_BUCKET_NAME)
        
        # Upload a test file
        with tempfile.NamedTemporaryFile(mode='w+') as temp:
            temp.write("Test content for S3 bucket")
            temp.flush()
            s3.upload_file(temp.name, TEST_BUCKET_NAME, "test-file.txt")
            s3.upload_file(temp.name, TEST_BUCKET_NAME, "test-folder/test-file2.txt")
        
        # Wait for bucket to be available
        waiter = s3.get_waiter('bucket_exists')
        waiter.wait(Bucket=TEST_BUCKET_NAME)
        
        # Verify bucket exists
        response = s3.list_buckets()
        buckets = [bucket['Name'] for bucket in response['Buckets']]
        assert TEST_BUCKET_NAME in buckets
    
    except Exception as e:
        pytest.fail(f"Failed to create test S3 bucket: {str(e)}")


# Test listing S3 objects (depends on test_create_s3_bucket)
@skip_resource_creation
def test_list_s3_objects():
    """Test listing objects in an S3 bucket"""
    # Skip if bucket wasn't created
    if TEST_BUCKET_NAME not in test_resources["s3_buckets"]:
        pytest.skip("Test bucket not available")
    
    # Test with no prefix
    result = list_s3_objects(TEST_BUCKET_NAME)
    data = json.loads(result)
    
    # Verify structure
    assert 'Objects' in data
    assert 'Count' in data
    assert 'IsTruncated' in data
    
    # Should have at least 2 objects
    assert data['Count'] >= 2
    
    # Test with prefix
    result = list_s3_objects(TEST_BUCKET_NAME, prefix="test-folder/")
    data = json.loads(result)
    
    # Should have only objects with the prefix
    for obj in data['Objects']:
        assert obj['Key'].startswith("test-folder/")


# Test listing EC2 instances
def test_list_ec2_instances():
    """Test listing EC2 instances"""
    result = list_ec2_instances(region=TEST_REGION)
    instances = json.loads(result)
    
    # Verify result is a list
    assert isinstance(instances, list)
    
    # Verify structure of instance data if any instances exist
    if instances:
        assert 'InstanceId' in instances[0]
        assert 'State' in instances[0]


# Test listing EC2 AMIs
def test_list_ec2_amis():
    """Test listing EC2 AMIs owned by the account"""
    result = list_ec2_amis(owners=['amazon'], region=TEST_REGION)
    amis = json.loads(result)
    
    # Should get at least some Amazon AMIs
    assert len(amis) > 0
    
    # Verify structure
    assert 'ImageId' in amis[0]
    assert 'Name' in amis[0]


# Create an EC2 instance for testing
@skip_resource_creation
def test_create_ec2_instance():
    """Test creating an EC2 instance"""
    try:
        # Find a suitable Amazon Linux AMI
        ec2 = boto3.client('ec2', region_name=TEST_REGION)
        response = ec2.describe_images(
            Owners=['amazon'],
            Filters=[
                {'Name': 'name', 'Values': ['amzn2-ami-hvm-*-x86_64-gp2']},
                {'Name': 'state', 'Values': ['available']}
            ]
        )
        
        # Sort by creation date and get the newest
        amis = sorted(response['Images'], key=lambda x: x['CreationDate'], reverse=True)
        if not amis:
            pytest.skip("No suitable AMI found for testing")
        
        ami_id = amis[0]['ImageId']
        
        # Get default VPC security group
        response = ec2.describe_security_groups(
            Filters=[{'Name': 'group-name', 'Values': ['default']}]
        )
        if not response['SecurityGroups']:
            pytest.skip("No default security group found")
        
        security_group_id = response['SecurityGroups'][0]['GroupId']
        
        # Create EC2 instance
        result = create_ec2_instance(
            ami_id=ami_id,
            instance_type="t2.micro",
            security_group_ids=[security_group_id],
            name=TEST_EC2_INSTANCE_NAME,
            region=TEST_REGION
        )
        data = json.loads(result)
        
        # Verify success
        assert data['Status'] == 'Success'
        
        # Add instance to resources for cleanup
        instance_id = data['InstanceId']
        test_resources["ec2_instances"].append(instance_id)
        
        # Wait for instance to be running
        waiter = ec2.get_waiter('instance_running')
        waiter.wait(InstanceIds=[instance_id])
        
        print(f"Created test EC2 instance: {instance_id}")
        return instance_id
    
    except Exception as e:
        pytest.fail(f"Failed to create test EC2 instance: {str(e)}")


# Test stopping EC2 instance
@skip_resource_creation
def test_stop_ec2_instance():
    """Test stopping an EC2 instance"""
    # Get the instance ID created by the previous test
    if not test_resources["ec2_instances"]:
        pytest.skip("No test EC2 instance available")
    
    instance_id = test_resources["ec2_instances"][0]
    
    # Stop the instance
    result = stop_ec2_instance(instance_id, region=TEST_REGION)
    data = json.loads(result)
    
    # Verify success
    assert data['Status'] == 'Success'
    assert data['InstanceId'] == instance_id
    
    # Wait for instance to stop
    ec2 = boto3.client('ec2', region_name=TEST_REGION)
    waiter = ec2.get_waiter('instance_stopped')
    waiter.wait(InstanceIds=[instance_id])
    
    # Verify the instance is stopped
    response = ec2.describe_instances(InstanceIds=[instance_id])
    state = response['Reservations'][0]['Instances'][0]['State']['Name']
    assert state == 'stopped'


# Test starting EC2 instance
@skip_resource_creation
def test_start_ec2_instance():
    """Test starting an EC2 instance"""
    # Get the instance ID created by the previous test
    if not test_resources["ec2_instances"]:
        pytest.skip("No test EC2 instance available")
    
    instance_id = test_resources["ec2_instances"][0]
    
    # Start the instance
    result = start_ec2_instance(instance_id, region=TEST_REGION)
    data = json.loads(result)
    
    # Verify success
    assert data['Status'] == 'Success'
    assert data['InstanceId'] == instance_id
    
    # Wait for instance to start
    ec2 = boto3.client('ec2', region_name=TEST_REGION)
    waiter = ec2.get_waiter('instance_running')
    waiter.wait(InstanceIds=[instance_id])
    
    # Verify the instance is running
    response = ec2.describe_instances(InstanceIds=[instance_id])
    state = response['Reservations'][0]['Instances'][0]['State']['Name']
    assert state == 'running'


# Test listing security groups
def test_list_security_groups():
    """Test listing security groups"""
    result = list_security_groups(region=TEST_REGION)
    groups = json.loads(result)
    
    # Verify result is a list
    assert isinstance(groups, list)
    
    # Verify structure of security group data if any exist
    if groups:
        assert 'GroupId' in groups[0]
        assert 'GroupName' in groups[0]


# Test listing Lambda functions
def test_list_lambda_functions():
    """Test listing Lambda functions"""
    result = list_lambda_functions(region=TEST_REGION)
    data = json.loads(result)
    
    # If no error, it should be a list (might be empty if no functions exist)
    if not isinstance(data, dict) or 'error' not in data:
        assert isinstance(data, list)
        # If functions exist, verify structure
        if data:
            assert 'FunctionName' in data[0]
            assert 'Runtime' in data[0]


# Test running AWS code
def test_run_aws_code():
    """Test running custom AWS code"""
    code = """
# List AWS regions
client = boto3.client('ec2')
regions = client.describe_regions()
result = [region['RegionName'] for region in regions['Regions']]
print(f"Available AWS regions: {len(result)}")
"""
    
    result = run_aws_code(code)
    
    # Verify that the code executed successfully
    assert "Available AWS regions:" in result
    assert "Error:" not in result


# Test run aws code with full S3 bucket listing
def test_run_aws_code_s3_listing():
    """Test running custom AWS code to list S3 buckets"""
    code = """
# List S3 buckets with creation date
s3 = boto3.client('s3')
response = s3.list_buckets()
result = [{
    'name': bucket['Name'],
    'created': bucket['CreationDate'].isoformat()
} for bucket in response['Buckets']]
"""
    
    result = run_aws_code(code)
    
    # Verify that the code executed without errors
    assert "Error:" not in result


# Run all tests
if __name__ == "__main__":
    # Run with -v flag for verbose output
    import sys
    sys.exit(pytest.main(["-v"]))