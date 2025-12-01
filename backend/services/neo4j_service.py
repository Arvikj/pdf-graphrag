"""
Neo4j Service - Simplified per Neo4j Python Driver Documentation

Uses driver.execute_query() which is the recommended approach per:
https://neo4j.com/docs/python-manual/current/query-simple/
"""
import os
import logging
from typing import Dict, List, Optional
from neo4j import GraphDatabase

logger = logging.getLogger(__name__)

# Configuration via environment variables
NEO4J_URI = os.getenv("NEO4J_URI", "bolt://localhost:7687")
NEO4J_USER = os.getenv("NEO4J_USER", "neo4j")
NEO4J_PASSWORD = os.getenv("NEO4J_PASSWORD", "password123")


class Neo4jService:
    """Minimal Neo4j service using recommended execute_query() pattern."""
    
    def __init__(self, uri: str = NEO4J_URI, user: str = NEO4J_USER, password: str = NEO4J_PASSWORD):
        self.driver = GraphDatabase.driver(uri, auth=(user, password))
        
    def close(self):
        self.driver.close()
        
    def verify_connection(self) -> bool:
        """Verify Neo4j is reachable."""
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
    
    def ingest_graph(self, graph_data: Dict) -> Dict[str, int]:
        """
        Ingest nodes and relationships into Neo4j using MERGE.
        Per docs: Use execute_query() with parameters for simple operations.
        """
        nodes = graph_data.get("nodes", [])
        relationships = graph_data.get("relationships", [])
        
        # Ingest nodes - MERGE by id with dynamic label
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
        
        # Ingest relationships
        rels_created = 0
        for rel in relationships:
            source_id = rel.get("source_id", "")
            target_id = rel.get("target_id", "")
            if not source_id or not target_id:
                continue
                
            rel_type = rel.get("type", "RELATED_TO").replace(" ", "_").replace("-", "_").upper()
            props = rel.get("properties", {})
            
            self.driver.execute_query(
                f"""
                MATCH (a {{id: $source_id}})
                MATCH (b {{id: $target_id}})
                MERGE (a)-[r:{rel_type}]->(b)
                SET r += $props
                """,
                source_id=source_id,
                target_id=target_id,
                props=props
            )
            rels_created += 1
        
        logger.info(f"Ingested {nodes_created} nodes, {rels_created} relationships")
        return {"nodes_created": nodes_created, "relationships_created": rels_created}
    
    def get_graph(self) -> Dict:
        """Retrieve all nodes and relationships for visualization."""
        # Get nodes
        records, _, _ = self.driver.execute_query(
            "MATCH (n) RETURN n.id AS id, labels(n) AS labels, properties(n) AS props"
        )
        nodes = []
        for record in records:
            props = dict(record["props"])
            props.pop("id", None)
            nodes.append({
                "id": record["id"],
                "label": record["labels"][0] if record["labels"] else "Entity",
                "properties": props
            })
        
        # Get relationships
        records, _, _ = self.driver.execute_query(
            "MATCH (a)-[r]->(b) RETURN a.id AS source, b.id AS target, type(r) AS type, properties(r) AS props"
        )
        relationships = [
            {
                "source_id": r["source"],
                "target_id": r["target"],
                "type": r["type"],
                "properties": dict(r["props"])
            }
            for r in records
        ]
        
        return {"nodes": nodes, "relationships": relationships}
    
    def search_nodes(self, query: str, limit: int = 10) -> List[Dict]:
        """Search nodes by text in id, name, or description."""
        records, _, _ = self.driver.execute_query(
            """
            MATCH (n)
            WHERE toLower(n.id) CONTAINS $query 
               OR toLower(coalesce(n.name, '')) CONTAINS $query
               OR toLower(coalesce(n.description, '')) CONTAINS $query
            RETURN n.id AS id, labels(n) AS labels, properties(n) AS props
            LIMIT $limit
            """,
            query=query.lower(),
            limit=limit
        )
        return [
            {
                "id": r["id"],
                "label": r["labels"][0] if r["labels"] else "Entity",
                "properties": dict(r["props"])
            }
            for r in records
        ]
    
    def get_node_context(self, node_ids: List[str]) -> Dict:
        """Get nodes and their neighbors for RAG context."""
        nodes = []
        relationships = []
        seen = set()
        
        for node_id in node_ids:
            records, _, _ = self.driver.execute_query(
                """
                MATCH (n {id: $node_id})
                OPTIONAL MATCH (n)-[r]-(neighbor)
                RETURN n.id AS nid, labels(n) AS nlabels, properties(n) AS nprops,
                       neighbor.id AS nbid, labels(neighbor) AS nblabels, properties(neighbor) AS nbprops,
                       type(r) AS rtype, properties(r) AS rprops
                """,
                node_id=node_id
            )
            
            for record in records:
                # Add main node
                if record["nid"] and record["nid"] not in seen:
                    seen.add(record["nid"])
                    props = dict(record["nprops"])
                    props.pop("id", None)
                    nodes.append({
                        "id": record["nid"],
                        "label": record["nlabels"][0] if record["nlabels"] else "Entity",
                        "properties": props
                    })
                
                # Add neighbor
                if record["nbid"] and record["nbid"] not in seen:
                    seen.add(record["nbid"])
                    props = dict(record["nbprops"]) if record["nbprops"] else {}
                    props.pop("id", None)
                    nodes.append({
                        "id": record["nbid"],
                        "label": record["nblabels"][0] if record["nblabels"] else "Entity",
                        "properties": props
                    })
                
                # Add relationship
                if record["rtype"] and record["nbid"]:
                    relationships.append({
                        "source_id": record["nid"],
                        "target_id": record["nbid"],
                        "type": record["rtype"],
                        "properties": dict(record["rprops"]) if record["rprops"] else {}
                    })
        
        return {"nodes": nodes, "relationships": relationships}
    
    def get_stats(self) -> Dict:
        """Get node and relationship counts."""
        records, _, _ = self.driver.execute_query("MATCH (n) RETURN count(n) AS nodes")
        node_count = records[0]["nodes"] if records else 0
        
        records, _, _ = self.driver.execute_query("MATCH ()-[r]->() RETURN count(r) AS rels")
        rel_count = records[0]["rels"] if records else 0
        
        return {"node_count": node_count, "relationship_count": rel_count}


# Singleton
_service: Optional[Neo4jService] = None

def get_neo4j_service() -> Neo4jService:
    global _service
    if _service is None:
        _service = Neo4jService()
    return _service
