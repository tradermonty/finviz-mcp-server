#!/usr/bin/env python3
"""
Test script for MCP uptrend screener functionality.
Tests the fixed-condition uptrend screener via MCP server.
"""

import asyncio
import json
import logging
import sys
import os
from typing import Dict, Any

# Add project root to path for imports
project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
sys.path.insert(0, project_root)

# Import server as a module
from src.server import server

# Set up logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


async def test_uptrend_screener():
    """Test the uptrend screener via MCP server."""
    try:
        logger.info("📊 Starting uptrend screener test...")
        
        # Call the uptrend screener tool via MCP server
        result = await server.call_tool("uptrend_screener", {"random_string": "test"})
        
        logger.info("✅ Successfully called uptrend screener")
        
        # Print the result
        if isinstance(result, list):
            for item in result:
                if hasattr(item, 'text'):
                    print(f"Result: {item.text}")
                else:
                    print(f"Result: {item}")
        else:
            if hasattr(result, 'text'):
                print(f"Result: {result.text}")
            else:
                print(f"Result: {result}")
                
        return result
        
    except Exception as e:
        logger.error(f"❌ Error testing uptrend screener: {str(e)}")
        logger.error(f"Error type: {type(e)}")
        import traceback
        logger.error(f"Traceback: {traceback.format_exc()}")
        raise


async def test_server_initialization():
    """Test that the MCP server is properly initialized."""
    try:
        logger.info("🔧 Testing server initialization...")
        
        # Check if server is initialized
        if server is None:
            raise ValueError("Server is not initialized")
            
        logger.info(f"Server name: {server.name}")
        
        # List available tools
        tools = await server.list_tools()
        tool_names = [tool.name for tool in tools]
        
        logger.info(f"Available tools: {len(tool_names)}")
        
        # Check if uptrend_screener is available
        if "uptrend_screener" not in tool_names:
            raise ValueError("uptrend_screener tool not found in server")
            
        logger.info("✅ Server initialization test passed")
        
        return True
        
    except Exception as e:
        logger.error(f"❌ Server initialization test failed: {str(e)}")
        raise


async def main():
    """Main test function."""
    print("=" * 60)
    print("🚀 MCP Uptrend Screener Test")
    print("=" * 60)
    
    try:
        # Test 1: Server initialization
        await test_server_initialization()
        print("\n" + "-" * 40)
        
        # Test 2: Uptrend screener functionality
        result = await test_uptrend_screener()
        print("\n" + "-" * 40)
        
        print("✅ All tests completed successfully!")
        
        # Display summary
        print("\n📋 Test Summary:")
        print("- Server initialization: ✅ PASSED")
        print("- Uptrend screener call: ✅ PASSED")
        
        return True
        
    except Exception as e:
        print(f"\n❌ Test failed with error: {str(e)}")
        return False


if __name__ == "__main__":
    # Run the async main function
    success = asyncio.run(main())
    
    # Exit with appropriate code
    sys.exit(0 if success else 1) 