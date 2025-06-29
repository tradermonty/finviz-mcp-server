#!/usr/bin/env python3
"""
Finviz MCP Server entry point
"""

import asyncio
import sys
import os

# プロジェクトルートをPythonパスに追加
project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, project_root)

from src.server import main

if __name__ == "__main__":
    asyncio.run(main())