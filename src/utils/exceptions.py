"""
Custom exceptions for Finviz MCP Server
"""


class ToolError(Exception):
    """Base exception for tool-related errors."""


class ValidationError(ToolError):
    """Exception raised for input validation errors."""


class NetworkError(ToolError):
    """Exception raised for network-related errors."""


class DataError(ToolError):
    """Exception raised for data processing errors."""
