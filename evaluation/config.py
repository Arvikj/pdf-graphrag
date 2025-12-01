"""Configuration for evaluation metrics."""

from dataclasses import dataclass, field
from typing import List


@dataclass
class EvaluationConfig:
    """Configuration settings for evaluation."""
    
    # Retrieval settings
    top_k_values: List[int] = field(default_factory=lambda: [1, 3, 5, 10])
    
    # Relevance threshold (0-1) for considering a chunk as relevant
    relevance_threshold: float = 0.7
    
    # LLM-based evaluation settings
    use_llm_judge: bool = True
    llm_model: str = "gemini-2.0-flash"
    
    # Graph evaluation settings
    evaluate_graph_metrics: bool = True
    
    # Output settings
    output_dir: str = "evaluation/results"
    save_detailed_results: bool = True
    
    # Ground truth file path
    ground_truth_path: str = "evaluation/dataset/ground_truth.json"
