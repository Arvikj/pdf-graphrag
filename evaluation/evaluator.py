"""
Main evaluator that combines all metrics for comprehensive evaluation.
"""

import os
import sys
import json
from datetime import datetime
from typing import Dict, Any, List, Optional
from dataclasses import dataclass, asdict

# Add parent directory to path to import from main project
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from evaluation.config import EvaluationConfig
from evaluation.metrics import (
    ContextRelevanceEvaluator,
    GraphMetricsEvaluator
)
from evaluation.dataset import TestCase, load_test_cases_from_json


@dataclass
class EvaluationReport:
    """Complete evaluation report."""
    timestamp: str
    config: Dict[str, Any]
    context_relevance_metrics: Dict[str, Any]
    graph_metrics: Dict[str, Any]
    summary: Dict[str, float]
    individual_results: List[Dict[str, Any]]


class GraphRAGEvaluator:
    """
    Main evaluator for GraphRAG system.
    Combines context relevance and graph-specific metrics.
    """
    
    def __init__(self, config: Optional[EvaluationConfig] = None):
        """
        Initialize the evaluator.
        
        Args:
            config: Evaluation configuration. Uses defaults if not provided.
        """
        self.config = config or EvaluationConfig()
        
        # Initialize metric evaluators
        self.context_evaluator = ContextRelevanceEvaluator(
            use_llm_judge=self.config.use_llm_judge,
            relevance_threshold=self.config.relevance_threshold,
            llm_model=self.config.llm_model
        )
        
        self.graph_evaluator = GraphMetricsEvaluator(
            use_llm=self.config.use_llm_judge,
            llm_model=self.config.llm_model
        )
    
    def evaluate_single_query(
        self,
        query: str,
        retrieved_chunks: List[str],
        retrieved_entities: List[str],
        extracted_relationships: List[tuple],
        graph,  # NetworkX graph
        test_case: Optional[TestCase] = None,
        context: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Evaluate a single query.
        
        Args:
            query: User query
            retrieved_chunks: Retrieved text chunks
            retrieved_entities: Entities retrieved from graph
            extracted_relationships: Relationships from graph
            graph: NetworkX graph object
            test_case: Optional test case with ground truth
            context: Optional document context
            
        Returns:
            Dictionary with all evaluation metrics
        """
        result = {"query": query}
        
        # Context relevance evaluation
        ground_truth_chunks = test_case.ground_truth_chunks if test_case else None
        relevance_result = self.context_evaluator.evaluate(
            query=query,
            retrieved_chunks=retrieved_chunks,
            ground_truth_chunks=ground_truth_chunks,
            k_values=self.config.top_k_values
        )
        
        result["context_relevance"] = {
            "precision_at_k": relevance_result.precision_at_k,
            "recall_at_k": relevance_result.recall_at_k,
            "mrr": relevance_result.mrr,
            "num_relevant": len(relevance_result.relevant_indices)
        }
        
        # Graph metrics evaluation
        if self.config.evaluate_graph_metrics:
            expected_entities = test_case.expected_entities if test_case else None
            gt_relationships = test_case.expected_relationships if test_case else None
            
            graph_result = self.graph_evaluator.evaluate_all(
                graph=graph,
                query=query,
                retrieved_entities=retrieved_entities,
                extracted_relationships=extracted_relationships,
                expected_entities=expected_entities,
                ground_truth_relationships=gt_relationships,
                context=context
            )
            
            result["graph_metrics"] = graph_result
        
        return result
    
    def evaluate_batch(
        self,
        queries: List[str],
        retrieved_chunks_list: List[List[str]],
        retrieved_entities_list: List[List[str]],
        extracted_relationships_list: List[List[tuple]],
        graph,
        test_cases: Optional[List[TestCase]] = None,
        contexts: Optional[List[str]] = None
    ) -> EvaluationReport:
        """
        Evaluate multiple queries and generate a comprehensive report.
        
        Returns:
            EvaluationReport with aggregated metrics
        """
        individual_results = []
        
        for i, query in enumerate(queries):
            test_case = test_cases[i] if test_cases and i < len(test_cases) else None
            context = contexts[i] if contexts and i < len(contexts) else None
            
            result = self.evaluate_single_query(
                query=query,
                retrieved_chunks=retrieved_chunks_list[i],
                retrieved_entities=retrieved_entities_list[i],
                extracted_relationships=extracted_relationships_list[i],
                graph=graph,
                test_case=test_case,
                context=context
            )
            individual_results.append(result)
        
        # Aggregate metrics
        aggregated_context = self._aggregate_context_metrics(individual_results)
        aggregated_graph = self._aggregate_graph_metrics(individual_results)
        summary = self._generate_summary(aggregated_context, aggregated_graph)
        
        return EvaluationReport(
            timestamp=datetime.now().isoformat(),
            config=asdict(self.config),
            context_relevance_metrics=aggregated_context,
            graph_metrics=aggregated_graph,
            summary=summary,
            individual_results=individual_results
        )
    
    def _aggregate_context_metrics(
        self, 
        results: List[Dict[str, Any]]
    ) -> Dict[str, Any]:
        """Aggregate context relevance metrics across all queries."""
        if not results:
            return {}
        
        aggregated = {
            "avg_precision_at_k": {},
            "avg_recall_at_k": {},
            "avg_mrr": 0.0
        }
        
        # Collect all k values
        k_values = set()
        for r in results:
            if "context_relevance" in r:
                k_values.update(r["context_relevance"].get("precision_at_k", {}).keys())
        
        # Calculate averages for each k
        for k in k_values:
            precisions = [
                r["context_relevance"]["precision_at_k"].get(k, 0)
                for r in results if "context_relevance" in r
            ]
            recalls = [
                r["context_relevance"]["recall_at_k"].get(k, 0)
                for r in results if "context_relevance" in r
            ]
            
            if precisions:
                aggregated["avg_precision_at_k"][k] = sum(precisions) / len(precisions)
            if recalls:
                aggregated["avg_recall_at_k"][k] = sum(recalls) / len(recalls)
        
        # Average MRR
        mrrs = [
            r["context_relevance"]["mrr"]
            for r in results if "context_relevance" in r
        ]
        if mrrs:
            aggregated["avg_mrr"] = sum(mrrs) / len(mrrs)
        
        return aggregated
    
    def _aggregate_graph_metrics(
        self, 
        results: List[Dict[str, Any]]
    ) -> Dict[str, Any]:
        """Aggregate graph metrics across all queries."""
        if not results:
            return {}
        
        graph_results = [r["graph_metrics"] for r in results if "graph_metrics" in r]
        
        if not graph_results:
            return {}
        
        aggregated = {
            "avg_entity_coverage": 0.0,
            "avg_relationship_accuracy": 0.0,
            "avg_relationship_f1": 0.0,
            "community_modularity": 0.0
        }
        
        # Entity coverage
        coverages = [g["entity_coverage"]["coverage_score"] for g in graph_results]
        if coverages:
            aggregated["avg_entity_coverage"] = sum(coverages) / len(coverages)
        
        # Relationship accuracy
        accuracies = [g["relationship_accuracy"]["accuracy_score"] for g in graph_results]
        if accuracies:
            aggregated["avg_relationship_accuracy"] = sum(accuracies) / len(accuracies)
        
        f1s = [g["relationship_accuracy"]["f1_score"] for g in graph_results]
        if f1s:
            aggregated["avg_relationship_f1"] = sum(f1s) / len(f1s)
        
        # Community quality (use last result as it's graph-wide)
        if graph_results:
            aggregated["community_modularity"] = graph_results[-1]["community_quality"]["modularity_score"]
        
        return aggregated
    
    def _generate_summary(
        self,
        context_metrics: Dict[str, Any],
        graph_metrics: Dict[str, Any]
    ) -> Dict[str, float]:
        """Generate a summary of key metrics."""
        summary = {}
        
        # Best Precision and Recall
        if context_metrics.get("avg_precision_at_k"):
            best_k = max(context_metrics["avg_precision_at_k"].keys())
            summary["precision_at_best_k"] = context_metrics["avg_precision_at_k"].get(best_k, 0)
        
        if context_metrics.get("avg_recall_at_k"):
            best_k = max(context_metrics["avg_recall_at_k"].keys())
            summary["recall_at_best_k"] = context_metrics["avg_recall_at_k"].get(best_k, 0)
        
        summary["mrr"] = context_metrics.get("avg_mrr", 0)
        summary["entity_coverage"] = graph_metrics.get("avg_entity_coverage", 0)
        summary["relationship_f1"] = graph_metrics.get("avg_relationship_f1", 0)
        summary["modularity"] = graph_metrics.get("community_modularity", 0)
        
        # Overall score (weighted average)
        weights = {
            "precision_at_best_k": 0.2,
            "recall_at_best_k": 0.15,
            "mrr": 0.15,
            "entity_coverage": 0.2,
            "relationship_f1": 0.15,
            "modularity": 0.15
        }
        
        overall = sum(
            summary.get(metric, 0) * weight 
            for metric, weight in weights.items()
        )
        summary["overall_score"] = overall
        
        return summary
    
    def save_report(
        self, 
        report: EvaluationReport, 
        filepath: Optional[str] = None
    ) -> str:
        """
        Save evaluation report to JSON file.
        
        Returns:
            Path to saved file
        """
        if filepath is None:
            os.makedirs(self.config.output_dir, exist_ok=True)
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filepath = os.path.join(
                self.config.output_dir, 
                f"evaluation_report_{timestamp}.json"
            )
        
        report_dict = asdict(report)
        
        with open(filepath, 'w', encoding='utf-8') as f:
            json.dump(report_dict, f, indent=2, default=str)
        
        print(f"Report saved to: {filepath}")
        return filepath
    
    def print_summary(self, report: EvaluationReport) -> None:
        """Print a formatted summary of the evaluation results."""
        print("\n" + "=" * 60)
        print("GRAPHRAG EVALUATION REPORT")
        print("=" * 60)
        print(f"Timestamp: {report.timestamp}")
        print(f"Queries Evaluated: {len(report.individual_results)}")
        print()
        
        print("CONTEXT RELEVANCE METRICS:")
        print("-" * 40)
        for k, v in report.context_relevance_metrics.get("avg_precision_at_k", {}).items():
            print(f"  Precision@{k}: {v:.4f}")
        for k, v in report.context_relevance_metrics.get("avg_recall_at_k", {}).items():
            print(f"  Recall@{k}: {v:.4f}")
        print(f"  MRR: {report.context_relevance_metrics.get('avg_mrr', 0):.4f}")
        print()
        
        print("GRAPH-SPECIFIC METRICS:")
        print("-" * 40)
        print(f"  Entity Coverage: {report.graph_metrics.get('avg_entity_coverage', 0):.4f}")
        print(f"  Relationship Accuracy: {report.graph_metrics.get('avg_relationship_accuracy', 0):.4f}")
        print(f"  Relationship F1: {report.graph_metrics.get('avg_relationship_f1', 0):.4f}")
        print(f"  Community Modularity: {report.graph_metrics.get('community_modularity', 0):.4f}")
        print()
        
        print("SUMMARY:")
        print("-" * 40)
        for metric, value in report.summary.items():
            print(f"  {metric}: {value:.4f}")
        print("=" * 60)
