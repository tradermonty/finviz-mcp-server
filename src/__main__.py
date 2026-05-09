#!/usr/bin/env python3
"""
Finviz MCP Server entry point
"""

import os
import sys

# プロジェクトルートをPythonパスに追加
project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, project_root)

from src.server import cli_main  # noqa: E402

if __name__ == "__main__":
    cli_main()
