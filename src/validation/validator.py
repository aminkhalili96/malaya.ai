from typing import Any, Dict, List, Tuple
from pydantic import ValidationError
from .schemas import ToolCallSchema

# Simulated Dead Letter Queue
DLQ = []

def validate_tool_call(payload: Dict[str, Any]) -> Tuple[Dict[str, Any], List[str]]:
    """
    Returns (clean, errors). 'clean' strictly follows the schema with defaults applied.
    - Trim strings; coerce numeric strings to ints.
    - Remove unknown keys.
    - If action=='answer', ignore 'q' if present (no error).
    - On fatal errors (e.g., missing/invalid 'action', or missing/empty 'q' for search), return ({}, errors).
    """
    errors = []
    
    # Layer 1: Deterministic Guardrails (Pydantic)
    try:
        # Pydantic handles coercion and schema enforcement
        # We use model_validate to parse the dict
        # extra='ignore' is default in Pydantic V2 but good to be explicit if we configured otherwise
        # However, to strictly "Remove unknown keys" as per requirement, Pydantic's default behavior 
        # of ignoring extras and only returning defined fields in model_dump() works perfectly.
        
        model = ToolCallSchema.model_validate(payload)
        
        # Convert back to dict to return "clean" data
        # exclude_unset=False ensures defaults like k=3 are included
        clean_data = model.model_dump(exclude_unset=False)
        
        # Special handling: if action is answer, we might want to ensure 'q' is not in the output 
        # if the schema allowed it as optional. 
        # The prompt says: "If action=='answer', ignore 'q' if present (no error)."
        # Our schema has 'q' as Optional. If it's present in payload, it will be in clean_data.
        # Let's explicitly remove it if action is answer to be "clean".
        if clean_data['action'] == 'answer' and 'q' in clean_data:
             clean_data.pop('q', None)
             
        return clean_data, []

    except ValidationError as e:
        # Collect errors
        for err in e.errors():
            loc = ".".join([str(x) for x in err['loc']])
            msg = err['msg']
            errors.append(f"{loc}: {msg}")
        
        # Layer 3: Fail-Stop Mechanism & DLQ
        # (Layer 2 Reflexion would happen outside this function in a real agent loop, 
        # but we log here for the "Fail-Stop" tracking)
        DLQ.append({"payload": payload, "errors": errors})
        
        return {}, errors
    except Exception as e:
        # Catch unexpected errors
        errors.append(str(e))
        DLQ.append({"payload": payload, "errors": errors})
        return {}, errors

def get_dlq():
    return DLQ
