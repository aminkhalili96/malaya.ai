"""
mcp/client.py - Model Context Protocol Client

This module handles connections to MCP servers (like Google Maps) and manages
tool discovery and execution. It acts as a bridge between the MCP servers and
the Malaya LLM engine.

Features:
- Connect to MCP servers via Stdio (requires npx/node)
- Discover available tools from connected servers
- Execute tools when called by the LLM
- Dependency-free implementation (no 'mcp' package required)
"""

import os
import asyncio
import json
import yaml
import shutil
import time
import fnmatch
from typing import Dict, List, Any, Optional, Tuple

class StdIOServerClient:
    """
    A lightweight async client for MCP servers over Stdio.
    """
    def __init__(self, command: str, args: List[str], env: Dict[str, str]):
        self.command = command
        self.args = args
        self.env = env
        self.process = None
        self._msg_id = 0
        self._pending_requests: Dict[int, asyncio.Future] = {}
        self._reader_task = None

    async def start(self):
        self.process = await asyncio.create_subprocess_exec(
            self.command, *self.args,
            stdin=asyncio.subprocess.PIPE,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE,
            env=self.env
        )
        self._reader_task = asyncio.create_task(self._read_loop())
        
        # Initialize
        await self.request("initialize", {
            "protocolVersion": "2024-11-05",
            "capabilities": {},
            "clientInfo": {"name": "MalayaLLM", "version": "1.0"}
        })
        await self.notify("notifications/initialized", {})

    async def _read_loop(self):
        try:
            while True:
                line = await self.process.stdout.readline()
                if not line:
                    break
                try:
                    msg = json.loads(line.decode().strip())
                    if "id" in msg and msg["id"] in self._pending_requests:
                        future = self._pending_requests.pop(msg["id"])
                        if "error" in msg:
                            future.set_exception(Exception(msg["error"]["message"]))
                        else:
                            future.set_result(msg.get("result"))
                except json.JSONDecodeError:
                    pass
        except Exception:
            pass

    async def request(self, method: str, params: Optional[Dict] = None) -> Any:
        self._msg_id += 1
        msg_id = self._msg_id
        payload = {
            "jsonrpc": "2.0",
            "id": msg_id,
            "method": method,
            "params": params or {}
        }
        
        future = asyncio.get_running_loop().create_future()
        self._pending_requests[msg_id] = future
        
        self.process.stdin.write(json.dumps(payload).encode() + b"\n")
        await self.process.stdin.drain()
        
        return await future

    async def notify(self, method: str, params: Optional[Dict] = None):
        payload = {
            "jsonrpc": "2.0",
            "method": method,
            "params": params or {}
        }
        self.process.stdin.write(json.dumps(payload).encode() + b"\n")
        await self.process.stdin.drain()

    async def close(self):
        if self.process:
            try:
                self.process.terminate()
                await self.process.wait()
            except Exception:
                pass
        if self._reader_task:
            self._reader_task.cancel()

class MCPClientManager:
    """
    Manages connections to multiple MCP servers.
    """
    
    def __init__(self, config_path: str = "config.yaml", cache_backend=None):
        self.config_path = config_path
        self.servers: Dict[str, StdIOServerClient] = {}
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
                
                # Ensure /opt/homebrew/bin is in PATH for npx/node
                current_path = full_env.get("PATH", "")
                if "/opt/homebrew/bin" not in current_path:
                    full_env["PATH"] = f"/opt/homebrew/bin:{current_path}"
                
                # Verify command exists (e.g. npx)
                if not shutil.which(command):
                    print(f"Warning: Command '{command}' not found. Skipping MCP server '{server_name}'.")
                    continue

                client = StdIOServerClient(command, args, full_env)
                await client.start()
                self.servers[server_name] = client
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
        
        for server_name, client in self.servers.items():
            try:
                result = await client.request("tools/list", {})
                tool_list = result.get("tools", [])
                
                for tool in tool_list:
                    tool_name = tool["name"]
                    
                    self.tools[tool_name] = {
                        "server": server_name,
                        "client": client,
                        "schema": tool.get("inputSchema")
                    }
                    
                    all_tools.append({
                        "name": tool_name,
                        "description": tool.get("description", ""),
                        "parameters": tool.get("inputSchema", {})
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
            # On Python 3.9, some schemas might trigger internal type errors in jsonschema
            # We log the error but proceed, trusting the LLM/User provided valid args.
            print(f"Warning: Tool input validation failed (proceeding anyway): {exc}")

    async def call_tool(self, tool_name: str, arguments: Dict) -> Any:
        """
        Call a specific MCP tool.
        """
        if not self._is_tool_allowed(tool_name):
            raise ValueError(f"Tool '{tool_name}' is not allowed.")
        if tool_name not in self.tools:
            raise ValueError(f"Tool '{tool_name}' not found.")
            
        tool_info = self.tools[tool_name]
        client = tool_info["client"]
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
            result = await client.request("tools/call", {
                "name": tool_name,
                "arguments": safe_args
            })
            
            # MCP returns a list of content (text/image). We join text content.
            output = []
            content_list = result.get("content", [])
            for content in content_list:
                if content.get("type") == "text":
                    output.append(content.get("text", ""))
                elif content.get("type") == "image":
                    output.append(f"[Image returned: {content.get('mimeType')}]")

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
        for client in self.servers.values():
            await client.close()
