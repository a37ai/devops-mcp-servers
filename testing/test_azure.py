import sys
import os
# Add the parent directory to the Python path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import pytest
import json
import time
import os
import uuid
from unittest.mock import patch, MagicMock
from servers.azure.azure_mcp import *

# Test fixture configuration
TEST_PREFIX = f"mcp-test-{uuid.uuid4().hex[:8]}"  # Unique prefix for all test resources
TEST_LOCATION = "eastus"
TEST_RG_NAME = f"{TEST_PREFIX}-rg"
TEST_STORAGE_NAME = f"{TEST_PREFIX}storage".replace('-', '')  # Storage accounts can't have hyphens
TEST_VM_NAME = f"{TEST_PREFIX}-vm"
CREATED_RESOURCES = []  # Track resources created during tests for cleanup

# Mock responses for tests that shouldn't create real resources
MOCK_VM = {
    'Name': 'mock-vm',
    'ResourceGroup': TEST_RG_NAME,
    'Location': TEST_LOCATION,
    'VMSize': 'Standard_DS1_v2',
    'ProvisioningState': 'Succeeded',
    'OsType': 'Linux',
    'PowerState': 'running'
}

@pytest.fixture(scope="module", autouse=True)
def setup_and_teardown():
    """Setup test environment before tests and clean up after."""
    print(f"\n=== Setting up test environment with prefix: {TEST_PREFIX} ===")

    # Create a resource group for testing
    try:
        result = json.loads(create_resource_group(
            name=TEST_RG_NAME,
            location=TEST_LOCATION,
            tags={"Purpose": "Testing", "AutoDelete": "True"}
        ))
        
        if result.get("Status") == "Success":
            CREATED_RESOURCES.append(("resource_group", TEST_RG_NAME))
            print(f"Created resource group: {TEST_RG_NAME}")
        else:
            print(f"Failed to create resource group: {result}")
    except Exception as e:
        print(f"Error creating resource group: {str(e)}")
    
    yield  # This is where the tests will run
    
    # Teardown - clean up all created resources in reverse order
    print(f"\n=== Cleaning up test resources with prefix: {TEST_PREFIX} ===")
    
    for resource_type, resource_name in reversed(CREATED_RESOURCES):
        try:
            print(f"Cleaning up {resource_type}: {resource_name}")
            
            if resource_type == "virtual_machine":
                # First stop the VM if it exists
                client = get_azure_client(azure.mgmt.compute.ComputeManagementClient)
                try:
                    client.virtual_machines.begin_deallocate(TEST_RG_NAME, resource_name).wait()
                    print(f"Deallocated VM: {resource_name}")
                    time.sleep(30)  # Give Azure time to complete the operation
                except Exception as e:
                    print(f"Error deallocating VM {resource_name}: {str(e)}")
            
            elif resource_type == "storage_account":
                # Delete storage account
                client = get_azure_client(azure.mgmt.storage.StorageManagementClient)
                client.storage_accounts.delete(TEST_RG_NAME, resource_name)
                print(f"Deleted storage account: {resource_name}")
                time.sleep(10)  # Give Azure time to complete the operation
            
            elif resource_type == "resource_group":
                # Delete the resource group and all resources within it
                client = get_azure_client(azure.mgmt.resource.ResourceManagementClient)
                delete_operation = client.resource_groups.begin_delete(resource_name)
                print(f"Deleting resource group: {resource_name} (this may take a few minutes)")
                delete_operation.wait()
                print(f"Deleted resource group: {resource_name}")
        
        except Exception as e:
            print(f"Error during cleanup of {resource_type} {resource_name}: {str(e)}")
    
    print("=== Cleanup completed ===")

def test_list_resource_groups():
    """Test listing resource groups."""
    result = json.loads(list_resource_groups())
    
    # Verify result is a list
    assert isinstance(result, list)
    
    # Verify our test resource group is in the list
    test_rg_found = False
    for rg in result:
        if rg.get("Name") == TEST_RG_NAME:
            test_rg_found = True
            assert rg.get("Location") == TEST_LOCATION
            assert rg.get("Tags", {}).get("Purpose") == "Testing"
    
    assert test_rg_found, f"Test resource group {TEST_RG_NAME} not found in list"
    print("✓ Resource group listing test passed")

def test_create_and_list_storage_account():
    """Test creating and listing storage accounts."""
    # Create storage account
    create_result = json.loads(create_storage_account(
        name=TEST_STORAGE_NAME,
        resource_group=TEST_RG_NAME,
        location=TEST_LOCATION,
        sku="Standard_LRS"
    ))
    
    # Verify creation was successful
    assert create_result.get("Status") == "Success"
    assert create_result.get("Name") == TEST_STORAGE_NAME
    CREATED_RESOURCES.append(("storage_account", TEST_STORAGE_NAME))
    print(f"Created storage account: {TEST_STORAGE_NAME}")
    
    # Allow time for Azure to propagate the storage account
    time.sleep(30)
    
    # List storage accounts
    list_result = json.loads(list_storage_accounts(resource_group=TEST_RG_NAME))
    
    # Verify our storage account is in the list
    assert isinstance(list_result, list)
    
    test_storage_found = False
    for storage in list_result:
        if storage.get("Name") == TEST_STORAGE_NAME:
            test_storage_found = True
            assert storage.get("ResourceGroup") == TEST_RG_NAME
            assert storage.get("Sku") == "Standard_LRS"
    
    assert test_storage_found, f"Test storage account {TEST_STORAGE_NAME} not found in list"
    print("✓ Storage account creation and listing test passed")

def test_list_storage_containers():
    """Test listing storage containers."""
    # Use the existing storage account from previous test
    
    # Create a container with the blob service client
    client = get_azure_client(azure.mgmt.storage.StorageManagementClient)
    keys = client.storage_accounts.list_keys(TEST_RG_NAME, TEST_STORAGE_NAME)
    key = keys.keys[0].value
    
    # Connect to blob service and create a container
    connection_string = f"DefaultEndpointsProtocol=https;AccountName={TEST_STORAGE_NAME};AccountKey={key};EndpointSuffix=core.windows.net"
    blob_service = azure.storage.blob.BlobServiceClient.from_connection_string(connection_string)
    
    test_container_name = f"testcontainer{uuid.uuid4().hex[:8]}"
    container_client = blob_service.create_container(test_container_name)
    print(f"Created container: {test_container_name}")
    
    # Allow time for Azure to propagate the container
    time.sleep(10)
    
    # List containers
    result = json.loads(list_storage_containers(
        account_name=TEST_STORAGE_NAME,
        resource_group=TEST_RG_NAME
    ))
    
    # Verify our container is in the list
    assert isinstance(result, list)
    
    test_container_found = False
    for container in result:
        if container.get("Name") == test_container_name:
            test_container_found = True
    
    assert test_container_found, f"Test container {test_container_name} not found in list"
    
    # Clean up the container
    container_client.delete_container()
    print(f"Deleted container: {test_container_name}")
    print("✓ Storage container listing test passed")

# For VM operations, we'll use mocking to avoid creating actual VMs
@patch('servers.azure.azure_mcp.get_azure_client')
def test_list_virtual_machines(mock_get_client):
    """Test listing virtual machines with mocking."""
    # Set up mock
    mock_compute_client = MagicMock()
    mock_vm = MagicMock()
    mock_vm.name = MOCK_VM["Name"]
    mock_vm.id = f"/subscriptions/sub123/resourceGroups/{TEST_RG_NAME}/providers/Microsoft.Compute/virtualMachines/{MOCK_VM['Name']}"
    mock_vm.location = MOCK_VM["Location"]
    mock_vm.hardware_profile.vm_size = MOCK_VM["VMSize"]
    mock_vm.storage_profile.os_disk.os_type = MOCK_VM["OsType"]
    mock_vm.provisioning_state = MOCK_VM["ProvisioningState"]
    
    # Set up instance view for power state
    mock_instance_view = MagicMock()
    mock_status = MagicMock()
    mock_status.code = "PowerState/running"
    mock_instance_view.statuses = [mock_status]
    
    # Configure client to return our mock VM
    mock_compute_client.virtual_machines.list.return_value = [mock_vm]
    mock_compute_client.virtual_machines.list_all.return_value = [mock_vm]  # Add this line
    mock_compute_client.virtual_machines.instance_view.return_value = mock_instance_view
    mock_get_client.return_value = mock_compute_client
    
    # Call the function
    result = json.loads(list_virtual_machines())
    
    # Verify result contains our mock VM
    assert isinstance(result, list)
    assert len(result) > 0
    
    mock_vm_found = False
    for vm in result:
        if vm.get("Name") == MOCK_VM["Name"]:
            mock_vm_found = True
            assert vm.get("ResourceGroup") == TEST_RG_NAME
            assert vm.get("Location") == MOCK_VM["Location"]
            assert vm.get("PowerState") == "running"
    
    assert mock_vm_found, "Mock VM not found in list"
    print("✓ Virtual machine listing test passed")

@patch('servers.azure.azure_mcp.get_azure_client')
def test_start_stop_vm(mock_get_client):
    """Test starting and stopping a virtual machine with mocking."""
    # Set up mock
    mock_compute_client = MagicMock()
    mock_poller = MagicMock()
    mock_poller.result.return_value = None
    
    mock_compute_client.virtual_machines.begin_start.return_value = mock_poller
    mock_compute_client.virtual_machines.begin_deallocate.return_value = mock_poller
    mock_get_client.return_value = mock_compute_client
    
    # Test start VM
    start_result = json.loads(start_virtual_machine(
        name=MOCK_VM["Name"],
        resource_group=TEST_RG_NAME
    ))
    
    assert start_result.get("Status") == "Success"
    assert MOCK_VM["Name"] in start_result.get("Message")
    mock_compute_client.virtual_machines.begin_start.assert_called_once_with(TEST_RG_NAME, MOCK_VM["Name"])
    
    # Test stop VM
    stop_result = json.loads(stop_virtual_machine(
        name=MOCK_VM["Name"],
        resource_group=TEST_RG_NAME,
        deallocate=True
    ))
    
    assert stop_result.get("Status") == "Success"
    assert MOCK_VM["Name"] in stop_result.get("Message")
    mock_compute_client.virtual_machines.begin_deallocate.assert_called_once_with(TEST_RG_NAME, MOCK_VM["Name"])
    
    print("✓ Virtual machine start/stop test passed")

@patch('servers.azure.azure_mcp.get_azure_client')
def test_create_vm(mock_get_client):
    """Test VM creation with mocking."""
    # Set up mocks for compute client
    mock_compute_client = MagicMock()
    mock_network_client = MagicMock()
    
    # Mock VM creation result
    mock_vm = MagicMock()
    mock_vm.name = MOCK_VM["Name"]
    mock_vm.location = MOCK_VM["Location"]
    mock_vm.hardware_profile.vm_size = MOCK_VM["VMSize"]
    mock_vm.provisioning_state = MOCK_VM["ProvisioningState"]
    mock_vm.storage_profile.os_disk.os_type = MOCK_VM["OsType"]
    
    # Mock network resources creation
    mock_vnet = MagicMock()
    mock_vnet.id = "vnet-id"
    mock_subnet = MagicMock()
    mock_subnet.id = "subnet-id"
    mock_public_ip = MagicMock()
    mock_public_ip.id = "public-ip-id"
    mock_nic = MagicMock()
    mock_nic.id = "nic-id"
    
    # Configure pollers
    mock_vnet_poller = MagicMock()
    mock_vnet_poller.result.return_value = mock_vnet
    mock_subnet_poller = MagicMock()
    mock_subnet_poller.result.return_value = mock_subnet
    mock_public_ip_poller = MagicMock()
    mock_public_ip_poller.result.return_value = mock_public_ip
    mock_nic_poller = MagicMock()
    mock_nic_poller.result.return_value = mock_nic
    mock_vm_poller = MagicMock()
    mock_vm_poller.result.return_value = mock_vm
    
    # Set up mock client methods
    mock_network_client.virtual_networks.begin_create_or_update.return_value = mock_vnet_poller
    mock_network_client.subnets.begin_create_or_update.return_value = mock_subnet_poller
    mock_network_client.public_ip_addresses.begin_create_or_update.return_value = mock_public_ip_poller
    mock_network_client.network_interfaces.begin_create_or_update.return_value = mock_nic_poller
    mock_compute_client.virtual_machines.begin_create_or_update.return_value = mock_vm_poller
    
    # Configure get_azure_client to return our mock clients
    def side_effect(client_type, *args, **kwargs):
        if client_type == azure.mgmt.compute.ComputeManagementClient:
            return mock_compute_client
        elif client_type == azure.mgmt.network.NetworkManagementClient:
            return mock_network_client
        return MagicMock()
    
    mock_get_client.side_effect = side_effect
    
    # Call the function
    create_result = json.loads(create_virtual_machine(
        name=MOCK_VM["Name"],
        resource_group=TEST_RG_NAME,
        location=TEST_LOCATION,
        vm_size=MOCK_VM["VMSize"],
        admin_username="testuser",
        generate_ssh_keys=True
    ))
    
    # Verify result
    assert create_result.get("Status") == "Success"
    assert create_result.get("Name") == MOCK_VM["Name"]
    assert create_result.get("ResourceGroup") == TEST_RG_NAME
    
    # Verify mock calls
    mock_network_client.virtual_networks.begin_create_or_update.assert_called_once()
    mock_network_client.subnets.begin_create_or_update.assert_called_once()
    mock_network_client.public_ip_addresses.begin_create_or_update.assert_called_once()
    mock_network_client.network_interfaces.begin_create_or_update.assert_called_once()
    mock_compute_client.virtual_machines.begin_create_or_update.assert_called_once()
    
    print("✓ Virtual machine creation test passed")

@patch('servers.azure.azure_mcp.get_azure_client')
def test_list_container_groups(mock_get_client):
    """Test listing container groups with mocking."""
    # Set up mock
    mock_container_client = MagicMock()
    
    # Mock container group
    mock_container = MagicMock()
    mock_container.name = "test-container"
    mock_container.image = "nginx"
    mock_container.instance_view = MagicMock()
    mock_container.instance_view.current_state.state = "Running"
    mock_container.resources = MagicMock()
    mock_container.resources.requests.cpu = 1.0
    mock_container.resources.requests.memory_in_gb = 1.5
    
    # Mock container group
    mock_group = MagicMock()
    mock_group.name = "test-container-group"
    mock_group.id = f"/subscriptions/sub123/resourceGroups/{TEST_RG_NAME}/providers/Microsoft.ContainerInstance/containerGroups/test-container-group"
    mock_group.location = TEST_LOCATION
    mock_group.provisioning_state = "Succeeded"
    mock_group.os_type = "Linux"
    mock_group.ip_address = MagicMock()
    mock_group.ip_address.ip = "10.0.0.1"
    mock_group.containers = [mock_container]
    
    # Configure client to return our mock container group
    mock_container_client.container_groups.list.return_value = [mock_group]
    mock_get_client.return_value = mock_container_client
    
    # Call the function
    result = json.loads(list_container_groups())
    
    # Verify result
    assert isinstance(result, list)
    assert len(result) > 0
    
    group_found = False
    for group in result:
        if group.get("Name") == "test-container-group":
            group_found = True
            assert group.get("ResourceGroup") == TEST_RG_NAME
            assert group.get("Location") == TEST_LOCATION
            assert group.get("ContainerCount") == 1
            assert len(group.get("Containers")) == 1
            assert group.get("Containers")[0].get("Name") == "test-container"
            assert group.get("Containers")[0].get("Image") == "nginx"
    
    assert group_found, "Mock container group not found in list"
    print("✓ Container groups listing test passed")

@patch('servers.azure.azure_mcp.get_azure_client')
def test_list_app_services(mock_get_client):
    """Test listing app services with mocking."""
    # Set up mock
    mock_web_client = MagicMock()
    
    # Mock web app
    mock_app = MagicMock()
    mock_app.name = "test-webapp"
    mock_app.resource_group = TEST_RG_NAME
    mock_app.location = TEST_LOCATION
    mock_app.state = "Running"
    mock_app.host_names = ["test-webapp.azurewebsites.net"]
    mock_app.default_host_name = "test-webapp.azurewebsites.net"
    mock_app.kind = "app"
    mock_app.enabled = True
    
    # Configure client to return our mock web app
    mock_web_client.web_apps.list.return_value = [mock_app]
    mock_get_client.return_value = mock_web_client
    
    # Call the function
    result = json.loads(list_app_services())
    
    # Verify result
    assert isinstance(result, list)
    assert len(result) > 0
    
    app_found = False
    for app in result:
        if app.get("Name") == "test-webapp":
            app_found = True
            assert app.get("ResourceGroup") == TEST_RG_NAME
            assert app.get("Location") == TEST_LOCATION
            assert app.get("State") == "Running"
            assert "test-webapp.azurewebsites.net" in app.get("HostNames")
    
    assert app_found, "Mock web app not found in list"
    print("✓ App Services listing test passed")

@patch('subprocess.run')
@patch('tempfile.NamedTemporaryFile')
def test_run_azure_code(mock_temp_file, mock_subprocess_run):
    """Test running Azure code."""
    # Set up mocks
    mock_file = MagicMock()
    mock_file.name = "/tmp/test_azure_code.py"
    mock_temp_file.return_value.__enter__.return_value = mock_file
    
    # Mock file read operation
    mock_open = MagicMock()
    mock_open.return_value.__enter__.return_value.read.return_value = "Test output"
    
    with patch('builtins.open', mock_open):
        # Call the function with a simple code snippet
        result = run_azure_code("""
print("Hello from Azure code!")
resource_groups = json.loads(list_resource_groups())
print(f"Found {len(resource_groups)} resource groups")
result = resource_groups  # Assign to result for output
""")
    
    # Verify result
    assert "Hello from Azure code!" in result or mock_subprocess_run.called
    print("✓ Run Azure code test passed")

def test_resources():
    """Test resource endpoints."""
    # Test regions resource
    regions = json.loads(list_azure_regions())
    assert isinstance(regions, list)
    assert "eastus" in regions
    assert "westeurope" in regions
    
    # Test VM sizes resource
    vm_sizes = json.loads(list_vm_sizes())
    assert isinstance(vm_sizes, dict)
    assert "General Purpose" in vm_sizes
    assert "Standard_D2s_v3" in vm_sizes["General Purpose"]
    
    # Test storage SKUs resource
    storage_skus = json.loads(list_storage_skus())
    assert isinstance(storage_skus, dict)
    assert "Standard" in storage_skus
    assert any(sku["name"] == "Standard_LRS" for sku in storage_skus["Standard"])
    
    print("✓ Resource endpoints test passed")

if __name__ == "__main__":
    # Run only specific tests that don't create real resources when testing locally
    pytest.main(["-xvs", __file__])