"""
Knowledge Graph Service
Builds and queries entity relationships for fact verification and context.
"""
from typing import Dict, List, Optional, Set, Tuple
from dataclasses import dataclass, field
from collections import defaultdict
import json
import os

@dataclass
class Entity:
    """Represents an entity in the knowledge graph."""
    id: str
    name: str
    entity_type: str  # person, place, organization, event, concept
    attributes: Dict = field(default_factory=dict)
    aliases: List[str] = field(default_factory=list)

@dataclass
class Relationship:
    """Represents a relationship between entities."""
    source_id: str
    target_id: str
    relation_type: str  # located_in, founded_by, part_of, etc.
    properties: Dict = field(default_factory=dict)

class KnowledgeGraphService:
    """
    In-memory knowledge graph for Malaysian context.
    Stores entities and relationships for fact verification.
    """
    
    def __init__(self, persist_path: str = "data/knowledge_graph.json"):
        self.entities: Dict[str, Entity] = {}
        self.relationships: List[Relationship] = []
        self.entity_index: Dict[str, Set[str]] = defaultdict(set)  # type -> entity_ids
        self.persist_path = persist_path
        
        # Load existing graph
        self._load()
        
        # Initialize with Malaysian facts
        self._seed_malaysian_knowledge()
    
    def _seed_malaysian_knowledge(self):
        """Seed graph with basic Malaysian knowledge."""
        if len(self.entities) > 0:
            return  # Already seeded
        
        # States
        states = [
            ("johor", "Johor", "state", {"capital": "Johor Bahru"}),
            ("kedah", "Kedah", "state", {"capital": "Alor Setar"}),
            ("kelantan", "Kelantan", "state", {"capital": "Kota Bharu"}),
            ("melaka", "Melaka", "state", {"capital": "Melaka City"}),
            ("negeri_sembilan", "Negeri Sembilan", "state", {"capital": "Seremban"}),
            ("pahang", "Pahang", "state", {"capital": "Kuantan"}),
            ("penang", "Penang", "state", {"capital": "George Town"}),
            ("perak", "Perak", "state", {"capital": "Ipoh"}),
            ("perlis", "Perlis", "state", {"capital": "Kangar"}),
            ("sabah", "Sabah", "state", {"capital": "Kota Kinabalu"}),
            ("sarawak", "Sarawak", "state", {"capital": "Kuching"}),
            ("selangor", "Selangor", "state", {"capital": "Shah Alam"}),
            ("terengganu", "Terengganu", "state", {"capital": "Kuala Terengganu"}),
        ]
        
        for sid, name, etype, attrs in states:
            self.add_entity(Entity(
                id=sid,
                name=name,
                entity_type=etype,
                attributes=attrs
            ))
        
        # Landmarks
        landmarks = [
            ("klcc", "KLCC", "landmark", {"height": "452m", "floors": "88"}),
            ("batu_caves", "Batu Caves", "landmark", {"type": "temple", "religion": "Hindu"}),
            ("langkawi", "Langkawi", "landmark", {"type": "island", "state": "Kedah"}),
        ]
        
        for lid, name, etype, attrs in landmarks:
            self.add_entity(Entity(
                id=lid,
                name=name,
                entity_type=etype,
                attributes=attrs
            ))
        
        # Relationships
        self.add_relationship(Relationship("langkawi", "kedah", "located_in"))
        self.add_relationship(Relationship("klcc", "selangor", "located_in"))
        
        self._save()
    
    def add_entity(self, entity: Entity) -> str:
        """Add an entity to the graph."""
        self.entities[entity.id] = entity
        self.entity_index[entity.entity_type].add(entity.id)
        return entity.id
    
    def add_relationship(self, relationship: Relationship):
        """Add a relationship to the graph."""
        self.relationships.append(relationship)
    
    def get_entity(self, entity_id: str) -> Optional[Entity]:
        """Retrieve an entity by ID."""
        return self.entities.get(entity_id)
    
    def search_entities(
        self, 
        query: str, 
        entity_type: Optional[str] = None
    ) -> List[Entity]:
        """Search entities by name or alias."""
        query_lower = query.lower()
        results = []
        
        candidates = (
            self.entity_index.get(entity_type, set()) 
            if entity_type 
            else set(self.entities.keys())
        )
        
        for eid in candidates:
            entity = self.entities[eid]
            if query_lower in entity.name.lower():
                results.append(entity)
            elif any(query_lower in alias.lower() for alias in entity.aliases):
                results.append(entity)
        
        return results
    
    def get_related_entities(
        self, 
        entity_id: str, 
        relation_type: Optional[str] = None
    ) -> List[Tuple[Entity, str]]:
        """Get entities related to the given entity."""
        results = []
        
        for rel in self.relationships:
            if rel.source_id == entity_id:
                if relation_type is None or rel.relation_type == relation_type:
                    target = self.get_entity(rel.target_id)
                    if target:
                        results.append((target, rel.relation_type))
            elif rel.target_id == entity_id:
                if relation_type is None or rel.relation_type == relation_type:
                    source = self.get_entity(rel.source_id)
                    if source:
                        results.append((source, f"inverse_{rel.relation_type}"))
        
        return results
    
    def verify_fact(self, subject: str, predicate: str, obj: str) -> Dict:
        """
        Verify a fact triple (subject, predicate, object).
        Example: ("Langkawi", "located_in", "Kedah")
        """
        # Find subject entity
        subject_entities = self.search_entities(subject)
        if not subject_entities:
            return {"verified": None, "reason": "Subject not found in knowledge graph"}
        
        subject_entity = subject_entities[0]
        
        # Check relationships
        related = self.get_related_entities(subject_entity.id)
        for entity, rel_type in related:
            if predicate.lower() in rel_type.lower():
                if obj.lower() in entity.name.lower():
                    return {"verified": True, "evidence": f"{subject_entity.name} {rel_type} {entity.name}"}
        
        # Check attributes
        for attr_key, attr_value in subject_entity.attributes.items():
            if predicate.lower() in attr_key.lower():
                if obj.lower() in str(attr_value).lower():
                    return {"verified": True, "evidence": f"{subject_entity.name}.{attr_key} = {attr_value}"}
        
        return {"verified": False, "reason": "Fact not found in knowledge graph"}
    
    def _save(self):
        """Persist graph to disk."""
        os.makedirs(os.path.dirname(self.persist_path), exist_ok=True)
        
        data = {
            "entities": {
                eid: {
                    "id": e.id,
                    "name": e.name,
                    "entity_type": e.entity_type,
                    "attributes": e.attributes,
                    "aliases": e.aliases
                }
                for eid, e in self.entities.items()
            },
            "relationships": [
                {
                    "source_id": r.source_id,
                    "target_id": r.target_id,
                    "relation_type": r.relation_type,
                    "properties": r.properties
                }
                for r in self.relationships
            ]
        }
        
        with open(self.persist_path, "w") as f:
            json.dump(data, f, indent=2)
    
    def _load(self):
        """Load graph from disk."""
        if not os.path.exists(self.persist_path):
            return
        
        try:
            with open(self.persist_path, "r") as f:
                data = json.load(f)
            
            for eid, edata in data.get("entities", {}).items():
                self.entities[eid] = Entity(**edata)
                self.entity_index[edata["entity_type"]].add(eid)
            
            for rdata in data.get("relationships", []):
                self.relationships.append(Relationship(**rdata))
        except Exception:
            pass  # Start fresh if load fails

    def get_stats(self) -> Dict:
        """Get graph statistics."""
        return {
            "total_entities": len(self.entities),
            "total_relationships": len(self.relationships),
            "entity_types": {k: len(v) for k, v in self.entity_index.items()}
        }


# Global instance
knowledge_graph = KnowledgeGraphService()
