"""
mcp/client.py - Model Context Protocol Client

This module handles connections to MCP servers (like Google Maps) and manages
tool discovery and execution. It acts as a bridge between the MCP servers and
the Malaya LLM engine.

Features:
- Connect to MCP servers via Stdio (requires npx/node)
- Discover available tools from connected servers
- Execute tools when called by the LLM
- Convert MCP tool definitions to LangChain/LLM compatible format
"""

import os
import asyncio
import json
import yaml
import shutil
import time
import fnmatch
from typing import Dict, List, Any, Optional, Tuple
from mcp import ClientSession, StdioServerParameters
from mcp.client.stdio import stdio_client
from contextlib import AsyncExitStack

class MCPClientManager:
    """
    Manages connections to multiple MCP servers.
    """
    
    def __init__(self, config_path: str = "config.yaml", cache_backend=None):
        self.config_path = config_path
        self.servers: Dict[str, Any] = {}
        self.exit_stack = AsyncExitStack()
        self.tools: Dict[str, Any] = {}
        self.allowed_tools: List[str] = []
        self.tool_arg_limits: Dict[str, int] = {}
        self.tool_cache_ttl = int(os.environ.get("MCP_TOOL_CACHE_TTL", "600"))
        self._tool_cache: Dict[Tuple[str, str], Dict[str, Any]] = {}
        self.cache_backend = cache_backend
        self._load_config()
        
    def _load_config(self):
        """Load MCP server configuration."""
        try:
            with open(self.config_path, "r") as f:
                config = yaml.safe_load(f)
                self.mcp_config = config.get("mcp_servers", {})
                self.allowed_tools = config.get("tool_allowlist", []) or []
                self.tool_arg_limits = config.get("tool_arg_limits", {}) or {}
                if "tool_cache_ttl" in config:
                    self.tool_cache_ttl = int(config.get("tool_cache_ttl", self.tool_cache_ttl))
        except Exception as e:
            print(f"Error loading MCP config: {e}")
            self.mcp_config = {}
            self.allowed_tools = []
            self.tool_arg_limits = {}

    async def connect_all(self):
        """Connect to all configured MCP servers."""
        for server_name, server_config in self.mcp_config.items():
            try:
                command = server_config.get("command")
                args = server_config.get("args", [])
                env = server_config.get("env", {}).copy()
                
                # Resolve environment variables
                for key, value in env.items():
                    if isinstance(value, str) and value.startswith("${") and value.endswith("}"):
                        env_var = value[2:-1]
                        env[key] = os.environ.get(env_var, "")
                
                # Merge with system env
                full_env = os.environ.copy()
                full_env.update(env)
                
                # Verify command exists (e.g. npx)
                if not shutil.which(command):
                    print(f"Warning: Command '{command}' not found. Skipping MCP server '{server_name}'.")
                    continue

                server_params = StdioServerParameters(
                    command=command,
                    args=args,
                    env=full_env
                )
                
                # Start connection manager
                connection = stdio_client(server_params)
                read, write = await self.exit_stack.enter_async_context(connection)
                session = await self.exit_stack.enter_async_context(ClientSession(read, write))
                
                await session.initialize()
                self.servers[server_name] = session
                print(f"Connected to MCP server: {server_name}")
                
            except Exception as e:
                print(f"Failed to connect to MCP server '{server_name}': {e}")

    async def list_tools(self) -> List[Dict]:
        """
        List all available tools from all connected servers.
        Refreshes the internal tools cache.
        """
        all_tools = []
        self.tools = {}
        
        for server_name, session in self.servers.items():
            try:
                response = await session.list_tools()
                
                for tool in response.tools:
                    # Namespace tools to avoid collisions: "server_name__tool_name"
                    # But for google maps, we want clean names if possible.
                    # Let's keep original names but store mapping.
                    tool_name = tool.name
                    
                    self.tools[tool_name] = {
                        "server": server_name,
                        "session": session,
                        "schema": tool.inputSchema
                    }
                    
                    all_tools.append({
                        "name": tool_name,
                        "description": tool.description,
                        "parameters": tool.inputSchema
                    })
            except Exception as e:
                print(f"Error listing tools from '{server_name}': {e}")
                
        return all_tools

    def _is_tool_allowed(self, tool_name: str) -> bool:
        if not self.allowed_tools:
            return True
        return any(fnmatch.fnmatch(tool_name, pattern) for pattern in self.allowed_tools)

    def _limit_tool_args(self, value: Any) -> Any:
        max_string = int(self.tool_arg_limits.get("max_string_chars", 2000))
        max_array = int(self.tool_arg_limits.get("max_array_items", 50))

        if isinstance(value, str):
            return value[:max_string]
        if isinstance(value, list):
            return [self._limit_tool_args(item) for item in value[:max_array]]
        if isinstance(value, dict):
            return {key: self._limit_tool_args(val) for key, val in value.items()}
        return value

    def _validate_tool_args(self, schema: Optional[Dict[str, Any]], arguments: Dict[str, Any]) -> None:
        if not schema:
            return
        try:
            from jsonschema import Draft202012Validator
            Draft202012Validator(schema).validate(arguments)
        except Exception as exc:
            raise ValueError(f"Tool input validation failed: {exc}") from exc

    async def call_tool(self, tool_name: str, arguments: Dict) -> Any:
        """
        Call a specific MCP tool.
        """
        if not self._is_tool_allowed(tool_name):
            raise ValueError(f"Tool '{tool_name}' is not allowed.")
        if tool_name not in self.tools:
            raise ValueError(f"Tool '{tool_name}' not found.")
            
        tool_info = self.tools[tool_name]
        session = tool_info["session"]
        schema = tool_info.get("schema")

        safe_args = self._limit_tool_args(arguments or {})
        self._validate_tool_args(schema, safe_args)

        cache_key = json.dumps({"tool": tool_name, "args": safe_args}, sort_keys=True, ensure_ascii=True)
        if self.cache_backend:
            cached = self.cache_backend.tool_cache_get(cache_key)
            if cached is not None:
                return cached
        else:
            cached = self._tool_cache.get((tool_name, cache_key))
            if cached and (time.time() - cached["ts"]) < self.tool_cache_ttl:
                return cached["value"]
        
        try:
            result = await session.call_tool(tool_name, safe_args)
            
            # MCP returns a list of content (text/image). We join text content.
            output = []
            for content in result.content:
                if content.type == "text":
                    output.append(content.text)
                elif content.type == "image":
                    output.append(f"[Image returned: {content.mimeType}]")

            value = "\n".join(output)
            if self.cache_backend:
                self.cache_backend.tool_cache_set(cache_key, value, self.tool_cache_ttl)
            else:
                self._tool_cache[(tool_name, cache_key)] = {"value": value, "ts": time.time()}
            return value
            
        except Exception as e:
            return f"Error executing tool '{tool_name}': {e}"

    async def close(self):
        """Close all connections."""
        await self.exit_stack.aclose()
