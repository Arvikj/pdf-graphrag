"""
Graph data models for Neo4j ingestion.

Minimal Pydantic models for representing knowledge graph structure.
"""
from typing import Dict, List, Optional
from pydantic import BaseModel, Field


class Node(BaseModel):
    """Represents a graph node/entity."""
    id: str = Field(..., description="Unique identifier for the node")
    label: str = Field(..., description="Node type/label (e.g., 'Person', 'Organization')")
    properties: Dict[str, str] = Field(default_factory=dict, description="Additional node properties")


class Relationship(BaseModel):
    """Represents a relationship between two nodes."""
    source_id: str = Field(..., description="ID of the source node")
    target_id: str = Field(..., description="ID of the target node")
    type: str = Field(..., description="Relationship type (e.g., 'WORKS_AT', 'LOCATED_IN')")
    properties: Dict[str, str] = Field(default_factory=dict, description="Additional relationship properties")


class GraphData(BaseModel):
    """Container for extracted graph data."""
    nodes: List[Node] = Field(default_factory=list, description="List of extracted nodes")
    relationships: List[Relationship] = Field(default_factory=list, description="List of extracted relationships")
