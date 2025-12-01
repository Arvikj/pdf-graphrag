"""
Script to run evaluation on your GraphRAG system.

Usage:
    python evaluation/run_evaluation.py
    python evaluation/run_evaluation.py --quick  # Quick test with mock data
"""

import os
import sys

# Add parent directory to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import networkx as nx
from evaluation import GraphRAGEvaluator, EvaluationConfig
from evaluation.dataset import load_test_cases_from_json


def run_evaluation():
    """Run comprehensive evaluation on the GraphRAG system."""
    
    # Initialize configuration
    config = EvaluationConfig(
        top_k_values=[1, 3, 5, 10],
        use_llm_judge=True,
        evaluate_graph_metrics=True,
        output_dir="evaluation/results"
    )
    
    # Initialize evaluator
    evaluator = GraphRAGEvaluator(config)
    
    print("=" * 60)
    print("GRAPHRAG EVALUATION SYSTEM")
    print("=" * 60)
    
    # Load document chunks
    print("\nLoading document chunks...")
    chunks = []
    chunks_path = "chunks/chunks.md"
    if os.path.exists(chunks_path):
        with open(chunks_path, 'r', encoding='utf-8') as f:
            content = f.read()
        # Split by chunk markers
        raw_chunks = content.split("# Chunk")
        for chunk in raw_chunks:
            if chunk.strip():
                # Remove the chunk number and clean up
                lines = chunk.strip().split('\n', 1)
                if len(lines) > 1:
                    chunk_text = lines[1].strip().replace('---', '').strip()
                    if chunk_text:
                        chunks.append(chunk_text)
        print(f"  Loaded {len(chunks)} document chunks")
    else:
        print(f"  Warning: Chunks file not found at {chunks_path}")
    
    # Load graph data
    print("\nLoading graph data...")
    graph = nx.DiGraph()
    
    graph_data_path = "results/graph_data.json"
    if os.path.exists(graph_data_path):
        import json
        with open(graph_data_path, 'r', encoding='utf-8') as f:
            graph_data = json.load(f)
        
        # Build graph from data
        for node in graph_data.get("nodes", []):
            node_id = node.get("id")
            props = node.get("properties", {})
            graph.add_node(node_id, label=node.get("label"), **props)
        
        for edge in graph_data.get("relationships", []):
            graph.add_edge(
                edge.get("source_id"), 
                edge.get("target_id"), 
                relationship=edge.get("type", "related_to"),
                **edge.get("properties", {})
            )
        print(f"  Loaded graph with {len(graph.nodes())} nodes and {len(graph.edges())} edges")
    else:
        print(f"  Warning: Graph data not found at {graph_data_path}")
    
    # Load test cases
    test_cases_path = "evaluation/dataset/ground_truth.json"
    if os.path.exists(test_cases_path):
        test_cases = load_test_cases_from_json(test_cases_path)
        print(f"\nLoaded {len(test_cases)} test cases from ground truth file")
    else:
        print("\nNo ground truth file found!")
        return
    
    # Prepare evaluation data
    queries = []
    retrieved_chunks_list = []
    retrieved_entities_list = []
    extracted_relationships_list = []
    contexts = []
    
    print("\nProcessing queries...")
    print("-" * 60)
    
    for idx, tc in enumerate(test_cases):
        query = tc.query
        print(f"\n[{idx+1}/{len(test_cases)}] Query: {query}")
        
        # Retrieve relevant chunks based on keyword matching
        query_words = set(word.lower() for word in query.split() if len(word) > 2)
        
        # Score chunks by relevance
        chunk_scores = []
        for i, chunk in enumerate(chunks):
            chunk_lower = chunk.lower()
            score = sum(1 for word in query_words if word in chunk_lower)
            if score > 0:
                chunk_scores.append((score, i, chunk))
        
        # Sort by score and get top chunks
        chunk_scores.sort(reverse=True, key=lambda x: x[0])
        retrieved_chunk_texts = [c[2] for c in chunk_scores[:5]] if chunk_scores else chunks[:3]
        
        print(f"  Retrieved {len(retrieved_chunk_texts)} relevant chunks")
        
        # Get entities from graph that match query keywords
        matched_entities = []
        for node_id, node_data in graph.nodes(data=True):
            node_name = node_data.get("name", "").lower()
            node_desc = node_data.get("description", "").lower()
            
            # Check if any query word matches node name or description
            for word in query_words:
                if word in node_name or word in node_desc or node_name in word:
                    entity_name = node_data.get("name", node_id)
                    if entity_name not in matched_entities:
                        matched_entities.append(entity_name)
                    break
        
        # If no keyword matches, get entities from relevant chunks
        if not matched_entities and retrieved_chunk_texts:
            chunk_text = " ".join(retrieved_chunk_texts).lower()
            for node_id, node_data in graph.nodes(data=True):
                node_name = node_data.get("name", "").lower()
                if node_name and node_name in chunk_text:
                    entity_name = node_data.get("name", node_id)
                    if entity_name not in matched_entities:
                        matched_entities.append(entity_name)
        
        print(f"  Retrieved entities: {matched_entities[:5]}")
        
        # Get relationships involving these entities
        relationships = []
        for u, v, edge_data in graph.edges(data=True):
            u_name = graph.nodes[u].get("name", u)
            v_name = graph.nodes[v].get("name", v)
            if any(ent.lower() in u_name.lower() or ent.lower() in v_name.lower() 
                   for ent in matched_entities):
                relationships.append((
                    u_name,
                    edge_data.get("relationship", "related_to"),
                    v_name
                ))
        
        print(f"  Retrieved relationships: {len(relationships)}")
        
        queries.append(query)
        retrieved_chunks_list.append(retrieved_chunk_texts)
        retrieved_entities_list.append(matched_entities)
        extracted_relationships_list.append(relationships)
        contexts.append(" ".join(retrieved_chunk_texts))
    
    # Run evaluation
    print("\n" + "=" * 60)
    print("Running evaluation metrics with LLM judge...")
    print("=" * 60)
    
    report = evaluator.evaluate_batch(
        queries=queries,
        retrieved_chunks_list=retrieved_chunks_list,
        retrieved_entities_list=retrieved_entities_list,
        extracted_relationships_list=extracted_relationships_list,
        graph=graph,
        test_cases=test_cases,
        contexts=contexts
    )
    
    # Print and save results
    evaluator.print_summary(report)
    report_path = evaluator.save_report(report)
    
    print(f"\nEvaluation complete! Report saved to: {report_path}")


def run_quick_evaluation():
    """
    Run a quick evaluation without loading the full RAG system.
    Useful for testing the evaluation framework itself.
    """
    print("=" * 60)
    print("QUICK EVALUATION TEST")
    print("=" * 60)
    
    # Initialize evaluator with LLM disabled for quick test
    config = EvaluationConfig(
        use_llm_judge=False,
        evaluate_graph_metrics=True,
        output_dir="evaluation/results"
    )
    evaluator = GraphRAGEvaluator(config)
    
    # Create mock data
    print("\nCreating mock test data...")
    
    queries = [
        "What is machine learning?",
        "How does natural language processing work?",
        "What are the applications of AI?"
    ]
    
    retrieved_chunks = [
        [
            "Machine learning is a subset of artificial intelligence that enables systems to learn from data.",
            "ML algorithms can improve their performance over time without being explicitly programmed.",
            "Deep learning is a type of machine learning using neural networks.",
            "Supervised learning uses labeled training data.",
            "Unsupervised learning finds patterns in unlabeled data."
        ],
        [
            "Natural language processing (NLP) is a branch of AI focused on human language.",
            "NLP enables computers to understand, interpret, and generate human language.",
            "Key NLP tasks include sentiment analysis, translation, and text summarization.",
            "Transformers have revolutionized NLP since 2017.",
            "BERT and GPT are popular NLP models."
        ],
        [
            "AI applications include healthcare diagnostics and treatment planning.",
            "Autonomous vehicles use AI for navigation and decision making.",
            "AI powers recommendation systems in streaming platforms.",
            "Financial services use AI for fraud detection.",
            "AI assists in drug discovery and development."
        ]
    ]
    
    retrieved_entities = [
        ["machine learning", "artificial intelligence", "deep learning", "neural networks"],
        ["natural language processing", "NLP", "transformers", "BERT", "GPT"],
        ["AI", "healthcare", "autonomous vehicles", "recommendation systems"]
    ]
    
    relationships = [
        [
            ("machine learning", "subset_of", "artificial intelligence"),
            ("deep learning", "type_of", "machine learning"),
            ("neural networks", "used_in", "deep learning")
        ],
        [
            ("NLP", "branch_of", "AI"),
            ("transformers", "revolutionized", "NLP"),
            ("BERT", "type_of", "transformer model")
        ],
        [
            ("AI", "applied_in", "healthcare"),
            ("AI", "powers", "autonomous vehicles"),
            ("AI", "enables", "recommendation systems")
        ]
    ]
    
    # Create a simple test graph
    print("Building test graph...")
    graph = nx.DiGraph()
    
    # Add nodes and edges
    all_entities = set()
    for entity_list in retrieved_entities:
        all_entities.update(entity_list)
    
    for entity in all_entities:
        graph.add_node(entity, type="concept")
    
    for rel_list in relationships:
        for source, rel, target in rel_list:
            if source in graph.nodes() and target in graph.nodes():
                graph.add_edge(source, target, relationship=rel)
            else:
                graph.add_node(source, type="concept")
                graph.add_node(target, type="concept")
                graph.add_edge(source, target, relationship=rel)
    
    print(f"  Graph has {len(graph.nodes())} nodes and {len(graph.edges())} edges")
    
    # Run evaluation
    print("\nRunning evaluation...")
    report = evaluator.evaluate_batch(
        queries=queries,
        retrieved_chunks_list=retrieved_chunks,
        retrieved_entities_list=retrieved_entities,
        extracted_relationships_list=relationships,
        graph=graph
    )
    
    # Print results
    evaluator.print_summary(report)
    
    # Save report
    report_path = evaluator.save_report(report)
    print(f"\nQuick evaluation complete! Report saved to: {report_path}")


def run_with_integration():
    """
    Run evaluation integrated with your actual GraphRAG system.
    This requires the backend services to be properly configured.
    """
    print("=" * 60)
    print("INTEGRATED GRAPHRAG EVALUATION")
    print("=" * 60)
    
    try:
        from backend.services.graphrag import RAGEngine
        from backend.services.pipeline import Pipeline
        import json
        
        # Initialize your system
        print("\nInitializing GraphRAG system...")
        pipeline = Pipeline()
        rag_engine = RAGEngine()
        
        # Load graph data
        graph = nx.DiGraph()
        graph_path = "results/graph_data.json"
        
        if os.path.exists(graph_path):
            with open(graph_path, 'r', encoding='utf-8') as f:
                data = json.load(f)
            
            for node in data.get("nodes", []):
                graph.add_node(node["id"], **node)
            for edge in data.get("edges", []):
                graph.add_edge(edge["source"], edge["target"], **edge)
            
            print(f"  Loaded graph: {len(graph.nodes())} nodes, {len(graph.edges())} edges")
        
        # Initialize evaluator
        config = EvaluationConfig(
            use_llm_judge=True,
            evaluate_graph_metrics=True
        )
        evaluator = GraphRAGEvaluator(config)
        
        # Load test cases
        test_cases = load_test_cases_from_json("evaluation/dataset/ground_truth.json")
        
        # Evaluate each query
        queries = []
        chunks_list = []
        entities_list = []
        rels_list = []
        
        for tc in test_cases:
            print(f"\nProcessing: {tc.query[:50]}...")
            
            # Get retrieval results
            result = rag_engine.query(tc.query)
            
            queries.append(tc.query)
            chunks_list.append(result.get("chunks", []))
            entities_list.append(result.get("entities", []))
            rels_list.append(result.get("relationships", []))
        
        # Run evaluation
        report = evaluator.evaluate_batch(
            queries=queries,
            retrieved_chunks_list=chunks_list,
            retrieved_entities_list=entities_list,
            extracted_relationships_list=rels_list,
            graph=graph,
            test_cases=test_cases
        )
        
        evaluator.print_summary(report)
        evaluator.save_report(report)
        
    except ImportError as e:
        print(f"\nError: Could not import required modules: {e}")
        print("Please ensure all dependencies are installed and the backend is configured.")
        print("\nFalling back to quick evaluation mode...")
        run_quick_evaluation()


if __name__ == "__main__":
    import argparse
    
    parser = argparse.ArgumentParser(description="Run GraphRAG Evaluation")
    parser.add_argument(
        "--quick", 
        action="store_true", 
        help="Run quick evaluation with mock data"
    )
    parser.add_argument(
        "--integrated",
        action="store_true",
        help="Run integrated evaluation with actual GraphRAG system"
    )
    args = parser.parse_args()
    
    if args.quick:
        run_quick_evaluation()
    elif args.integrated:
        run_with_integration()
    else:
        run_evaluation()
