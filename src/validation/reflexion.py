import json
from typing import Dict, Any, Tuple
from .validator import validate_tool_call

def mock_llm_fix(payload: Dict[str, Any], errors: list) -> Dict[str, Any]:
    """
    Simulates an LLM fixing the JSON based on error messages.
    In a real system, this would call chat_model.invoke() with the error context.
    """
    # Simple heuristic fixes for demonstration purposes
    fixed = payload.copy()
    
    for error in errors:
        if "k" in error and "valid integer" in error:
            # Simulate fixing 'k'
            if isinstance(fixed.get('k'), str) and fixed['k'].isdigit():
                fixed['k'] = int(fixed['k'])
        if "q" in error and "required" in error:
            # Simulate adding missing 'q'
            fixed['q'] = "search query inferred from context"
            
    return fixed

def validate_with_reflexion(payload: Dict[str, Any], max_retries: int = 2) -> Tuple[Dict[str, Any], list, list]:
    """
    Implements the Reflexion loop:
    1. Validate
    2. If error, send back to LLM (mocked)
    3. Retry
    Returns: (final_result, final_errors, history_of_attempts)
    """
    attempt = 0
    history = []
    current_payload = payload
    
    while attempt <= max_retries:
        clean, errors = validate_tool_call(current_payload)
        history.append({"attempt": attempt + 1, "payload": current_payload, "errors": errors})
        
        if not errors:
            return clean, [], history
            
        # If we have errors, try to fix
        if attempt < max_retries:
            current_payload = mock_llm_fix(current_payload, errors)
            
        attempt += 1
        
    return {}, errors, history
