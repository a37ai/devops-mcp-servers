# DevOps MCP Servers

This repository is a collection of Model Context Protocol (MCP) server implementations specifically designed for DevOps tools and platforms. These servers enable Large Language Models (LLMs) to interact directly with popular DevOps systems, providing a standardized way to automate and control infrastructure, deployment pipelines, monitoring, and other DevOps operations.

Each MCP server implementation provides a comprehensive set of tools that map to the respective DevOps platform's API, allowing LLMs to perform complex operations through simple function calls.

## 🛠️ Available Servers

The following MCP servers are included in this repository (in alphabetical order):

* **[Ansible Tower](https://github.com/a37ai/devops-mcp-servers/tree/main/servers/ansible_tower)** - Comprehensive API integration with Ansible Tower/AWX for managing inventories, hosts, job templates, projects, and more
* **[Artifactory](https://github.com/a37ai/devops-mcp-servers/tree/main/servers/artifactory)** - JFrog Artifactory integration for artifact management, repository configuration, and binary management
* **[AWS](https://github.com/a37ai/devops-mcp-servers/tree/main/servers/aws)** - AWS service integration for S3, EC2, Lambda, and custom AWS code execution
* **[Azure](https://github.com/a37ai/devops-mcp-servers/tree/main/servers/azure)** - Azure resource management including resource groups, storage accounts, virtual machines, and more
* **[Bitbucket Cloud](https://github.com/a37ai/devops-mcp-servers/tree/main/servers/bitbucket_cloud)** - Bitbucket Cloud API integration for repositories, pull requests, pipelines, and code management
* **[CircleCI](https://github.com/a37ai/devops-mcp-servers/tree/main/servers/circleci)** - CircleCI API integration for pipelines, workflows, jobs, and CI/CD automation
* **[Consul](https://github.com/a37ai/devops-mcp-servers/tree/main/servers/consul)** - Consul service discovery, registration, and configuration management
* **[Datadog](https://github.com/a37ai/devops-mcp-servers/tree/main/servers/datadog)** - Datadog monitoring platform integration for metrics, events, logs, dashboards, and monitors
* **[Docker](https://github.com/a37ai/devops-mcp-servers/tree/main/servers/docker)** - Docker container management, image operations, network and volume controls
* **[Elasticsearch](https://github.com/a37ai/devops-mcp-servers/tree/main/servers/elasticsearch)** - ELK stack integration with comprehensive Elasticsearch API coverage
* **[GCP](https://github.com/a37ai/devops-mcp-servers/tree/main/servers/gcp)** - Google Cloud Platform integration for Cloud Storage, Compute Engine, BigQuery, and more
* **[GitHub](https://github.com/a37ai/devops-mcp-servers/tree/main/servers/github)** - GitHub API integration for repository management, file operations, and code workflows
* **[GitLab](https://github.com/a37ai/devops-mcp-servers/tree/main/servers/gitlab)** - GitLab API integration for repository management, CI/CD pipelines, and issue tracking
* **[Grafana](https://github.com/a37ai/devops-mcp-servers/tree/main/servers/grafana)** - Grafana monitoring platform integration for dashboards, data sources, and alerts
* **[Jenkins](https://github.com/a37ai/devops-mcp-servers/tree/main/servers/jenkins)** - Jenkins CI/CD server integration for jobs, builds, plugins, and automation
* **[Kubernetes](https://github.com/a37ai/devops-mcp-servers/tree/main/servers/kubernetes)** - Kubernetes cluster management, resource operations, and advanced configurations
* **[New Relic](https://github.com/a37ai/devops-mcp-servers/tree/main/servers/newrelic)** - New Relic monitoring platform integration for APM, infrastructure, synthetics, and alerts
* **[Nexus](https://github.com/a37ai/devops-mcp-servers/tree/main/servers/nexus)** - Sonatype Nexus repository manager integration for artifact management and security
* **[Prometheus](https://github.com/a37ai/devops-mcp-servers/tree/main/servers/prometheus)** - Prometheus monitoring system integration for metrics, queries, alerts, and analysis
* **[Puppet](https://github.com/a37ai/devops-mcp-servers/tree/main/servers/puppet)** - Puppet infrastructure automation integration for configuration management

## 🚀 Getting Started

Each server implementation includes its own README with detailed documentation on installation, configuration, and available tools. Navigate to the specific server directory for more information.

Most servers require API credentials or tokens to interact with their respective services. Refer to the individual server documentation for setup instructions.

## 🔧 Common Requirements

- Python 3.7+
- FastMCP framework 
- Service-specific API tokens or credentials
- Required Python packages (specified in each server's documentation)

## 📚 Resources

- [Model Context Protocol (MCP) Documentation](https://github.com/anthropics/anthropic-cookbook/tree/main/mcp)
- [FastMCP Framework Documentation](https://github.com/anthropics/anthropic-cookbook/tree/main/mcp/python)

## 📄 License

This project is licensed under the MIT License - see the LICENSE file for details.