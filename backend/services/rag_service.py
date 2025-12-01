import os
from typing import List
from dotenv import load_dotenv
from ollama import Client
from neo4j_graphrag.indexes import create_vector_index
from neo4j_graphrag.retrievers import VectorCypherRetriever
from langchain_community.chat_models import ChatOllama
from langchain_ollama import OllamaEmbeddings
from neo4j_graphrag.generation import GraphRAG, RagTemplate

from neo4j import GraphDatabase

load_dotenv()

URI = os.getenv("NEO4J_URI")
USER = os.getenv("NEO4J_USER")
PASS = os.getenv("NEO4J_PASSWORD")

if not URI or not USER or not PASS:
    raise ValueError("Missing required Neo4j configuration.")

driver = GraphDatabase.driver(URI, auth=(USER, PASS))

async def answer_query(database: str, query_text: str, top_k: int = 5, use_graph_retriever: bool = True) -> str:
    
    create_vector_index(
        driver, 
        name="text_embeddings", 
        label="Chunk", 
        embedding_property="embedding", 
        dimensions=768, 
        similarity_fn="cosine"
    )

    simple_retrieval_query = """
    MATCH (node:Chunk)
    RETURN node.text AS info
    """
    
    graph_retrieval_apoc = """
    MATCH (n)
    WHERE n.id CONTAINS $query 
       OR coalesce(n.description, '') CONTAINS $query
       OR coalesce(n.name, '') CONTAINS $query
       OR any(prop IN keys(n) WHERE prop <> 'id' AND prop <> 'embedding' AND toString(n[prop]) CONTAINS $query)
    
    OPTIONAL MATCH p = (n)-[r]-(m)
    WITH n, COLLECT(DISTINCT {node: m, rel: type(r)}) AS neighbors
    
    RETURN 
        labels(n)[0] + ' - ' + n.id + ': ' + coalesce(n.description, coalesce(n.name, '')) + '\n' +
        CASE WHEN size(neighbors) > 0 THEN
            'Related entities:\n' +
            apoc.text.join(
                [x IN neighbors |
                    '  - ' + x.rel + ' -> ' + labels(x.node)[0] + ' - ' + x.node.id + ': ' + coalesce(x.node.description, coalesce(x.node.name, ''))
                ],
                '\n'
            )
        ELSE ''
        END AS info
    """

    # Choose retrieval query based on what's available
    # Start with simple, then try graph-based
    retrieval_query = simple_retrieval_query  # Change this based on your needs

    embedder = OllamaEmbeddings(model="nomic-embed-text")

    graph_retriever = VectorCypherRetriever(
        driver,
        index_name="text_embeddings",
        embedder=embedder,
        retrieval_query=retrieval_query,
    )

    llm = ChatOllama(model="gemma3:1b")

    rag_template = RagTemplate(template='''Answer the Question using the following Context. Only respond with information mentioned in the Context. 
provide a focused and concise answer based on the question asked. Do not include extra things

# Question:
{query_text}

# Context:
{context}

# Answer:
''', expected_inputs=['query_text', 'context'])



    rag = GraphRAG(retriever=graph_retriever, llm=llm, prompt_template=rag_template)

    print('rag_template', rag_template)
    
    try:
        response = rag.search(
            query_text=query_text, 
            retriever_config={"top_k": top_k}
        ).answer
        print(f"Generated answer: {response}")
        return response
    except Exception as e:
        print(f"Error during RAG search: {e}")
        raise