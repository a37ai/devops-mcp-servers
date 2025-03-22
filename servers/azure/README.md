Azure MCP Server

Overview
────────
The Azure MCP Server is a robust MCP (Multi-Cloud Plugin) implementation built on top of the FastMCP framework to integrate with Microsoft Azure. Leveraging multiple Azure management libraries, this server provides an extensive suite of tools for managing your Azure resources—ranging from resource groups and storage accounts to virtual machines, container instances, and App Services.

Features
────────
• Resource Group Management
  – List existing resource groups in your subscription.
  – Create new resource groups with custom location and optional tags.

• Storage Account Management
  – List storage accounts across your subscription or within a given resource group.
  – List blob containers inside a specified storage account.
  – Create new storage accounts with configurable SKU and kind.

• Virtual Machine Operations
  – List virtual machines (VMs) with detailed information including VM size, OS type, provisioning, and power state.
  – Start and stop (or deallocate) virtual machines.
  – Create new virtual machines, complete with network configuration (VNet, Subnet, Public IP, NIC) and optional SSH key generation for Linux VMs.

• Container Instances and App Services
  – List container groups for Azure Container Instances along with container details.
  – List Azure App Services (web apps) and review their configuration and state.

• Azure Code Execution
  – Dynamically run Python code snippets that interact with Azure services.
  – Capture and return output from code execution, enabling flexible, ad-hoc operations.

• Azure Resource Listings
  – Provide resources for common Azure regions.
  – Offer a list of popular virtual machine sizes and storage account SKUs.

Tools Overview
──────────────
Each tool is implemented as a decorated function within the MCP server, allowing direct invocation via the FastMCP interface. Below is a summary of the available tools:

1. Resource Group Tools
   • list_resource_groups(subscription_id: Optional[str])
     – Returns a JSON-formatted list of all resource groups.

   • create_resource_group(name: str, location: str, tags: Optional[Dict[str, str]], subscription_id: Optional[str])
     – Creates a new resource group with specified name, region, and tags.

2. Storage Account Tools
   • list_storage_accounts(resource_group: Optional[str], subscription_id: Optional[str])
     – Lists storage accounts either globally or filtered by resource group.

   • list_storage_containers(account_name: str, resource_group: str, subscription_id: Optional[str])
     – Enumerates blob containers within a specified storage account.

   • create_storage_account(name: str, resource_group: str, location: str, sku: str, kind: str, subscription_id: Optional[str])
     – Initiates creation of a new storage account.

3. Virtual Machine Tools
   • list_virtual_machines(resource_group: Optional[str], subscription_id: Optional[str])
     – Details all VMs with metadata such as VM size, OS type, and power status.

   • start_virtual_machine(name: str, resource_group: str, subscription_id: Optional[str])
     – Starts the specified virtual machine.

   • stop_virtual_machine(name: str, resource_group: str, deallocate: bool, subscription_id: Optional[str])
     – Stops (or deallocates) the specified virtual machine.

   • create_virtual_machine(name: str, resource_group: str, location: str, vm_size: str, admin_username: str, image_reference: Optional[Dict[str, str]], generate_ssh_keys: bool, subscription_id: Optional[str])
     – Provisions a new virtual machine along with necessary network components.

4. Container Instance Tool
   • list_container_groups(resource_group: Optional[str], subscription_id: Optional[str])
     – Lists container groups and their properties for Azure Container Instances.

5. App Services Tool
   • list_app_services(resource_group: Optional[str], subscription_id: Optional[str])
     – Lists web apps deployed as Azure App Services.

6. Azure Code Runner
   • run_azure_code(code: str, imports: Optional[str])
     – Executes arbitrary Python code that interacts with Azure services, capturing and returning its output.

7. Resource Providers
   • list_azure_regions – Returns a predefined list of common Azure regions.
   • list_vm_sizes – Provides a categorized list of common Azure VM sizes.
   • list_storage_skus – Lists details of available storage account SKUs.

Getting Started
───────────────
Pre-requisites:
  • Python 3.x
  • Azure Subscription with AZURE_SUBSCRIPTION_ID set in your environment, or pass subscription_id explicitly
  • Necessary Azure SDK libraries:
      - azure-identity
      - azure-mgmt-resource
      - azure-mgmt-compute
      - azure-mgmt-storage
      - azure-mgmt-network
      - azure-mgmt-containerinstance
      - azure-mgmt-web
      - azure-storage-blob

Installation:
  1. Install the required packages via pip:
       pip install azure-identity azure-mgmt-resource azure-mgmt-compute azure-mgmt-storage azure-mgmt-network azure-mgmt-containerinstance azure-mgmt-web azure-storage-blob

  2. Set the AZURE_SUBSCRIPTION_ID environment variable if not providing subscription IDs explicitly:
       export AZURE_SUBSCRIPTION_ID="your_subscription_id_here" (Linux/Mac)
       set AZURE_SUBSCRIPTION_ID="your_subscription_id_here" (Windows)

Configuration:
  • Authentication is handled via DefaultAzureCredential.
  • For production deployments, ensure proper management of credentials and secure storage of sensitive information.
  • Adjust the SSH key snippet in the create_virtual_machine tool to include your actual public key if generating SSH configurations.

Running the Server
──────────────────
The server is executed by running the script directly. At the end of the file the FastMCP instance is launched:
  
    python <script_name>.py

This will initialize the MCP server with the identifier "azure-server" and enable access to all the defined tools and resources.

Usage
─────
Once running, each tool can be invoked through the MCP framework. For instance, to list resource groups:
  • Call list_resource_groups (optionally with a provided subscription_id) to receive a JSON response detailing your resource groups.

Similarly, other tools accept their designated parameters, perform the corresponding Azure operation, and return detailed JSON responses (or error messages if encountered).

Support & Contribution
────────────────────────
For any issues, feature requests, or contributions, please follow your organization’s contribution guidelines or contact the maintainers. Contributions are welcome to enhance functionality, add new tools, or fix issues.

Conclusion
──────────
The Azure MCP Server provides a powerful, extensible interface to manage various Azure services programmatically. Its modular design allows you to integrate additional tools and services as needed, making it ideal for operations, automation, or as the backbone of cloud management interfaces.

For additional documentation and advanced use cases, refer to the Azure SDK documentation and the FastMCP framework guidelines.