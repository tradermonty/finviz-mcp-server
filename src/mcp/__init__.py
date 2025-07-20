"""Stub implementation of the MCP package used only when the real
`mcp` library is not installed.

The official MCP (Model Context Protocol) Python package is not available on
PyPI yet, but the test-suite expects the following public interface:

* `mcp.server.fastmcp.FastMCP` class with a ``tool`` decorator
* `mcp.types.TextContent` dataclass-like object (with ``type`` and ``text``)

This stub provides those symbols so that importing modules (and the extensive
pytest suite) work in environments where the real package is absent.

If the _real_ MCP package *is* present, importing this module will be ignored
because Python’s import machinery will load the external one first. Therefore
placing this file inside ``src/mcp`` is safe.
"""

from types import ModuleType
import sys
from typing import Callable, Optional

# ----------------------------------------------------------------------------
# Public replacement types
# ----------------------------------------------------------------------------

class TextContent:  # pylint: disable=too-few-public-methods
    """Lightweight replacement for ``mcp.types.TextContent``."""

    def __init__(self, type: str, text: str):  # noqa: A002 (shadow built-in)
        self.type = type
        self.text = text

    def __repr__(self):  # pragma: no cover – str representation only
        return f"<TextContent type={self.type!r} text={self.text[:30]!r}…>"


class _ToolDecorator:  # pylint: disable=too-few-public-methods
    """No-op decorator returned by ``FastMCP.tool``."""

    def __call__(self, func: Optional[Callable] = None):  # noqa: D401
        if func is None:
            # Usage pattern: ``@server.tool()`` – decorator with parentheses
            def wrapper(f):
                return f

            return wrapper
        # Usage pattern: ``@server.tool`` – decorator without parentheses
        return func


class FastMCP:  # pylint: disable=too-few-public-methods
    """Minimal stub replicating the public interface of FastMCP."""

    def __init__(self, _name: str):
        self._name = _name

    def tool(self):  # noqa: D401
        """Return a decorator that leaves the function unchanged."""
        return _ToolDecorator()


# ----------------------------------------------------------------------------
# Dynamically create expected sub-modules so that ``import`` works:
#   import mcp.server.fastmcp as ...
#   import mcp.types as ...
# ----------------------------------------------------------------------------

# mcp.server sub-module tree
server_module = ModuleType("mcp.server")
fastmcp_module = ModuleType("mcp.server.fastmcp")
fastmcp_module.FastMCP = FastMCP  # type: ignore[attr-defined]
server_module.fastmcp = fastmcp_module  # type: ignore[attr-defined]

# Register in sys.modules so that future imports resolve correctly
sys.modules.setdefault("mcp.server", server_module)
sys.modules.setdefault("mcp.server.fastmcp", fastmcp_module)

# mcp.types module
types_module = ModuleType("mcp.types")
types_module.TextContent = TextContent  # type: ignore[attr-defined]
sys.modules.setdefault("mcp.types", types_module)

# Re-export for ``from mcp import FastMCP, TextContent`` convenience
__all__ = ["FastMCP", "TextContent"] 