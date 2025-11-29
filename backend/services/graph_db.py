from neo4j import AsyncGraphDatabase
from neo4j import AsyncSession
from neo4j import SummaryCounters
from pathlib import Path
from typing import List
import json
import asyncio
import os
from dotenv import load_dotenv

load_dotenv()

URI = os.getenv("NEO4J_URI")
USER = os.getenv("NEO4J_USER")
PASS = os.getenv("NEO4J_PASSWORD")

if not URI or not USER or not PASS:
    raise ValueError("Missing required Neo4j configuration.")

driver = AsyncGraphDatabase.driver(URI, auth=(USER, PASS))

async def merge_nodes(session: AsyncSession, nodes: List[dict]) -> List[SummaryCounters]:
    # Need to split the nodes into their unique labels and bulk insert per label
    labels = set(node["label"] for node in nodes)

    results = []
    for label in labels:
        batch = [node for node in nodes if node["label"] == label]

        # Generate query based on label
        query = f"""
            UNWIND $batch as row
            MERGE (n:`{label}` {{id: row.id}})
            SET n += row.properties
        """
        
        result = await session.run(
            query, # type: ignore
            batch=batch
        )
        summary = await result.consume()
        results.append(summary.counters)
    
    return results

async def merge_relationships(session: AsyncSession, relationships: List[dict]) -> List[SummaryCounters]:
    # Bulk insert by relationship type
    types = set(rel["type"] for rel in relationships)

    results = []
    for type in types:
        batch = [rel for rel in relationships if rel["type"] == type]

        # Generate query based on type
        query = f"""
            UNWIND $batch as row
            MATCH (a {{id: row.source_id}})
            MATCH (b {{id: row.target_id}})
            MERGE (a)-[rel:{type}]->(b)
            SET rel += row.properties
        """
        
        result = await session.run(
            query, # type: ignore
            batch=batch
        )
        summary = await result.consume()
        results.append(summary.counters)
    
    return results

async def populate_graph(database: str, graph_data):
    records = await run_cypher("system", "SHOW DATABASES")
    if database not in [record["name"] for record in records]:
        await run_cypher("system", f"CREATE DATABASE {database}")

    async with driver.session(database=database) as session:
        node_counters = await merge_nodes(session, graph_data["nodes"])
        relationship_counters = await merge_relationships(session, graph_data["relationships"])

        print(f"Total nodes created: {sum(counters.nodes_created for counters in node_counters)}")
        print(f"Total relationships created: {sum(counters.relationships_created for counters in relationship_counters)}")

async def run_cypher(database: str, query: str):
    await driver.verify_connectivity()

    async with driver.session(database=database) as session:
        result = await session.run(query) # type: ignore
        return await result.data()

async def list_node_types(database: str):
    records = await run_cypher(
        database,
        """CALL db.labels()""")
    await driver.verify_connectivity()

    async with driver.session(database=database) as session:
        result = await session.run("SHOW DATABASES")
        records = await result.data()
        return [record["name"] for record in records if record["name"] not in ("neo4j", "system")]
                
# Test populating database
# with open(Path("results") / "graph_data.json", "r") as data_file:
#     asyncio.run(populate_graph("insurance", json.load(data_file)))