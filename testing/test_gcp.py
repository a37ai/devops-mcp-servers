import pytest
import json
import tempfile
import os
import sys
from unittest.mock import patch, MagicMock, ANY
import subprocess
from google.auth.exceptions import DefaultCredentialsError

# Import the module containing the functions to test
# Assuming the code is saved in a file called gcp_server.py
# Adjust imports as necessary for your file structure
import sys
sys.path.append('.')  # Adjust if needed
from servers.gcp.gcp_mcp import (
    get_gcp_client, list_gcs_buckets, list_gcs_objects,
    list_gce_instances, list_gce_images, start_gce_instance, stop_gce_instance,
    create_gce_instance, list_firewall_rules, list_cloud_functions,
    list_bigquery_datasets, list_bigquery_tables, list_gke_clusters,
    run_gcp_code, list_gcp_regions, list_machine_types
)

# Basic test to verify that the module imports correctly
def test_module_imports():
    """Verify that the module imports correctly."""
    assert callable(get_gcp_client)
    assert callable(list_gcs_buckets)
    assert callable(list_gce_instances)

# Fixtures
@pytest.fixture
def mock_auth():
    """Mock google.auth.default to return test credentials and project."""
    with patch('google.auth.default') as mock_auth:
        mock_auth.return_value = (MagicMock(), 'test-project')
        yield mock_auth

@pytest.fixture
def mock_storage_client():
    """Mock the Storage Client for GCS operations."""
    with patch('google.cloud.storage.Client') as mock_client:
        # Create a mock bucket
        mock_bucket = MagicMock()
        mock_bucket.name = 'test-bucket'
        mock_bucket.time_created.isoformat.return_value = '2023-01-01T00:00:00'
        mock_bucket.location = 'us-central1'
        mock_bucket.storage_class = 'STANDARD'
        
        # Set up the list_buckets method
        mock_client.return_value.list_buckets.return_value = [mock_bucket]
        
        # Create a mock blob
        mock_blob = MagicMock()
        mock_blob.name = 'test-file.txt'
        mock_blob.size = 1024
        mock_blob.content_type = 'text/plain'
        mock_blob.updated.isoformat.return_value = '2023-01-02T00:00:00'
        mock_blob.storage_class = 'STANDARD'
        
        # Set up the bucket.list_blobs method
        mock_client.return_value.bucket.return_value.list_blobs.return_value = [mock_blob]
        
        yield mock_client

@pytest.fixture
def mock_discovery_build():
    """Mock googleapiclient.discovery.build for GCE operations."""
    with patch('googleapiclient.discovery.build') as mock_build:
        # Create mock compute service
        mock_service = MagicMock()
        mock_build.return_value = mock_service
        
        # Mock instances API
        mock_instances = MagicMock()
        mock_service.instances.return_value = mock_instances
        
        # Mock instances.list response
        mock_instance = {
            'name': 'test-instance',
            'machineType': 'projects/test-project/zones/us-central1-a/machineTypes/e2-micro',
            'status': 'RUNNING',
            'networkInterfaces': [{
                'networkIP': '10.0.0.1',
                'accessConfigs': [{'natIP': '35.192.0.1'}]
            }],
            'creationTimestamp': '2023-01-01T00:00:00'
        }
        mock_instances.list.return_value.execute.return_value = {'items': [mock_instance]}
        
        # Mock zones.list response
        mock_service.zones.return_value.list.return_value.execute.return_value = {
            'items': [{'name': 'us-central1-a'}]
        }
        
        # Mock start/stop/insert operations
        operation_response = {'id': 'op-123', 'status': 'RUNNING'}
        mock_instances.start.return_value.execute.return_value = operation_response
        mock_instances.stop.return_value.execute.return_value = operation_response
        mock_instances.insert.return_value.execute.return_value = operation_response
        
        # Mock images API
        mock_images = MagicMock()
        mock_service.images.return_value = mock_images
        
        # Mock images.list response
        mock_images.list.return_value.execute.return_value = {
            'items': [{
                'name': 'debian-11',
                'family': 'debian-11',
                'status': 'READY',
                'creationTimestamp': '2023-01-01T00:00:00',
                'selfLink': 'projects/debian-cloud/global/images/debian-11',
                'diskSizeGb': '10',
                'description': 'Debian 11'
            }]
        }
        mock_images.list_next.return_value = None  # No more pages
        
        # Mock images.getFromFamily response
        mock_images.getFromFamily.return_value.execute.return_value = {
            'selfLink': 'projects/debian-cloud/global/images/debian-11'
        }
        
        # Mock firewalls API
        mock_firewalls = MagicMock()
        mock_service.firewalls.return_value = mock_firewalls
        
        # Mock firewalls.list response
        mock_firewalls.list.return_value.execute.return_value = {
            'items': [{
                'name': 'default-allow-internal',
                'network': 'projects/test-project/global/networks/default',
                'direction': 'INGRESS',
                'priority': 1000,
                'allowed': [{'IPProtocol': 'tcp', 'ports': ['0-65535']}],
                'sourceRanges': ['10.0.0.0/8']
            }]
        }
        
        yield mock_build

@pytest.fixture
def mock_cloud_functions():
    """Mock the Cloud Functions client."""
    with patch('google.cloud.functions_v1.CloudFunctionsServiceClient') as mock_client:
        # Create a mock function
        mock_function = MagicMock()
        mock_function.name = 'projects/test-project/locations/us-central1/functions/test-function'
        mock_function.runtime = 'python39'
        mock_function.entry_point = 'handler'
        mock_function.status.name = 'ACTIVE'
        mock_function.update_time.isoformat.return_value = '2023-01-01T00:00:00'
        mock_function.version_id = '1'
        mock_function.available_memory_mb = 256
        mock_function.timeout.seconds = 60
        mock_function.https_trigger = MagicMock()
        mock_function.https_trigger.url = 'https://test-function-url.com'
        
        # Set up list_functions method
        mock_client.return_value.list_functions.return_value = [mock_function]
        
        yield mock_client

@pytest.fixture
def mock_bigquery_client():
    """Mock the BigQuery client."""
    with patch('google.cloud.bigquery.Client') as mock_client:
        # Create a mock dataset
        mock_dataset = MagicMock()
        mock_dataset.dataset_id = 'test_dataset'
        mock_dataset.created.isoformat.return_value = '2023-01-01T00:00:00'
        mock_dataset.modified.isoformat.return_value = '2023-01-02T00:00:00'
        mock_dataset.location = 'US'
        mock_dataset.description = 'Test dataset'
        
        # Set up list_datasets method
        mock_client.return_value.list_datasets.return_value = [mock_dataset]
        
        # Create a mock table
        mock_table = MagicMock()
        mock_table.table_id = 'test_table'
        mock_table.table_type = 'TABLE'
        mock_table.created.isoformat.return_value = '2023-01-01T00:00:00'
        mock_table.modified.isoformat.return_value = '2023-01-02T00:00:00'
        
        # Set up list_tables method
        mock_client.return_value.list_tables.return_value = [mock_table]
        
        yield mock_client

@pytest.fixture
def mock_container_client():
    """Mock the GKE Container client."""
    with patch('google.cloud.container_v1.ClusterManagerClient') as mock_client:
        # Create a mock node pool
        mock_node_pool = MagicMock()
        mock_node_pool.name = 'default-pool'
        mock_node_pool.initial_node_count = 3
        
        # Create a mock cluster
        mock_cluster = MagicMock()
        mock_cluster.name = 'test-cluster'
        mock_cluster.location = 'us-central1'
        mock_cluster.status.name = 'RUNNING'
        mock_cluster.node_pools = [mock_node_pool]
        mock_cluster.master_version = '1.24.0'
        mock_cluster.network = 'default'
        mock_cluster.subnetwork = 'default'
        mock_cluster.endpoint = '35.192.0.2'
        mock_cluster.create_time.isoformat.return_value = '2023-01-01T00:00:00'
        
        # Set up list_clusters method
        mock_response = MagicMock()
        mock_response.clusters = [mock_cluster]
        mock_client.return_value.list_clusters.return_value = mock_response
        
        yield mock_client

# Test classes organized by GCP service
class TestHelperFunctions:
    """Test helper functions in the GCP server."""
    
    def test_get_gcp_client(self, mock_auth):
        """Test the get_gcp_client helper function."""
        with patch('google.cloud.storage.Client') as mock_storage:
            # Test getting a storage client
            client = get_gcp_client('storage')
            assert client is not None
            mock_storage.assert_called_once_with(project='test-project', credentials=ANY)
        
        with patch('google.cloud.compute.ComputeClient') as mock_compute:
            # Test getting a compute client
            client = get_gcp_client('compute')
            assert client is not None
            mock_compute.assert_called_once_with(credentials=ANY)
        
        # Test invalid service
        with pytest.raises(ValueError):
            get_gcp_client('invalid-service')

class TestGCSFunctions:
    """Test Google Cloud Storage related functions."""
    
    def test_list_gcs_buckets(self, mock_auth, mock_storage_client):
        """Test listing GCS buckets."""
        # Test default project
        result = list_gcs_buckets()
        result_data = json.loads(result)
        
        assert isinstance(result_data, list)
        assert len(result_data) == 1
        assert result_data[0]['Name'] == 'test-bucket'
        assert result_data[0]['Location'] == 'us-central1'
        
        # Test specific project
        result = list_gcs_buckets(project_id='custom-project')
        mock_storage_client.assert_called_with(project='custom-project', credentials=ANY)
    
    def test_list_gcs_objects(self, mock_auth, mock_storage_client):
        """Test listing objects in a GCS bucket."""
        # Test with default parameters
        result = list_gcs_objects('test-bucket')
        result_data = json.loads(result)
        
        assert 'Objects' in result_data
        assert len(result_data['Objects']) == 1
        assert result_data['Objects'][0]['Name'] == 'test-file.txt'
        assert result_data['Objects'][0]['Size'] == 1024
        
        # Test with custom parameters
        result = list_gcs_objects('test-bucket', prefix='test/', max_items=50)
        mock_storage_client.return_value.bucket.assert_called_with('test-bucket')
        mock_storage_client.return_value.bucket.return_value.list_blobs.assert_called_with(
            prefix='test/', max_results=50)
    
    def test_gcs_error_handling(self, mock_auth):
        """Test error handling in GCS functions."""
        with patch('google.cloud.storage.Client', side_effect=Exception("Storage API error")):
            result = list_gcs_buckets()
            result_data = json.loads(result)
            assert 'Status' in result_data
            assert result_data['Status'] == 'Error'
            assert 'Message' in result_data
            assert 'Storage API error' in result_data['Message']

class TestGCEFunctions:
    """Test Google Compute Engine related functions."""
    
    def test_list_gce_instances(self, mock_auth, mock_discovery_build):
        """Test listing GCE instances."""
        # Test listing all instances
        result = list_gce_instances()
        result_data = json.loads(result)
        
        assert isinstance(result_data, list)
        assert len(result_data) == 1
        assert result_data[0]['Name'] == 'test-instance'
        assert result_data[0]['Status'] == 'RUNNING'
        
        # Test with specific zone
        result = list_gce_instances(zone='us-central1-a')
        mock_discovery_build.return_value.instances.return_value.list.assert_called_with(
            project='test-project', zone='us-central1-a')
    
    def test_list_gce_images(self, mock_auth, mock_discovery_build):
        """Test listing GCE images."""
        # Test listing all images
        result = list_gce_images()
        result_data = json.loads(result)
        
        assert isinstance(result_data, list)
        assert len(result_data) == 1
        assert result_data[0]['Name'] == 'debian-11'
        assert result_data[0]['Family'] == 'debian-11'
        
        # Test with specific project and family
        result = list_gce_images(project_id='debian-cloud', family='debian-11')
        # Verify discovery_build was called
        mock_discovery_build.assert_called_with('compute', 'v1', credentials=ANY)
    
    def test_start_gce_instance(self, mock_auth, mock_discovery_build):
        """Test starting a GCE instance."""
        result = start_gce_instance('test-instance', 'us-central1-a')
        result_data = json.loads(result)
        
        assert result_data['Status'] == 'Success'
        assert result_data['InstanceName'] == 'test-instance'
        assert result_data['Zone'] == 'us-central1-a'
        
        # Verify API call
        mock_discovery_build.return_value.instances.return_value.start.assert_called_with(
            project='test-project', zone='us-central1-a', instance='test-instance')
    
    def test_stop_gce_instance(self, mock_auth, mock_discovery_build):
        """Test stopping a GCE instance."""
        result = stop_gce_instance('test-instance', 'us-central1-a')
        result_data = json.loads(result)
        
        assert result_data['Status'] == 'Success'
        assert result_data['InstanceName'] == 'test-instance'
        assert result_data['Zone'] == 'us-central1-a'
        
        # Verify API call
        mock_discovery_build.return_value.instances.return_value.stop.assert_called_with(
            project='test-project', zone='us-central1-a', instance='test-instance')
    
    def test_create_gce_instance(self, mock_auth, mock_discovery_build):
        """Test creating a GCE instance."""
        # Test with default parameters
        result = create_gce_instance('new-instance')
        result_data = json.loads(result)
        
        assert result_data['Status'] == 'Success'
        assert result_data['InstanceName'] == 'new-instance'
        assert result_data['MachineType'] == 'e2-micro'
        assert result_data['Zone'] == 'us-central1-a'
        
        # Test with custom parameters
        result = create_gce_instance(
            'custom-instance',
            machine_type='e2-medium',
            image_project='ubuntu-os-cloud',
            image_family='ubuntu-2004-lts',
            zone='us-west1-b',
            project_id='custom-project',
            network='custom-network',
            subnet='custom-subnet',
            external_ip=False
        )
        result_data = json.loads(result)
        
        assert result_data['Status'] == 'Success'
        assert result_data['InstanceName'] == 'custom-instance'
        assert result_data['MachineType'] == 'e2-medium'
        assert result_data['Zone'] == 'us-west1-b'
        
        # Verify API call was made (checking that insert was called)
        mock_discovery_build.return_value.instances.return_value.insert.assert_called()
    
    def test_gce_error_handling(self, mock_auth):
        """Test error handling in GCE functions."""
        with patch('googleapiclient.discovery.build', side_effect=Exception("Compute API error")):
            result = list_gce_instances()
            result_data = json.loads(result)
            assert result_data['Status'] == 'Error'
            assert 'Compute API error' in result_data['Message']

class TestFirewallFunctions:
    """Test Firewall related functions."""
    
    def test_list_firewall_rules(self, mock_auth, mock_discovery_build):
        """Test listing firewall rules."""
        result = list_firewall_rules()
        result_data = json.loads(result)
        
        assert isinstance(result_data, list)
        assert len(result_data) == 1
        assert result_data[0]['Name'] == 'default-allow-internal'
        assert result_data[0]['Direction'] == 'INGRESS'
        
        # Verify API call
        mock_discovery_build.return_value.firewalls.return_value.list.assert_called_with(
            project='test-project')
    
    def test_firewall_error_handling(self, mock_auth):
        """Test error handling in firewall functions."""
        with patch('googleapiclient.discovery.build', side_effect=Exception("Firewall API error")):
            result = list_firewall_rules()
            result_data = json.loads(result)
            assert result_data['Status'] == 'Error'
            assert 'Firewall API error' in result_data['Message']

class TestCloudFunctionsFunctions:
    """Test Cloud Functions related functions."""
    
    def test_list_cloud_functions(self, mock_auth, mock_cloud_functions):
        """Test listing Cloud Functions."""
        # Test with default region
        result = list_cloud_functions()
        result_data = json.loads(result)
        
        assert isinstance(result_data, list)
        assert len(result_data) == 1
        assert result_data[0]['Name'] == 'test-function'
        assert result_data[0]['Runtime'] == 'python39'
        
        # Test with custom region
        result = list_cloud_functions(region='us-west1')
        mock_cloud_functions.return_value.list_functions.assert_called_with(
            request={"parent": "projects/test-project/locations/us-west1"})
    
    def test_cloud_functions_error_handling(self, mock_auth):
        """Test error handling in Cloud Functions functions."""
        with patch('google.cloud.functions_v1.CloudFunctionsServiceClient', 
                  side_effect=Exception("Functions API error")):
            result = list_cloud_functions()
            result_data = json.loads(result)
            assert result_data['Status'] == 'Error'
            assert 'Functions API error' in result_data['Message']

class TestBigQueryFunctions:
    """Test BigQuery related functions."""
    
    def test_list_bigquery_datasets(self, mock_auth, mock_bigquery_client):
        """Test listing BigQuery datasets."""
        # Test with default project
        result = list_bigquery_datasets()
        result_data = json.loads(result)
        
        assert isinstance(result_data, list)
        assert len(result_data) == 1
        assert result_data[0]['DatasetId'] == 'test_dataset'
        assert result_data[0]['Location'] == 'US'
        
        # Test with custom project
        result = list_bigquery_datasets(project_id='custom-project')
        mock_bigquery_client.assert_called_with(project='custom-project', credentials=ANY)
    
    def test_list_bigquery_tables(self, mock_auth, mock_bigquery_client):
        """Test listing tables in a BigQuery dataset."""
        result = list_bigquery_tables('test_dataset')
        result_data = json.loads(result)
        
        assert isinstance(result_data, list)
        assert len(result_data) == 1
        assert result_data[0]['TableId'] == 'test_table'
        assert result_data[0]['Type'] == 'TABLE'
        
        # Verify API call
        mock_bigquery_client.return_value.list_tables.assert_called_with('test-project.test_dataset')
    
    def test_bigquery_error_handling(self, mock_auth):
        """Test error handling in BigQuery functions."""
        with patch('google.cloud.bigquery.Client', side_effect=Exception("BigQuery API error")):
            result = list_bigquery_datasets()
            result_data = json.loads(result)
            assert result_data['Status'] == 'Error'
            assert 'BigQuery API error' in result_data['Message']

class TestGKEFunctions:
    """Test GKE related functions."""
    
    def test_list_gke_clusters(self, mock_auth, mock_container_client):
        """Test listing GKE clusters."""
        # Test without zone specification
        result = list_gke_clusters()
        result_data = json.loads(result)
        
        assert isinstance(result_data, list)
        assert len(result_data) == 1
        assert result_data[0]['Name'] == 'test-cluster'
        assert result_data[0]['Status'] == 'RUNNING'
        
        # Test with zone specification
        result = list_gke_clusters(zone='us-central1')
        mock_container_client.return_value.list_clusters.assert_called_with(
            parent="projects/test-project/locations/us-central1")
    
    def test_gke_error_handling(self, mock_auth):
        """Test error handling in GKE functions."""
        with patch('google.cloud.container_v1.ClusterManagerClient', 
                  side_effect=Exception("GKE API error")):
            result = list_gke_clusters()
            result_data = json.loads(result)
            assert result_data['Status'] == 'Error'
            assert 'GKE API error' in result_data['Message']

class TestRunGCPCode:
    """Test the run_gcp_code function."""
    
    def test_run_gcp_code_success(self):
        """Test successful code execution."""
        with patch('tempfile.NamedTemporaryFile') as mock_temp_file, \
             patch('subprocess.run') as mock_run, \
             patch('builtins.open', create=True) as mock_open, \
             patch('os.path.exists', return_value=True), \
             patch('os.remove'):
            
            # Mock the temporary file
            mock_temp = MagicMock()
            mock_temp.name = '/tmp/test_file.py'
            mock_temp_file.return_value.__enter__.return_value = mock_temp
            
            # Mock the subprocess run
            mock_run.return_value = MagicMock(returncode=0)
            
            # Mock reading the output file
            mock_file_handle = MagicMock()
            mock_file_handle.read.return_value = "Hello, GCP!"
            mock_context_manager = MagicMock()
            mock_context_manager.__enter__.return_value = mock_file_handle
            mock_open.return_value = mock_context_manager
            
            # Call the function
            result = run_gcp_code('print("Hello, GCP!")')
            
            # Verify results
            assert result == "Hello, GCP!"
            
            # Verify subprocess was called correctly
            mock_run.assert_called_with(['python', '/tmp/test_file.py'], timeout=30)
    
    def test_run_gcp_code_timeout(self):
        """Test code execution timeout."""
        with patch('tempfile.NamedTemporaryFile') as mock_temp_file, \
             patch('subprocess.run', side_effect=subprocess.TimeoutExpired('cmd', 30)), \
             patch('os.path.exists', return_value=True), \
             patch('os.remove'):
            
            # Mock the temporary file
            mock_temp = MagicMock()
            mock_temp.name = '/tmp/test_file.py'
            mock_temp_file.return_value.__enter__.return_value = mock_temp
            
            # Call the function
            result = run_gcp_code('print("This will timeout")')
            
            # Verify results
            assert "Execution timed out" in result
    
    def test_run_gcp_code_error(self):
        """Test code execution error."""
        with patch('tempfile.NamedTemporaryFile', side_effect=Exception("File error")):
            result = run_gcp_code('print("This will fail")')
            assert "Error executing code:" in result
            assert "File error" in result

class TestResourceFunctions:
    """Test resource functions."""
    
    def test_list_gcp_regions(self):
        """Test listing GCP regions."""
        result = list_gcp_regions()
        result_data = json.loads(result)
        
        assert isinstance(result_data, list)
        assert "us-central1" in result_data
        assert "europe-west1" in result_data
        assert len(result_data) > 20  # Ensure we have a reasonable number of regions
    
    def test_list_machine_types(self):
        """Test listing machine types."""
        result = list_machine_types()
        result_data = json.loads(result)
        
        assert isinstance(result_data, dict)
        assert "General Purpose" in result_data
        assert "e2-micro" in result_data["General Purpose"]
        assert "Memory Optimized" in result_data
        assert "Compute Optimized" in result_data

class TestAuthentication:
    """Test authentication edge cases."""
    
    def test_auth_error_handling(self):
        """Test handling authentication errors."""
        with patch('google.auth.default', side_effect=DefaultCredentialsError("No credentials")):
            result = list_gcs_buckets()
            result_data = json.loads(result)
            assert result_data['Status'] == 'Error'
            assert 'No credentials' in result_data['Message']

# Run the tests
if __name__ == "__main__":
    pytest.main(["-v"])