Kubernetes MCP Server
=====================

Overview
--------
The Kubernetes MCP Server is a cutting-edge implementation of the Model Context Protocol (MCP) tailored specifically for Kubernetes environments. This server enables modern large language models (LLMs) such as Claude to seamlessly interact with and manage your Kubernetes clusters. Built in Python using the official Kubernetes client libraries, the server supports a comprehensive suite of tools for cluster administration—from namespace management to detailed resource monitoring.

Features
--------
•  Full Kubernetes API Integration  
   – Utilize the official Kubernetes client library to load configuration (via kubeconfig or in-cluster)  
   – Support for managing core, apps, batch, storage, networking, RBAC, and custom resource definitions  

•  Extensive Resource Management Tools  
   – List and manage namespaces, pods, deployments, nodes, services, StatefulSets, DaemonSets, CronJobs, and more  
   – Create, describe, update, and delete resources using YAML manifests or dynamic parameters  
   – Rollback deployments and update container images or replica counts with minimal effort  

•  Port Forwarding and Remote Command Execution  
   – Easily setup and tear down port-forwarding from local ports to Kubernetes resources  
   – Execute raw kubectl and helm commands directly through the MCP server interface  

•  Advanced Configurations and Metrics  
   – Retrieve cluster and node metrics (CPU, memory, and pods utilization) using aggregated data  
   – List and manage PersistentVolumes, PersistentVolumeClaims, ConfigMaps, Secrets, Roles and RoleBindings  
   – Integrate with Flux and ArgoCD for GitOps and continuous deployment management  

•  Dashboard Access  
   – Automatically create a kubectl proxy and optionally open the Kubernetes Dashboard in your browser  

Tools
-----
The server exposes an extensive set of tools via MCP endpoints, providing modular Kubernetes administration functions. Some of the key tools include:

•  choose_namespace(namespace)  
   – Set the default namespace for subsequent commands. Validates that the namespace exists.

•  list_namespaces()  
   – List all namespaces in the cluster along with metadata such as status and creation time.

•  list_pods(namespace, label_selector)  
   – List pods in a specified namespace. Supports filtering by labels.

•  list_services(namespace)  
   – Retrieve service details including type, cluster IP, external IPs, and port information.

•  list_deployments(namespace)  
   – Provide details for deployments including replica count and status.

•  list_nodes()  
   – Output detailed node information including roles, version, and readiness state.

•  create_pod(manifest, namespace) and delete_pod(name, namespace)  
   – Create or delete pods using YAML manifests with built–in error handling.

•  describe_pod(name, namespace)  
   – Show detailed pod information—including containers, resources, statuses, and events.

•  get_pod_logs(name, namespace, container, tail_lines, previous)  
   – Fetch pod logs from a running or previous container instance.

•  exec_kubectl(command, namespace)  
   – Execute raw kubectl commands, automatically appending the namespace if needed.

•  Helm Chart Management  
   – Tools for installing, upgrading, uninstalling, and listing Helm releases with support for override values.

•  Port Forwarding Tools  
   – port_forward(resource, local_port, remote_port, namespace, resource_type) and stop_port_forward(local_port)  
   – Manage port forwarding processes for accessing in-cluster applications.

•  Resource Listing and Creation for Advanced objects  
   – List and create PersistentVolumes, PVCs, ConfigMaps, Secrets, as well as view Role and RoleBinding configurations.

•  Metrics and Resource Utilization  
   – get_cluster_metrics() collects aggregated CPU, memory, and pod usage across the cluster  
   – list_network_policies(), list_custom_resource_definitions(), and more for holistic cluster oversight

•  GitOps and Dashboard Integration  
   – get_argo_cd_applications(namespace) and get_flux_resources(namespace) to manage GitOps deployments  
   – open_web_dashboard(browser) to create a proxy and open the Kubernetes Dashboard

Configuration
-------------
1. Kubernetes Configuration:  
   The server attempts to load the Kubernetes configuration first via a local kubeconfig file. If that fails, it falls back to in-cluster configuration. Make sure your environment has proper Kubernetes credentials and access rights to interact with the cluster.

2. Environment Requirements:  
   – Python 3.7+  
   – Kubernetes Python Client  
   – PyYAML  
   – Helm (for helm commands)  
   – kubectl (installed and accessible in the environment’s PATH)  

Installation
------------
1. Clone the repository containing the Kubernetes MCP Server script.

2. Install Dependencies:
   •  pip install kubernetes pyyaml

3. Ensure that both kubectl and helm are installed and configured correctly in your environment.

4. Verify that you have access to your Kubernetes cluster via kubeconfig or in-cluster credentials.

Usage
-----
Run the MCP server from the command line:

   $ ./kubernetes-mcp-server.py

The MCP server will start using stdio as the transport layer. Once running, LLMs (such as Claude) can invoke any of the available MCP tools by sending requests that specify the method parameters as defined in the tool descriptions.

Each tool is decorated to handle asynchronous operation and proper error reporting. Detailed logging is provided to aid in debugging and operational transparency.

Contributing
------------
Contributions are welcome. Feel free to fork the repository, make improvements to the toolset or add new features, and submit pull requests. Ensure that new functionality is well documented and tested.

License
-------
This project is released under an open source license. Please refer to the LICENSE file for details.

Contact
-------
For questions or support, please reach out via the repository’s issue tracker or contact the maintainers directly.

Enjoy leveraging Kubernetes MCP Server to simplify and empower your Kubernetes management workflows!