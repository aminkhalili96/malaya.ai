from pydantic import BaseModel, Field, field_validator, model_validator
from typing import Literal, Optional

class ToolCallSchema(BaseModel):
    action: Literal["search", "answer"]
    q: Optional[str] = None
    k: int = Field(default=3, ge=1, le=5)

    @model_validator(mode='before')
    @classmethod
    def preprocess_input(cls, data: dict):
        # Coerce 'k' from string to int if present
        if 'k' in data and isinstance(data['k'], str):
            if data['k'].isdigit():
                data['k'] = int(data['k'])
        
        # Trim strings
        for key, value in data.items():
            if isinstance(value, str):
                data[key] = value.strip()
        return data

    @model_validator(mode='after')
    def validate_logic(self):
        if self.action == 'search':
            if not self.q:
                raise ValueError("Field 'q' is required when action is 'search'")
        return self
