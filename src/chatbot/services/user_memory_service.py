"""
User Memory Service - v2 Phase 2: Personalization
==================================================
Provides persistent user memory using vector storage.
Stores conversation summaries, preferences, and facts about users.
"""

import logging
import json
import hashlib
from typing import Optional, Dict, Any, List
from datetime import datetime
from pathlib import Path
import os

logger = logging.getLogger(__name__)


class UserMemory:
    """
    Represents a single user's memory store.
    Contains facts, preferences, and conversation history.
    """
    
    def __init__(self, user_id: str):
        self.user_id = user_id
        self.facts: List[Dict[str, Any]] = []  # Known facts about user
        self.preferences: Dict[str, Any] = {}  # User preferences
        self.conversation_summaries: List[Dict[str, Any]] = []  # Past conversation summaries
        self.created_at: str = datetime.now().isoformat()
        self.last_active: str = self.created_at
        
    def add_fact(self, fact: str, source: str = "conversation", confidence: float = 0.8):
        """Add a fact about the user."""
        self.facts.append({
            "fact": fact,
            "source": source,
            "confidence": confidence,
            "added_at": datetime.now().isoformat()
        })
        self.last_active = datetime.now().isoformat()
        
    def add_preference(self, key: str, value: Any):
        """Set a user preference."""
        self.preferences[key] = {
            "value": value,
            "updated_at": datetime.now().isoformat()
        }
        self.last_active = datetime.now().isoformat()
        
    def add_conversation_summary(self, summary: str, topics: List[str] = None):
        """Add a conversation summary."""
        self.conversation_summaries.append({
            "summary": summary,
            "topics": topics or [],
            "created_at": datetime.now().isoformat()
        })
        # Keep only last 20 summaries
        if len(self.conversation_summaries) > 20:
            self.conversation_summaries = self.conversation_summaries[-20:]
        self.last_active = datetime.now().isoformat()
        
    def get_context_for_llm(self, max_facts: int = 10, max_summaries: int = 5) -> str:
        """Get user context formatted for LLM injection."""
        context_parts = []
        
        # Add recent facts
        if self.facts:
            recent_facts = self.facts[-max_facts:]
            facts_text = "\n".join([f"- {f['fact']}" for f in recent_facts])
            context_parts.append(f"[User Facts]\n{facts_text}")
        
        # Add preferences
        if self.preferences:
            prefs_text = "\n".join([f"- {k}: {v['value']}" for k, v in self.preferences.items()])
            context_parts.append(f"[User Preferences]\n{prefs_text}")
        
        # Add recent conversation summaries
        if self.conversation_summaries:
            recent_summaries = self.conversation_summaries[-max_summaries:]
            summaries_text = "\n".join([f"- {s['summary']}" for s in recent_summaries])
            context_parts.append(f"[Previous Conversations]\n{summaries_text}")
        
        return "\n\n".join(context_parts) if context_parts else ""
    
    def to_dict(self) -> Dict[str, Any]:
        """Serialize to dictionary."""
        return {
            "user_id": self.user_id,
            "facts": self.facts,
            "preferences": self.preferences,
            "conversation_summaries": self.conversation_summaries,
            "created_at": self.created_at,
            "last_active": self.last_active
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "UserMemory":
        """Deserialize from dictionary."""
        memory = cls(data["user_id"])
        memory.facts = data.get("facts", [])
        memory.preferences = data.get("preferences", {})
        memory.conversation_summaries = data.get("conversation_summaries", [])
        memory.created_at = data.get("created_at", memory.created_at)
        memory.last_active = data.get("last_active", memory.last_active)
        return memory


class UserMemoryService:
    """
    Service for managing user memories.
    Provides persistence and retrieval of user-specific information.
    """
    
    def __init__(self, storage_dir: Optional[str] = None):
        """
        Initialize memory service.
        
        Args:
            storage_dir: Directory for storing memory files (default: data/user_memories)
        """
        self.storage_dir = Path(storage_dir or os.path.join(
            os.path.dirname(__file__), 
            '..', '..', 'data', 'user_memories'
        ))
        self.storage_dir.mkdir(parents=True, exist_ok=True)
        
        self._cache: Dict[str, UserMemory] = {}
        self._vector_index = None  # For future semantic search
        
    def _get_storage_path(self, user_id: str) -> Path:
        """Get file path for user memory."""
        # Hash user_id for privacy
        safe_id = hashlib.sha256(user_id.encode()).hexdigest()[:16]
        return self.storage_dir / f"{safe_id}.json"
    
    def get_or_create_memory(self, user_id: str) -> UserMemory:
        """Get existing memory or create new one."""
        # Check cache first
        if user_id in self._cache:
            return self._cache[user_id]
        
        # Try to load from disk
        storage_path = self._get_storage_path(user_id)
        if storage_path.exists():
            try:
                with open(storage_path, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                memory = UserMemory.from_dict(data)
                self._cache[user_id] = memory
                return memory
            except Exception as e:
                logger.error(f"Failed to load user memory: {e}")
        
        # Create new memory
        memory = UserMemory(user_id)
        self._cache[user_id] = memory
        return memory
    
    def save_memory(self, user_id: str):
        """Persist user memory to disk."""
        if user_id not in self._cache:
            return
        
        memory = self._cache[user_id]
        storage_path = self._get_storage_path(user_id)
        
        try:
            with open(storage_path, 'w', encoding='utf-8') as f:
                json.dump(memory.to_dict(), f, indent=2, ensure_ascii=False)
            logger.debug(f"Saved memory for user: {user_id[:8]}...")
        except Exception as e:
            logger.error(f"Failed to save user memory: {e}")
    
    def add_user_fact(self, user_id: str, fact: str, source: str = "conversation"):
        """Add a fact about a user."""
        memory = self.get_or_create_memory(user_id)
        memory.add_fact(fact, source)
        self.save_memory(user_id)
    
    def set_user_preference(self, user_id: str, key: str, value: Any):
        """Set a user preference."""
        memory = self.get_or_create_memory(user_id)
        memory.add_preference(key, value)
        self.save_memory(user_id)
    
    def add_conversation_summary(self, user_id: str, summary: str, topics: List[str] = None):
        """Add a conversation summary for a user."""
        memory = self.get_or_create_memory(user_id)
        memory.add_conversation_summary(summary, topics)
        self.save_memory(user_id)
    
    def get_user_context(self, user_id: str) -> str:
        """Get user context for LLM injection."""
        memory = self.get_or_create_memory(user_id)
        return memory.get_context_for_llm()
    
    def extract_facts_from_message(self, user_id: str, message: str) -> List[str]:
        """
        Extract facts from a user message.
        This is a simple heuristic-based extraction.
        For better results, use an LLM to extract facts.
        """
        extracted = []
        message_lower = message.lower()
        
        # Name patterns
        name_patterns = [
            (r"(?:nama saya|my name is|i'm|i am)\s+(\w+)", "User's name is {0}"),
            (r"(?:panggil saya|call me)\s+(\w+)", "User prefers to be called {0}"),
        ]
        
        # Preference patterns
        pref_patterns = [
            (r"(?:saya suka|i like|i love)\s+(.+?)(?:\.|$)", "User likes {0}"),
            (r"(?:saya tak suka|i don't like|i hate)\s+(.+?)(?:\.|$)", "User dislikes {0}"),
            (r"(?:saya dari|i'm from|i come from)\s+(\w+)", "User is from {0}"),
        ]
        
        import re
        
        for pattern, template in name_patterns + pref_patterns:
            matches = re.findall(pattern, message_lower)
            for match in matches:
                if isinstance(match, tuple):
                    match = match[0]
                fact = template.format(match.strip())
                extracted.append(fact)
        
        # Auto-add extracted facts
        for fact in extracted:
            self.add_user_fact(user_id, fact, source="auto_extract")
        
        return extracted
    
    def get_all_users(self) -> List[str]:
        """Get list of all user IDs with stored memories."""
        users = []
        for path in self.storage_dir.glob("*.json"):
            try:
                with open(path, 'r') as f:
                    data = json.load(f)
                users.append(data.get("user_id", path.stem))
            except:
                pass
        return users
    
    def delete_user_memory(self, user_id: str):
        """Delete all memory for a user."""
        # Remove from cache
        if user_id in self._cache:
            del self._cache[user_id]
        
        # Remove from disk
        storage_path = self._get_storage_path(user_id)
        if storage_path.exists():
            storage_path.unlink()
            logger.info(f"Deleted memory for user: {user_id[:8]}...")


# Singleton instance
_memory_service: Optional[UserMemoryService] = None


def get_user_memory_service() -> UserMemoryService:
    """Get or create singleton UserMemoryService."""
    global _memory_service
    if _memory_service is None:
        _memory_service = UserMemoryService()
    return _memory_service
