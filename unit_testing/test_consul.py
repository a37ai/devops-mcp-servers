#!/usr/bin/env python3
"""
MCP Server Test Script
----------------------
This script tests all tools and functionalities of the MCP server
using the provided Consul credentials.
"""

import json
import time
import sys
from servers.consul.consul_mcp import *
from consul import Consul

# Consul credentials
CONSUL_URL = ""
CONSUL_TOKEN = ""

CONSUL_HOST = None
CONSUL_PORT = None

def setup_consul_client():
    """Initialize the Consul client with the provided credentials."""
    try:
        client = Consul(host=CONSUL_HOST, port=CONSUL_PORT, token=CONSUL_TOKEN)
        print("✅ Successfully connected to Consul")
        return client
    except Exception as e:
        print(f"❌ Failed to connect to Consul: {str(e)}")
        sys.exit(1)

def test_kv_operations(client):
    """Test Key-Value store operations."""
    print("\n🔍 Testing Key-Value Operations...")
    
    test_key = "test/mcp/key"
    test_value = json.dumps({"timestamp": time.time(), "message": "MCP test value"})
    
    # Put operation
    try:
        success = client.kv.put(test_key, test_value)
        if success:
            print(f"✅ Successfully put value at key: {test_key}")
        else:
            print(f"❌ Failed to put value at key: {test_key}")
    except Exception as e:
        print(f"❌ Exception during KV put: {str(e)}")
    
    # Get operation
    try:
        index, data = client.kv.get(test_key)
        if data and data['Value']:
            retrieved_value = data['Value'].decode('utf-8')
            print(f"✅ Successfully retrieved value from key: {test_key}")
            print(f"   Value: {retrieved_value}")
        else:
            print(f"❌ Failed to retrieve value from key: {test_key}")
    except Exception as e:
        print(f"❌ Exception during KV get: {str(e)}")
    
    # List operation
    try:
        index, data = client.kv.get("test/mcp", recurse=True)
        print(f"✅ Successfully listed keys under 'test/mcp'")
        if data:
            for item in data:
                print(f"   - {item['Key']}")
    except Exception as e:
        print(f"❌ Exception during KV list: {str(e)}")
    
    # Delete operation
    try:
        success = client.kv.delete(test_key)
        if success:
            print(f"✅ Successfully deleted key: {test_key}")
        else:
            print(f"❌ Failed to delete key: {test_key}")
    except Exception as e:
        print(f"❌ Exception during KV delete: {str(e)}")

def test_catalog_operations(client):
    """Test Catalog operations."""
    print("\n🔍 Testing Catalog Operations...")
    
    # List datacenters
    try:
        datacenters = client.catalog.datacenters()
        print(f"✅ Successfully retrieved datacenters:")
        for dc in datacenters:
            print(f"   - {dc}")
    except Exception as e:
        print(f"❌ Exception during catalog datacenters: {str(e)}")
    
    # List nodes
    try:
        index, nodes = client.catalog.nodes()
        print(f"✅ Successfully retrieved nodes:")
        for node in nodes:
            print(f"   - {node['Node']} ({node['Address']})")
    except Exception as e:
        print(f"❌ Exception during catalog nodes: {str(e)}")
    
    # List services
    try:
        index, services = client.catalog.services()
        print(f"✅ Successfully retrieved services:")
        for service_name, tags in services.items():
            print(f"   - {service_name} (Tags: {', '.join(tags) if tags else 'None'})")
    except Exception as e:
        print(f"❌ Exception during catalog services: {str(e)}")

def test_health_operations(client):
    """Test Health check operations."""
    print("\n🔍 Testing Health Check Operations...")
    
    # List all checks
    try:
        index, checks = client.health.state("any")
        print(f"✅ Successfully retrieved all health checks:")
        for check in checks:
            print(f"   - {check['CheckID']}: {check['Status']} for {check['ServiceName'] or 'Node'}")
    except Exception as e:
        print(f"❌ Exception during health state: {str(e)}")
    
    # Get service health
    # First get a service name from the catalog
    try:
        index, services = client.catalog.services()
        if services:
            service_name = list(services.keys())[0]
            index, service_checks = client.health.service(service_name)
            print(f"✅ Successfully retrieved health for service '{service_name}':")
            for entry in service_checks:
                node = entry["Node"]["Node"]
                for check in entry["Checks"]:
                    print(f"   - [{check['Status']}] {check['CheckID']} on {node}")
    except Exception as e:
        print(f"❌ Exception during health service: {str(e)}")

def test_agent_operations(client):
    """Test Agent operations."""
    print("\n🔍 Testing Agent Operations...")
    
    # Get agent info
    try:
        agent_info = client.agent.self()
        print("✅ Successfully retrieved agent information:")
        print(f"   - Node name: {agent_info['Config']['NodeName']}")
        print(f"   - Datacenter: {agent_info['Config']['Datacenter']}")
        print(f"   - Version: {agent_info['Config']['Version']}")
    except Exception as e:
        print(f"❌ Exception during agent self: {str(e)}")
    
    # List members
    try:
        members = client.agent.members()
        print("✅ Successfully retrieved agent members:")
        for member in members:
            print(f"   - {member['Name']} ({member['Addr']}:{member['Port']})")
    except Exception as e:
        print(f"❌ Exception during agent members: {str(e)}")
    
    # Get local services
    try:
        services = client.agent.services()
        print("✅ Successfully retrieved local services:")
        for service_id, service in services.items():
            print(f"   - {service['Service']} (ID: {service_id})")
    except Exception as e:
        print(f"❌ Exception during agent services: {str(e)}")
    
    # Get local checks
    try:
        checks = client.agent.checks()
        print("✅ Successfully retrieved local checks:")
        for check_id, check in checks.items():
            print(f"   - {check['Name']} (ID: {check_id}, Status: {check['Status']})")
    except Exception as e:
        print(f"❌ Exception during agent checks: {str(e)}")

def test_session_operations(client):
    """Test Session operations."""
    print("\n🔍 Testing Session Operations...")
    
    # Create a session
    session_id = None
    try:
        session_id = client.session.create(name="mcp-test-session", ttl="10s")
        print(f"✅ Successfully created session: {session_id}")
    except Exception as e:
        print(f"❌ Exception during session create: {str(e)}")
    
    if session_id:
        # Info on session
        try:
            index, session_info = client.session.info(session_id)
            print("✅ Successfully retrieved session info:")
            print(f"   - Name: {session_info['Name']}")
            print(f"   - TTL: {session_info['TTL']}")
            print(f"   - Node: {session_info['Node']}")
        except Exception as e:
            print(f"❌ Exception during session info: {str(e)}")
        
        # List sessions
        try:
            index, sessions = client.session.list()
            print("✅ Successfully listed all sessions:")
            for session in sessions:
                print(f"   - {session['ID']} ({session['Name']})")
        except Exception as e:
            print(f"❌ Exception during session list: {str(e)}")
        
        # Renew session
        try:
            session_info = client.session.renew(session_id)
            print(f"✅ Successfully renewed session: {session_id}")
        except Exception as e:
            print(f"❌ Exception during session renew: {str(e)}")
        
        # Destroy session
        try:
            success = client.session.destroy(session_id)
            if success:
                print(f"✅ Successfully destroyed session: {session_id}")
            else:
                print(f"❌ Failed to destroy session: {session_id}")
        except Exception as e:
            print(f"❌ Exception during session destroy: {str(e)}")

def test_acl_operations(client):
    """Test ACL operations."""
    print("\n🔍 Testing ACL Operations...")
    
    # Get self token info
    try:
        token_info = client.acl.info(CONSUL_TOKEN)
        if token_info:
            print("✅ Successfully retrieved token info:")
            print(f"   - ID: {token_info['ID']}")
            if 'Name' in token_info:
                print(f"   - Name: {token_info['Name']}")
            if 'Policies' in token_info:
                print(f"   - Policies: {', '.join([p['Name'] for p in token_info['Policies']])}")
        else:
            print("❌ Failed to retrieve token info or token not found")
    except Exception as e:
        print(f"❌ Exception during ACL info: {str(e)}")
    
    # List tokens (may require higher privileges)
    try:
        tokens = client.acl.list()
        print("✅ Successfully listed ACL tokens:")
        for token in tokens:
            print(f"   - {token['ID']} ({token.get('Name', 'Unnamed')})")
    except Exception as e:
        print(f"ℹ️ ACL token listing requires management privileges: {str(e)}")

def main():
    """Main function to run all tests."""
    print("🚀 Starting MCP Server Test Script")
    
    client = setup_consul_client()
    
    # Run all test functions
    test_kv_operations(client)
    test_catalog_operations(client)
    test_health_operations(client)
    test_agent_operations(client)
    test_session_operations(client)
    test_acl_operations(client)
    
    print("\n✨ MCP Server Test Script Completed!")

if __name__ == "__main__":
    main()