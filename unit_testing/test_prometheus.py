#!/usr/bin/env python3
"""
Test script for Prometheus MCP functions.
This script tests all functions and tools in the Prometheus MCP server.
"""

import os
import sys
import asyncio
from datetime import datetime, timedelta
import logging

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

try:
    # Import the MCP server
    from servers.prometheus.prometheus_mcp import *
    logger.info("Successfully imported Prometheus MCP")
except ImportError as e:
    logger.error(f"Failed to import Prometheus MCP: {e}")
    sys.exit(1)

async def test_resources():
    """Test all resource endpoints"""
    logger.info("Testing resource endpoints...")
    
    # Test get_targets
    try:
        targets = await get_targets()
        logger.info(f"Successfully fetched targets, length: {len(targets)}")
    except Exception as e:
        logger.error(f"Error testing get_targets: {e}")
    
    # Test get_alerts
    try:
        alerts = await get_alerts()
        logger.info(f"Successfully fetched alerts")
    except Exception as e:
        logger.error(f"Error testing get_alerts: {e}")
    
    # Test get_rules
    try:
        rules = await get_rules()
        logger.info(f"Successfully fetched rules")
    except Exception as e:
        logger.error(f"Error testing get_rules: {e}")
    
    # Test get_metrics with a common pattern
    try:
        metrics = await get_metrics("up")
        logger.info(f"Successfully fetched metrics for pattern 'up'")
    except Exception as e:
        logger.error(f"Error testing get_metrics: {e}")

async def test_tools():
    """Test all tool functions"""
    logger.info("Testing tool functions...")
    
    # Test query_metrics with a simple instant query
    try:
        result = await query_metrics(query="up")
        logger.info(f"Successfully tested query_metrics (instant)")
    except Exception as e:
        logger.error(f"Error testing query_metrics (instant): {e}")
    
    # Test query_metrics with a range query
    try:
        now = datetime.now()
        end = now.isoformat()
        start = (now - timedelta(hours=1)).isoformat()
        result = await query_metrics(
            query="up", 
            start=start,
            end=end,
            step="15s"
        )
        logger.info(f"Successfully tested query_metrics (range)")
    except Exception as e:
        logger.error(f"Error testing query_metrics (range): {e}")
    
    # Test find_metrics
    try:
        result = await find_metrics(pattern=".*")
        logger.info(f"Successfully tested find_metrics")
    except Exception as e:
        logger.error(f"Error testing find_metrics: {e}")
    
    # Test analyze_metric
    try:
        result = await analyze_metric(metric="up", duration="1h")
        logger.info(f"Successfully tested analyze_metric")
    except Exception as e:
        logger.error(f"Error testing analyze_metric: {e}")
    
    # Test get_targets_health
    try:
        result = await get_targets_health()
        logger.info(f"Successfully tested get_targets_health")
    except Exception as e:
        logger.error(f"Error testing get_targets_health: {e}")
    
    # Test get_alert_summary
    try:
        result = await get_alert_summary()
        logger.info(f"Successfully tested get_alert_summary")
    except Exception as e:
        logger.error(f"Error testing get_alert_summary: {e}")

async def test_prompts():
    """Test all prompt functions"""
    logger.info("Testing prompt functions...")
    
    # Test analyze_system_health prompt
    try:
        prompt = analyze_system_health()
        logger.info(f"Successfully tested analyze_system_health prompt")
    except Exception as e:
        logger.error(f"Error testing analyze_system_health prompt: {e}")
    
    # Test performance_analysis prompt
    try:
        prompt = performance_analysis(service="node-exporter")
        logger.info(f"Successfully tested performance_analysis prompt")
    except Exception as e:
        logger.error(f"Error testing performance_analysis prompt: {e}")
    
    # Test capacity_planning prompt
    try:
        prompt = capacity_planning(service="node-exporter")
        logger.info(f"Successfully tested capacity_planning prompt")
    except Exception as e:
        logger.error(f"Error testing capacity_planning prompt: {e}")
    
    # Test alert_investigation prompt
    try:
        prompt = alert_investigation(alert_name="HighCPULoad")
        logger.info(f"Successfully tested alert_investigation prompt")
    except Exception as e:
        logger.error(f"Error testing alert_investigation prompt: {e}")

async def test_sample_workflow():
    """Test a sample workflow that connects multiple functions"""
    logger.info("Testing a sample workflow...")
    
    try:
        # Step 1: Check if any targets are down
        targets_health = await get_targets_health()
        logger.info("Step 1: Checked targets health")
        
        # Step 2: Look for any firing alerts
        alerts = await get_alert_summary(state="firing")
        logger.info("Step 2: Checked firing alerts")
        
        # Step 3: Analyze some important metrics
        cpu_usage = await analyze_metric(metric="node_cpu_seconds_total", duration="1h")
        logger.info("Step 3: Analyzed CPU usage")
        
        memory_usage = await analyze_metric(metric="node_memory_MemAvailable_bytes", duration="1h")
        logger.info("Step 4: Analyzed memory usage")
        
        logger.info("Successfully completed sample workflow")
    except Exception as e:
        logger.error(f"Error in sample workflow: {e}")

async def main():
    """Main function to run all tests"""
    logger.info("Starting Prometheus MCP tests")
    
    try:
        await test_resources()
        await test_tools()
        await test_prompts()
        await test_sample_workflow()
        
        logger.info("All tests completed")
    except Exception as e:
        logger.error(f"Error during testing: {e}")

if __name__ == "__main__":
    asyncio.run(main())