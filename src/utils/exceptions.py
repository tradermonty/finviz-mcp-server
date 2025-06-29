"""
Custom exceptions for Finviz MCP Server
"""

class ToolError(Exception):
    """Base exception for tool-related errors."""
    pass

class ValidationError(ToolError):
    """Exception raised for input validation errors."""
    pass

class NetworkError(ToolError):
    """Exception raised for network-related errors."""
    pass

class DataError(ToolError):
    """Exception raised for data processing errors."""
    pass 