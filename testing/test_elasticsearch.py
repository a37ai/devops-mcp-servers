#!/usr/bin/env python3
import asyncio
import json
import sys
import os
from dotenv import load_dotenv
import logging
from typing import Any, Dict, List, Optional, Union

# Import the MCP tools directly
from mcp.server.fastmcp import FastMCP
from servers.elasticsearch.elasticsearch_mcp import *  # Import all tools from the elk_mcp server

# Setup logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger("elk-mcp-server-test")

# Load environment variables from .env file
load_dotenv()

# Test index name - will be created and deleted during testing
TEST_INDEX_NAME = "test-index-" + str(int(asyncio.get_event_loop().time()))
TEST_DOC_ID = "test-doc-1"
TEST_PIPELINE_ID = "test-pipeline"
TEST_TEMPLATE_NAME = "test-template"

def print_result(operation: str, result: Any):
    """Print the result of an operation in a readable format."""
    logger.info(f"Result of {operation}:")
    
    if isinstance(result, str):
        try:
            parsed = json.loads(result)
            print(json.dumps(parsed, indent=2))
        except:
            print(result)
    else:
        print(json.dumps(result, indent=2) if isinstance(result, dict) else result)
    
    print("-" * 80)

async def test_cluster_apis():
    """Test the cluster-related APIs."""
    logger.info("Testing Cluster APIs...")
    
    # Test cluster_health
    logger.info("Testing cluster_health...")
    result = await cluster_health()
    print_result("cluster_health", result)
    
    # Test cluster_stats
    logger.info("Testing cluster_stats...")
    result = await cluster_stats()
    print_result("cluster_stats", result)
    
    # Test cluster_settings
    logger.info("Testing cluster_settings (get)...")
    result = await cluster_settings(action="get")
    print_result("cluster_settings (get)", result)

async def test_info_apis():
    """Test the information-related APIs."""
    logger.info("Testing Info APIs...")
    
    # Test cluster_info
    logger.info("Testing cluster_info...")
    result = await cluster_info()
    print_result("cluster_info", result)
    
    # Test node_info
    logger.info("Testing node_info...")
    result = await node_info()
    print_result("node_info", result)
    
    # Test node_stats
    logger.info("Testing node_stats...")
    result = await node_stats()
    print_result("node_stats", result)
    
    # Test cat_indices
    logger.info("Testing cat_indices...")
    result = await cat_indices()
    print_result("cat_indices", result)
    
    # Test cat_nodes
    logger.info("Testing cat_nodes...")
    result = await cat_nodes()
    print_result("cat_nodes", result)
    
    # Test cat_aliases
    logger.info("Testing cat_aliases...")
    result = await cat_aliases()
    print_result("cat_aliases", result)

async def test_index_apis():
    """Test the index-related APIs."""
    logger.info("Testing Index APIs...")
    
    # Test create_index
    logger.info(f"Testing create_index ({TEST_INDEX_NAME})...")
    result = await create_index(
        index_name=TEST_INDEX_NAME,
        settings={
            "number_of_shards": 1,
            "number_of_replicas": 0
        },
        mappings={
            "properties": {
                "name": {"type": "text"},
                "age": {"type": "integer"},
                "created": {"type": "date"}
            }
        }
    )
    print_result("create_index", result)
    
    # Test get_index
    logger.info(f"Testing get_index ({TEST_INDEX_NAME})...")
    result = await get_index(index_name=TEST_INDEX_NAME)
    print_result("get_index", result)
    
    # Test get_mapping
    logger.info(f"Testing get_mapping ({TEST_INDEX_NAME})...")
    result = await get_mapping(index_name=TEST_INDEX_NAME)
    print_result("get_mapping", result)
    
    # Test update_mapping
    logger.info(f"Testing update_mapping ({TEST_INDEX_NAME})...")
    result = await update_mapping(
        index_name=TEST_INDEX_NAME,
        properties={
            "email": {"type": "keyword"},
            "description": {"type": "text"}
        }
    )
    print_result("update_mapping", result)
    
    # Test list_indices
    logger.info("Testing list_indices...")
    result = await list_indices()
    print_result("list_indices", result)

async def test_document_apis():
    """Test the document-related APIs."""
    logger.info("Testing Document APIs...")
    
    # Test index_document
    logger.info(f"Testing index_document ({TEST_INDEX_NAME})...")
    document = {
        "name": "Test User",
        "age": 30,
        "email": "test@example.com",
        "description": "This is a test document",
        "created": "2023-01-01T00:00:00Z"
    }
    result = await index_document(
        index_name=TEST_INDEX_NAME,
        document=document,
        id=TEST_DOC_ID,
        refresh="true"
    )
    print_result("index_document", result)
    
    # Test get_document
    logger.info(f"Testing get_document ({TEST_INDEX_NAME}/{TEST_DOC_ID})...")
    result = await get_document(
        index_name=TEST_INDEX_NAME,
        id=TEST_DOC_ID
    )
    print_result("get_document", result)
    
    # Test count_documents
    logger.info(f"Testing count_documents ({TEST_INDEX_NAME})...")
    result = await count_documents(
        index_name=TEST_INDEX_NAME
    )
    print_result("count_documents", result)
    
    # Test bulk_operations with a second document
    logger.info(f"Testing bulk_operations ({TEST_INDEX_NAME})...")
    bulk_ops = (
        '{"index": {"_index": "' + TEST_INDEX_NAME + '", "_id": "test-doc-2"}}\n'
        '{"name": "Another User", "age": 25, "email": "another@example.com", "created": "2023-02-01T00:00:00Z"}\n'
    )
    result = await bulk_operations(
        operations=bulk_ops,
        refresh="true"
    )
    print_result("bulk_operations", result)

async def test_search_apis():
    """Test the search-related APIs."""
    logger.info("Testing Search APIs...")
    
    # Wait a moment for indexing to complete
    await asyncio.sleep(1)
    
    # Test search
    logger.info(f"Testing search ({TEST_INDEX_NAME})...")
    result = await search(
        index_name=TEST_INDEX_NAME,
        query={"match_all": {}}
    )
    print_result("search", result)
    
    # Test simple_search
    logger.info(f"Testing simple_search ({TEST_INDEX_NAME})...")
    result = await simple_search(
        index_name=TEST_INDEX_NAME,
        keyword="test",
        field="name"
    )
    print_result("simple_search", result)
    
    # Test multi_search
    logger.info(f"Testing multi_search ({TEST_INDEX_NAME})...")
    result = await multi_search(
        searches=[
            {
                "index": TEST_INDEX_NAME,
                "query": {"match": {"name": "Test"}}
            },
            {
                "index": TEST_INDEX_NAME,
                "query": {"match": {"name": "Another"}}
            }
        ]
    )
    print_result("multi_search", result)

async def test_ingest_apis():
    """Test the ingest-related APIs."""
    logger.info("Testing Ingest APIs...")
    
    # Test create_pipeline
    logger.info(f"Testing create_pipeline ({TEST_PIPELINE_ID})...")
    result = await create_pipeline(
        pipeline_id=TEST_PIPELINE_ID,
        processors=[
            {
                "set": {
                    "field": "processed",
                    "value": True
                }
            }
        ],
        description="Test pipeline that adds a processed field"
    )
    print_result("create_pipeline", result)
    
    # Test get_pipeline
    logger.info(f"Testing get_pipeline ({TEST_PIPELINE_ID})...")
    result = await get_pipeline(
        pipeline_id=TEST_PIPELINE_ID
    )
    print_result("get_pipeline", result)
    
    # Test simulate_pipeline
    logger.info(f"Testing simulate_pipeline ({TEST_PIPELINE_ID})...")
    result = await simulate_pipeline(
        pipeline_id=TEST_PIPELINE_ID,
        documents=[
            {"name": "Pipeline Test", "age": 40}
        ],
        verbose=True
    )
    print_result("simulate_pipeline", result)

async def test_template_apis():
    """Test the template-related APIs."""
    logger.info("Testing Template APIs...")
    
    # Test create_index_template
    logger.info(f"Testing create_index_template ({TEST_TEMPLATE_NAME})...")
    result = await create_index_template(
        name=TEST_TEMPLATE_NAME,
        index_patterns=["test-*"],
        template={
            "settings": {
                "number_of_shards": 1
            },
            "mappings": {
                "properties": {
                    "field1": {"type": "keyword"},
                    "field2": {"type": "text"}
                }
            }
        },
        version=1,
        priority=100
    )
    print_result("create_index_template", result)
    
    # Test get_index_template
    logger.info(f"Testing get_index_template ({TEST_TEMPLATE_NAME})...")
    result = await get_index_template(
        name=TEST_TEMPLATE_NAME
    )
    print_result("get_index_template", result)

async def cleanup():
    """Clean up resources created during testing."""
    logger.info("Cleaning up test resources...")
    
    # Delete document
    logger.info(f"Deleting test document ({TEST_INDEX_NAME}/{TEST_DOC_ID})...")
    result = await delete_document(
        index_name=TEST_INDEX_NAME,
        id=TEST_DOC_ID
    )
    print_result("delete_document", result)
    
    # Delete template
    logger.info(f"Deleting test template ({TEST_TEMPLATE_NAME})...")
    result = await delete_index_template(
        name=TEST_TEMPLATE_NAME
    )
    print_result("delete_index_template", result)
    
    # Delete pipeline
    logger.info(f"Deleting test pipeline ({TEST_PIPELINE_ID})...")
    result = await delete_pipeline(
        pipeline_id=TEST_PIPELINE_ID
    )
    print_result("delete_pipeline", result)
    
    # Delete index
    logger.info(f"Deleting test index ({TEST_INDEX_NAME})...")
    result = await delete_index(
        index_name=TEST_INDEX_NAME
    )
    print_result("delete_index", result)

async def run_tests():
    """Run all tests."""
    try:
        # First, test cluster and info APIs which don't modify anything
        await test_cluster_apis()
        await test_info_apis()
        
        # Then, test APIs that modify the cluster
        await test_index_apis()
        await test_document_apis()
        await test_search_apis()
        await test_ingest_apis()
        await test_template_apis()
        
        # Finally, clean up
        await cleanup()
        
        logger.info("All tests completed successfully!")
    except Exception as e:
        logger.error(f"Error during tests: {e}")
        # Try to clean up anyway
        try:
            await cleanup()
        except:
            logger.error("Error during cleanup")
        sys.exit(1)

if __name__ == "__main__":
    asyncio.run(run_tests())