from mcp.server.fastmcp import FastMCP
import azure.mgmt.resource
import azure.mgmt.compute
import azure.mgmt.storage
import azure.mgmt.network
import azure.mgmt.containerinstance
import azure.mgmt.web
import azure.storage.blob
from azure.identity import DefaultAzureCredential
import json
import subprocess
import tempfile
import os
from typing import Optional, Dict, Any, List

# Initialize the MCP server
mcp = FastMCP("azure-server")

# Helper function to get Azure clients
def get_azure_client(client_type, subscription_id=None):
    """Get an Azure client for a specific service.
    
    Args:
        client_type: The Azure client class to instantiate
        subscription_id: Optional subscription ID to use (default: use environment variable)
    
    Returns:
        An initialized Azure client
    """
    credential = DefaultAzureCredential()
    subscription = subscription_id or os.environ.get("AZURE_SUBSCRIPTION_ID")
    if not subscription:
        raise ValueError("No subscription ID provided and AZURE_SUBSCRIPTION_ID not set in environment")
    
    return client_type(credential, subscription)

# Core Resource Group Tools
@mcp.tool()
def list_resource_groups(subscription_id: Optional[str] = None) -> str:
    """List all resource groups in the Azure subscription.
    
    Args:
        subscription_id: Optional Azure subscription ID
    
    Returns:
        JSON string with resource group information
    """
    client = get_azure_client(azure.mgmt.resource.ResourceManagementClient, subscription_id)
    
    resource_groups = []
    for rg in client.resource_groups.list():
        resource_groups.append({
            'Name': rg.name,
            'Location': rg.location,
            'ProvisioningState': rg.properties.provisioning_state,
            'Tags': rg.tags or {}
        })
    
    return json.dumps(resource_groups, indent=2)

@mcp.tool()
def create_resource_group(
    name: str,
    location: str,
    tags: Optional[Dict[str, str]] = None,
    subscription_id: Optional[str] = None
) -> str:
    """Create a new resource group.
    
    Args:
        name: Name of the resource group
        location: Azure region for the resource group
        tags: Optional tags to apply to the resource group
        subscription_id: Optional Azure subscription ID
    
    Returns:
        JSON string with resource group information
    """
    client = get_azure_client(azure.mgmt.resource.ResourceManagementClient, subscription_id)
    
    try:
        params = {
            'location': location
        }
        
        if tags:
            params['tags'] = tags
            
        result = client.resource_groups.create_or_update(name, params)
        
        return json.dumps({
            'Status': 'Success',
            'Name': result.name,
            'Location': result.location,
            'ProvisioningState': result.properties.provisioning_state,
            'Tags': result.tags or {}
        }, indent=2)
    except Exception as e:
        return json.dumps({
            'Status': 'Error',
            'Message': str(e)
        }, indent=2)

# Core Storage Account Tools
@mcp.tool()
def list_storage_accounts(
    resource_group: Optional[str] = None,
    subscription_id: Optional[str] = None
) -> str:
    """List storage accounts in the subscription or resource group.
    
    Args:
        resource_group: Optional resource group name to filter by
        subscription_id: Optional Azure subscription ID
    
    Returns:
        JSON string with storage account information
    """
    client = get_azure_client(azure.mgmt.storage.StorageManagementClient, subscription_id)
    
    accounts = []
    
    if resource_group:
        storage_accounts = client.storage_accounts.list_by_resource_group(resource_group)
    else:
        storage_accounts = client.storage_accounts.list()
    
    for account in storage_accounts:
        accounts.append({
            'Name': account.name,
            'ResourceGroup': account.id.split('/')[4],  # Extract resource group from ID
            'Location': account.location,
            'Kind': account.kind,
            'Sku': account.sku.name,
            'Https': account.enable_https_traffic_only,
            'CreationTime': account.creation_time.isoformat() if account.creation_time else None
        })
    
    return json.dumps(accounts, indent=2)

@mcp.tool()
def list_storage_containers(
    account_name: str,
    resource_group: str,
    subscription_id: Optional[str] = None
) -> str:
    """List blob containers in a storage account.
    
    Args:
        account_name: Name of the storage account
        resource_group: Resource group of the storage account
        subscription_id: Optional Azure subscription ID
    
    Returns:
        JSON string with container information
    """
    client = get_azure_client(azure.mgmt.storage.StorageManagementClient, subscription_id)
    
    try:
        # Get storage account keys
        keys = client.storage_accounts.list_keys(resource_group, account_name)
        key = keys.keys[0].value
        
        # Connect to blob service
        connection_string = f"DefaultEndpointsProtocol=https;AccountName={account_name};AccountKey={key};EndpointSuffix=core.windows.net"
        blob_service = azure.storage.blob.BlobServiceClient.from_connection_string(connection_string)
        
        containers = []
        for container in blob_service.list_containers():
            containers.append({
                'Name': container.name,
                'LastModified': container.last_modified.isoformat() if container.last_modified else None,
                'PublicAccess': container.public_access if hasattr(container, 'public_access') else None,
                'LeaseState': container.lease.state if hasattr(container, 'lease') else None
            })
        
        return json.dumps(containers, indent=2)
    except Exception as e:
        return json.dumps({
            'Status': 'Error',
            'Message': str(e)
        }, indent=2)

@mcp.tool()
def create_storage_account(
    name: str,
    resource_group: str,
    location: str,
    sku: str = "Standard_LRS",
    kind: str = "StorageV2",
    subscription_id: Optional[str] = None
) -> str:
    """Create a new storage account.
    
    Args:
        name: Name of the storage account (must be globally unique)
        resource_group: Resource group for the storage account
        location: Azure region for the storage account
        sku: Storage account SKU (default: Standard_LRS)
        kind: Storage account kind (default: StorageV2)
        subscription_id: Optional Azure subscription ID
    
    Returns:
        JSON string with storage account information
    """
    client = get_azure_client(azure.mgmt.storage.StorageManagementClient, subscription_id)
    
    try:
        poller = client.storage_accounts.begin_create(
            resource_group,
            name,
            {
                'location': location,
                'kind': kind,
                'sku': {'name': sku}
            }
        )
        
        account = poller.result()
        
        return json.dumps({
            'Status': 'Success',
            'Name': account.name,
            'Location': account.location,
            'ResourceGroup': resource_group,
            'Kind': account.kind,
            'Sku': account.sku.name
        }, indent=2)
    except Exception as e:
        return json.dumps({
            'Status': 'Error',
            'Message': str(e)
        }, indent=2)

# Core Virtual Machine Tools
@mcp.tool()
def list_virtual_machines(
    resource_group: Optional[str] = None,
    subscription_id: Optional[str] = None
) -> str:
    """List virtual machines in the subscription or resource group.
    
    Args:
        resource_group: Optional resource group name to filter by
        subscription_id: Optional Azure subscription ID
    
    Returns:
        JSON string with VM information
    """
    compute_client = get_azure_client(azure.mgmt.compute.ComputeManagementClient, subscription_id)
    
    vms = []
    
    if resource_group:
        vm_list = compute_client.virtual_machines.list(resource_group)
    else:
        vm_list = compute_client.virtual_machines.list_all()
    
    for vm in vm_list:
        vm_info = {
            'Name': vm.name,
            'ResourceGroup': vm.id.split('/')[4],
            'Location': vm.location,
            'VMSize': vm.hardware_profile.vm_size,
            'OsType': vm.storage_profile.os_disk.os_type,
            'ProvisioningState': vm.provisioning_state,
            'PowerState': None  # Will be filled later
        }
        
        # Get power state
        instance_view = compute_client.virtual_machines.instance_view(vm_info['ResourceGroup'], vm.name)
        for status in instance_view.statuses:
            if status.code.startswith('PowerState/'):
                vm_info['PowerState'] = status.code.split('/')[1]
                break
                
        vms.append(vm_info)
    
    return json.dumps(vms, indent=2)

@mcp.tool()
def start_virtual_machine(
    name: str,
    resource_group: str,
    subscription_id: Optional[str] = None
) -> str:
    """Start a virtual machine.
    
    Args:
        name: Name of the VM
        resource_group: Resource group of the VM
        subscription_id: Optional Azure subscription ID
    
    Returns:
        JSON string with result information
    """
    client = get_azure_client(azure.mgmt.compute.ComputeManagementClient, subscription_id)
    
    try:
        poller = client.virtual_machines.begin_start(resource_group, name)
        result = poller.result()
        
        return json.dumps({
            'Status': 'Success',
            'Message': f"VM {name} started successfully"
        }, indent=2)
    except Exception as e:
        return json.dumps({
            'Status': 'Error',
            'Message': str(e)
        }, indent=2)

@mcp.tool()
def stop_virtual_machine(
    name: str,
    resource_group: str,
    deallocate: bool = True,
    subscription_id: Optional[str] = None
) -> str:
    """Stop a virtual machine.
    
    Args:
        name: Name of the VM
        resource_group: Resource group of the VM
        deallocate: Whether to deallocate the VM (default: True)
        subscription_id: Optional Azure subscription ID
    
    Returns:
        JSON string with result information
    """
    client = get_azure_client(azure.mgmt.compute.ComputeManagementClient, subscription_id)
    
    try:
        if deallocate:
            poller = client.virtual_machines.begin_deallocate(resource_group, name)
            action = "deallocated"
        else:
            poller = client.virtual_machines.begin_power_off(resource_group, name)
            action = "powered off"
            
        result = poller.result()
        
        return json.dumps({
            'Status': 'Success',
            'Message': f"VM {name} {action} successfully"
        }, indent=2)
    except Exception as e:
        return json.dumps({
            'Status': 'Error',
            'Message': str(e)
        }, indent=2)

@mcp.tool()
def create_virtual_machine(
    name: str,
    resource_group: str,
    location: str,
    vm_size: str = "Standard_DS1_v2",
    admin_username: str = "azureadmin",
    image_reference: Dict[str, str] = None,
    generate_ssh_keys: bool = True,
    subscription_id: Optional[str] = None
) -> str:
    """Create a new virtual machine.
    
    Args:
        name: Name for the VM
        resource_group: Resource group for the VM
        location: Azure region for the VM
        vm_size: VM size (default: Standard_DS1_v2)
        admin_username: Admin username for the VM
        image_reference: Dict containing publisher, offer, sku, version (default: Ubuntu Server)
        generate_ssh_keys: Whether to generate SSH keys (default: True)
        subscription_id: Optional Azure subscription ID
    
    Returns:
        JSON string with VM creation information
    """
    compute_client = get_azure_client(azure.mgmt.compute.ComputeManagementClient, subscription_id)
    network_client = get_azure_client(azure.mgmt.network.NetworkManagementClient, subscription_id)
    
    # Set default image if not provided
    if not image_reference:
        image_reference = {
            'publisher': 'Canonical',
            'offer': 'UbuntuServer',
            'sku': '18.04-LTS',
            'version': 'latest'
        }
    
    try:
        # Create supporting network resources
        # 1. Create a VNet
        vnet_name = f"{name}-vnet"
        poller = network_client.virtual_networks.begin_create_or_update(
            resource_group,
            vnet_name,
            {
                'location': location,
                'address_space': {'address_prefixes': ['10.0.0.0/16']}
            }
        )
        vnet = poller.result()
        
        # 2. Create a subnet
        subnet_name = f"{name}-subnet"
        poller = network_client.subnets.begin_create_or_update(
            resource_group, 
            vnet_name,
            subnet_name,
            {'address_prefix': '10.0.0.0/24'}
        )
        subnet = poller.result()
        
        # 3. Create a public IP
        public_ip_name = f"{name}-ip"
        poller = network_client.public_ip_addresses.begin_create_or_update(
            resource_group,
            public_ip_name,
            {
                'location': location,
                'sku': {'name': 'Basic'},
                'public_ip_allocation_method': 'Dynamic'
            }
        )
        public_ip = poller.result()
        
        # 4. Create a NIC
        nic_name = f"{name}-nic"
        poller = network_client.network_interfaces.begin_create_or_update(
            resource_group,
            nic_name,
            {
                'location': location,
                'ip_configurations': [{
                    'name': f"{name}-ipconfig",
                    'subnet': {'id': subnet.id},
                    'public_ip_address': {'id': public_ip.id}
                }]
            }
        )
        nic = poller.result()
        
        # Create VM parameters
        vm_parameters = {
            'location': location,
            'hardware_profile': {'vm_size': vm_size},
            'storage_profile': {
                'image_reference': image_reference,
                'os_disk': {
                    'create_option': 'FromImage',
                    'managed_disk': {'storage_account_type': 'Standard_LRS'}
                }
            },
            'os_profile': {
                'computer_name': name,
                'admin_username': admin_username,
            },
            'network_profile': {
                'network_interfaces': [{'id': nic.id}]
            }
        }
        
        # Add SSH configuration for Linux VMs
        if image_reference['publisher'] in ['Canonical', 'RedHat', 'SUSE', 'OpenLogic']:
            if generate_ssh_keys:
                vm_parameters['os_profile']['linux_configuration'] = {
                    'disable_password_authentication': True,
                    'ssh': {
                        'public_keys': [{
                            'path': f"/home/{admin_username}/.ssh/authorized_keys",
                            'key_data': 'ssh-rsa AAAAB3NzaC1yc2EAAAADA...'  # This would be a real key in production
                        }]
                    }
                }
            else:
                # For demo purposes - in real use, would prompt for password
                vm_parameters['os_profile']['admin_password'] = 'P@ssw0rd1234'  
                vm_parameters['os_profile']['linux_configuration'] = {
                    'disable_password_authentication': False
                }
        # For Windows VMs
        else:
            vm_parameters['os_profile']['admin_password'] = 'P@ssw0rd1234'  # For demo - not production use
            
        # Create the VM
        poller = compute_client.virtual_machines.begin_create_or_update(
            resource_group,
            name,
            vm_parameters
        )
        vm = poller.result()
        
        return json.dumps({
            'Status': 'Success',
            'Name': vm.name,
            'ResourceGroup': resource_group,
            'Location': vm.location,
            'VMSize': vm.hardware_profile.vm_size,
            'ProvisioningState': vm.provisioning_state,
            'OsType': vm.storage_profile.os_disk.os_type,
            'PublicIPName': public_ip_name,
            'NetworkInterface': nic_name
        }, indent=2)
    except Exception as e:
        return json.dumps({
            'Status': 'Error',
            'Message': str(e)
        }, indent=2)

# Container Instances
@mcp.tool()
def list_container_groups(
    resource_group: Optional[str] = None,
    subscription_id: Optional[str] = None
) -> str:
    """List Azure Container Instances container groups.
    
    Args:
        resource_group: Optional resource group name to filter by
        subscription_id: Optional Azure subscription ID
    
    Returns:
        JSON string with container group information
    """
    client = get_azure_client(azure.mgmt.containerinstance.ContainerInstanceManagementClient, subscription_id)
    
    container_groups = []
    
    try:
        if resource_group:
            container_groups_list = client.container_groups.list_by_resource_group(resource_group)
        else:
            container_groups_list = client.container_groups.list()
            
        for group in container_groups_list:
            containers = []
            for container in group.containers:
                containers.append({
                    'Name': container.name,
                    'Image': container.image,
                    'State': container.instance_view.current_state.state if container.instance_view else 'Unknown',
                    'CPUs': container.resources.requests.cpu,
                    'MemoryInGB': container.resources.requests.memory_in_gb
                })
                
            container_groups.append({
                'Name': group.name,
                'ResourceGroup': group.id.split('/')[4],
                'Location': group.location,
                'ProvisioningState': group.provisioning_state,
                'OSType': group.os_type,
                'IPAddress': group.ip_address.ip if group.ip_address else None,
                'ContainerCount': len(group.containers),
                'Containers': containers
            })
        
        return json.dumps(container_groups, indent=2)
    except Exception as e:
        return json.dumps({
            'Status': 'Error',
            'Message': str(e)
        }, indent=2)

# App Services
@mcp.tool()
def list_app_services(
    resource_group: Optional[str] = None,
    subscription_id: Optional[str] = None
) -> str:
    """List Azure App Services web apps.
    
    Args:
        resource_group: Optional resource group name to filter by
        subscription_id: Optional Azure subscription ID
    
    Returns:
        JSON string with web app information
    """
    client = get_azure_client(azure.mgmt.web.WebSiteManagementClient, subscription_id)
    
    apps = []
    
    try:
        if resource_group:
            web_apps = client.web_apps.list_by_resource_group(resource_group)
        else:
            web_apps = client.web_apps.list()
            
        for app in web_apps:
            apps.append({
                'Name': app.name,
                'ResourceGroup': app.resource_group,
                'Location': app.location,
                'State': app.state,
                'HostNames': app.host_names,
                'DefaultHostName': app.default_host_name,
                'Kind': app.kind,
                'IsEnabled': app.enabled
            })
        
        return json.dumps(apps, indent=2)
    except Exception as e:
        return json.dumps({
            'Status': 'Error',
            'Message': str(e)
        }, indent=2)

# Run Azure Code
@mcp.tool()
def run_azure_code(code: str, imports: Optional[str] = "from azure.identity import DefaultAzureCredential") -> str:
    """Run Python code that interacts with Azure services.
    
    Args:
        code: Python code to run
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

# Resource providing a list of Azure regions
@mcp.resource("azure://regions")
def list_azure_regions() -> str:
    """Return a list of Azure regions as a resource."""
    # Common Azure regions
    regions = [
        "eastus", "eastus2", "westus", "westus2", "westus3",
        "centralus", "northcentralus", "southcentralus",
        "westeurope", "northeurope",
        "uksouth", "ukwest",
        "eastasia", "southeastasia",
        "japaneast", "japanwest",
        "australiaeast", "australiasoutheast",
        "brazilsouth",
        "southafricanorth",
        "centralindia", "southindia"
    ]
    return json.dumps(regions, indent=2)

# Resource providing a list of common VM sizes
@mcp.resource("azure://compute/vm-sizes")
def list_vm_sizes() -> str:
    """Return a list of common Azure VM sizes."""
    vm_sizes = {
        "General Purpose": [
            "Standard_B1s", "Standard_B2s", "Standard_B4ms",
            "Standard_D2s_v3", "Standard_D4s_v3", "Standard_D8s_v3",
            "Standard_D2a_v4", "Standard_D4a_v4", "Standard_D8a_v4"
        ],
        "Compute Optimized": [
            "Standard_F2s_v2", "Standard_F4s_v2", "Standard_F8s_v2",
            "Standard_F16s_v2", "Standard_F32s_v2"
        ],
        "Memory Optimized": [
            "Standard_E2s_v3", "Standard_E4s_v3", "Standard_E8s_v3",
            "Standard_E16s_v3", "Standard_E32s_v3"
        ],
        "Storage Optimized": [
            "Standard_L4s", "Standard_L8s", "Standard_L16s",
            "Standard_L32s"
        ],
        "GPU": [
            "Standard_NC6", "Standard_NC12", "Standard_NC24",
            "Standard_NC6s_v3", "Standard_NC12s_v3", "Standard_NC24s_v3"
        ]
    }
    return json.dumps(vm_sizes, indent=2)

# Resource providing storage account SKUs
@mcp.resource("azure://storage/skus")
def list_storage_skus() -> str:
    """Return a list of Azure Storage Account SKUs."""
    skus = {
        "Standard": [
            {"name": "Standard_LRS", "description": "Locally redundant storage"},
            {"name": "Standard_ZRS", "description": "Zone-redundant storage"},
            {"name": "Standard_GRS", "description": "Geo-redundant storage"},
            {"name": "Standard_RAGRS", "description": "Read-access geo-redundant storage"},
            {"name": "Standard_GZRS", "description": "Geo-zone-redundant storage"},
            {"name": "Standard_RAGZRS", "description": "Read-access geo-zone-redundant storage"}
        ],
        "Premium": [
            {"name": "Premium_LRS", "description": "Premium locally redundant storage"},
            {"name": "Premium_ZRS", "description": "Premium zone-redundant storage"},
            {"name": "Premium_Page_Blobs", "description": "Premium storage for page blobs"},
            {"name": "Premium_Block_Blobs", "description": "Premium storage for block blobs"},
            {"name": "Premium_Files", "description": "Premium storage for file shares"}
        ]
    }
    return json.dumps(skus, indent=2)

if __name__ == "__main__":
    mcp.run()