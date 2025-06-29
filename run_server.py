#!/usr/bin/env python3
"""
Convenient entry point to run the Finviz MCP Server
"""

import asyncio
import sys
import os

# Add project root to Python path
project_root = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, project_root)

from src.server import main

if __name__ == "__main__":
    print("Starting Finviz MCP Server...")
    print("Press Ctrl+C to stop the server")
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("\nServer stopped by user")
    except Exception as e:
        print(f"Error starting server: {e}")
        sys.exit(1)