"""
Neo4j Service - Simple implementation following Neo4j Python Driver docs.

Uses driver.execute_query() which is the recommended pattern per:
https://neo4j.com/docs/python-manual/current/query-simple/
"""
import os
import logging
from typing import Dict, List, Optional
from neo4j import GraphDatabase

logger = logging.getLogger(__name__)

# Configuration
NEO4J_URI = os.getenv("NEO4J_URI", "bolt://localhost:7687")
NEO4J_USER = os.getenv("NEO4J_USER", "neo4j")
NEO4J_PASSWORD = os.getenv("NEO4J_PASSWORD", "password123")


class Neo4jService:
    """Simple Neo4j service using execute_query() pattern."""
    
    def __init__(self, uri: str = NEO4J_URI, user: str = NEO4J_USER, password: str = NEO4J_PASSWORD):
        self.driver = GraphDatabase.driver(uri, auth=(user, password))
        
    def close(self):
        self.driver.close()
        
    def verify_connection(self) -> bool:
        """Check if Neo4j is reachable."""
        try:
            self.driver.verify_connectivity()
            return True
        except Exception as e:
            logger.error(f"Neo4j connection failed: {e}")
            return False
    
    def clear_database(self):
        """Delete all nodes and relationships."""
        self.driver.execute_query("MATCH (n) DETACH DELETE n")
        logger.info("Database cleared")
    
    def ingest_graph(self, graph_data: Dict, chunks: List[Dict] = None) -> Dict[str, int]:
        """
        Ingest nodes, relationships, and chunks into Neo4j.
        
        Args:
            graph_data: Dict with "nodes" and "relationships"
            chunks: List of {"id": str, "text": str} for RAG retrieval
        """
        nodes = graph_data.get("nodes", [])
        relationships = graph_data.get("relationships", [])
        
        # 1. Store chunks for RAG retrieval
        chunks_created = 0
        if chunks:
            for chunk in chunks:
                self.driver.execute_query(
                    "MERGE (c:Chunk {id: $id}) SET c.text = $text",
                    id=chunk["id"],
                    text=chunk["text"]
                )
                chunks_created += 1
            logger.info(f"Stored {chunks_created} chunks")
        
        # 2. Create nodes with dynamic labels
        nodes_created = 0
        for node in nodes:
            if not node.get("id"):
                continue
            label = node.get("label", "Entity").replace(" ", "_").replace("-", "_")
            props = {"id": node["id"], **node.get("properties", {})}
            
            self.driver.execute_query(
                f"MERGE (n:{label} {{id: $id}}) SET n += $props",
                id=node["id"],
                props=props
            )
            nodes_created += 1
        
        # 3. Create relationships (only if both nodes exist)
        valid_ids = {node.get("id") for node in nodes if node.get("id")}
        rels_created = 0
        
        for rel in relationships:
            source = rel.get("source_id", "")
            target = rel.get("target_id", "")
            
            if not source or not target:
                continue
            if source not in valid_ids or target not in valid_ids:
                continue
                
            rel_type = rel.get("type", "RELATED_TO").replace(" ", "_").replace("-", "_").upper()
            props = rel.get("properties", {})
            
            self.driver.execute_query(
                f"""
                MATCH (a {{id: $source}})
                MATCH (b {{id: $target}})
                MERGE (a)-[r:{rel_type}]->(b)
                SET r += $props
                """,
                source=source,
                target=target,
                props=props
            )
            rels_created += 1
        
        logger.info(f"Ingested {nodes_created} nodes, {rels_created} relationships")
        return {"nodes_created": nodes_created, "relationships_created": rels_created, "chunks_created": chunks_created}
    
    def get_graph(self) -> Dict:
        """Get all nodes and relationships for visualization."""
        # Get nodes (exclude Chunk nodes - they're for RAG, not visualization)
        records, _, _ = self.driver.execute_query(
            "MATCH (n) WHERE NOT n:Chunk RETURN n.id AS id, labels(n) AS labels, properties(n) AS props"
        )
        nodes = []
        for r in records:
            props = dict(r["props"])
            props.pop("id", None)
            nodes.append({
                "id": r["id"],
                "label": r["labels"][0] if r["labels"] else "Entity",
                "properties": props
            })
        
        # Get relationships (exclude internal chunk relationships)
        records, _, _ = self.driver.execute_query(
            "MATCH (a)-[r]->(b) WHERE NOT a:Chunk AND NOT b:Chunk RETURN a.id AS source, b.id AS target, type(r) AS type"
        )
        relationships = [
            {"source_id": r["source"], "target_id": r["target"], "type": r["type"], "properties": {}}
            for r in records
        ]
        
        return {"nodes": nodes, "relationships": relationships}
    
    def search_chunks(self, query: str, limit: int = 5) -> List[str]:
        """Search chunks by keyword (case-insensitive)."""
        records, _, _ = self.driver.execute_query(
            """
            MATCH (c:Chunk)
            WHERE toLower(c.text) CONTAINS $query
            RETURN c.text AS text
            LIMIT $limit
            """,
            query=query.lower(),
            limit=limit
        )
        return [r["text"] for r in records]
    
    def get_all_chunks(self) -> List[str]:
        """Get all chunk texts (for fallback when search returns nothing)."""
        records, _, _ = self.driver.execute_query(
            "MATCH (c:Chunk) RETURN c.text AS text ORDER BY c.id"
        )
        return [r["text"] for r in records]
    
    def get_stats(self) -> Dict:
        """Get database statistics."""
        records, _, _ = self.driver.execute_query(
            "MATCH (n) WHERE NOT n:Chunk RETURN count(n) AS nodes"
        )
        node_count = records[0]["nodes"] if records else 0
        
        records, _, _ = self.driver.execute_query(
            "MATCH ()-[r]->() RETURN count(r) AS rels"
        )
        rel_count = records[0]["rels"] if records else 0
        
        records, _, _ = self.driver.execute_query(
            "MATCH (c:Chunk) RETURN count(c) AS chunks"
        )
        chunk_count = records[0]["chunks"] if records else 0
        
        return {"node_count": node_count, "relationship_count": rel_count, "chunk_count": chunk_count}


# Singleton instance
_service: Optional[Neo4jService] = None

def get_neo4j_service() -> Neo4jService:
    global _service
    if _service is None:
        _service = Neo4jService()
    return _service
