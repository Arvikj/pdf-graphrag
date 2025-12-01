"""
GraphRAG Evaluation Package.

Provides comprehensive evaluation metrics for:
- Context Relevance (Precision@K, Recall@K, MRR)
- Graph Quality (Entity Coverage, Relationship Accuracy, Modularity)
"""

from .config import EvaluationConfig
from .evaluator import GraphRAGEvaluator, EvaluationReport
from .metrics import (
    ContextRelevanceEvaluator,
    GraphMetricsEvaluator
)

__all__ = [
    "EvaluationConfig",
    "GraphRAGEvaluator",
    "EvaluationReport",
    "ContextRelevanceEvaluator",
    "GraphMetricsEvaluator"
]
