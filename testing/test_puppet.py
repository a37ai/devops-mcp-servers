import os
import json
import unittest
from unittest.mock import patch, MagicMock
import pytest
import requests

# Import the puppet_mcp module
import servers.puppet.puppet_mcp as puppet_mcp
from mcp.server.fastmcp import Context


class TestPuppetMCP(unittest.TestCase):
    """Tests for Puppet MCP Server functionality"""

    def setUp(self):
        """Set up test environment"""
        # Set required environment variables for testing
        os.environ["PUPPET_URL"] = "https://puppet.example.com:4433"
        os.environ["PUPPET_AUTH_TOKEN"] = "test_token"
        
        # Create a test context
        self.ctx = Context(
            execution_id="test-execution-id",
            user_id="test-user",
            correlation_id="test-correlation-id"
        )

    @patch('server.puppet.puppet_mcp.requests.request')
    def test_puppet_request(self, mock_request):
        """Test the puppet_request helper function"""
        # Configure the mock response
        mock_response = MagicMock()
        mock_response.json.return_value = {"status": "success"}
        mock_request.return_value = mock_response
        
        # Call the function with test data
        result = puppet_mcp.puppet_request(
            self.ctx,
            "GET",
            "/test-endpoint",
            data={"key": "value"},
            params={"param": "value"}
        )
        
        # Verify the function called requests with the right parameters
        mock_request.assert_called_once_with(
            method="GET",
            url="https://puppet.example.com:4433/test-endpoint",
            json={"key": "value"},
            params={"param": "value"},
            headers={"X-Authentication": "test_token"}
        )
        
        # Verify the result
        assert result == {"status": "success"}
    
    @patch('server.puppet.puppet_mcp.puppet_request')
    def test_list_environments(self, mock_puppet_request):
        """Test list_environments resource"""
        # Configure the mock response
        mock_puppet_request.return_value = {
            "environments": {
                "production": {},
                "development": {},
                "testing": {}
            }
        }
        
        # Call the function
        result = puppet_mcp.list_environments(self.ctx)
        
        # Verify the puppet_request was called correctly
        mock_puppet_request.assert_called_once_with(
            self.ctx,
            "GET",
            "/puppet/v3/environments"
        )
        
        # Verify the result
        result_data = json.loads(result)
        assert "environments" in result_data
        assert "production" in result_data["environments"]
        assert "development" in result_data["environments"]
        assert "testing" in result_data["environments"]
    
    @patch('server.puppet.puppet_mcp.puppet_request')
    def test_get_node(self, mock_puppet_request):
        """Test get_node resource"""
        # Configure the mock response
        mock_puppet_request.return_value = {
            "name": "test-node.example.com",
            "environment": "production",
            "parameters": {"role": "webserver"}
        }
        
        # Call the function
        result = puppet_mcp.get_node("test-node.example.com", self.ctx)
        
        # Verify the puppet_request was called correctly
        mock_puppet_request.assert_called_once_with(
            self.ctx,
            "GET",
            "/puppet/v3/nodes/test-node.example.com"
        )
        
        # Verify the result
        result_data = json.loads(result)
        assert result_data["name"] == "test-node.example.com"
        assert result_data["environment"] == "production"
        assert result_data["parameters"]["role"] == "webserver"
    
    @patch('server.puppet.puppet_mcp.puppet_request')
    def test_get_facts(self, mock_puppet_request):
        """Test get_facts resource"""
        # Configure the mock response
        mock_puppet_request.return_value = {
            "name": "test-node.example.com",
            "values": {
                "os": {"name": "Ubuntu", "release": {"full": "20.04"}},
                "memory": {"system": {"total": "16.00 GB"}}
            }
        }
        
        # Call the function
        result = puppet_mcp.get_facts("test-node.example.com", self.ctx)
        
        # Verify the puppet_request was called correctly
        mock_puppet_request.assert_called_once_with(
            self.ctx,
            "GET",
            "/puppet/v3/facts/test-node.example.com"
        )
        
        # Verify the result
        result_data = json.loads(result)
        assert result_data["name"] == "test-node.example.com"
        assert result_data["values"]["os"]["name"] == "Ubuntu"
        assert result_data["values"]["memory"]["system"]["total"] == "16.00 GB"
    
    @patch('server.puppet.puppet_mcp.puppet_request')
    def test_run_puppet(self, mock_puppet_request):
        """Test run_puppet tool"""
        # Configure the mock response
        mock_puppet_request.return_value = {
            "job": {
                "id": "123",
                "status": "running"
            }
        }
        
        # Call the function
        result = puppet_mcp.run_puppet(
            ["node1.example.com", "node2.example.com"],
            self.ctx,
            environment="production",
            noop=True
        )
        
        # Verify the puppet_request was called correctly
        mock_puppet_request.assert_called_once_with(
            self.ctx,
            "POST",
            "/orchestrator/v1/command/deploy",
            data={
                "environment": "production",
                "scope": {
                    "nodes": ["node1.example.com", "node2.example.com"]
                },
                "noop": True
            }
        )
        
        # Verify the result
        result_data = json.loads(result)
        assert result_data["job"]["id"] == "123"
        assert result_data["job"]["status"] == "running"
    
    @patch('server.puppet.puppet_mcp.puppet_request')
    def test_query_puppetdb(self, mock_puppet_request):
        """Test query_puppetdb tool"""
        # Configure the mock response
        mock_puppet_request.return_value = [
            {"certname": "node1.example.com", "facts": {"os": "Ubuntu"}},
            {"certname": "node2.example.com", "facts": {"os": "CentOS"}}
        ]
        
        # Test query string
        test_query = '["=", "facts.os.name", "Ubuntu"]'
        
        # Call the function
        result = puppet_mcp.query_puppetdb(test_query, self.ctx)
        
        # Verify the puppet_request was called correctly
        mock_puppet_request.assert_called_once_with(
            self.ctx,
            "GET",
            "/pdb/query/v4",
            params={"query": test_query}
        )
        
        # Verify the result
        result_data = json.loads(result)
        assert len(result_data) == 2
        assert result_data[0]["certname"] == "node1.example.com"
        assert result_data[1]["certname"] == "node2.example.com"
    
    def test_missing_environment_variables(self):
        """Test behavior when environment variables are missing"""
        # Save current environment variables
        puppet_url = os.environ.get("PUPPET_URL")
        puppet_token = os.environ.get("PUPPET_AUTH_TOKEN")
        
        try:
            # Clear environment variables
            if "PUPPET_URL" in os.environ:
                del os.environ["PUPPET_URL"]
            if "PUPPET_AUTH_TOKEN" in os.environ:
                del os.environ["PUPPET_AUTH_TOKEN"]
            
            # Test puppet_request with missing variables
            with pytest.raises(ValueError, match="PUPPET_AUTH_TOKEN environment variable is not set"):
                puppet_mcp.puppet_request(self.ctx, "GET", "/test")
        
        finally:
            # Restore environment variables
            if puppet_url:
                os.environ["PUPPET_URL"] = puppet_url
            if puppet_token:
                os.environ["PUPPET_AUTH_TOKEN"] = puppet_token
    
    @patch('server.puppet.puppet_mcp.requests.request')
    def test_request_error_handling(self, mock_request):
        """Test error handling in puppet_request"""
        # Configure the mock to raise an exception
        mock_request.side_effect = requests.exceptions.RequestException("Test error")
        
        # Test error handling
        with pytest.raises(requests.exceptions.RequestException, match="Test error"):
            puppet_mcp.puppet_request(self.ctx, "GET", "/test-endpoint")


# Function to run all tests
def run_tests():
    # Run all tests in the class
    unittest.main(argv=['first-arg-is-ignored'], exit=False)


if __name__ == "__main__":
    run_tests()