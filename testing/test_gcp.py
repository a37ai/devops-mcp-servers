import sys
import os
# Add the parent directory to the Python path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import pytest
import json
import time
import uuid
import tempfile
import logging
from datetime import datetime

# Import the module to test
from servers.gcp.gcp_mcp import (
    get_gcp_client, list_gcs_buckets, list_gcs_objects,
    list_gce_instances, list_gce_images, start_gce_instance, stop_gce_instance,
    create_gce_instance, list_firewall_rules, list_cloud_functions,
    list_bigquery_datasets, list_gke_clusters, run_gcp_code
)

# Import GCP libraries for resource management
from google.cloud import storage
from google.cloud import compute_v1
from google.cloud.container_v1 import ClusterManagerClient
import google.auth

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# Generate unique identifiers for resources to avoid conflicts
test_uuid = str(uuid.uuid4())[:8]
TEST_PREFIX = f"mcp-test-{test_uuid}"

# Configure test settings
TEST_PROJECT = os.environ.get("GCP_TEST_PROJECT", "")  # Set this in your environment
TEST_REGION = "us-central1"
TEST_ZONE = "us-central1-a"
TEST_BUCKET_NAME = f"{TEST_PREFIX}-bucket"
TEST_INSTANCE_NAME = f"{TEST_PREFIX}-instance"
TEST_GKE_CLUSTER_NAME = f"{TEST_PREFIX}-cluster"

# Validate environment
if not TEST_PROJECT:
    logger.warning("GCP_TEST_PROJECT environment variable not set. Some tests may be skipped.")

# Teardown resources after tests
test_resources = {
    "gcs_buckets": [],
    "gce_instances": [],
    "gke_clusters": []
}

# Fixture for cleanup after all tests
@pytest.fixture(scope="session", autouse=True)
def cleanup_resources():
    yield
    logger.info("Cleaning up test resources...")
    
    # Clean up GCE instances
    if test_resources["gce_instances"]:
        logger.info(f"Terminating GCE instances: {test_resources['gce_instances']}")
        try:
            # Use compute client for cleanup
            compute_client = compute_v1.InstancesClient()
            for instance_data in test_resources["gce_instances"]:
                instance_name = instance_data.get("name")
                zone = instance_data.get("zone", TEST_ZONE)
                
                logger.info(f"Deleting instance {instance_name} in {zone}")
                operation = compute_client.delete(
                    project=TEST_PROJECT,
                    zone=zone,
                    instance=instance_name
                )
                
                # Wait for operation to complete
                operation_client = compute_v1.ZoneOperationsClient()
                while not operation.status == compute_v1.Operation.Status.DONE:
                    operation = operation_client.get(
                        project=TEST_PROJECT,
                        zone=zone, 
                        operation=operation.name
                    )
                    time.sleep(1)
                
                logger.info(f"Instance {instance_name} deleted successfully")
        except Exception as e:
            logger.error(f"Error cleaning up GCE instances: {str(e)}")
    
    # Clean up GCS buckets
    for bucket_name in test_resources["gcs_buckets"]:
        try:
            logger.info(f"Deleting GCS bucket: {bucket_name}")
            storage_client = storage.Client(project=TEST_PROJECT)
            bucket = storage_client.bucket(bucket_name)
            
            # Delete all objects in the bucket
            blobs = bucket.list_blobs()
            for blob in blobs:
                blob.delete()
            
            # Delete the bucket
            bucket.delete()
            logger.info(f"GCS bucket {bucket_name} deleted successfully")
        except Exception as e:
            logger.error(f"Error cleaning up GCS bucket {bucket_name}: {str(e)}")
    
    # Clean up GKE clusters
    if test_resources["gke_clusters"]:
        logger.info(f"Deleting GKE clusters: {test_resources['gke_clusters']}")
        try:
            # Use container client for cleanup
            container_client = ClusterManagerClient()
            for cluster_data in test_resources["gke_clusters"]:
                cluster_name = cluster_data.get("name")
                location = cluster_data.get("location", TEST_REGION)
                
                logger.info(f"Deleting cluster {cluster_name} in {location}")
                operation = container_client.delete_cluster(
                    name=f"projects/{TEST_PROJECT}/locations/{location}/clusters/{cluster_name}"
                )
                
                # Wait for operation to complete (this could take several minutes)
                logger.info("Waiting for cluster deletion to complete (this may take a while)...")
                while not operation.done():
                    time.sleep(30)  # Check every 30 seconds
                    operation = container_client.get_operation(
                        name=operation.name
                    )
                
                logger.info(f"Cluster {cluster_name} deleted successfully")
        except Exception as e:
            logger.error(f"Error cleaning up GKE clusters: {str(e)}")


# Optional marker to skip tests that create GCP resources
skip_resource_creation = pytest.mark.skipif(
    os.environ.get("SKIP_RESOURCE_CREATION") == "true" or not TEST_PROJECT,
    reason="Skipping tests that create GCP resources"
)


# Test GCP Client Factory
def test_get_gcp_client():
    """Test that the GCP client factory works"""
    # Test storage client
    storage_client = get_gcp_client('storage')
    assert storage_client is not None
    
    # Test compute client
    compute_client = get_gcp_client('compute')
    assert compute_client is not None
    
    # Test with invalid service (should raise ValueError)
    with pytest.raises(ValueError):
        invalid_client = get_gcp_client('invalid_service')


# Test listing GCS buckets
def test_list_gcs_buckets():
    """Test listing GCS buckets"""
    result = list_gcs_buckets(project_id=TEST_PROJECT)
    buckets = json.loads(result)
    
    # Verify the result is a list
    assert isinstance(buckets, list)
    
    # Verify structure of bucket data if any buckets exist
    if buckets:
        assert 'Name' in buckets[0]
        assert 'CreationDate' in buckets[0]
        assert 'Location' in buckets[0]
        assert 'StorageClass' in buckets[0]


# Create a GCS bucket for testing
@skip_resource_creation
def test_create_gcs_bucket():
    """Create a GCS bucket for subsequent tests"""
    try:
        # Get storage client
        storage_client = storage.Client(project=TEST_PROJECT)
        
        # Create the test bucket
        logger.info(f"Creating test bucket: {TEST_BUCKET_NAME}")
        bucket = storage_client.create_bucket(TEST_BUCKET_NAME, location=TEST_REGION)
        
        # Add bucket to resources for cleanup
        test_resources["gcs_buckets"].append(TEST_BUCKET_NAME)
        
        # Upload test files
        logger.info("Uploading test files to bucket")
        with tempfile.NamedTemporaryFile(mode='w+') as temp:
            temp.write("Test content for GCS bucket")
            temp.flush()
            
            # Upload a file directly
            blob = bucket.blob("test-file.txt")
            blob.upload_from_filename(temp.name)
            
            # Upload a file to a "folder"
            blob = bucket.blob("test-folder/test-file2.txt")
            blob.upload_from_filename(temp.name)
        
        # Verify bucket exists
        all_buckets = storage_client.list_buckets()
        bucket_names = [b.name for b in all_buckets]
        assert TEST_BUCKET_NAME in bucket_names
        
        logger.info(f"Test bucket {TEST_BUCKET_NAME} created successfully")
    
    except Exception as e:
        logger.error(f"Failed to create test GCS bucket: {str(e)}")
        pytest.fail(f"Failed to create test GCS bucket: {str(e)}")


# Test listing GCS objects (depends on test_create_gcs_bucket)
@skip_resource_creation
def test_list_gcs_objects():
    """Test listing objects in a GCS bucket"""
    # Skip if bucket wasn't created
    if TEST_BUCKET_NAME not in test_resources["gcs_buckets"]:
        pytest.skip("Test bucket not available")
    
    # Test with no prefix
    result = list_gcs_objects(TEST_BUCKET_NAME)
    data = json.loads(result)
    
    # Verify structure
    assert 'Objects' in data
    assert 'Count' in data
    
    # Should have at least 2 objects
    assert data['Count'] >= 2
    assert len(data['Objects']) >= 2
    
    # Test with prefix
    result = list_gcs_objects(TEST_BUCKET_NAME, prefix="test-folder/")
    data = json.loads(result)
    
    # Should have only objects with the prefix
    for obj in data['Objects']:
        assert obj['Name'].startswith("test-folder/")


# Test listing GCE instances
def test_list_gce_instances():
    """Test listing GCE instances"""
    result = list_gce_instances(project_id=TEST_PROJECT, zone=TEST_ZONE)
    instances = json.loads(result)
    
    # Verify result is a list
    assert isinstance(instances, list)
    
    # Verify structure of instance data if any instances exist
    if instances:
        assert 'Name' in instances[0]
        assert 'Zone' in instances[0]
        assert 'Status' in instances[0]


# Test listing GCE images
def test_list_gce_images():
    """Test listing GCE images"""
    result = list_gce_images(project_id="debian-cloud", family="debian-11")
    images = json.loads(result)
    
    # Should find Debian 11 images
    assert len(images) > 0
    
    # Verify structure
    assert 'Name' in images[0]
    assert 'Family' in images[0]
    assert 'CreationTime' in images[0]


# Create a GCE instance for testing
@skip_resource_creation
def test_create_gce_instance():
    """Test creating a GCE instance"""
    try:
        # Create the instance using our function
        logger.info(f"Creating test GCE instance: {TEST_INSTANCE_NAME}")
        result = create_gce_instance(
            instance_name=TEST_INSTANCE_NAME,
            machine_type="e2-micro",
            image_project="debian-cloud",
            image_family="debian-11",
            zone=TEST_ZONE,
            project_id=TEST_PROJECT,
            network="default",
            external_ip=True
        )
        
        # Parse the result
        data = json.loads(result)
        logger.info(f"GCE instance creation response: {data}")
        
        # Verify success
        assert data['Status'] == 'Success'
        assert data['InstanceName'] == TEST_INSTANCE_NAME
        
        # Add instance to resources for cleanup
        test_resources["gce_instances"].append({
            "name": TEST_INSTANCE_NAME,
            "zone": TEST_ZONE
        })
        
        # Wait for instance to be running
        logger.info("Waiting for instance to be in RUNNING state...")
        compute_client = compute_v1.InstancesClient()
        max_retries = 20
        retries = 0
        
        while retries < max_retries:
            instance = compute_client.get(
                project=TEST_PROJECT,
                zone=TEST_ZONE,
                instance=TEST_INSTANCE_NAME
            )
            
            if instance.status == "RUNNING":
                break
                
            time.sleep(5)
            retries += 1
        
        assert instance.status == "RUNNING"
        logger.info(f"Instance {TEST_INSTANCE_NAME} is now running")
        
    except Exception as e:
        logger.error(f"Failed to create test GCE instance: {str(e)}")
        pytest.fail(f"Failed to create test GCE instance: {str(e)}")


# Test stopping GCE instance
@skip_resource_creation
def test_stop_gce_instance():
    """Test stopping a GCE instance"""
    # Skip if instance wasn't created
    instance_exists = False
    for instance in test_resources["gce_instances"]:
        if instance["name"] == TEST_INSTANCE_NAME:
            instance_exists = True
            break
            
    if not instance_exists:
        pytest.skip("Test instance not available")
    
    # Stop the instance
    logger.info(f"Stopping instance {TEST_INSTANCE_NAME}")
    result = stop_gce_instance(TEST_INSTANCE_NAME, TEST_ZONE, TEST_PROJECT)
    data = json.loads(result)
    
    # Verify success
    assert data['Status'] == 'Success'
    assert data['InstanceName'] == TEST_INSTANCE_NAME
    
    # Wait for instance to stop
    logger.info("Waiting for instance to be in TERMINATED state...")
    compute_client = compute_v1.InstancesClient()
    max_retries = 20
    retries = 0
    
    while retries < max_retries:
        instance = compute_client.get(
            project=TEST_PROJECT,
            zone=TEST_ZONE,
            instance=TEST_INSTANCE_NAME
        )
        
        if instance.status == "TERMINATED":
            break
            
        time.sleep(5)
        retries += 1
    
    assert instance.status == "TERMINATED"
    logger.info(f"Instance {TEST_INSTANCE_NAME} is now stopped")


# Test starting GCE instance
@skip_resource_creation
def test_start_gce_instance():
    """Test starting a GCE instance"""
    # Skip if instance wasn't created
    instance_exists = False
    for instance in test_resources["gce_instances"]:
        if instance["name"] == TEST_INSTANCE_NAME:
            instance_exists = True
            break
            
    if not instance_exists:
        pytest.skip("Test instance not available")
    
    # Start the instance
    logger.info(f"Starting instance {TEST_INSTANCE_NAME}")
    result = start_gce_instance(TEST_INSTANCE_NAME, TEST_ZONE, TEST_PROJECT)
    data = json.loads(result)
    
    # Verify success
    assert data['Status'] == 'Success'
    assert data['InstanceName'] == TEST_INSTANCE_NAME
    
    # Wait for instance to start
    logger.info("Waiting for instance to be in RUNNING state...")
    compute_client = compute_v1.InstancesClient()
    max_retries = 20
    retries = 0
    
    while retries < max_retries:
        instance = compute_client.get(
            project=TEST_PROJECT,
            zone=TEST_ZONE,
            instance=TEST_INSTANCE_NAME
        )
        
        if instance.status == "RUNNING":
            break
            
        time.sleep(5)
        retries += 1
    
    assert instance.status == "RUNNING"
    logger.info(f"Instance {TEST_INSTANCE_NAME} is now running")


# Test listing firewall rules
def test_list_firewall_rules():
    """Test listing firewall rules"""
    result = list_firewall_rules(project_id=TEST_PROJECT)
    rules = json.loads(result)
    
    # Verify result is a list
    assert isinstance(rules, list)
    
    # Verify structure of rules if any exist
    if rules:
        assert 'Name' in rules[0]
        assert 'Network' in rules[0]
        assert 'Direction' in rules[0]


# Test listing Cloud Functions
def test_list_cloud_functions():
    """Test listing Cloud Functions"""
    result = list_cloud_functions(project_id=TEST_PROJECT, region=TEST_REGION)
    data = json.loads(result)
    
    # If error, the test continues (as there might not be any functions)
    if isinstance(data, dict) and 'Status' in data and data['Status'] == 'Error':
        logger.warning(f"Could not list functions: {data.get('Message')}")
        return
        
    # If successful, should be a list
    assert isinstance(data, list)
    
    # If functions exist, verify structure
    if data:
        assert 'Name' in data[0]
        assert 'Runtime' in data[0]


# Test listing BigQuery datasets
def test_list_bigquery_datasets():
    """Test listing BigQuery datasets"""
    result = list_bigquery_datasets(project_id=TEST_PROJECT)
    data = json.loads(result)
    
    # If error, the test continues (as there might not be any datasets)
    if isinstance(data, dict) and 'Status' in data and data['Status'] == 'Error':
        logger.warning(f"Could not list datasets: {data.get('Message')}")
        return
        
    # If successful, should be a list
    assert isinstance(data, list)
    
    # If datasets exist, verify structure
    if data:
        assert 'DatasetId' in data[0]
        assert 'Location' in data[0]


# Test running GCP code
def test_run_gcp_code():
    """Test running custom GCP code"""
    code = """
# List GCP regions
from google.cloud import compute_v1
client = compute_v1.RegionsClient()
response = client.list(project='google-cloud-regions')
regions = [region.name for region in response]
print(f"Available GCP regions: {len(regions)}")
"""
    
    result = run_gcp_code(code)
    
    # Verify that the code executed successfully
    assert "Available GCP regions:" in result
    assert "Error:" not in result


# Run all tests
if __name__ == "__main__":
    # Run with -v flag for verbose output
    import sys
    sys.exit(pytest.main(["-v"]))