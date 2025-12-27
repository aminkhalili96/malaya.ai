from typing import List, Dict, Any
import json

class ItineraryService:
    """
    Generates structured travel itineraries using Google Maps data.
    """
    
    def __init__(self, llm, mcp_manager):
        self.llm = llm
        self.mcp_manager = mcp_manager
    
    async def generate_itinerary(self, location: str, duration: str, preferences: str) -> Dict:
        """
        Creates a day-by-day itinerary.
        """
        prompt = f"""
        Plan a {duration} trip to {location}.
        Preferences: {preferences}.
        
        Use the Google Maps tools to find real places.
        
        Return the result as a STRICT JSON object with this structure:
        {{
            "title": "Trip Title",
            "days": [
                {{
                    "day": 1,
                    "activities": [
                       {{ "time": "09:00", "place": "Place Name", "description": "..." }}
                    ]
                }}
            ]
        }}
        """
        
        # In a real impl, we'd bind the Maps tools here and let the LLM call them.
        # For this demo, we'll assume the LLM has general knowledge or access to the tools.
        
        response = await self.llm.ainvoke(prompt)
        content = response.content
        
        # Simple cleanup to extract JSON
        if "```json" in content:
            content = content.split("```json")[1].split("```")[0]
            
        return json.loads(content)
