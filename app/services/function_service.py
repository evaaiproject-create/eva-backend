"""
Function calling service for Eva.
Provides a framework for registering and executing functions with various capabilities.
"""
from typing import Dict, Callable, Any, Optional
from datetime import datetime
import time
import asyncio

from app.models import FunctionCall, FunctionResponse
from app.services.firestore_service import firestore_service


class FunctionRegistry:
    """
    Registry for callable functions.
    
    Functions can be registered and then called by name with parameters.
    This enables a plugin-like architecture where new capabilities can be added.
    """
    
    def __init__(self):
        """Initialize the function registry."""
        self._functions: Dict[str, Callable] = {}
        self._function_metadata: Dict[str, Dict[str, Any]] = {}
        
        # Register built-in functions
        self._register_builtin_functions()
    
    def register(self, name: str, func: Callable, description: str = "", 
                parameters_schema: Optional[Dict[str, Any]] = None):
        """
        Register a function in the registry.
        
        Args:
            name: Function name (unique identifier)
            func: Callable function
            description: Human-readable description
            parameters_schema: JSON schema for function parameters
        """
        self._functions[name] = func
        self._function_metadata[name] = {
            "description": description,
            "parameters_schema": parameters_schema or {},
            "registered_at": datetime.utcnow()
        }
    
    def get_function(self, name: str) -> Optional[Callable]:
        """
        Get a registered function by name.
        
        Args:
            name: Function name
            
        Returns:
            Callable function or None if not found
        """
        return self._functions.get(name)
    
    def list_functions(self) -> Dict[str, Dict[str, Any]]:
        """
        List all registered functions with their metadata.
        
        Returns:
            Dictionary of function names to metadata
        """
        return self._function_metadata.copy()
    
    async def call(self, function_call: FunctionCall) -> FunctionResponse:
        """
        Execute a function call.
        
        Args:
            function_call: FunctionCall object with name and parameters
            
        Returns:
            FunctionResponse with result or error
        """
        start_time = time.time()
        
        # Get function
        func = self.get_function(function_call.function_name)
        if not func:
            return FunctionResponse(
                success=False,
                error=f"Function '{function_call.function_name}' not found",
                execution_time=time.time() - start_time
            )
        
        # Execute function
        try:
            # Check if function is async
            if asyncio.iscoroutinefunction(func):
                result = await func(**function_call.parameters)
            else:
                result = func(**function_call.parameters)
            
            execution_time = time.time() - start_time
            
            # Log the function call
            await firestore_service.log_function_call(
                function_name=function_call.function_name,
                parameters=function_call.parameters,
                user_id=function_call.user_id,
                result={"success": True, "result": result}
            )
            
            return FunctionResponse(
                success=True,
                result=result if isinstance(result, dict) else {"value": result},
                execution_time=execution_time
            )
            
        except Exception as e:
            execution_time = time.time() - start_time
            
            # Log the failed call
            await firestore_service.log_function_call(
                function_name=function_call.function_name,
                parameters=function_call.parameters,
                user_id=function_call.user_id,
                result={"success": False, "error": str(e)}
            )
            
            return FunctionResponse(
                success=False,
                error=str(e),
                execution_time=execution_time
            )
    
    def _register_builtin_functions(self):
        """Register built-in functions that are always available."""
        
        # Example: Echo function
        def echo(message: str) -> Dict[str, str]:
            """Echo back a message."""
            return {"echo": message}
        
        self.register(
            name="echo",
            func=echo,
            description="Echo back a message",
            parameters_schema={
                "type": "object",
                "properties": {
                    "message": {"type": "string", "description": "Message to echo"}
                },
                "required": ["message"]
            }
        )
        
        # Example: Get current time
        def get_time() -> Dict[str, str]:
            """Get current time."""
            return {
                "timestamp": datetime.utcnow().isoformat(),
                "formatted": datetime.utcnow().strftime("%Y-%m-%d %H:%M:%S UTC")
            }
        
        self.register(
            name="get_time",
            func=get_time,
            description="Get current server time",
            parameters_schema={"type": "object", "properties": {}}
        )
        
        # Example: Calculate function
        def calculate(operation: str, a: float, b: float) -> Dict[str, float]:
            """Perform basic arithmetic operations."""
            operations = {
                "add": lambda x, y: x + y,
                "subtract": lambda x, y: x - y,
                "multiply": lambda x, y: x * y,
                "divide": lambda x, y: x / y if y != 0 else None
            }
            
            if operation not in operations:
                raise ValueError(f"Unknown operation: {operation}")
            
            result = operations[operation](a, b)
            if result is None:
                raise ValueError("Division by zero")
            
            return {"result": result}
        
        self.register(
            name="calculate",
            func=calculate,
            description="Perform basic arithmetic operations",
            parameters_schema={
                "type": "object",
                "properties": {
                    "operation": {
                        "type": "string",
                        "enum": ["add", "subtract", "multiply", "divide"],
                        "description": "Operation to perform"
                    },
                    "a": {"type": "number", "description": "First operand"},
                    "b": {"type": "number", "description": "Second operand"}
                },
                "required": ["operation", "a", "b"]
            }
        )


# Global function registry instance
function_registry = FunctionRegistry()
