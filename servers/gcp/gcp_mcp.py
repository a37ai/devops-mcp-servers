from mcp.server.fastmcp import FastMCP
from google.cloud import bigquery
from google.cloud import storage
from google.cloud import functions_v1
from google.cloud.container_v1 import ClusterManagerClient
import google.auth
import json
import subprocess
import tempfile
import os
from typing import Optional, Dict, Any, List
from googleapiclient import discovery

# Initialize the MCP server
mcp = FastMCP("gcp-server")

# Helper function to get GCP clients
def get_gcp_client(service: str, project_id: Optional[str] = None):
    """Get a GCP client for the specified service"""
    credentials, default_project = google.auth.default()
    project = project_id or default_project
    
    if service == 'storage':
        return storage.Client(project=project, credentials=credentials)
    elif service == 'compute':
        # Google Compute Engine uses discovery API, not a direct client
        return discovery.build('compute', 'v1', credentials=credentials)
    elif service == 'bigquery':
        return bigquery.Client(project=project, credentials=credentials)
    elif service == 'functions':
        return functions_v1.CloudFunctionsServiceClient(credentials=credentials)
    elif service == 'container':
        return ClusterManagerClient(credentials=credentials)
    else:
        raise ValueError(f"Unsupported service: {service}")

# Core GCS (Google Cloud Storage) Tools
@mcp.tool()
def list_gcs_buckets(project_id: Optional[str] = None) -> str:
    """List all GCS buckets in the Google Cloud project.
    
    Args:
        project_id: Optional Google Cloud project ID
    
    Returns:
        JSON string with bucket information
    """
    try:
        storage_client = get_gcp_client('storage', project_id)
        
        buckets = []
        for bucket in storage_client.list_buckets():
            buckets.append({
                'Name': bucket.name,
                'CreationDate': bucket.time_created.isoformat() if bucket.time_created else None,
                'Location': bucket.location,
                'StorageClass': bucket.storage_class
            })
        
        return json.dumps(buckets, indent=2)
    except Exception as e:
        return json.dumps({
            'Status': 'Error',
            'Message': str(e)
        }, indent=2)

@mcp.tool()
def list_gcs_objects(bucket_name: str, prefix: Optional[str] = "", max_items: int = 100) -> str:
    """List objects in a GCS bucket.
    
    Args:
        bucket_name: Name of the GCS bucket
        prefix: Optional prefix to filter objects
        max_items: Maximum number of items to return
    
    Returns:
        JSON string with object information
    """
    try:
        storage_client = get_gcp_client('storage')
        
        bucket = storage_client.bucket(bucket_name)
        blobs = bucket.list_blobs(prefix=prefix, max_results=max_items)
        
        objects = []
        for blob in blobs:
            objects.append({
                'Name': blob.name,
                'Size': blob.size,
                'ContentType': blob.content_type,
                'Updated': blob.updated.isoformat() if blob.updated else None,
                'StorageClass': blob.storage_class
            })
        
        return json.dumps({
            'Objects': objects,
            'Count': len(objects)
        }, indent=2)
    except Exception as e:
        return json.dumps({
            'Status': 'Error',
            'Message': str(e)
        }, indent=2)

# Core GCE (Google Compute Engine) Tools
@mcp.tool()
def list_gce_instances(project_id: Optional[str] = None, zone: Optional[str] = None) -> str:
    """List Compute Engine instances with their details.
    
    Args:
        project_id: Optional Google Cloud project ID
        zone: Optional compute zone (e.g., 'us-central1-a')
    
    Returns:
        JSON string with GCE instance information
    """
    try:
        credentials, default_project = google.auth.default()
        project = project_id or default_project
        
        # Using the lower-level REST API via the discovery service
        service = discovery.build('compute', 'v1', credentials=credentials)
        
        instances = []
        
        # If zone is specified, only list instances in that zone
        if zone:
            request = service.instances().list(project=project, zone=zone)
            response = request.execute()
            
            if 'items' in response:
                for instance in response['items']:
                    instances.append({
                        'Name': instance['name'],
                        'Zone': zone,
                        'MachineType': instance['machineType'].split('/')[-1],
                        'Status': instance['status'],
                        'InternalIP': get_instance_ip(instance, 'INTERNAL'),
                        'ExternalIP': get_instance_ip(instance, 'EXTERNAL'),
                        'CreationTime': instance['creationTimestamp']
                    })
        else:
            # List all zones first, then get instances from each zone
            zones_request = service.zones().list(project=project)
            zones_response = zones_request.execute()
            
            for zone_item in zones_response.get('items', []):
                zone_name = zone_item['name']
                request = service.instances().list(project=project, zone=zone_name)
                response = request.execute()
                
                if 'items' in response:
                    for instance in response['items']:
                        instances.append({
                            'Name': instance['name'],
                            'Zone': zone_name,
                            'MachineType': instance['machineType'].split('/')[-1],
                            'Status': instance['status'],
                            'InternalIP': get_instance_ip(instance, 'INTERNAL'),
                            'ExternalIP': get_instance_ip(instance, 'EXTERNAL'),
                            'CreationTime': instance['creationTimestamp']
                        })
        
        return json.dumps(instances, indent=2)
    except Exception as e:
        return json.dumps({
            'Status': 'Error',
            'Message': str(e)
        }, indent=2)

def get_instance_ip(instance, network_type):
    """Helper function to extract IP addresses from instance network interfaces"""
    if 'networkInterfaces' not in instance:
        return None
    
    for interface in instance['networkInterfaces']:
        if network_type == 'INTERNAL':
            return interface.get('networkIP')
        elif network_type == 'EXTERNAL':
            if 'accessConfigs' in interface:
                for config in interface['accessConfigs']:
                    if 'natIP' in config:
                        return config['natIP']
    return None

@mcp.tool()
def list_gce_images(project_id: Optional[str] = None, family: Optional[str] = None) -> str:
    """List available Compute Engine images.
    
    Args:
        project_id: Optional Google Cloud project ID (default: common GCP image projects)
        family: Optional image family (e.g., 'debian-10', 'ubuntu-2004-lts')
    
    Returns:
        JSON string with image information
    """
    try:
        credentials, default_project = google.auth.default()
        
        # Using the lower-level REST API via the discovery service
        service = discovery.build('compute', 'v1', credentials=credentials)
        
        # List of common image projects
        image_projects = ['debian-cloud', 'ubuntu-os-cloud', 'centos-cloud', 'cos-cloud']
        
        # If project_id is specified, use only that project
        if project_id:
            image_projects = [project_id]
        
        images = []
        
        for project in image_projects:
            request = service.images().list(project=project)
            while request is not None:
                response = request.execute()
                
                for image in response.get('items', []):
                    # Filter by family if specified
                    if family and image.get('family') != family:
                        continue
                        
                    images.append({
                        'Name': image['name'],
                        'Project': project,
                        'Family': image.get('family', 'N/A'),
                        'Status': image['status'],
                        'CreationTime': image['creationTimestamp'],
                        'DiskSizeGb': image.get('diskSizeGb', 'N/A'),
                        'Description': image.get('description', ''),
                        'SelfLink': image['selfLink']
                    })
                
                request = service.images().list_next(previous_request=request, previous_response=response)
        
        # Sort by creation time (newest first)
        images.sort(key=lambda x: x['CreationTime'], reverse=True)
        
        return json.dumps(images, indent=2)
    except Exception as e:
        return json.dumps({
            'Status': 'Error',
            'Message': str(e)
        }, indent=2)

@mcp.tool()
def start_gce_instance(instance_name: str, zone: str, project_id: Optional[str] = None) -> str:
    """Start a Compute Engine instance.
    
    Args:
        instance_name: Name of the GCE instance
        zone: Compute zone where the instance is located
        project_id: Optional Google Cloud project ID
    
    Returns:
        JSON string with result information
    """
    try:
        credentials, default_project = google.auth.default()
        project = project_id or default_project
        
        # Using the lower-level REST API via the discovery service
        service = discovery.build('compute', 'v1', credentials=credentials)
        
        operation = service.instances().start(project=project, zone=zone, instance=instance_name).execute()
        
        return json.dumps({
            'Status': 'Success',
            'InstanceName': instance_name,
            'Zone': zone,
            'OperationId': operation['id'],
            'OperationStatus': operation['status']
        }, indent=2)
    except Exception as e:
        return json.dumps({
            'Status': 'Error',
            'Message': str(e)
        }, indent=2)

@mcp.tool()
def stop_gce_instance(instance_name: str, zone: str, project_id: Optional[str] = None) -> str:
    """Stop a Compute Engine instance.
    
    Args:
        instance_name: Name of the GCE instance
        zone: Compute zone where the instance is located
        project_id: Optional Google Cloud project ID
    
    Returns:
        JSON string with result information
    """
    try:
        credentials, default_project = google.auth.default()
        project = project_id or default_project
        
        # Using the lower-level REST API via the discovery service
        service = discovery.build('compute', 'v1', credentials=credentials)
        
        operation = service.instances().stop(project=project, zone=zone, instance=instance_name).execute()
        
        return json.dumps({
            'Status': 'Success',
            'InstanceName': instance_name,
            'Zone': zone,
            'OperationId': operation['id'],
            'OperationStatus': operation['status']
        }, indent=2)
    except Exception as e:
        return json.dumps({
            'Status': 'Error',
            'Message': str(e)
        }, indent=2)

@mcp.tool()
def create_gce_instance(
    instance_name: str,
    machine_type: str = "e2-micro",
    image_project: str = "debian-cloud",
    image_family: str = "debian-11",
    zone: str = "us-central1-a",
    project_id: Optional[str] = None,
    network: str = "default",
    subnet: Optional[str] = None,
    external_ip: bool = True
) -> str:
    """Create a new Compute Engine instance.
    
    Args:
        instance_name: Name for the new instance
        machine_type: Machine type (default: e2-micro)
        image_project: Project containing the image
        image_family: Image family to use
        zone: Compute zone for the instance
        project_id: Optional Google Cloud project ID
        network: Network to use (default: default)
        subnet: Optional subnet to use
        external_ip: Whether to assign an external IP (default: True)
    
    Returns:
        JSON string with instance information
    """
    try:
        credentials, default_project = google.auth.default()
        project = project_id or default_project
        
        # Using the lower-level REST API via the discovery service
        service = discovery.build('compute', 'v1', credentials=credentials)
        
        # Get the latest image from the family
        image_response = service.images().getFromFamily(
            project=image_project,
            family=image_family
        ).execute()
        source_image = image_response['selfLink']
        
        # Configure the machine
        machine_type_url = f"projects/{project}/zones/{zone}/machineTypes/{machine_type}"
        
        # Configure the disk
        disk_config = {
            'boot': True,
            'autoDelete': True,
            'initializeParams': {
                'sourceImage': source_image
            }
        }
        
        # Configure the network interface
        network_interface = {
            'network': f"projects/{project}/global/networks/{network}"
        }
        
        if subnet:
            network_interface['subnetwork'] = f"projects/{project}/regions/{zone[:-2]}/subnetworks/{subnet}"
        
        if external_ip:
            network_interface['accessConfigs'] = [{'type': 'ONE_TO_ONE_NAT', 'name': 'External NAT'}]
        
        # Create the instance
        instance_body = {
            'name': instance_name,
            'machineType': machine_type_url,
            'disks': [disk_config],
            'networkInterfaces': [network_interface],
            'metadata': {
                'items': [
                    {
                        'key': 'startup-script',
                        'value': '#!/bin/bash\necho "Instance created by GCP MCP Server" > /tmp/startup.log'
                    }
                ]
            }
        }
        
        operation = service.instances().insert(
            project=project,
            zone=zone,
            body=instance_body
        ).execute()
        
        return json.dumps({
            'Status': 'Success',
            'InstanceName': instance_name,
            'Zone': zone,
            'MachineType': machine_type,
            'OperationId': operation['id'],
            'OperationStatus': operation['status']
        }, indent=2)
    except Exception as e:
        return json.dumps({
            'Status': 'Error',
            'Message': str(e)
        }, indent=2)

# Firewall Rules
@mcp.tool()
def list_firewall_rules(project_id: Optional[str] = None) -> str:
    """List firewall rules in the project.
    
    Args:
        project_id: Optional Google Cloud project ID
    
    Returns:
        JSON string with firewall rule information
    """
    try:
        credentials, default_project = google.auth.default()
        project = project_id or default_project
        
        # Using the lower-level REST API via the discovery service
        service = discovery.build('compute', 'v1', credentials=credentials)
        
        request = service.firewalls().list(project=project)
        response = request.execute()
        
        firewall_rules = []
        for rule in response.get('items', []):
            allowed = []
            for item in rule.get('allowed', []):
                protocol = item.get('IPProtocol', '')
                ports = item.get('ports', [])
                allowed.append({
                    'protocol': protocol,
                    'ports': ports
                })
            
            denied = []
            for item in rule.get('denied', []):
                protocol = item.get('IPProtocol', '')
                ports = item.get('ports', [])
                denied.append({
                    'protocol': protocol,
                    'ports': ports
                })
            
            firewall_rules.append({
                'Name': rule['name'],
                'Network': rule['network'].split('/')[-1],
                'Direction': rule.get('direction', 'INGRESS'),
                'Priority': rule.get('priority', 1000),
                'Allowed': allowed,
                'Denied': denied,
                'SourceRanges': rule.get('sourceRanges', []),
                'DestinationRanges': rule.get('destinationRanges', []),
                'Description': rule.get('description', '')
            })
        
        return json.dumps(firewall_rules, indent=2)
    except Exception as e:
        return json.dumps({
            'Status': 'Error',
            'Message': str(e)
        }, indent=2)

# Cloud Functions
@mcp.tool()
def list_cloud_functions(project_id: Optional[str] = None, region: str = "us-central1") -> str:
    """List all Cloud Functions in the project.
    
    Args:
        project_id: Optional Google Cloud project ID
        region: Region to list functions from (default: us-central1)
    
    Returns:
        JSON string with Cloud Functions information
    """
    try:
        credentials, default_project = google.auth.default()
        project = project_id or default_project
        
        client = functions_v1.CloudFunctionsServiceClient(credentials=credentials)
        
        parent = f'projects/{project}/locations/{region}'
        functions = client.list_functions(request={"parent": parent})
        
        function_list = []
        for function in functions:
            function_dict = {
                'Name': function.name.split('/')[-1],
                'Runtime': function.runtime,
                'EntryPoint': function.entry_point,
                'Status': function.status.name,
                'UpdateTime': function.update_time.isoformat() if function.update_time else None,
                'VersionId': function.version_id,
                'MemoryMb': function.available_memory_mb,
                'Timeout': function.timeout.seconds,
                'HttpsTrigger': bool(function.https_trigger.url) if hasattr(function, 'https_trigger') else False,
                'EventTrigger': bool(function.event_trigger) if hasattr(function, 'event_trigger') else False
            }
            
            if hasattr(function, 'https_trigger') and function.https_trigger.url:
                function_dict['Url'] = function.https_trigger.url
            
            function_list.append(function_dict)
        
        return json.dumps(function_list, indent=2)
    except Exception as e:
        return json.dumps({
            'Status': 'Error',
            'Message': str(e)
        }, indent=2)

# BigQuery Tools
@mcp.tool()
def list_bigquery_datasets(project_id: Optional[str] = None) -> str:
    """List all BigQuery datasets in the project.
    
    Args:
        project_id: Optional Google Cloud project ID
    
    Returns:
        JSON string with dataset information
    """
    try:
        credentials, default_project = google.auth.default()
        project = project_id or default_project
        
        client = bigquery.Client(project=project, credentials=credentials)
        
        datasets = list(client.list_datasets())
        
        dataset_list = []
        for dataset in datasets:
            dataset_list.append({
                'DatasetId': dataset.dataset_id,
                'FullyQualifiedId': f"{project}.{dataset.dataset_id}",
                'CreationTime': dataset.created.isoformat() if dataset.created else None,
                'LastModified': dataset.modified.isoformat() if dataset.modified else None,
                'Location': dataset.location,
                'Description': dataset.description
            })
        
        return json.dumps(dataset_list, indent=2)
    except Exception as e:
        return json.dumps({
            'Status': 'Error',
            'Message': str(e)
        }, indent=2)

@mcp.tool()
def list_bigquery_tables(dataset_id: str, project_id: Optional[str] = None) -> str:
    """List all tables in a BigQuery dataset.
    
    Args:
        dataset_id: BigQuery dataset ID
        project_id: Optional Google Cloud project ID
    
    Returns:
        JSON string with table information
    """
    try:
        credentials, default_project = google.auth.default()
        project = project_id or default_project
        
        client = bigquery.Client(project=project, credentials=credentials)
        
        tables = list(client.list_tables(f"{project}.{dataset_id}"))
        
        table_list = []
        for table in tables:
            table_list.append({
                'TableId': table.table_id,
                'FullyQualifiedId': f"{project}.{dataset_id}.{table.table_id}",
                'Type': table.table_type,
                'CreationTime': table.created.isoformat() if table.created else None,
                'LastModified': table.modified.isoformat() if table.modified else None,
                'NumRows': 'Unknown (requires table.get())'
            })
        
        return json.dumps(table_list, indent=2)
    except Exception as e:
        return json.dumps({
            'Status': 'Error',
            'Message': str(e)
        }, indent=2)

# GKE (Google Kubernetes Engine) Tools
@mcp.tool()
def list_gke_clusters(project_id: Optional[str] = None, zone: Optional[str] = None) -> str:
    """List all GKE clusters in the project.
    
    Args:
        project_id: Optional Google Cloud project ID
        zone: Optional zone or region
    
    Returns:
        JSON string with cluster information
    """
    try:
        credentials, default_project = google.auth.default()
        project = project_id or default_project
        
        client = ClusterManagerClient(credentials=credentials)
        
        if zone:
            parent = f"projects/{project}/locations/{zone}"
        else:
            parent = f"projects/{project}/locations/-"
                
        clusters = client.list_clusters(parent=parent)
        
        cluster_list = []
        for cluster in clusters.clusters:
            cluster_list.append({
                'Name': cluster.name,
                'Location': cluster.location,
                'Status': cluster.status.name,
                'NodeCount': sum(pool.initial_node_count for pool in cluster.node_pools),
                'NodePools': [pool.name for pool in cluster.node_pools],
                'MasterVersion': cluster.master_version,
                'Network': cluster.network,
                'Subnetwork': cluster.subnetwork,
                'Endpoint': cluster.endpoint,
                'CreateTime': cluster.create_time.isoformat() if cluster.create_time else None
            })
        
        return json.dumps(cluster_list, indent=2)
    except Exception as e:
        return json.dumps({
            'Status': 'Error',
            'Message': str(e)
        }, indent=2)

# Run GCP Code (this is the main flexible tool)
@mcp.tool()
def run_gcp_code(code: str, imports: Optional[str] = "from google.cloud import storage") -> str:
    """Run Python code that interacts with GCP services.
    
    Args:
        code: Python code to run (using Google Cloud libraries)
        imports: Optional import statements to include
    
    Returns:
        Output from the executed code
    """
    try:
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

# Resource providing a list of GCP regions
@mcp.resource("gcp://regions")
def list_gcp_regions() -> str:
    """Return a list of GCP regions as a resource."""
    regions = [
        "us-central1", "us-east1", "us-east4", "us-west1", "us-west2", "us-west3", "us-west4",
        "northamerica-northeast1", "northamerica-northeast2", "southamerica-east1", "southamerica-west1",
        "europe-central2", "europe-north1", "europe-west1", "europe-west2", "europe-west3", 
        "europe-west4", "europe-west6", "europe-west8", "europe-west9", "europe-southwest1",
        "asia-east1", "asia-east2", "asia-northeast1", "asia-northeast2", "asia-northeast3",
        "asia-south1", "asia-south2", "asia-southeast1", "asia-southeast2",
        "australia-southeast1", "australia-southeast2",
        "africa-south1"
    ]
    return json.dumps(regions, indent=2)

# Resource providing a list of GCE machine types
@mcp.resource("gcp://compute/machine-types")
def list_machine_types() -> str:
    """Return a list of common GCE machine types."""
    machine_types = {
        "General Purpose": ["e2-micro", "e2-small", "e2-medium", "n1-standard-1", "n1-standard-2", "n2-standard-2", "n2-standard-4"],
        "Memory Optimized": ["n1-highmem-2", "n1-highmem-4", "n2-highmem-2", "n2-highmem-4", "m1-megamem-96"],
        "Compute Optimized": ["n1-highcpu-2", "n1-highcpu-4", "n2-highcpu-2", "n2-highcpu-4", "c2-standard-4"],
        "Accelerator Optimized": ["a2-highgpu-1g", "g2-standard-4"],
        "Shared Core": ["f1-micro", "g1-small"]
    }
    return json.dumps(machine_types, indent=2)

if __name__ == "__main__":
    mcp.run()