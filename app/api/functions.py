"""
Function calling API routes.
Enables dynamic function execution framework.
"""
from fastapi import APIRouter, Depends, HTTPException, status
from typing import Dict, Any, List

from app.models import User, FunctionCall, FunctionResponse
from app.utils.dependencies import get_current_user
from app.services.function_service import function_registry
from app.services.firestore_service import firestore_service


router = APIRouter(prefix="/functions", tags=["Functions"])


@router.get("/", response_model=Dict[str, Dict[str, Any]])
async def list_functions(current_user: User = Depends(get_current_user)) -> Dict[str, Dict[str, Any]]:
    """
    List all available functions.
    
    Returns metadata for each registered function including:
    - Description
    - Parameter schema
    - Registration timestamp
    
    This allows clients to discover what functions they can call.
    
    Args:
        current_user: Authenticated user from dependency
        
    Returns:
        Dictionary of function names to metadata
    """
    return function_registry.list_functions()


@router.post("/call", response_model=FunctionResponse)
async def call_function(
    function_name: str,
    parameters: Dict[str, Any] = {},
    device_id: str = None,
    current_user: User = Depends(get_current_user)
) -> FunctionResponse:
    """
    Execute a function by name with given parameters.
    
    This is the core of Eva's function calling framework. Clients can:
    1. Discover available functions via GET /functions
    2. Call any function with appropriate parameters
    3. Get structured responses with results or errors
    
    Function calls are logged to Firestore for history/analytics.
    
    Example usage:
        POST /functions/call
        {
            "function_name": "calculate",
            "parameters": {"operation": "add", "a": 5, "b": 3}
        }
    
    Args:
        function_name: Name of the function to call
        parameters: Function parameters as key-value pairs
        device_id: Optional device identifier
        current_user: Authenticated user from dependency
        
    Returns:
        FunctionResponse with success status, result, and execution time
    """
    function_call = FunctionCall(
        function_name=function_name,
        parameters=parameters,
        user_id=current_user.uid,
        device_id=device_id
    )
    
    response = await function_registry.call(function_call)
    return response


@router.get("/history", response_model=List[Dict[str, Any]])
async def get_function_history(
    limit: int = 50,
    current_user: User = Depends(get_current_user)
) -> List[Dict[str, Any]]:
    """
    Get function call history for the current user.
    
    This shows a log of all functions called by the user,
    useful for:
    - Debugging
    - Analytics
    - Repeating previous actions
    - Understanding usage patterns
    
    Args:
        limit: Maximum number of records to return (default 50)
        current_user: Authenticated user from dependency
        
    Returns:
        List of function call records with timestamps and results
    """
    if limit > 100:
        limit = 100  # Cap at 100 to prevent excessive data transfer
    
    history = await firestore_service.get_user_function_history(current_user.uid, limit)
    return history
