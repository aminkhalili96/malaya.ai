"""
Tool Service - v2 Phase 2: Function Calling / Agent Tools
==========================================================
Provides tool execution framework for the chatbot.
Supports: Calculator, Web Search, Code Execution, Custom Tools.
"""

import logging
import json
import re
import math
from typing import Optional, Dict, Any, List, Callable, Union
from dataclasses import dataclass, field
from datetime import datetime

logger = logging.getLogger(__name__)


@dataclass
class ToolDefinition:
    """Definition of a callable tool."""
    name: str
    description: str
    parameters: Dict[str, Any]
    function: Callable
    requires_confirmation: bool = False
    

@dataclass
class ToolResult:
    """Result of a tool execution."""
    tool_name: str
    success: bool
    result: Any
    error: Optional[str] = None
    execution_time_ms: float = 0.0


class ToolRegistry:
    """Registry for managing available tools."""
    
    def __init__(self):
        self._tools: Dict[str, ToolDefinition] = {}
        self._register_builtin_tools()
    
    def _register_builtin_tools(self):
        """Register built-in tools."""
        
        # Calculator tool
        self.register(ToolDefinition(
            name="calculator",
            description="Perform mathematical calculations. Supports basic arithmetic, powers, sqrt, etc.",
            parameters={
                "type": "object",
                "properties": {
                    "expression": {
                        "type": "string",
                        "description": "Mathematical expression to evaluate (e.g., '2 + 2', 'sqrt(16)', '10 ** 2')"
                    }
                },
                "required": ["expression"]
            },
            function=self._calculate
        ))
        
        # Date/Time tool
        self.register(ToolDefinition(
            name="get_datetime",
            description="Get current date and time in Malaysia timezone.",
            parameters={
                "type": "object",
                "properties": {
                    "format": {
                        "type": "string",
                        "description": "Date format (default: 'full'). Options: 'full', 'date', 'time', 'iso'"
                    }
                }
            },
            function=self._get_datetime
        ))
        
        # Currency converter (simple)
        self.register(ToolDefinition(
            name="currency_convert",
            description="Convert between currencies. Supports MYR, USD, SGD, etc.",
            parameters={
                "type": "object",
                "properties": {
                    "amount": {"type": "number", "description": "Amount to convert"},
                    "from_currency": {"type": "string", "description": "Source currency (e.g., 'USD')"},
                    "to_currency": {"type": "string", "description": "Target currency (e.g., 'MYR')"}
                },
                "required": ["amount", "from_currency", "to_currency"]
            },
            function=self._currency_convert
        ))
        
        # Unit converter
        self.register(ToolDefinition(
            name="unit_convert",
            description="Convert between units (length, weight, temperature).",
            parameters={
                "type": "object",
                "properties": {
                    "value": {"type": "number", "description": "Value to convert"},
                    "from_unit": {"type": "string", "description": "Source unit (e.g., 'km')"},
                    "to_unit": {"type": "string", "description": "Target unit (e.g., 'miles')"}
                },
                "required": ["value", "from_unit", "to_unit"]
            },
            function=self._unit_convert
        ))
    
    def register(self, tool: ToolDefinition):
        """Register a new tool."""
        self._tools[tool.name] = tool
        logger.info(f"Registered tool: {tool.name}")
    
    def get(self, name: str) -> Optional[ToolDefinition]:
        """Get tool by name."""
        return self._tools.get(name)
    
    def list_tools(self) -> List[Dict[str, Any]]:
        """List all available tools in OpenAI function calling format."""
        return [
            {
                "type": "function",
                "function": {
                    "name": tool.name,
                    "description": tool.description,
                    "parameters": tool.parameters
                }
            }
            for tool in self._tools.values()
        ]
    
    def execute(self, tool_name: str, arguments: Dict[str, Any]) -> ToolResult:
        """Execute a tool by name with given arguments."""
        import time
        
        start = time.perf_counter()
        
        tool = self.get(tool_name)
        if not tool:
            return ToolResult(
                tool_name=tool_name,
                success=False,
                result=None,
                error=f"Tool not found: {tool_name}"
            )
        
        try:
            result = tool.function(**arguments)
            execution_time = (time.perf_counter() - start) * 1000
            
            return ToolResult(
                tool_name=tool_name,
                success=True,
                result=result,
                execution_time_ms=execution_time
            )
        except Exception as e:
            logger.error(f"Tool execution failed: {tool_name} - {e}")
            return ToolResult(
                tool_name=tool_name,
                success=False,
                result=None,
                error=str(e)
            )
    
    # Built-in tool implementations
    
    def _calculate(self, expression: str) -> Union[float, str]:
        """Safe mathematical expression evaluator."""
        # Sanitize input
        allowed_chars = set("0123456789+-*/().^ sqrtabcdefghijklmnopqrstuvwxyz_")
        if not all(c in allowed_chars or c.isspace() for c in expression.lower()):
            raise ValueError("Invalid characters in expression")
        
        # Replace common functions
        expr = expression.lower()
        expr = expr.replace("^", "**")
        expr = expr.replace("sqrt", "math.sqrt")
        expr = expr.replace("sin", "math.sin")
        expr = expr.replace("cos", "math.cos")
        expr = expr.replace("tan", "math.tan")
        expr = expr.replace("log", "math.log")
        expr = expr.replace("pi", "math.pi")
        expr = expr.replace("e ", "math.e ")
        
        # Evaluate safely
        try:
            result = eval(expr, {"__builtins__": {}, "math": math}, {})
            return round(result, 10) if isinstance(result, float) else result
        except Exception as e:
            raise ValueError(f"Cannot evaluate expression: {e}")
    
    def _get_datetime(self, format: str = "full") -> str:
        """Get current datetime in Malaysia timezone."""
        from datetime import timezone, timedelta
        
        # Malaysia is UTC+8
        myt = timezone(timedelta(hours=8))
        now = datetime.now(myt)
        
        if format == "date":
            return now.strftime("%d %B %Y")
        elif format == "time":
            return now.strftime("%I:%M %p")
        elif format == "iso":
            return now.isoformat()
        else:  # full
            return now.strftime("%A, %d %B %Y, %I:%M %p MYT")
    
    def _currency_convert(self, amount: float, from_currency: str, to_currency: str) -> Dict[str, Any]:
        """Simple currency conversion with hardcoded rates."""
        # Approximate rates (for demo - real implementation should use API)
        rates_to_myr = {
            "USD": 4.70,
            "EUR": 5.10,
            "GBP": 5.95,
            "SGD": 3.50,
            "JPY": 0.031,
            "CNY": 0.65,
            "MYR": 1.0
        }
        
        from_curr = from_currency.upper()
        to_curr = to_currency.upper()
        
        if from_curr not in rates_to_myr or to_curr not in rates_to_myr:
            raise ValueError(f"Unsupported currency. Supported: {list(rates_to_myr.keys())}")
        
        # Convert to MYR first, then to target
        amount_myr = amount * rates_to_myr[from_curr]
        result = amount_myr / rates_to_myr[to_curr]
        
        return {
            "from": f"{amount:.2f} {from_curr}",
            "to": f"{result:.2f} {to_curr}",
            "rate": f"1 {from_curr} = {rates_to_myr[from_curr]/rates_to_myr[to_curr]:.4f} {to_curr}",
            "note": "Rates are approximate. For accurate rates, check a financial service."
        }
    
    def _unit_convert(self, value: float, from_unit: str, to_unit: str) -> Dict[str, Any]:
        """Convert between common units."""
        conversions = {
            # Length
            ("km", "miles"): lambda x: x * 0.621371,
            ("miles", "km"): lambda x: x * 1.60934,
            ("m", "ft"): lambda x: x * 3.28084,
            ("ft", "m"): lambda x: x * 0.3048,
            ("cm", "inch"): lambda x: x * 0.393701,
            ("inch", "cm"): lambda x: x * 2.54,
            
            # Weight
            ("kg", "lb"): lambda x: x * 2.20462,
            ("lb", "kg"): lambda x: x * 0.453592,
            ("g", "oz"): lambda x: x * 0.035274,
            ("oz", "g"): lambda x: x * 28.3495,
            
            # Temperature
            ("c", "f"): lambda x: (x * 9/5) + 32,
            ("f", "c"): lambda x: (x - 32) * 5/9,
            ("c", "k"): lambda x: x + 273.15,
            ("k", "c"): lambda x: x - 273.15,
        }
        
        key = (from_unit.lower(), to_unit.lower())
        if key not in conversions:
            raise ValueError(f"Unsupported conversion: {from_unit} to {to_unit}")
        
        result = conversions[key](value)
        
        return {
            "from": f"{value} {from_unit}",
            "to": f"{result:.4f} {to_unit}"
        }


class ToolService:
    """
    High-level tool service for the chatbot.
    Manages tool registry and provides easy integration with LLM.
    """
    
    def __init__(self):
        self.registry = ToolRegistry()
    
    def get_tools_for_llm(self) -> List[Dict[str, Any]]:
        """Get tool definitions in LLM-compatible format."""
        return self.registry.list_tools()
    
    def execute_tool_call(self, tool_call: Dict[str, Any]) -> str:
        """
        Execute a tool call from LLM response.
        
        Args:
            tool_call: Dict with 'name' and 'arguments' (as JSON string or dict)
            
        Returns:
            Result as string for LLM context
        """
        name = tool_call.get("name", "")
        args = tool_call.get("arguments", {})
        
        # Parse arguments if string
        if isinstance(args, str):
            try:
                args = json.loads(args)
            except json.JSONDecodeError:
                return f"Error: Invalid arguments JSON"
        
        result = self.registry.execute(name, args)
        
        if result.success:
            if isinstance(result.result, dict):
                return json.dumps(result.result, indent=2)
            return str(result.result)
        else:
            return f"Error: {result.error}"
    
    def add_custom_tool(
        self, 
        name: str, 
        description: str, 
        parameters: Dict[str, Any],
        function: Callable
    ):
        """Add a custom tool to the registry."""
        self.registry.register(ToolDefinition(
            name=name,
            description=description,
            parameters=parameters,
            function=function
        ))


# Singleton instance
_tool_service: Optional[ToolService] = None


def get_tool_service() -> ToolService:
    """Get or create singleton ToolService."""
    global _tool_service
    if _tool_service is None:
        _tool_service = ToolService()
    return _tool_service
