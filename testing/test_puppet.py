#!/usr/bin/env python3

import requests
import json
import urllib3
import sys
import getpass
import time
import random
import string
import traceback # Import traceback for detailed error logging
import os # For accessing environment variables
from typing import Dict, List, Optional, Union, Any
from datetime import datetime, timedelta

# Disable SSL warnings (for self-signed certificates)
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

class PuppetAPI:
    # ==========================================================================
    #   PuppetAPI Class (Keep the previously corrected version)
    #   ... includes methods like get_auth_token, check_status, get_nodes,
    #   ... create_node_group, list_roles, create_role, etc. ...
    #   ... with improved error handling returning None/False on failure ...
    # ==========================================================================
    def __init__(self, base_url: str, auth_token: Optional[str] = None):
        """
        Initialize the PuppetAPI client with base URL and authentication token.

        Args:
            base_url: Base URL or hostname of the Puppet Enterprise server
            auth_token: Authentication token for API access (optional)
        """
        self.base_url = base_url # Store the hostname/IP
        self.auth_token = auth_token
        self.headers = {"Content-Type": "application/json"}
        if auth_token:
            self.headers["X-Authentication"] = auth_token

    def _make_request(self, method: str, endpoint: str, port: int, **kwargs) -> requests.Response:
        """Internal helper to construct URL and make requests."""
        url = f"https://{self.base_url}:{port}/{endpoint.lstrip('/')}"
        # Ensure headers are included, especially the auth token if set
        if not kwargs.get('headers'):
             kwargs['headers'] = self.headers
        # Ensure verify=False is set unless overridden
        if 'verify' not in kwargs:
            kwargs['verify'] = False
        # Ensure a default timeout unless overridden
        if 'timeout' not in kwargs:
            kwargs['timeout'] = 15 # Default timeout

        return requests.request(method, url, **kwargs)


    def get_auth_token(self, username: str, password: str, lifetime: str = "4h") -> Optional[str]:
        """
        Generate a new authentication token using username and password.

        Args:
            username: RBAC username
            password: RBAC password
            lifetime: Token lifetime (default: 4h)

        Returns:
            Authentication token string or None on failure
        """
        endpoint = "rbac-api/v1/auth/token"
        port = 4433
        data = {
            "login": username,
            "password": password,
            "lifetime": lifetime
        }

        try:
            # Short timeout specifically for auth
            response = self._make_request("post", endpoint, port, json=data, timeout=10)
            response.raise_for_status() # Raise HTTPError for bad responses (4xx or 5xx)
            token_data = response.json()
            self.auth_token = token_data.get("token")
            if self.auth_token:
                self.headers["X-Authentication"] = self.auth_token
                print(f"Successfully generated auth token (valid for {lifetime})")
                return self.auth_token
            else:
                print("Auth token generation succeeded but token was missing in response.")
                return None
        except requests.exceptions.RequestException as e:
            print(f"An error occurred while getting auth token: {e}")
            if hasattr(e, 'response') and e.response is not None:
                print(f"Status code: {e.response.status_code}")
                try: print(f"Response: {e.response.text}")
                except Exception: pass
            return None
        except json.JSONDecodeError as e:
            print(f"Failed to decode JSON response while getting auth token: {e}")
            if 'response' in locals(): print(f"Response Text: {response.text}")
            return None


    def revoke_token(self, token: Optional[str] = None) -> bool:
        """
        Revoke an authentication token.

        Args:
            token: Token to revoke (defaults to current token)

        Returns:
            True if successful, False otherwise
        """
        target_token = token or self.auth_token
        if not target_token:
            print("No token provided or stored to revoke")
            return False

        endpoint = "rbac-api/v1/auth/token/revoke"
        port = 4433
        data = {"token": target_token}

        try:
            # Use current headers (which should include auth if revoking own token)
            response = self._make_request("post", endpoint, port, json=data, timeout=10)
            # Treat 200 OK or 204 No Content as success
            if response.status_code in [200, 204]:
                print("Successfully revoked token")
                if target_token == self.auth_token:
                    self.auth_token = None
                    if "X-Authentication" in self.headers:
                        del self.headers["X-Authentication"]
                return True
            else:
                # Let raise_for_status handle standard errors
                response.raise_for_status()
                # If raise_for_status doesn't throw for some reason, report failure
                print(f"Failed to revoke token. Status code: {response.status_code}")
                if response.text: print(response.text)
                return False
        except requests.exceptions.RequestException as e:
            print(f"An error occurred while revoking token: {e}")
            if hasattr(e, 'response') and e.response is not None:
                print(f"Status code: {e.response.status_code}")
                try: print(f"Response: {e.response.text}")
                except Exception: pass
            return False


    #######################
    # Status API Endpoints
    #######################

    def check_status(self) -> Optional[Dict]:
        """
        Check the status of Puppet Enterprise services.

        Returns:
            Dictionary containing status information or None on failure.
        """
        endpoint = "status/v1/services"
        port = 4433
        try:
            response = self._make_request("get", endpoint, port, timeout=10)
            response.raise_for_status() # Check for HTTP errors
            print("Status code: 200")
            print("Connection successful!")
            return response.json()
        except requests.exceptions.RequestException as e:
            print(f"Failed to get status: {e}")
            if hasattr(e, 'response') and e.response is not None:
                print(f"Status code: {e.response.status_code}")
                try: print(f"Response: {e.response.text}")
                except Exception: pass
            return None # Indicate failure
        except json.JSONDecodeError as e:
            print(f"Failed to decode JSON response while checking status: {e}")
            if 'response' in locals(): print(f"Response Text: {response.text}")
            return None


    #######################
    # Certificate API Endpoints
    #######################

    def get_certificate_statuses(self) -> Optional[List]:
        """
        Get all certificate statuses from the Puppet CA.

        Returns:
            List of certificate status objects or None on failure.
        """
        endpoint = "puppet-ca/v1/certificate_statuses/any_key"
        port = 8140
        try:
            response = self._make_request("get", endpoint, port, timeout=15) # Slightly longer timeout for CA
            response.raise_for_status()
            print("Successfully fetched certificate statuses.")
            return response.json()
        except requests.exceptions.RequestException as e:
            print(f"Failed to fetch certificate statuses: {e}")
            if hasattr(e, 'response') and e.response is not None:
                print(f"Status code: {e.response.status_code}")
                try: print(f"Response: {e.response.text}")
                except Exception: pass
            return None # Indicate failure
        except json.JSONDecodeError as e:
            print(f"Failed to decode JSON response while getting cert statuses: {e}")
            if 'response' in locals(): print(f"Response Text: {response.text}")
            return None


    def get_certificate(self, certname: str) -> Optional[str]:
        """
        Get a specific certificate by name.

        Args:
            certname: Name of the certificate to retrieve

        Returns:
            Certificate content as string or None on failure.
        """
        endpoint = f"puppet-ca/v1/certificate/{certname}"
        port = 8140
        try:
            response = self._make_request("get", endpoint, port, timeout=10)
            response.raise_for_status()
            print(f"Successfully fetched certificate: {certname}")
            return response.text
        except requests.exceptions.RequestException as e:
            print(f"Failed to fetch certificate {certname}: {e}")
            if hasattr(e, 'response') and e.response is not None:
                print(f"Status code: {e.response.status_code}")
                try: print(f"Response: {e.response.text}")
                except Exception: pass
            return None # Indicate failure


    def sign_certificate_request(self, certname: str) -> bool:
        """
        Sign a pending certificate request.

        Args:
            certname: Name of the certificate request to sign

        Returns:
            True if successful, False otherwise
        """
        endpoint = f"puppet-ca/v1/certificate_status/{certname}"
        port = 8140
        data = {"desired_state": "signed"}

        try:
            response = self._make_request("put", endpoint, port, json=data, timeout=10)
            # Treat 200 OK or 204 No Content as success
            if response.status_code in [200, 204]:
                print(f"Successfully signed certificate request: {certname}")
                return True
            else:
                response.raise_for_status() # Raise exception for other codes
                return False # Should not be reached if raise_for_status works
        except requests.exceptions.RequestException as e:
            print(f"Failed to sign certificate request {certname}: {e}")
            if hasattr(e, 'response') and e.response is not None:
                print(f"Status code: {e.response.status_code}")
                try: print(f"Response: {e.response.text}")
                except Exception: pass
            return False


    def revoke_certificate(self, certname: str) -> bool:
        """
        Revoke a certificate.

        Args:
            certname: Name of the certificate to revoke

        Returns:
            True if successful, False otherwise
        """
        endpoint = f"puppet-ca/v1/certificate_status/{certname}"
        port = 8140
        data = {"desired_state": "revoked"}

        try:
            response = self._make_request("put", endpoint, port, json=data, timeout=10)
            if response.status_code in [200, 204]:
                print(f"Successfully revoked certificate: {certname}")
                return True
            else:
                response.raise_for_status()
                return False
        except requests.exceptions.RequestException as e:
            print(f"Failed to revoke certificate {certname}: {e}")
            if hasattr(e, 'response') and e.response is not None:
                print(f"Status code: {e.response.status_code}")
                try: print(f"Response: {e.response.text}")
                except Exception: pass
            return False


    #######################
    # Node Group API Endpoints
    #######################

    def get_node_groups(self) -> Optional[List]:
        """
        Get all node classification groups.

        Returns:
            List of node group objects or None on failure.
        """
        endpoint = "classifier-api/v1/groups"
        port = 4433
        try:
            response = self._make_request("get", endpoint, port, timeout=15) # Classifier can be slightly slower
            response.raise_for_status()
            print("Successfully fetched node groups.")
            return response.json()
        except requests.exceptions.RequestException as e:
            print(f"Failed to fetch node groups: {e}")
            if hasattr(e, 'response') and e.response is not None:
                print(f"Status code: {e.response.status_code}")
                try: print(f"Response: {e.response.text}")
                except Exception: pass
            return None # Indicate failure
        except json.JSONDecodeError as e:
            print(f"Failed to decode JSON response while getting node groups: {e}")
            if 'response' in locals(): print(f"Response Text: {response.text}")
            return None


    def get_node_group(self, group_id: str) -> Optional[Dict]:
        """
        Get a specific node group by ID.

        Args:
            group_id: ID of the group to retrieve

        Returns:
            Node group object or None on failure.
        """
        endpoint = f"classifier-api/v1/groups/{group_id}"
        port = 4433
        try:
            response = self._make_request("get", endpoint, port, timeout=10)
            response.raise_for_status()
            print(f"Successfully fetched node group: {group_id}")
            return response.json()
        except requests.exceptions.RequestException as e:
            print(f"Failed to fetch node group {group_id}: {e}")
            if hasattr(e, 'response') and e.response is not None:
                print(f"Status code: {e.response.status_code}")
                try: print(f"Response: {e.response.text}")
                except Exception: pass
            return None # Indicate failure
        except json.JSONDecodeError as e:
            print(f"Failed to decode JSON response while getting node group {group_id}: {e}")
            if 'response' in locals(): print(f"Response Text: {response.text}")
            return None


    def create_node_group(self, name: str, description: str, parent_id: str,
                          environment: str = "production", rule: Optional[List] = None,
                          classes: Optional[Dict] = None) -> Optional[Dict]:
        """
        Create a new node classification group.

        Args:
            name: Name of the group
            description: Description of the group
            parent_id: ID of the parent group
            environment: Puppet environment to use (default: production)
            rule: Rule for node matching
            classes: Classes to apply to nodes in this group

        Returns:
            Response data (usually includes group ID) or None on failure.
        """
        endpoint = "classifier-api/v1/groups"
        port = 4433

        if rule is None:
            rule = ["and", ["~", "name", ".*"]] # Default rule matches all nodes
        if classes is None:
            classes = {}

        data = {
            "name": name,
            "description": description,
            "parent": parent_id,
            "environment": environment,
            "classes": classes,
            "rule": rule
        }

        try:
            # Using 15s timeout as classification can involve DB lookups
            response = self._make_request("post", endpoint, port, json=data, timeout=15)

            # Status code 303 See Other is also a success for create group
            if response.status_code in [200, 201, 303]:
                print(f"Successfully initiated creation for node group: {name}")
                group_info = None
                group_id_from_header = None

                if 'Location' in response.headers:
                     location_url = response.headers['Location']
                     group_id_from_header = location_url.split('/')[-1]

                try:
                    # Try to parse JSON even for 303, might contain data sometimes
                    if response.text: # Avoid parsing empty body
                       group_info = response.json()
                except json.JSONDecodeError:
                    if response.status_code == 303 and group_id_from_header:
                         print(f"Group {name} created (Status 303), ID from Location header: {group_id_from_header}")
                         return {"id": group_id_from_header, "name": name} # Synthesized success response
                    else:
                         print(f"Group {name} created (Status {response.status_code}) but response was not valid JSON.")
                         # Return a generic success if no ID available but status is OK
                         return {"success": True, "name": name}

                # If JSON parsed:
                if group_info is not None:
                    if "id" not in group_info and group_id_from_header:
                         print(f"Warning: Group {name} created but response JSON missing 'id'. Using ID from header: {group_id_from_header}")
                         group_info["id"] = group_id_from_header # Inject ID if missing
                         return group_info
                    elif "id" in group_info:
                         return group_info
                    else:
                         # Should not happen if status was 200/201/303 and JSON parsed, but handle defensively
                         print(f"Warning: Group {name} created (Status {response.status_code}) but response missing 'id' and Location header.")
                         return {"success": True, "name": name} # Generic success
                else:
                     # If JSON parsing failed and it wasn't a 303 with header ID
                     print(f"Warning: Group {name} created (Status {response.status_code}) but response had no body or ID.")
                     return {"success": True, "name": name} # Generic success

            else:
                response.raise_for_status() # Let RequestException handle other errors
                return None # Should not be reached

        except requests.exceptions.RequestException as e:
            print(f"Failed to create node group {name}: {e}")
            if hasattr(e, 'response') and e.response is not None:
                print(f"Status code: {e.response.status_code}")
                try: print(f"Response: {e.response.text}")
                except Exception: pass
            return None # Indicate failure


    def update_node_group(self, group_id: str, data: Dict) -> Optional[Dict]:
        """
        Update an existing node group. Use POST with group ID.

        Args:
            group_id: ID of the group to update
            data: Updated group data (must include all required fields like name, parent, rule etc.)

        Returns:
            Response data or None on failure
        """
        endpoint = f"classifier-api/v1/groups/{group_id}"
        port = 4433
        try:
            response = self._make_request("post", endpoint, port, json=data, timeout=15)
            response.raise_for_status() # Check for 200 OK explicitly
            print(f"Successfully updated node group: {group_id}")
            try:
                return response.json()
            except json.JSONDecodeError:
                print("Updated successfully but no JSON response")
                return {"success": True}
        except requests.exceptions.RequestException as e:
            print(f"Failed to update node group {group_id}: {e}")
            if hasattr(e, 'response') and e.response is not None:
                print(f"Status code: {e.response.status_code}")
                try: print(f"Response: {e.response.text}")
                except Exception: pass
            return None # Indicate failure


    def delete_node_group(self, group_id: str) -> bool:
        """
        Delete a node group.

        Args:
            group_id: ID of the group to delete

        Returns:
            True if successful, False otherwise
        """
        endpoint = f"classifier-api/v1/groups/{group_id}"
        port = 4433
        try:
            response = self._make_request("delete", endpoint, port, timeout=10)
            if response.status_code in [200, 204]: # 204 No Content is typical success
                print(f"Successfully deleted node group: {group_id}")
                return True
            else:
                response.raise_for_status()
                return False
        except requests.exceptions.RequestException as e:
            print(f"Failed to delete node group {group_id}: {e}")
            if hasattr(e, 'response') and e.response is not None:
                print(f"Status code: {e.response.status_code}")
                try: print(f"Response: {e.response.text}")
                except Exception: pass
            return False


    def pin_nodes_to_group(self, group_id: str, node_names: List[str]) -> bool:
        """
        Pin specific nodes to a node group.

        Args:
            group_id: ID of the group to pin nodes to
            node_names: List of node names to pin

        Returns:
            True if successful, False otherwise.
        """
        endpoint = f"classifier-api/v1/groups/{group_id}/pin"
        port = 4433
        data = {"nodes": node_names}

        try:
            response = self._make_request("post", endpoint, port, json=data, timeout=15)
            # 204 No Content is expected success for pin operations
            if response.status_code in [200, 201, 204]:
                print(f"Successfully pinned {len(node_names)} node(s) to group {group_id}")
                return True
            else:
                response.raise_for_status()
                return False
        except requests.exceptions.RequestException as e:
            print(f"Failed to pin nodes to group {group_id}: {e}")
            if hasattr(e, 'response') and e.response is not None:
                print(f"Status code: {e.response.status_code}")
                try: print(f"Response: {e.response.text}")
                except Exception: pass
            return False # Indicate failure


    def unpin_nodes_from_group(self, group_id: str, node_names: List[str]) -> bool:
        """
        Unpin nodes from a group.

        Args:
            group_id: ID of the group to unpin nodes from
            node_names: List of node names to unpin

        Returns:
            True if successful, False otherwise
        """
        endpoint = f"classifier-api/v1/groups/{group_id}/unpin"
        port = 4433
        data = {"nodes": node_names}

        try:
            response = self._make_request("post", endpoint, port, json=data, timeout=15)
            if response.status_code in [200, 201, 204]:
                print(f"Successfully unpinned {len(node_names)} node(s) from group {group_id}")
                return True
            else:
                response.raise_for_status()
                return False
        except requests.exceptions.RequestException as e:
            print(f"Failed to unpin nodes from group {group_id}: {e}")
            if hasattr(e, 'response') and e.response is not None:
                print(f"Status code: {e.response.status_code}")
                try: print(f"Response: {e.response.text}")
                except Exception: pass
            return False


    #######################
    # PuppetDB API Endpoints
    #######################

    def _pdb_query(self, query: str, timeout: int = 30) -> Optional[Union[List, Dict]]:
        """Internal helper for making PDB PQL queries."""
        endpoint = "pdb/query/v4"
        port = 8081
        params = {"query": query}
        try:
            response = self._make_request("get", endpoint, port, params=params, timeout=timeout)
            response.raise_for_status()
            return response.json()
        except requests.exceptions.ConnectTimeout:
            print(f"Connection timed out connecting to PuppetDB ({self.base_url}:{port}).")
            print("Verify PuppetDB is running, port is open, hostname resolves, and network path is clear.")
            return None
        except requests.exceptions.RequestException as e:
            print(f"An error occurred querying PuppetDB: {e}")
            if hasattr(e, 'response') and e.response is not None:
                print(f"Status code: {e.response.status_code}")
                try: print(f"Response: {e.response.text}")
                except Exception: pass
            return None
        except json.JSONDecodeError as e:
            print(f"Failed to decode JSON response from PuppetDB: {e}")
            if 'response' in locals(): print(f"Response Text: {response.text}")
            return None


    def get_node_facts(self, node_name: str) -> Optional[List]:
        """
        Get facts for a specific node using PuppetDB PQL query.

        Args:
            node_name: Name of the node to get facts for

        Returns:
            List containing node facts object, or None on failure.
            (PQL inventory endpoint returns a list)
        """
        query = f'inventory[certname, facts.kernel, facts.os.family, facts.os.name] {{ certname = "{node_name}" }}'
        result = self._pdb_query(query)
        if result is not None:
             print(f"Successfully fetched facts for node: {node_name}")
        # Ensure return type matches annotation
        return result if isinstance(result, list) else None


    def get_nodes(self) -> Optional[List]:
        """
        Get a list of all nodes known to PuppetDB.

        Returns:
            List of node objects or None on failure.
        """
        query = 'nodes[certname, report_timestamp, catalog_timestamp, facts_timestamp] { }'
        result = self._pdb_query(query)
        if result is not None:
            print("Successfully fetched nodes list from PuppetDB")
        # Ensure return type matches annotation
        return result if isinstance(result, list) else None


    def get_reports(self, node_name: Optional[str] = None, limit: int = 10) -> Optional[List]:
        """
        Get recent reports for all or a specific node.

        Args:
            node_name: Optional name of node to filter reports
            limit: Maximum number of reports to return

        Returns:
            List of report objects or None on failure.
        """
        if node_name:
            query = f'reports[certname, hash, receive_time, status, environment] {{ certname = "{node_name}" }} order by receive_time desc limit {limit}'
        else:
            query = f'reports[certname, hash, receive_time, status, environment] {{ }} order by receive_time desc limit {limit}'

        result = self._pdb_query(query)
        if result is not None:
            print(f"Successfully fetched {limit} reports" + (f" for node {node_name}" if node_name else ""))
        # Ensure return type matches annotation
        return result if isinstance(result, list) else None


    def get_report_metrics(self, report_hash: str) -> Optional[List]:
        """
        Get metrics for a specific report. PDB returns a list.

        Args:
            report_hash: Hash of the report to get metrics for

        Returns:
            List containing report metrics object or None on failure.
        """
        query = f'reports[metrics] {{ hash = "{report_hash}" }}'
        result = self._pdb_query(query)
        if result is not None:
            print(f"Successfully fetched report metrics for {report_hash}")
        # Ensure return type matches annotation
        return result if isinstance(result, list) else None


    def get_resources(self, node_name: Optional[str] = None, resource_type: Optional[str] = None, limit: int = 50) -> Optional[List]:
        """
        Get resources for a specific node or resource type.

        Args:
            node_name: Optional name of node to filter resources
            resource_type: Optional resource type to filter (case sensitive, e.g., 'File', 'User')
            limit: Maximum number of resources to return

        Returns:
            List of resource objects or None on failure.
        """
        conditions = []
        if node_name:
            conditions.append(f'certname = "{node_name}"')
        if resource_type:
            # PDB resource types are usually capitalized
            conditions.append(f'type = "{resource_type.capitalize()}"')

        where_clause = " and ".join(conditions) if conditions else ""
        filter_str = f"{{ {where_clause} }}" if where_clause else "{ }" # PDB needs {} even if empty

        query = f'resources[certname, type, title, parameters, file, line] {filter_str} limit {limit}'
        result = self._pdb_query(query)
        if result is not None:
             print(f"Successfully fetched resources")
        # Ensure return type matches annotation
        return result if isinstance(result, list) else None


    #######################
    # Environment API Endpoints
    #######################

    def list_environments(self) -> Optional[List]:
        """
        List all available Puppet environments.

        Returns:
            List of environment names or None on failure.
        """
        endpoint = "puppet/v3/environments"
        port = 8140
        try:
            response = self._make_request("get", endpoint, port, timeout=10)
            response.raise_for_status()
            print("Successfully fetched environments.")
            environments_data = response.json()
            # Structure is {"environments": {"env_name": {...}, ...}, "search_paths": [...]}
            return list(environments_data.get('environments', {}).keys())
        except requests.exceptions.RequestException as e:
            print(f"Failed to fetch environments: {e}")
            if hasattr(e, 'response') and e.response is not None:
                print(f"Status code: {e.response.status_code}")
                try:
                    if e.response.status_code == 403:
                         print("Received 403 Forbidden. Check RBAC permissions for listing environments.")
                         print(" -> Ensure 'Puppet environment' -> 'View instances' -> 'All' is granted.")
                    print(f"Response: {e.response.text}")
                except Exception: pass
            return None # Indicate failure
        except json.JSONDecodeError as e:
            print(f"Failed to decode JSON response while listing environments: {e}")
            if 'response' in locals(): print(f"Response Text: {response.text}")
            return None


    def get_environment(self, env_name: str) -> Optional[Dict]:
        """
        Get details for a specific environment.

        Args:
            env_name: Name of the environment

        Returns:
            Environment details or None on failure.
        """
        endpoint = f"puppet/v3/environment/{env_name}"
        port = 8140
        try:
            response = self._make_request("get", endpoint, port, timeout=10)
            response.raise_for_status()
            print(f"Successfully fetched environment: {env_name}")
            return response.json()
        except requests.exceptions.RequestException as e:
            print(f"Failed to fetch environment {env_name}: {e}")
            if hasattr(e, 'response') and e.response is not None:
                print(f"Status code: {e.response.status_code}")
                try: print(f"Response: {e.response.text}")
                except Exception: pass
            return None
        except json.JSONDecodeError as e:
            print(f"Failed to decode JSON response while getting environment {env_name}: {e}")
            if 'response' in locals(): print(f"Response Text: {response.text}")
            return None


    #######################
    # Code Manager API Endpoints
    #######################

    def deploy_code(self, environments: Optional[List[str]] = None, wait: bool = True) -> Optional[Dict]:
        """
        Deploy code to environments using Code Manager.

        Args:
            environments: List of environments to deploy to (None for all managed environments)
            wait: Whether to wait for deployment to complete (can take time)

        Returns:
            Deployment status details or None on failure.
        """
        endpoint = "code-manager/v1/deploys"
        port = 8170

        data: Dict[str, Any] = {}
        # Key should be "deploy-all" if deploying all, otherwise "environments"
        if environments is None:
            data["deploy-all"] = True
        else:
            data["environments"] = environments

        if wait:
            data["wait"] = True # Request Code Manager to wait for file sync

        # Set a longer timeout if waiting, as deployments can take time
        timeout_seconds = 180 if wait else 30

        try:
            response = self._make_request("post", endpoint, port, json=data, timeout=timeout_seconds)
            response.raise_for_status() # Check for 200 OK or 202 Accepted (if not waiting)
            print("Successfully triggered code deployment")
            return response.json()
        except requests.exceptions.RequestException as e:
            print(f"Failed to deploy code: {e}")
            if hasattr(e, 'response') and e.response is not None:
                print(f"Status code: {e.response.status_code}")
                try: print(f"Response: {e.response.text}")
                except Exception: pass
            return None
        except json.JSONDecodeError as e:
            print(f"Failed to decode JSON response from code deploy: {e}")
            if 'response' in locals(): print(f"Response Text: {response.text}")
            return None


    def get_code_deployment_status(self, deployment_id: str) -> Optional[Dict]:
        """
        Get status of a code deployment using deploy ID (from deploy_code response).

        Args:
            deployment_id: ID of the deployment (typically found in Location header or response body)

        Returns:
            Deployment status details or None on failure.
        """
        # Note: The API endpoint might vary slightly based on how the ID is obtained.
        # Assuming the ID is directly usable in the path.
        endpoint = f"code-manager/v1/deploys/{deployment_id}"
        port = 8170

        try:
            response = self._make_request("get", endpoint, port, timeout=10)
            response.raise_for_status()
            print(f"Successfully fetched deployment status for: {deployment_id}")
            return response.json()
        except requests.exceptions.RequestException as e:
            print(f"Failed to fetch deployment status for {deployment_id}: {e}")
            if hasattr(e, 'response') and e.response is not None:
                print(f"Status code: {e.response.status_code}")
                try: print(f"Response: {e.response.text}")
                except Exception: pass
            return None
        except json.JSONDecodeError as e:
            print(f"Failed to decode JSON response from deployment status: {e}")
            if 'response' in locals(): print(f"Response Text: {response.text}")
            return None


    #######################
    # Task API Endpoints
    #######################

    def list_tasks(self) -> Optional[List]:
        """
        List all available Puppet tasks from the orchestrator.

        Returns:
            List of task objects or None on failure.
        """
        endpoint = "orchestrator/v1/tasks"
        port = 8143

        try:
            response = self._make_request("get", endpoint, port, timeout=15) # Orchestrator can be slow
            response.raise_for_status()
            print("Successfully fetched tasks list")
            # Response format is typically {"items": [...]}
            return response.json().get("items", [])
        except requests.exceptions.RequestException as e:
            print(f"Failed to fetch tasks list: {e}")
            if hasattr(e, 'response') and e.response is not None:
                print(f"Status code: {e.response.status_code}")
                try:
                     if e.response.status_code == 403:
                          print("Received 403 Forbidden. Check RBAC permissions for listing tasks.")
                     print(f"Response: {e.response.text}")
                except Exception: pass
            return None # Indicate failure
        except json.JSONDecodeError as e:
            print(f"Failed to decode JSON response from list tasks: {e}")
            if 'response' in locals(): print(f"Response Text: {response.text}")
            return None


    def run_task(self, task: str, params: Dict, nodes: List[str], environment: str = "production") -> Optional[Dict]:
        """
        Run a Puppet task on specific nodes via the orchestrator.

        Args:
            task: Task name (e.g., "package::install")
            params: Task parameters dictionary
            nodes: List of node certnames to run the task on
            environment: Environment context for the task

        Returns:
            Task run job details (includes job ID) or None on failure.
        """
        endpoint = "orchestrator/v1/command/task"
        port = 8143

        data = {
            "task": task,
            "params": params,
            "environment": environment,
            "scope": {
                "nodes": nodes
            }
        }

        try:
            response = self._make_request("post", endpoint, port, json=data, timeout=15)
            # Expect 202 Accepted for successful task submission
            if response.status_code == 202:
                print(f"Successfully started task: {task}")
                return response.json() # Contains job ID: {"job": {"id": "...", "name": "..."}}
            else:
                response.raise_for_status()
                return None
        except requests.exceptions.RequestException as e:
            print(f"Failed to run task {task}: {e}")
            if hasattr(e, 'response') and e.response is not None:
                print(f"Status code: {e.response.status_code}")
                try: print(f"Response: {e.response.text}")
                except Exception: pass
            return None
        except json.JSONDecodeError as e:
            print(f"Failed to decode JSON response from run task: {e}")
            if 'response' in locals(): print(f"Response Text: {response.text}")
            return None


    def get_task_status(self, job_id: str) -> Optional[Dict]:
        """
        Get status of a task run (job) from the orchestrator.

        Args:
            job_id: ID of the task run job

        Returns:
            Task run status details or None on failure.
        """
        endpoint = f"orchestrator/v1/jobs/{job_id}"
        port = 8143

        try:
            response = self._make_request("get", endpoint, port, timeout=10)
            response.raise_for_status()
            print(f"Successfully fetched task status for job: {job_id}")
            return response.json()
        except requests.exceptions.RequestException as e:
            print(f"Failed to fetch task status for job {job_id}: {e}")
            if hasattr(e, 'response') and e.response is not None:
                print(f"Status code: {e.response.status_code}")
                try: print(f"Response: {e.response.text}")
                except Exception: pass
            return None
        except json.JSONDecodeError as e:
            print(f"Failed to decode JSON response from task status: {e}")
            if 'response' in locals(): print(f"Response Text: {response.text}")
            return None


    #######################
    # RBAC API Endpoints
    #######################

    def list_users(self) -> Optional[List]:
        """
        List all users configured in RBAC.

        Returns:
            List of user objects or None on failure.
        """
        endpoint = "rbac-api/v1/users"
        port = 4433

        try:
            response = self._make_request("get", endpoint, port, timeout=10)
            response.raise_for_status()
            print("Successfully fetched users")
            return response.json() # Response is directly the list of users
        except requests.exceptions.RequestException as e:
            print(f"Failed to fetch users: {e}")
            if hasattr(e, 'response') and e.response is not None:
                print(f"Status code: {e.response.status_code}")
                try: print(f"Response: {e.response.text}")
                except Exception: pass
            return None
        except json.JSONDecodeError as e:
            print(f"Failed to decode JSON response from list users: {e}")
            if 'response' in locals(): print(f"Response Text: {response.text}")
            return None


    def create_user(self, login: str, email: str, display_name: str, role_ids: List[int]) -> Optional[Dict]:
        """
        Create a new local user in RBAC.

        Args:
            login: Username for the new user
            email: Email address
            display_name: Display name shown in console
            role_ids: List of *integer* role IDs to assign

        Returns:
            Newly created user object details or None on failure.
            Note: Requires password to be set separately usually.
        """
        endpoint = "rbac-api/v1/users"
        port = 4433

        data = {
            "login": login,
            "email": email,
            "display_name": display_name,
            "role_ids": role_ids, # API expects integer IDs
            "is_remote": False, # Assuming local user creation
            "is_revoked": False,
            "is_superuser": False # Typically false unless specifically needed
        }

        try:
            # Expect 201 Created or 303 See Other on success
            response = self._make_request("post", endpoint, port, json=data, timeout=10)
            if response.status_code in [201, 303]:
                print(f"Successfully submitted request to create user: {login}")
                # 303 might not have JSON body, handle potential error
                try:
                     # Try parsing even if 303
                     if response.text:
                         return response.json() # Contains user details including UUID
                     else: # Handle empty body (common with 303)
                         print("User created but response body was empty (may occur with 303).")
                         # Can try to get UUID from Location header if needed
                         if 'Location' in response.headers:
                              user_uuid = response.headers['Location'].split('/')[-1]
                              return {"success": True, "login": login, "id": user_uuid}
                         else:
                              return {"success": True, "login": login}
                except json.JSONDecodeError:
                    print("User created but response was not valid JSON (may occur with 303).")
                    # Can try to get UUID from Location header if needed
                    if 'Location' in response.headers:
                         user_uuid = response.headers['Location'].split('/')[-1]
                         return {"success": True, "login": login, "id": user_uuid}
                    else:
                         return {"success": True, "login": login}
            else:
                response.raise_for_status()
                return None
        except requests.exceptions.RequestException as e:
            print(f"Failed to create user {login}: {e}")
            if hasattr(e, 'response') and e.response is not None:
                print(f"Status code: {e.response.status_code}")
                try: print(f"Response: {e.response.text}")
                except Exception: pass
            return None


    def list_roles(self) -> Optional[List]:
        """
        List all roles configured in RBAC.

        Returns:
            List of role objects or None on failure.
        """
        endpoint = "rbac-api/v1/roles"
        port = 4433

        try:
            response = self._make_request("get", endpoint, port, timeout=10)
            response.raise_for_status()
            print("Successfully fetched roles")
            return response.json() # Response is directly the list of roles
        except requests.exceptions.RequestException as e:
            print(f"Failed to fetch roles: {e}")
            if hasattr(e, 'response') and e.response is not None:
                print(f"Status code: {e.response.status_code}")
                try: print(f"Response: {e.response.text}")
                except Exception: pass
            return None
        except json.JSONDecodeError as e:
            print(f"Failed to decode JSON response from list roles: {e}")
            if 'response' in locals(): print(f"Response Text: {response.text}")
            return None


    def create_role(self, display_name: str, description: str, permissions: List[Dict], user_ids: Optional[List[str]] = None, group_ids: Optional[List[str]] = None) -> Optional[Dict]:
        """
        Create a new role in RBAC.

        Args:
            display_name: Display name for the role
            description: Role description
            permissions: List of permission objects (e.g., {"object_type": "nodes", "action": "view", "instance": "*"}),
            user_ids: List of user UUIDs to assign to this role (optional)
            group_ids: List of user group UUIDs to assign to this role (optional)

        Returns:
            Role object details or None on failure.
        """
        endpoint = "rbac-api/v1/roles"
        port = 4433

        data = {
            "display_name": display_name,
            "description": description,
            "permissions": permissions, # Make sure this is the correct structure
            "user_ids": user_ids or [], # API expects lists even if empty
            "group_ids": group_ids or []
        }

        try:
            # Expect 201 Created or 303 See Other
            response = self._make_request("post", endpoint, port, json=data, timeout=10)
            if response.status_code in [201, 303]:
                print(f"Successfully submitted request to create role: {display_name}")
                try:
                     if response.text:
                          role_details = response.json() # Contains role details including ID
                          if "id" not in role_details and 'Location' in response.headers:
                               role_id = response.headers['Location'].split('/')[-1]
                               role_details['id'] = int(role_id) # Assume role ID is integer
                          return role_details
                     else: # Empty body (common with 303)
                          print("Role created but response body was empty (may occur with 303).")
                          if 'Location' in response.headers:
                               role_id = response.headers['Location'].split('/')[-1]
                               return {"success": True, "display_name": display_name, "id": int(role_id)}
                          else:
                               return {"success": True, "display_name": display_name}
                except json.JSONDecodeError:
                    print("Role created but response was not valid JSON (may occur with 303).")
                    if 'Location' in response.headers:
                         role_id = response.headers['Location'].split('/')[-1]
                         return {"success": True, "display_name": display_name, "id": int(role_id)}
                    else:
                         return {"success": True, "display_name": display_name}
                except ValueError: # Handle if role ID from header is not int
                     print("Warning: Could not convert role ID from Location header to integer.")
                     return {"success": True, "display_name": display_name}

            else:
                response.raise_for_status()
                return None
        except requests.exceptions.RequestException as e:
            print(f"Failed to create role {display_name}: {e}")
            if hasattr(e, 'response') and e.response is not None:
                print(f"Status code: {e.response.status_code}")
                # Print specific message for 400 related to permissions
                try:
                     if e.response.status_code == 400 and "invalid-request" in e.response.text and "permissions" in e.response.text:
                          print(" -> Received 'Invalid permissions in request'. Check the structure/content of the 'permissions' data.")
                     print(f"Response: {e.response.text}")
                except Exception: pass
            return None


    #######################
    # Activity API Endpoints
    #######################

    def get_activity_events(self, limit: int = 100, offset: int = 0) -> Optional[Dict]:
        """
        Get activity events from the PE Activity Service.

        Args:
            limit: Maximum number of events to return
            offset: Offset for pagination

        Returns:
            Dictionary containing activity events response (usually {"events": [...], "total": ...}) or None on failure.
        """
        endpoint = "activity-api/v1/events"
        port = 4433
        params = {
            "limit": limit,
            "offset": offset
        }

        try:
            response = self._make_request("get", endpoint, port, params=params, timeout=15) # Activity can be slower
            response.raise_for_status() # Check for 200 OK
            print("Successfully fetched activity events")
            return response.json() # Expect {"events": [...], "total": ...}
        except requests.exceptions.RequestException as e:
            print(f"Failed to fetch activity events: {e}")
            if hasattr(e, 'response') and e.response is not None:
                print(f"Status code: {e.response.status_code}")
                try:
                    if e.response.status_code == 400:
                        print("Received 400 Bad Request. Check API parameters/RBAC permissions for Activity Service.")
                        print(" -> Check pe-console-services logs for details.")
                    elif e.response.status_code == 403:
                        print("Received 403 Forbidden. Check RBAC permissions for viewing Activity Service events.")
                    print(f"Response: {e.response.text}")
                except Exception: pass
            return None # Indicate failure
        except json.JSONDecodeError as e:
            print(f"Failed to decode JSON response from activity events: {e}")
            if 'response' in locals(): print(f"Response Text: {response.text}")
            return None


    def get_activity_report(self, start_time: Optional[str] = None, end_time: Optional[str] = None) -> Optional[Dict]:
        """
        Get an activity report summarizing events for a time period.

        Args:
            start_time: Start time in ISO 8601 format (default: 24 hours ago)
            end_time: End time in ISO 8601 format (default: now)

        Returns:
            Activity report summary or None on failure.
        """
        if not start_time:
            start_time = (datetime.utcnow() - timedelta(days=1)).isoformat() + 'Z'
        if not end_time:
            end_time = datetime.utcnow().isoformat() + 'Z'

        endpoint = "activity-api/v1/reports"
        port = 4433
        params = {
            "start_time": start_time,
            "end_time": end_time
        }

        try:
            # Increased timeout slightly as reports might take longer
            response = self._make_request("get", endpoint, port, params=params, timeout=20)
            response.raise_for_status()
            print("Successfully fetched activity report")
            return response.json()
        except requests.exceptions.RequestException as e:
            print(f"Failed to fetch activity report: {e}")
            if hasattr(e, 'response') and e.response is not None:
                print(f"Status code: {e.response.status_code}")
                try: print(f"Response: {e.response.text}")
                except Exception: pass
            return None
        except json.JSONDecodeError as e:
            print(f"Failed to decode JSON response from activity report: {e}")
            if 'response' in locals(): print(f"Response Text: {response.text}")
            return None


#######################
# Expanded Test Suite Functions
#######################

# (Test suite functions remain the same as provided, they already use the API methods)
def run_test_suite(api: PuppetAPI):
    """Run a more comprehensive test of the Puppet API functions."""

    print("\n" + "="*80)
    print(" PUPPET ENTERPRISE API COMPREHENSIVE TEST SUITE ")
    print("="*80)
    print(f" Target Server: {api.base_url}") # Show target server
    print(" WARNING: This suite performs CREATE and DELETE operations.")
    print(" WARNING: Ensure you are running against a TEST instance.")
    print(" WARNING: Ensure the API user has sufficient RBAC permissions.")
    print("="*80)

    # Shared state between tests
    test_state = {
        "pe_server_node_name": None,
        "all_nodes_id": None,
        "test_group_id": None,
        "test_group_name": None,
        "test_role_id": None,
        "test_role_name": None,
        "test_user_uuid": None,
        "test_user_login": None,
        "available_roles": None, # Store fetched roles
        "available_nodes": None, # Store fetched nodes
        "available_tasks": None, # Store fetched tasks
        "last_report_hash": None, # Store for metrics test
        "deployment_job_id": None # Store for code manager status
    }

    # Track test results
    results = {
        "passed": 0,
        "failed": 0,
        "skipped": 0,
        "total": 0
    }
    test_passed_flags = {} # Track individual test pass/fail for dependencies

    def run_test(name, test_func, depends_on=None):
        """
        Helper to run a single test, track results, and handle basic dependency.
        depends_on: Optional list of test names that must have passed.
        """
        results["total"] += 1
        print(f"\n[TEST {results['total']}] {name}")
        print("-" * 60)

        # Check dependencies
        skip_dependency = False
        if depends_on:
            for dep_name in depends_on:
                if not test_passed_flags.get(dep_name, False):
                    print(f" -> SKIPPING: Dependency '{dep_name}' failed or did not run.")
                    skip_dependency = True
                    break

        if skip_dependency:
            results["skipped"] += 1
            test_passed_flags[name] = False # Mark as not passed for dependency chain
            return False # Return False to indicate skip due to dependency

        # --- Execute Test ---
        start_time = time.time()
        passed = False
        is_explicit_skip = False
        try:
            # Test function returns True on success, False on failure, "skip" for explicit skip
            result_data = test_func()

            if result_data is True:
                 passed = True
            elif result_data == "skip":
                 is_explicit_skip = True
                 passed = False # Explicitly skipped tests are not counted as passed
            else: # result_data is False or None
                 passed = False
            # Failure details should be printed within the test function
        except Exception as e:
            print(f"!!! UNCAUGHT EXCEPTION in test {name}: {e}")
            traceback.print_exc() # Print full traceback for uncaught errors
            passed = False
        finally:
            end_time = time.time()
            duration = end_time - start_time

            # --- Report Result ---
            if is_explicit_skip:
                 results["skipped"] += 1
                 print(f" -> SKIPPED: {name} (Explicitly) ({duration:.2f}s)")
                 test_passed_flags[name] = False # Treat as non-passed for dependencies
            elif passed:
                 print(f"✓ PASSED: {name} ({duration:.2f}s)")
                 results["passed"] += 1
                 test_passed_flags[name] = True
            else:
                 # Failure message should have been printed by test_func or exception handler
                 print(f"✗ FAILED: {name} ({duration:.2f}s)")
                 results["failed"] += 1
                 test_passed_flags[name] = False
        # Return True only if the test function itself passed successfully
        return passed


    # --- Test Definitions ---

    def test_01_status():
        """Test the status API."""
        status = api.check_status()
        if status is None: return False
        if isinstance(status, dict) and status:
            print("Status check returned data.")
            # Attempt to find PE server name (might vary based on PE version status output)
            pe_server_certname = None
            if 'status-service' in status and 'status' in status['status-service']:
                # Newer PE might expose hostname here, heuristic guess
                host = status['status-service']['status'].get('host')
                if host: pe_server_certname = host
            # Fallback: Try pe-master service if available
            if not pe_server_certname and 'pe-master' in status and 'host' in status['pe-master']:
                pe_server_certname = status['pe-master']['host']

            if pe_server_certname:
                test_state["pe_server_node_name"] = pe_server_certname
                print(f" -> Inferred PE server host: {test_state['pe_server_node_name']}")
            else:
                print(" -> Could not reliably infer PE server hostname from status output.")
            return True
        else:
            print("Status check returned unexpected format or was empty.")
            return False

    def test_02_cert_list():
        """Test fetching certificate statuses."""
        certs = api.get_certificate_statuses()
        if certs is None: return False
        if isinstance(certs, list):
            print(f"Found {len(certs)} certificate statuses.")
            return True
        else: return False

    # --- RBAC Setup (Needed early for creating things) ---
    def test_03_rbac_list_roles():
        """Fetch RBAC roles, needed for user/role creation tests."""
        roles = api.list_roles()
        if roles is None: return False
        if not isinstance(roles, list): return False
        print(f"Found {len(roles)} roles.")
        test_state["available_roles"] = roles # Store for later use
        return True

    def test_04_rbac_list_users():
        """Fetch RBAC users."""
        users = api.list_users()
        if users is None: return False
        if not isinstance(users, list): return False
        print(f"Found {len(users)} users.")
        return True

    # --- Node Group Setup ---
    def test_05_group_list_initial():
        """List initial groups and find All Nodes ID."""
        all_groups = api.get_node_groups()
        if all_groups is None: return False
        all_nodes_id = None
        for group in all_groups:
            if group.get("name") == "All Nodes":
                all_nodes_id = group.get("id")
                break
        if not all_nodes_id:
            print("Could not find 'All Nodes' group ID.")
            return False
        print(f"Found 'All Nodes' group ID: {all_nodes_id}")
        test_state["all_nodes_id"] = all_nodes_id
        return True

    def test_06_group_create():
        """Create a test node group."""
        parent_id = test_state["all_nodes_id"]
        if not parent_id: return False # Should be caught by dependency check

        group_name = f"Test_Group_Suite_{random.randint(10000, 99999)}"
        print(f"Attempting to create test group: {group_name}")
        new_group_details = api.create_node_group(
            name=group_name,
            description="Test group created by comprehensive API test suite",
            parent_id=parent_id,
            classes={"puppet_enterprise::profile::agent": {}} # Example class
        )
        if not new_group_details or not new_group_details.get("id"):
            print(f"Failed to create test group '{group_name}' or response lacked ID.")
            return False

        test_state["test_group_id"] = new_group_details["id"]
        test_state["test_group_name"] = group_name # Use generated name
        print(f"Created test group '{group_name}' with ID: {test_state['test_group_id']}")
        return True

    # --- PuppetDB List ---
    def test_07_pdb_list_nodes():
        """Test fetching nodes from PuppetDB."""
        print(" -> Using increased timeout (30s) for this PDB test.")
        nodes = api.get_nodes()
        if nodes is None: return False # API call failed (timeout, etc)
        if not isinstance(nodes, list): return False
        print(f"Found {len(nodes)} nodes in PuppetDB.")
        test_state["available_nodes"] = nodes
        # Try to get PE server name if not already found and nodes exist
        if nodes and not test_state.get("pe_server_node_name"):
            potential_name = nodes[0].get('certname')
            if potential_name:
                test_state["pe_server_node_name"] = potential_name
                print(f" -> Using '{potential_name}' as target node for specific PDB tests.")
        # Pass even if 0 nodes found, but store the result.
        return True

    # --- Environment List ---
    def test_08_env_list():
        """Test environment list operation."""
        print(" -> Checking RBAC permissions if this test fails (needs Env View).")
        environments = api.list_environments()
        if environments is None: return False # API call failed (403 likely)
        if not isinstance(environments, list): return False
        print(f"Found {len(environments)} environments: {', '.join(environments)}")
        return True

    # --- Task List ---
    def test_09_task_list():
        """Test tasks list API."""
        tasks = api.list_tasks()
        if tasks is None: return False # API call failed
        if not isinstance(tasks, list): return False
        print(f"Fetched {len(tasks)} available tasks.")
        test_state["available_tasks"] = tasks
        return True

    # --- Activity List ---
    def test_10_activity_list():
        """Test activity events list API."""
        print(" -> Checking RBAC ('Activity Service'?) & pe-console-services logs if this test fails (400/403).")
        events_response = api.get_activity_events(limit=5)
        if events_response is None: return False # API call failed (400/403 likely)
        if isinstance(events_response, dict) and "events" in events_response:
            print(f"Fetched {len(events_response['events'])} recent activity events.")
            return True
        else: return False

    # --- Get Specific Items (using created IDs or known items) ---
    def test_11_group_get_specific():
        """Get the details of the created test group."""
        group_id = test_state["test_group_id"]
        group_data = api.get_node_group(group_id)
        if group_data is None: return False
        if group_data.get("id") == group_id:
            print(f"Successfully fetched details for group {group_id}")
            return True
        else: return False

    def test_12_env_get_specific():
        """Get details for the 'production' environment."""
        env_details = api.get_environment("production")
        if env_details is None: return False # Likely 403 if list failed
        if env_details.get("name") == "production":
            print("Successfully fetched details for 'production' environment.")
            return True
        else: return False

    def test_13_cert_get_specific():
        """Get details for a known certificate (e.g., the PE server)."""
        node_name = test_state.get("pe_server_node_name")
        if not node_name:
            nodes = test_state.get("available_nodes")
            if nodes:
                node_name = nodes[0].get('certname')
                print(f" -> Using fallback node name for cert check: {node_name}")
                test_state["pe_server_node_name"] = node_name # Store if found now

        if not node_name:
            print(" -> SKIPPING: Cannot determine target node name for cert check.")
            return "skip"

        print(f"Attempting to fetch certificate for: {node_name}")
        cert_content = api.get_certificate(node_name)
        if cert_content is None: return False
        if isinstance(cert_content, str) and len(cert_content) > 100:
            print(f"Successfully fetched certificate content for {node_name}.")
            return True
        else:
            print(f"Fetched certificate content seems incorrect for {node_name}.")
            return False

    # --- PuppetDB Specific Queries ---
    def test_14_pdb_get_facts():
        """Get facts for the PE server node."""
        node_name = test_state.get("pe_server_node_name")
        if not node_name:
             nodes = test_state.get("available_nodes")
             if nodes: node_name = nodes[0].get('certname')

        if not node_name:
            print(" -> SKIPPING: No target node name known for fact check.")
            return "skip"

        print(" -> Using increased timeout (30s) for this PDB test.")
        facts = api.get_node_facts(node_name)
        if facts is None: return False
        # PDB Inventory returns a list
        if isinstance(facts, list) and facts:
            print(f"Successfully fetched facts for node {node_name}.")
            return True
        elif isinstance(facts, list) and not facts:
            print(f"Node {node_name} found, but no facts returned by inventory query.")
            return True # API worked, even if no facts
        else: return False

    def test_15_pdb_get_reports():
        """Get reports for the PE server node."""
        node_name = test_state.get("pe_server_node_name")
        if not node_name:
            nodes = test_state.get("available_nodes")
            if nodes: node_name = nodes[0].get('certname')

        if not node_name:
            print(" -> SKIPPING: No target node name known for report check.")
            return "skip"

        print(" -> Using increased timeout (30s) for this PDB test.")
        reports = api.get_reports(node_name, limit=1)
        if reports is None: return False
        if isinstance(reports, list):
            print(f"Successfully fetched {len(reports)} report(s) for node {node_name}.")
            if reports:
                test_state["last_report_hash"] = reports[0].get("hash")
            return True
        else: return False

    def test_16_pdb_get_resources():
        """Get File resources for the PE server node."""
        node_name = test_state.get("pe_server_node_name")
        if not node_name:
            nodes = test_state.get("available_nodes")
            if nodes: node_name = nodes[0].get('certname')

        if not node_name:
            print(" -> SKIPPING: No target node name known for resource check.")
            return "skip"

        print(" -> Using increased timeout (30s) for this PDB test.")
        resources = api.get_resources(node_name=node_name, resource_type="File", limit=5)
        if resources is None: return False
        if isinstance(resources, list):
            print(f"Successfully fetched {len(resources)} 'File' resources for node {node_name}.")
            return True
        else: return False

    def test_17_pdb_get_report_metrics():
        """Get metrics for the last fetched report hash."""
        report_hash = test_state.get("last_report_hash")
        if not report_hash:
            print(" -> SKIPPING: No report hash available from previous test.")
            return "skip"

        print(" -> Using increased timeout (30s) for this PDB test.")
        metrics = api.get_report_metrics(report_hash)
        if metrics is None: return False
        # PDB returns list, check if it contains the metrics data
        if isinstance(metrics, list) and metrics and 'metrics' in metrics[0]:
            print(f"Successfully fetched metrics for report {report_hash}.")
            return True
        else:
            print(f"Failed to get valid metrics structure for report {report_hash}.")
            return False

    # --- RBAC Create ---
    def test_18_rbac_create_role():
        """Create a test role."""
        role_name = f"Test Role Suite {random.randint(10000, 99999)}"
        print(f"Attempting to create test role: {role_name}")

        # Using a known-good basic permission structure (adjust if needed for specific PE versions)
        permissions = [{"object_type": "console_page", "action": "view", "instance": "*"}]
        print(f" -> Using basic permissions: {permissions}")

        role_details = api.create_role(display_name=role_name, description="Test role via API suite", permissions=permissions)

        if role_details is None or not role_details.get("id"):
            print("Failed to create test role or get ID.")
            return False

        test_state["test_role_id"] = role_details["id"] # API returns integer ID
        test_state["test_role_name"] = role_name
        print(f"Created test role '{role_name}' with ID: {test_state['test_role_id']}")
        return True

    def test_19_rbac_create_user():
        """Create a test user assigned to the test role."""
        role_id = test_state.get("test_role_id")
        if role_id is None: return False # Dependency check should catch this

        login = f"testuser_suite_{random.randint(10000, 99999)}"
        email = f"{login}@example.com"
        display_name = f"Test User Suite {random.randint(10000, 99999)}"
        print(f"Attempting to create test user: {login}")

        user_details = api.create_user(login=login, email=email, display_name=display_name, role_ids=[role_id]) # Pass role_id as list
        if user_details is None or not user_details.get("id"):
            print("Failed to create test user or get UUID.")
            return False
        test_state["test_user_uuid"] = user_details["id"] # API returns string UUID
        test_state["test_user_login"] = login
        print(f"Created test user '{login}' with UUID: {test_state['test_user_uuid']}")
        return True

    # --- Node Group Actions ---
    def test_20_group_pin_unpin():
        """Pin and unpin a node from the test group (if nodes exist)."""
        group_id = test_state.get("test_group_id")
        nodes = test_state.get("available_nodes")
        if not group_id: return False # Should be caught by dependency
        if not nodes: # Check if list exists and is not empty
            print(" -> SKIPPING: No nodes available to test pin/unpin.")
            return "skip"

        node_to_pin = nodes[0]['certname'] # Use the first available node
        print(f"Attempting to pin node '{node_to_pin}' to group '{test_state['test_group_name']}'")
        pin_ok = api.pin_nodes_to_group(group_id, [node_to_pin])
        if not pin_ok:
            print("Pin operation failed.")
            return False # Fail the test if pin fails

        print(f"Attempting to unpin node '{node_to_pin}'")
        unpin_ok = api.unpin_nodes_from_group(group_id, [node_to_pin])
        if not unpin_ok:
            print("Unpin operation failed.")
            return False # Fail the test if unpin fails

        print("Pin and Unpin operations successful.")
        return True

    # --- Skipped / Placeholder Tests ---
    def test_21_cert_sign_revoke():
        print(" -> SKIPPING: Cert Sign/Revoke tests require specific setup.")
        return "skip"

    def test_22_code_manager_deploy():
        print(" -> SKIPPING: Code Manager deploy test requires CM setup.")
        return "skip"

    def test_23_code_manager_status():
        print(" -> SKIPPING: Code Manager status test requires CM setup and deploy ID.")
        return "skip"

    def test_24_task_run_status():
        print(" -> SKIPPING: Task Run/Status test requires safe task/target selection.")
        return "skip"

    # --- Activity Report ---
    def test_25_activity_report():
        """Test fetching the activity report."""
        report = api.get_activity_report() # Use default last 24h
        if report is None: return False
        if isinstance(report, dict):
            print("Successfully fetched activity report summary.")
            # Simple check for expected keys (might vary by PE version)
            if "counts" in report or "changes" in report or "since" in report:
                return True
            else:
                print("Activity report structure seems unexpected.")
                return False
        else: return False

    # --- Cleanup Tests (Run Last) ---
    def test_97_cleanup_user():
        """Delete the created test user."""
        user_uuid = test_state.get("test_user_uuid")
        if not user_uuid:
            print(" -> SKIPPING: No test user UUID found to delete.")
            return "skip"

        print(f"Attempting to delete test user: {test_state.get('test_user_login','N/A')} ({user_uuid})")
        # RBAC delete user endpoint usually requires DELETE /rbac-api/v1/users/<UUID>
        endpoint = f"rbac-api/v1/users/{user_uuid}"
        port = 4433
        try:
            response = api._make_request("delete", endpoint, port, timeout=10)
            if response.status_code in [200, 204]:
                print(f"Successfully deleted user {user_uuid}")
                return True
            else:
                response.raise_for_status()
                return False
        except requests.exceptions.RequestException as e:
            print(f"Failed to delete user {user_uuid}: {e}")
            if hasattr(e, 'response') and e.response is not None: print(f"Status: {e.response.status_code}, Body: {e.response.text}")
            return False # Indicate cleanup failure

    def test_98_cleanup_role():
        """Delete the created test role."""
        role_id = test_state.get("test_role_id")
        if role_id is None: # Check for None specifically as ID is integer
            print(" -> SKIPPING: No test role ID found to delete.")
            return "skip"

        print(f"Attempting to delete test role: {test_state.get('test_role_name','N/A')} ({role_id})")
        # RBAC delete role endpoint usually requires DELETE /rbac-api/v1/roles/<ID>
        endpoint = f"rbac-api/v1/roles/{role_id}"
        port = 4433
        try:
            response = api._make_request("delete", endpoint, port, timeout=10)
            if response.status_code in [200, 204]:
                print(f"Successfully deleted role {role_id}")
                return True
            else:
                response.raise_for_status()
                return False
        except requests.exceptions.RequestException as e:
            print(f"Failed to delete role {role_id}: {e}")
            if hasattr(e, 'response') and e.response is not None: print(f"Status: {e.response.status_code}, Body: {e.response.text}")
            return False # Indicate cleanup failure

    def test_99_cleanup_group():
        """Delete the created test node group."""
        group_id = test_state.get("test_group_id")
        if not group_id:
            print(" -> SKIPPING: No test group ID found to delete.")
            return "skip"

        print(f"Attempting to delete test group: {test_state.get('test_group_name','N/A')} ({group_id})")
        deleted = api.delete_node_group(group_id)
        return deleted # delete_node_group returns boolean

    # --- Define Test Order and Dependencies ---
    run_test("01: Status Check", test_01_status)
    run_test("02: Cert List", test_02_cert_list)
    run_test("03: RBAC List Roles", test_03_rbac_list_roles)
    run_test("04: RBAC List Users", test_04_rbac_list_users)
    run_test("05: Group List Initial", test_05_group_list_initial)
    run_test("07: PDB List Nodes", test_07_pdb_list_nodes)
    run_test("08: Environment List", test_08_env_list)
    run_test("09: Task List", test_09_task_list)
    run_test("10: Activity List Events", test_10_activity_list)

    run_test("06: Group Create", test_06_group_create, depends_on=["05: Group List Initial"])
    run_test("18: RBAC Create Role", test_18_rbac_create_role, depends_on=["03: RBAC List Roles"])
    run_test("19: RBAC Create User", test_19_rbac_create_user, depends_on=["18: RBAC Create Role"])

    run_test("11: Group Get Specific", test_11_group_get_specific, depends_on=["06: Group Create"])
    run_test("12: Environment Get Specific", test_12_env_get_specific, depends_on=["08: Environment List"])
    run_test("13: Cert Get Specific", test_13_cert_get_specific, depends_on=["07: PDB List Nodes"])

    run_test("14: PDB Get Facts", test_14_pdb_get_facts, depends_on=["07: PDB List Nodes"])
    run_test("15: PDB Get Reports", test_15_pdb_get_reports, depends_on=["07: PDB List Nodes"])
    run_test("16: PDB Get Resources", test_16_pdb_get_resources, depends_on=["07: PDB List Nodes"])
    run_test("17: PDB Get Report Metrics", test_17_pdb_get_report_metrics, depends_on=["15: PDB Get Reports"])

    run_test("20: Group Pin/Unpin", test_20_group_pin_unpin, depends_on=["06: Group Create", "07: PDB List Nodes"])
    run_test("21: Cert Sign/Revoke (Skipped)", test_21_cert_sign_revoke)
    run_test("22: Code Manager Deploy (Skipped)", test_22_code_manager_deploy)
    run_test("23: Code Manager Status (Skipped)", test_23_code_manager_status)
    run_test("24: Task Run/Status (Skipped)", test_24_task_run_status)

    run_test("25: Activity Report", test_25_activity_report, depends_on=["10: Activity List Events"])

    run_test("97: Cleanup User", test_97_cleanup_user, depends_on=["19: RBAC Create User"])
    run_test("98: Cleanup Role", test_98_cleanup_role, depends_on=["18: RBAC Create Role"])
    run_test("99: Cleanup Group", test_99_cleanup_group, depends_on=["06: Group Create"])


    # --- Final Summary ---
    print("\n" + "="*80)
    print(" TEST SUITE FINAL SUMMARY ")
    print(f" Total Tests Attempted: {results['total']}")
    print(f" Passed:              {results['passed']}")
    print(f" Failed:              {results['failed']}")
    print(f" Skipped:             {results['skipped']}")
    print("="*80)

    # Check for cleanup failures
    cleanup_tests = ["97: Cleanup User", "98: Cleanup Role", "99: Cleanup Group"]
    cleanup_failures = []
    cleanup_skipped = []
    for name in cleanup_tests:
        if name in test_passed_flags: # Check if test was attempted
             if not test_passed_flags[name]: # If it failed or was skipped
                  # Determine if it was a failure or skip based on artifact existence
                  is_skip = False
                  if name == "97: Cleanup User" and not test_state.get("test_user_uuid"): is_skip = True
                  if name == "98: Cleanup Role" and test_state.get("test_role_id") is None: is_skip = True
                  if name == "99: Cleanup Group" and not test_state.get("test_group_id"): is_skip = True

                  if is_skip:
                       cleanup_skipped.append(name)
                  else:
                       cleanup_failures.append(name)
        # else: Test dependency failed earlier, implicitly skipped.

    if cleanup_failures:
        print("\nWARNING: The following cleanup steps FAILED:")
        for name in cleanup_failures: print(f" - {name}")
        print("Manual cleanup might be required on the PE server.")
        print("="*80)
    if cleanup_skipped:
        print("\nINFO: The following cleanup steps were SKIPPED (due to dependencies or missing artifact):")
        for name in cleanup_skipped: print(f" - {name}")
        print("="*80)

    return results # Return summary dict


def main():
    """Main function to demonstrate the usage of the PuppetAPI class."""

    # Configuration - Get the Puppet Enterprise server hostname/IP
    # Recommended: Set the PE_SERVER_HOST environment variable
    # Alternative: Replace the placeholder below directly
    PUPPET_SERVER_HOST = os.environ.get("PE_SERVER_HOST", "YOUR_PUPPET_SERVER_HOSTNAME")

    if PUPPET_SERVER_HOST == "YOUR_PUPPET_SERVER_HOSTNAME":
         print("\nERROR: Puppet Server hostname not configured.")
         print("Please set the PE_SERVER_HOST environment variable or edit the script where")
         print("PUPPET_SERVER_HOST is defined in the main() function.")
         sys.exit(1)

    # Create PuppetAPI client with no token initially
    api = PuppetAPI(PUPPET_SERVER_HOST)

    print("="*80)
    print(" PUPPET ENTERPRISE API CLIENT ")
    print(f" Target Server: {api.base_url}")
    print("="*80)
    print("\n1. Interactive Mode")
    print("2. Run Comprehensive Test Suite") # Updated label
    choice = input("\nSelect mode (1 or 2): ").strip()

    # Get authentication token
    print("\n=== Authentication ===")
    use_existing = input("Do you have an existing auth token? (y/n): ").lower().strip() == 'y'

    auth_token = None
    if use_existing:
        auth_token = getpass.getpass("Enter your authentication token: ").strip() # Use getpass for token too
        if not auth_token:
            print("No token entered. Exiting.")
            sys.exit(1)
        api.auth_token = auth_token
        api.headers["X-Authentication"] = auth_token
        # Optional: Add a basic check here, like trying to list users to validate token
        print("Validating provided token by attempting to list users...")
        users = api.list_users()
        if users is None:
            print("Token validation failed (could not list users). Check token and permissions.")
            # Decide whether to exit or proceed cautiously
            if input("Proceed anyway? (y/n): ").lower() != 'y':
                sys.exit(1)
        else:
            print("Token appears valid.")

    else:
        print("Generating new authentication token...")
        username = input("Enter Puppet Enterprise username: ").strip()
        # Use getpass for secure password entry
        password = getpass.getpass("Enter password: ")
        auth_token = api.get_auth_token(username, password)
        if not auth_token:
            print("\nAuthentication failed. Exiting...")
            sys.exit(1)

    if choice == '2':
        # Run test suite
        run_test_suite(api)
        # Revoke token if it was generated in this session
        if not use_existing and auth_token:
            print("\nRevoking generated token...")
            api.revoke_token(auth_token)
        sys.exit(0) # Exit after test suite

    # ==========================================================================
    #   Interactive Mode Menu (Keep the previously corrected version)
    #   ... includes choices 0-29 ...
    #   ... with checks for None return values from API calls ...
    # ==========================================================================
    while True:
        print("\n" + "="*80)
        print(" PUPPET ENTERPRISE API OPERATIONS ")
        print("="*80)

        print("\nGeneral APIs:")
        print("1. Check PE services status")

        print("\nCertificate APIs:")
        print("2. Get certificate statuses")
        print("3. Get specific certificate")
        print("4. Sign certificate request")
        print("5. Revoke certificate")

        print("\nNode Group APIs:")
        print("6. Get node groups")
        print("7. Get specific node group")
        print("8. Create a new node group")
        print("9. Update node group (Experimental - requires full group data)")
        print("10. Delete node group")
        print("11. Pin nodes to a group")
        print("12. Unpin nodes from a group")

        print("\nPuppetDB APIs:")
        print("13. Get node facts")
        print("14. Get nodes list")
        print("15. Get reports")
        print("16. Get node resources")

        print("\nEnvironment APIs:")
        print("17. List environments")
        print("18. Get environment details")

        print("\nCode Manager APIs:")
        print("19. Deploy code")
        print("20. Get deployment status")

        print("\nTask APIs:")
        print("21. List tasks")
        print("22. Run task")
        print("23. Get task status")

        print("\nRBAC APIs:")
        print("24. List users")
        print("25. Create user")
        print("26. List roles")
        print("27. Create role")

        print("\nActivity APIs:")
        print("28. Get activity events")
        print("29. Get activity report")

        print("\n0. Exit")

        choice = input("\nEnter your choice (0-29): ").strip()

        if choice == '0':
            print("Exiting...")
            # Revoke token if it was generated in this session
            if not use_existing and auth_token:
                print("Revoking generated token...")
                api.revoke_token(auth_token)
            break

        #######################
        # Status API
        #######################

        elif choice == '1':
            print("\n=== Checking Puppet Enterprise Services Status ===")
            services_status = api.check_status()
            if services_status:
                print(json.dumps(services_status, indent=2))

        #######################
        # Certificate API
        #######################

        elif choice == '2':
            print("\n=== Getting Certificate Statuses ===")
            cert_statuses = api.get_certificate_statuses()
            if cert_statuses is not None: # Check for API failure
                if cert_statuses:
                    # Print just the names and states for brevity
                    for cert in cert_statuses:
                         print(f"Certificate: {cert.get('name', 'N/A')}, State: {cert.get('state', 'N/A')}")

                    # Optional detailed view
                    show_detail = input("\nShow detailed certificate info? (y/n): ").lower().strip()
                    if show_detail == 'y':
                         print(json.dumps(cert_statuses, indent=2))
                else:
                    print("No certificate statuses found.")

        elif choice == '3':
            print("\n=== Get Specific Certificate ===")
            certname = input("Enter certificate name: ").strip()
            if certname:
                cert_content = api.get_certificate(certname)
                if cert_content:
                    print(f"Certificate content (excerpt):\n{cert_content[:500]}...")
            else:
                print("Certificate name cannot be empty")

        elif choice == '4':
            print("\n=== Sign Certificate Request ===")
            certname = input("Enter certificate request name: ").strip()
            if certname:
                # Optional: Add check here to see if cert is actually in 'requested' state first
                result = api.sign_certificate_request(certname)
                # Message printed by API method
            else:
                print("Certificate name cannot be empty")

        elif choice == '5':
            print("\n=== Revoke Certificate ===")
            certname = input("Enter certificate name to revoke: ").strip()
            if certname:
                confirm = input(f"Are you sure you want to revoke '{certname}'? (y/n): ").lower().strip()
                if confirm == 'y':
                    result = api.revoke_certificate(certname)
                    # Message printed by API method
            else:
                print("Certificate name cannot be empty")

        #######################
        # Node Group API
        #######################

        elif choice == '6':
            print("\n=== Getting Node Groups ===")
            groups = api.get_node_groups()
            if groups is not None:
                if groups:
                    for group in groups:
                        print(f"Group: {group.get('name', 'N/A')}, ID: {group.get('id', 'N/A')}")
                else:
                    print("No node groups found.")

        elif choice == '7':
            print("\n=== Get Specific Node Group ===")
            group_id = input("Enter group ID: ").strip()
            if group_id:
                group_details = api.get_node_group(group_id)
                if group_details:
                    print(json.dumps(group_details, indent=2))
            else:
                print("Group ID cannot be empty")

        elif choice == '8':
            print("\n=== Creating a New Node Group ===")
            groups = api.get_node_groups()
            if groups is None:
                print("Failed to fetch existing groups. Cannot create a new group.")
                continue

            print("\nAvailable parent groups:")
            group_map_by_num = {}
            for i, group in enumerate(groups):
                print(f"{i+1}. {group.get('name', 'N/A')} (ID: {group.get('id', 'N/A')})")
                group_map_by_num[i+1] = group.get('id')

            parent_id = None
            parent_choice = input("\nSelect parent group number or paste group ID: ").strip()

            if parent_choice.isdigit():
                try:
                    parent_idx = int(parent_choice)
                    if parent_idx in group_map_by_num:
                        parent_id = group_map_by_num[parent_idx]
                    else: print("Invalid selection number."); continue
                except ValueError: print("Invalid selection number."); continue
            else:
                # Basic UUID validation
                if len(parent_choice) == 36 and parent_choice.count('-') == 4:
                    parent_id = parent_choice
                    if not any(g['id'] == parent_id for g in groups):
                        print(f"Warning: Provided parent ID {parent_id} not found in fetched groups. Proceeding anyway.")
                else: print("Invalid Group ID format. Expected number or UUID."); continue

            name = input("Enter group name: ").strip()
            if not name: print("Group name cannot be empty."); continue
            description = input("Enter group description: ").strip()
            environment = input("Enter environment (default: production): ").strip() or "production"
            # Optional: Add inputs for classes/rules interactively

            new_group = api.create_node_group(
                name=name, description=description, parent_id=parent_id, environment=environment
            )
            if new_group:
                print(f"\nGroup creation request successful for: {name}")
                print(json.dumps(new_group, indent=2)) # Show response

        elif choice == '9':
            print("\n=== Update Node Group (Experimental) ===")
            print("NOTE: Updating requires providing the full group definition.")
            group_id = input("Enter group ID to update: ").strip()
            if not group_id: print("Group ID cannot be empty."); continue

            print(f"Fetching current data for group {group_id}...")
            current_data = api.get_node_group(group_id)
            if not current_data:
                print("Could not fetch current group data. Cannot update.")
                continue

            print("\nCurrent Group Data:")
            print(json.dumps(current_data, indent=2))
            print("\nModify the required fields (name, description, rule, classes etc).")
            print("You need to provide the complete structure back.")
            try:
                print("Paste the complete updated JSON data below (Ctrl+D or empty line then Enter to finish):")
                lines = sys.stdin.readlines() # Read until EOF (Ctrl+D) or empty lines accepted by user flow
                updated_json_str = "".join(lines).strip()

                if not updated_json_str: print("Update cancelled."); continue

                updated_data = json.loads(updated_json_str)
                if not all(k in updated_data for k in ["name", "id", "parent", "rule", "environment", "classes"]):
                    print("Warning: Input JSON seems incomplete. Ensure all required fields are present.")
                    if input("Proceed anyway? (y/n): ").lower() != 'y': continue

                result = api.update_node_group(group_id, updated_data)
                if result:
                    print("Node group update successful.")
                    print(json.dumps(result, indent=2))
            except json.JSONDecodeError: print("Invalid JSON input.")
            except Exception as e: print(f"An error occurred during update: {e}")

        elif choice == '10':
            print("\n=== Delete Node Group ===")
            group_id = input("Enter group ID to DELETE: ").strip()
            if not group_id: print("Group ID cannot be empty."); continue

            group_name = group_id
            group_data = api.get_node_group(group_id) # Attempt to get name for confirmation
            if group_data: group_name = group_data.get('name', group_id)

            confirm = input(f"\nAre you sure you want to DELETE the group '{group_name}' ({group_id})? (y/n): ").lower().strip()
            if confirm == 'y':
                result = api.delete_node_group(group_id)
                # Message printed by method

        elif choice == '11':
            print("\n=== Pinning Nodes to Group ===")
            group_id = input("Enter group ID to pin nodes to: ").strip()
            if not group_id: print("Group ID cannot be empty."); continue
            node_input = input("Enter node names (comma-separated): ").strip()
            node_names = [n.strip() for n in node_input.split(',') if n.strip()]

            if not node_names: print("No valid node names provided."); continue
            result = api.pin_nodes_to_group(group_id, node_names)
            # Message printed by method

        elif choice == '12':
            print("\n=== Unpinning Nodes from Group ===")
            group_id = input("Enter group ID to unpin nodes from: ").strip()
            if not group_id: print("Group ID cannot be empty."); continue
            node_input = input("Enter node names to unpin (comma-separated): ").strip()
            node_names = [n.strip() for n in node_input.split(',') if n.strip()]

            if not node_names: print("No valid node names provided."); continue
            result = api.unpin_nodes_from_group(group_id, node_names)
            # Message printed by method

        #######################
        # PuppetDB API
        #######################

        elif choice == '13':
            print("\n=== Getting Node Facts ===")
            node_name = input("Enter node name: ").strip()
            if not node_name: print("Node name cannot be empty."); continue

            facts_list = api.get_node_facts(node_name) # Returns list or None
            if facts_list is not None:
                if facts_list:
                    # PDB Inventory returns a list, usually with one item
                    print(json.dumps(facts_list[0], indent=2))
                else:
                    print(f"No facts found for node: {node_name}")

        elif choice == '14':
            print("\n=== Getting Nodes List ===")
            nodes = api.get_nodes() # Returns list or None
            if nodes is not None:
                print(f"Found {len(nodes)} nodes:")
                if nodes:
                    for i, node in enumerate(nodes):
                        print(f"{i+1}. {node.get('certname', 'N/A')}")

                    show_detail = input("\nShow detailed node info? (y/n): ").lower().strip() == 'y'
                    if show_detail: print(json.dumps(nodes, indent=2))

        elif choice == '15':
            print("\n=== Getting Recent Reports ===")
            filter_by_node = input("Filter by node? (y/n): ").lower().strip() == 'y'
            node_name = None
            if filter_by_node:
                node_name = input("Enter node name: ").strip()
                if not node_name: print("Node name cannot be empty."); continue

            limit = 10
            try:
                limit_input = input("Enter number of reports to show (default: 10): ").strip()
                if limit_input: limit = int(limit_input)
            except ValueError: print("Invalid number, using default of 10.")

            reports = api.get_reports(node_name, limit) # Returns list or None
            if reports is not None:
                if reports:
                    print("\nRecent Reports:")
                    for i, report in enumerate(reports):
                        timestamp = report.get('receive_time', 'N/A')
                        status = report.get('status', 'N/A')
                        node = report.get('certname', 'N/A')
                        env = report.get('environment', 'N/A')
                        rhash = report.get('hash', 'N/A')
                        print(f"{i+1}. Node: {node}, Status: {status}, Env: {env}, Time: {timestamp}, Hash: {rhash}")

                    show_detail = input("\nShow detailed report info? (y/n): ").lower().strip() == 'y'
                    if show_detail: print(json.dumps(reports, indent=2))
                else:
                    print("No reports found matching criteria.")

        elif choice == '16':
            print("\n=== Getting Node Resources ===")
            filter_by_node = input("Filter by node? (y/n): ").lower().strip() == 'y'
            node_name = None
            if filter_by_node:
                node_name = input("Enter node name: ").strip()
                if not node_name: print("Node name cannot be empty."); continue

            filter_by_type = input("Filter by resource type? (y/n): ").lower().strip() == 'y'
            resource_type = None
            if filter_by_type:
                resource_type = input("Enter resource type (e.g., File, User - case sensitive): ").strip()
                if not resource_type: print("Resource type cannot be empty if filtering."); continue

            limit = 50
            try:
                limit_input = input("Enter number of resources to show (default: 50): ").strip()
                if limit_input: limit = int(limit_input)
            except ValueError: print("Invalid number, using default of 50.")

            resources = api.get_resources(node_name, resource_type, limit) # Returns list or None
            if resources is not None:
                if resources:
                    print(f"\nFound {len(resources)} resources:")
                    for i, res in enumerate(resources[:10]): # Show first 10 summary
                        node = res.get('certname', 'N/A')
                        r_type = res.get('type', 'N/A')
                        title = res.get('title', 'N/A')
                        print(f"{i+1}. Node: {node}, Type: {r_type}, Title: {title}")

                    if len(resources) > 10: print(f"... and {len(resources) - 10} more")

                    show_detail = input("\nShow detailed resource info? (y/n): ").lower().strip() == 'y'
                    if show_detail: print(json.dumps(resources, indent=2))
                else:
                    print("No resources found matching criteria.")

        #######################
        # Environment API
        #######################

        elif choice == '17':
            print("\n=== Listing Environments ===")
            environments = api.list_environments() # Returns list or None
            if environments is not None:
                if environments:
                    print("\nAvailable Environments:")
                    for i, env in enumerate(environments): print(f"{i+1}. {env}")
                else:
                    print("No environments found (or failed to fetch).")

        elif choice == '18':
            print("\n=== Get Environment Details ===")
            env_name = input("Enter environment name: ").strip()
            if not env_name: print("Environment name cannot be empty."); continue

            env_details = api.get_environment(env_name) # Returns dict or None
            if env_details:
                print(json.dumps(env_details, indent=2))

        #######################
        # Code Manager API
        #######################

        elif choice == '19':
            print("\n=== Deploy Code ===")
            deploy_specific = input("Deploy specific environment(s)? (y/n - 'n' deploys all): ").lower().strip() == 'y'
            environments = None
            if deploy_specific:
                env_input = input("Enter environment names (comma-separated): ").strip()
                environments = [e.strip() for e in env_input.split(',') if e.strip()]
                if not environments: print("No environments specified."); continue

            wait = input("Wait for deployment to complete? (y/n - can take time): ").lower().strip() == 'y'
            result = api.deploy_code(environments, wait) # Returns dict or None
            if result:
                print("Deployment request submitted successfully.")
                print(json.dumps(result, indent=2))
                # Check for deploy signature or ID in response
                deploy_id = result.get("deploy-signature") or result.get("id") # Check common keys
                if deploy_id:
                    print(f"\nDeployment ID/Signature: {deploy_id}")
                    print("Use option 20 to check status.")

        elif choice == '20':
            print("\n=== Get Deployment Status ===")
            deployment_id = input("Enter deployment ID/Signature: ").strip()
            if not deployment_id: print("Deployment ID cannot be empty"); continue
            status = api.get_code_deployment_status(deployment_id) # Returns dict or None
            if status:
                print(json.dumps(status, indent=2))

        #######################
        # Task API
        #######################

        elif choice == '21':
            print("\n=== List Tasks ===")
            tasks = api.list_tasks() # Returns list or None
            if tasks is not None:
                if tasks:
                    print(f"\nFound {len(tasks)} tasks:")
                    for i, task in enumerate(tasks[:25]): # Show first 25
                        task_id = task.get('id', 'N/A') # ID includes module::name
                        print(f"{i+1}. {task_id}")
                    if len(tasks) > 25: print(f"... and {len(tasks) - 25} more")

                    show_detail = input("\nShow detailed task info? (y/n): ").lower().strip() == 'y'
                    if show_detail: print(json.dumps(tasks, indent=2))
                else:
                    print("No tasks found (or failed to fetch).")

        elif choice == '22':
            print("\n=== Run Task ===")
            task_name = input("Enter full task name (e.g., package::install): ").strip()
            if not task_name: print("Task name cannot be empty."); continue

            nodes_input = input("Enter node names to run task on (comma-separated): ").strip()
            nodes = [n.strip() for n in nodes_input.split(',') if n.strip()]
            if not nodes: print("No valid node names provided."); continue

            environment = input("Enter environment (default: production): ").strip() or "production"

            print("\nEnter task parameters (key=value format, one per line, empty line to finish):")
            params = {}
            while True:
                param_line = input("> ").strip()
                if not param_line: break
                if '=' in param_line:
                    key, value = param_line.split('=', 1)
                    # Try to infer type (basic json loads)
                    try: params[key.strip()] = json.loads(value.strip())
                    except json.JSONDecodeError: params[key.strip()] = value.strip() # Store as string
                else: print("Skipping invalid format (expected key=value).")

            result = api.run_task(task_name, params, nodes, environment) # Returns dict or None
            if result:
                print("Task started successfully.")
                print(json.dumps(result, indent=2))
                job_id = result.get('job', {}).get('id')
                if job_id:
                    print(f"\nJob ID: {job_id}")
                    print("You can check status with option 23.")

        elif choice == '23':
            print("\n=== Get Task Status ===")
            job_id = input("Enter job ID: ").strip()
            if not job_id: print("Job ID cannot be empty"); continue
            status = api.get_task_status(job_id) # Returns dict or None
            if status:
                print(json.dumps(status, indent=2))

        #######################
        # RBAC API
        #######################

        elif choice == '24':
            print("\n=== List Users ===")
            users = api.list_users() # Returns list or None
            if users is not None:
                if users:
                    print(f"\nFound {len(users)} users:")
                    for i, user in enumerate(users):
                        login = user.get('login', 'N/A')
                        name = user.get('display_name', 'N/A')
                        uuid = user.get('id', 'N/A')
                        print(f"{i+1}. Login: {login} (Name: {name}, ID: {uuid})")

                    show_detail = input("\nShow detailed user info? (y/n): ").lower().strip() == 'y'
                    if show_detail: print(json.dumps(users, indent=2))
                else:
                    print("No users found.")

        elif choice == '25':
            print("\n=== Create User ===")
            login = input("Enter login (username): ").strip()
            if not login: print("Login cannot be empty"); continue
            email = input("Enter email: ").strip()
            if not email: print("Email cannot be empty"); continue
            display_name = input("Enter display name: ").strip()
            if not display_name: print("Display name cannot be empty"); continue

            roles = api.list_roles()
            if roles is None: print("Failed to fetch roles. Cannot assign."); continue

            print("\nAvailable Roles:")
            role_map = {} # id -> name
            role_num_map = {} # number -> id
            for i, role in enumerate(roles):
                 name = role.get('display_name', 'N/A')
                 role_id = role.get('id') # API expects integer ID
                 if role_id is not None:
                      role_map[role_id] = name
                      role_num_map[i+1] = role_id
                      print(f"{i+1}. {name} (ID: {role_id})")

            role_input = input("\nSelect role numbers to assign (comma-separated): ").strip()
            selections = [s.strip() for s in role_input.split(',') if s.strip()]
            role_ids_to_assign = []
            try:
                for sel in selections:
                    num = int(sel)
                    if num in role_num_map: role_ids_to_assign.append(role_num_map[num])
                    else: print(f"Warning: Invalid role number {num} skipped.")
            except ValueError: print("Invalid input. Please enter numbers only."); continue

            if not role_ids_to_assign: print("No valid roles selected."); continue

            result = api.create_user(login, email, display_name, role_ids_to_assign)
            if result:
                print(f"User creation request submitted for: {login}")
                print("(Note: Password typically needs to be set via console or password reset)")
                print(json.dumps(result, indent=2))

        elif choice == '26':
            print("\n=== List Roles ===")
            roles = api.list_roles() # Returns list or None
            if roles is not None:
                if roles:
                    print(f"\nFound {len(roles)} roles:")
                    for i, role in enumerate(roles):
                        name = role.get('display_name', 'N/A')
                        role_id = role.get('id', 'N/A')
                        desc = role.get('description', '')
                        desc_excerpt = desc[:50] + '...' if len(desc) > 50 else desc
                        print(f"{i+1}. Name: {name} (ID: {role_id}, Desc: {desc_excerpt})")

                    show_detail = input("\nShow detailed role info (incl. permissions)? (y/n): ").lower().strip() == 'y'
                    if show_detail: print(json.dumps(roles, indent=2))
                else:
                    print("No roles found.")

        elif choice == '27':
            print("\n=== Create Role ===")
            display_name = input("Enter role display name: ").strip()
            if not display_name: print("Display name cannot be empty"); continue
            description = input("Enter role description: ").strip()

            print("\nEnter permissions (one per line, format: type:action:instance, e.g., node_groups:view:*, empty line to finish):")
            permissions = []
            while True:
                perm_line = input("> ").strip()
                if not perm_line: break
                parts = perm_line.split(':')
                if len(parts) == 3:
                    permissions.append({"object_type": parts[0], "action": parts[1], "instance": parts[2]})
                else: print("Invalid format. Should be object_type:action:instance")

            if not permissions: print("Warning: No valid permissions provided.");

            # Optional: Assign users/groups interactively (more complex)
            result = api.create_role(display_name, description, permissions)
            if result:
                print(f"Role creation request submitted for: {display_name}")
                print(json.dumps(result, indent=2))

        #######################
        # Activity API
        #######################

        elif choice == '28':
            print("\n=== Get Activity Events ===")
            limit = 20
            try:
                limit_input = input("Enter number of events to show (default: 20): ").strip()
                if limit_input: limit = int(limit_input)
            except ValueError: print("Invalid number, using default of 20.")

            events_data = api.get_activity_events(limit) # Returns dict or None
            if events_data:
                events = events_data.get("events", [])
                total = events_data.get("total", len(events))
                print(f"\nFound {len(events)} events (Total reported: {total}):")
                if events:
                    for i, event in enumerate(events):
                        event_type = event.get('type', 'N/A')
                        timestamp = event.get('timestamp', 'N/A')
                        subject = event.get('subject', {}).get('name', 'N/A')
                        details_obj = event.get('details', {})
                        details_str = json.dumps(details_obj) if isinstance(details_obj, dict) else str(details_obj)
                        details_excerpt = details_str[:50] + '...' if len(details_str) > 50 else details_str
                        print(f"{i+1}. Type: {event_type}, Subject: {subject}, Time: {timestamp}, Details: {details_excerpt}")

                    show_detail = input("\nShow full event details? (y/n): ").lower().strip() == 'y'
                    if show_detail: print(json.dumps(events, indent=2))
                else:
                    print("No activity events returned.")

        elif choice == '29':
            print("\n=== Get Activity Report ===")
            default_start = (datetime.utcnow() - timedelta(days=1)).isoformat() + 'Z'
            default_end = datetime.utcnow().isoformat() + 'Z'
            print(f"Default time range is the last 24 hours:")
            print(f" Start: {default_start}")
            print(f" End:   {default_end}")

            custom_range = input("\nCustomize time range (ISO format)? (y/n): ").lower().strip() == 'y'
            start_time = default_start
            end_time = default_end
            if custom_range:
                custom_start = input(f"Enter custom start time (e.g. {default_start}): ").strip()
                if custom_start: start_time = custom_start
                custom_end = input(f"Enter custom end time (e.g. {default_end}): ").strip()
                if custom_end: end_time = custom_end

            report = api.get_activity_report(start_time, end_time) # Returns dict or None
            if report:
                print(json.dumps(report, indent=2))

        else:
            print("Invalid choice. Please enter a number between 0 and 29.")


# Deprecated entry point
def test_puppet_api():
    """(Deprecated) Use main() with choice '2' instead."""
    print("This function is deprecated. Run the script and choose mode '2' for the test suite.")
    return False


if __name__ == "__main__":
    # Allow running test suite directly via argument, otherwise run main interactive/menu
    if len(sys.argv) > 1 and sys.argv[1] == "--test":
         # Non-interactive test mode
         print("Running in Non-Interactive Test Mode...")

         # !! IMPORTANT: Handle credentials and server securely for non-interactive use !!
         # Use environment variables
         PUPPET_SERVER_HOST = os.environ.get("PE_SERVER_HOST")
         test_user = os.environ.get("PE_API_USER")
         test_pass = os.environ.get("PE_API_PASSWORD")

         if not PUPPET_SERVER_HOST:
             print("ERROR: PE_SERVER_HOST environment variable must be set for non-interactive test.")
             sys.exit(1)
         if not test_user or not test_pass:
             print("ERROR: PE_API_USER and PE_API_PASSWORD environment variables must be set for non-interactive test.")
             sys.exit(1)

         api_instance = PuppetAPI(PUPPET_SERVER_HOST)
         print(f"Attempting non-interactive authentication as {test_user} on {PUPPET_SERVER_HOST}...")
         token = api_instance.get_auth_token(test_user, test_pass)
         if token:
             run_test_suite(api_instance)
             # Revoke token after non-interactive run
             print("\nRevoking non-interactive token...")
             api_instance.revoke_token(token)
         else:
             print("Non-interactive authentication failed. Cannot run test suite.")
             sys.exit(1)
    else:
        # Normal interactive mode
        main()