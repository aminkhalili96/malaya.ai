"""
Shared Conversations & Prompt Library Service
Community features for sharing and discovering prompts.
"""
import os
import json
import hashlib
from typing import Dict, List, Optional
from datetime import datetime, timedelta

class SharedConversationService:
    """
    Manages shared conversations with public links.
    """
    
    def __init__(self, storage_path: str = "data/shared_conversations.json"):
        self.storage_path = storage_path
        self.conversations: Dict[str, Dict] = {}
        self._load()
    
    def _load(self):
        """Load shared conversations from storage."""
        if os.path.exists(self.storage_path):
            try:
                with open(self.storage_path, "r") as f:
                    self.conversations = json.load(f)
            except Exception:
                self.conversations = {}
    
    def _save(self):
        """Save to storage."""
        os.makedirs(os.path.dirname(self.storage_path), exist_ok=True)
        with open(self.storage_path, "w") as f:
            json.dump(self.conversations, f, indent=2)
    
    def create_share_link(
        self,
        conversation_id: str,
        messages: List[Dict],
        title: Optional[str] = None,
        expires_days: int = 30
    ) -> Dict:
        """
        Create a shareable link for a conversation.
        """
        # Generate share ID
        share_id = hashlib.sha256(
            f"{conversation_id}:{datetime.now().isoformat()}".encode()
        ).hexdigest()[:12]
        
        # Store conversation
        self.conversations[share_id] = {
            "conversation_id": conversation_id,
            "title": title or "Shared Conversation",
            "messages": messages,
            "created_at": datetime.now().isoformat(),
            "expires_at": (datetime.now() + timedelta(days=expires_days)).isoformat(),
            "view_count": 0
        }
        
        self._save()
        
        return {
            "share_id": share_id,
            "share_url": f"/share/{share_id}",
            "expires_at": self.conversations[share_id]["expires_at"]
        }
    
    def get_shared_conversation(self, share_id: str) -> Optional[Dict]:
        """Retrieve a shared conversation."""
        if share_id not in self.conversations:
            return None
        
        conv = self.conversations[share_id]
        
        # Check expiration
        if datetime.fromisoformat(conv["expires_at"]) < datetime.now():
            del self.conversations[share_id]
            self._save()
            return None
        
        # Increment view count
        conv["view_count"] += 1
        self._save()
        
        return conv
    
    def delete_share(self, share_id: str) -> bool:
        """Delete a shared conversation."""
        if share_id in self.conversations:
            del self.conversations[share_id]
            self._save()
            return True
        return False


class PromptLibraryService:
    """
    Community prompt library for discovering and sharing prompts.
    """
    
    CATEGORIES = [
        "productivity",
        "writing",
        "coding",
        "learning",
        "creative",
        "business",
        "malaysian",
        "fun",
    ]
    
    def __init__(self, storage_path: str = "data/prompt_library.json"):
        self.storage_path = storage_path
        self.prompts: Dict[str, Dict] = {}
        self._load()
        self._seed_defaults()
    
    def _load(self):
        """Load prompt library."""
        if os.path.exists(self.storage_path):
            try:
                with open(self.storage_path, "r") as f:
                    self.prompts = json.load(f)
            except Exception:
                self.prompts = {}
    
    def _save(self):
        """Save prompt library."""
        os.makedirs(os.path.dirname(self.storage_path), exist_ok=True)
        with open(self.storage_path, "w") as f:
            json.dump(self.prompts, f, indent=2)
    
    def _seed_defaults(self):
        """Seed with default Malaysian prompts."""
        if self.prompts:
            return
        
        defaults = [
            {
                "title": "Malaysian Food Recommendation",
                "prompt": "Recommend the best local {food_type} in {location}. Include mamak stalls and hidden gems. Mention price range in MYR.",
                "category": "malaysian",
                "variables": ["food_type", "location"]
            },
            {
                "title": "Manglish Email Writer",
                "prompt": "Write a professional but friendly email to {recipient} about {topic}. Start with 'Hi Boss' if appropriate. Keep Malaysian business culture in mind.",
                "category": "business",
                "variables": ["recipient", "topic"]
            },
            {
                "title": "Code Explanation in Manglish",
                "prompt": "Explain this code like you're a Malaysian programmer chatting at mamak: {code}",
                "category": "coding",
                "variables": ["code"]
            },
            {
                "title": "Travel Itinerary Generator",
                "prompt": "Create a {days}-day itinerary for {location}. Include local food spots, best times to visit attractions, and budget tips in MYR.",
                "category": "malaysian",
                "variables": ["days", "location"]
            },
            {
                "title": "Study Notes Summarizer",
                "prompt": "Summarize these notes into key points for exam revision. Use bullet points and highlight important terms: {notes}",
                "category": "learning",
                "variables": ["notes"]
            },
        ]
        
        for i, prompt_data in enumerate(defaults):
            prompt_id = f"default_{i}"
            self.prompts[prompt_id] = {
                **prompt_data,
                "id": prompt_id,
                "author": "Malaya LLM",
                "created_at": datetime.now().isoformat(),
                "uses": 0,
                "likes": 0
            }
        
        self._save()
    
    def add_prompt(
        self,
        title: str,
        prompt: str,
        category: str,
        author: str = "anonymous",
        variables: List[str] = None
    ) -> Dict:
        """Add a new prompt to the library."""
        prompt_id = hashlib.md5(f"{title}:{prompt}".encode()).hexdigest()[:10]
        
        if category not in self.CATEGORIES:
            category = "fun"
        
        self.prompts[prompt_id] = {
            "id": prompt_id,
            "title": title,
            "prompt": prompt,
            "category": category,
            "author": author,
            "variables": variables or [],
            "created_at": datetime.now().isoformat(),
            "uses": 0,
            "likes": 0
        }
        
        self._save()
        return self.prompts[prompt_id]
    
    def get_prompt(self, prompt_id: str) -> Optional[Dict]:
        """Get a prompt by ID."""
        if prompt_id in self.prompts:
            self.prompts[prompt_id]["uses"] += 1
            self._save()
            return self.prompts[prompt_id]
        return None
    
    def search_prompts(
        self,
        query: str = None,
        category: str = None,
        limit: int = 10
    ) -> List[Dict]:
        """Search prompts."""
        results = list(self.prompts.values())
        
        if category:
            results = [p for p in results if p["category"] == category]
        
        if query:
            query_lower = query.lower()
            results = [
                p for p in results
                if query_lower in p["title"].lower() or query_lower in p["prompt"].lower()
            ]
        
        # Sort by popularity
        results.sort(key=lambda x: x["uses"] + x["likes"], reverse=True)
        
        return results[:limit]
    
    def like_prompt(self, prompt_id: str) -> bool:
        """Like a prompt."""
        if prompt_id in self.prompts:
            self.prompts[prompt_id]["likes"] += 1
            self._save()
            return True
        return False
    
    def get_categories(self) -> List[str]:
        """Get all categories."""
        return self.CATEGORIES
    
    def get_popular(self, limit: int = 5) -> List[Dict]:
        """Get most popular prompts."""
        prompts = list(self.prompts.values())
        prompts.sort(key=lambda x: x["uses"] + x["likes"], reverse=True)
        return prompts[:limit]


# Global instances
shared_conversations = SharedConversationService()
prompt_library = PromptLibraryService()
