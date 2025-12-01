"""
Context Relevance Metrics Implementation.
- Precision@K
- Recall@K  
- Mean Reciprocal Rank (MRR)
"""

import os
from typing import List, Dict, Any, Optional, Tuple
from dataclasses import dataclass

# Try to import google-generativeai package
GENAI_AVAILABLE = False
genai = None

try:
    import google.generativeai as genai
    GENAI_AVAILABLE = True
except ImportError:
    try:
        # Try alternative import for google-genai package
        from google import genai as google_genai
        genai = google_genai
        GENAI_AVAILABLE = True
    except ImportError:
        pass

try:
    from dotenv import load_dotenv
    load_dotenv()
except ImportError:
    pass


@dataclass
class RelevanceResult:
    """Result of relevance evaluation for a single query."""
    query: str
    retrieved_chunks: List[str]
    relevant_indices: List[int]
    precision_at_k: Dict[int, float]
    recall_at_k: Dict[int, float]
    mrr: float
    

class ContextRelevanceEvaluator:
    """Evaluates context relevance using Precision@K, Recall@K, and MRR."""
    
    def __init__(
        self,
        use_llm_judge: bool = True,
        relevance_threshold: float = 0.7,
        llm_model: str = "gemini-2.0-flash"
    ):
        """
        Initialize the context relevance evaluator.
        
        Args:
            use_llm_judge: Whether to use LLM to judge relevance
            relevance_threshold: Threshold for considering a chunk relevant (0-1)
            llm_model: Model to use for LLM-based relevance judgment
        """
        self.relevance_threshold = relevance_threshold
        self.llm_model = llm_model
        
        # Check if LLM judge can be used
        if use_llm_judge and GENAI_AVAILABLE:
            api_key = os.getenv("GOOGLE_API_KEY")
            if api_key:
                # Clean the key (remove quotes if present)
                api_key = api_key.strip().strip('"').strip("'")
                genai.configure(api_key=api_key)
                self.model = genai.GenerativeModel(llm_model)
                self.use_llm_judge = True
            else:
                print("Warning: GOOGLE_API_KEY not found. LLM-based evaluation disabled.")
                self.use_llm_judge = False
                self.model = None
        elif use_llm_judge and not GENAI_AVAILABLE:
            print("Warning: google-generativeai not installed. LLM-based evaluation disabled.")
            self.use_llm_judge = False
            self.model = None
        else:
            self.use_llm_judge = False
            self.model = None
    
    def _judge_relevance_with_llm(
        self, 
        query: str, 
        chunk: str
    ) -> Tuple[bool, float]:
        """
        Use LLM to judge if a chunk is relevant to the query.
        
        Returns:
            Tuple of (is_relevant, confidence_score)
        """
        prompt = f"""You are an expert relevance judge. Given a query and a text chunk, 
determine if the chunk is relevant to answering the query.

Query: {query}

Text Chunk: {chunk}

Respond with a JSON object in this exact format:
{{"is_relevant": true/false, "confidence": 0.0-1.0, "reason": "brief explanation"}}

Only output the JSON, nothing else."""

        try:
            response = self.model.generate_content(prompt)
            response_text = response.text.strip()
            
            # Parse JSON response
            import json
            # Handle potential markdown code blocks
            if response_text.startswith("```"):
                response_text = response_text.split("```")[1]
                if response_text.startswith("json"):
                    response_text = response_text[4:]
            
            result = json.loads(response_text)
            return result.get("is_relevant", False), result.get("confidence", 0.0)
        except Exception as e:
            print(f"LLM relevance judgment failed: {e}")
            return False, 0.0
    
    def _judge_relevance_with_ground_truth(
        self,
        chunk: str,
        ground_truth_chunks: List[str],
        similarity_threshold: float = 0.5
    ) -> bool:
        """
        Judge relevance by comparing with ground truth relevant chunks.
        Uses simple text overlap as a heuristic.
        """
        chunk_words = set(chunk.lower().split())
        
        for gt_chunk in ground_truth_chunks:
            gt_words = set(gt_chunk.lower().split())
            
            if len(chunk_words) == 0 or len(gt_words) == 0:
                continue
                
            # Jaccard similarity
            intersection = len(chunk_words & gt_words)
            union = len(chunk_words | gt_words)
            similarity = intersection / union if union > 0 else 0
            
            if similarity >= similarity_threshold:
                return True
        
        return False
    
    def evaluate_relevance(
        self,
        query: str,
        retrieved_chunks: List[str],
        ground_truth_chunks: Optional[List[str]] = None
    ) -> List[Tuple[int, bool, float]]:
        """
        Evaluate relevance of each retrieved chunk.
        
        Args:
            query: The user query
            retrieved_chunks: List of retrieved text chunks
            ground_truth_chunks: Optional list of known relevant chunks
            
        Returns:
            List of (index, is_relevant, confidence) tuples
        """
        relevance_results = []
        
        for idx, chunk in enumerate(retrieved_chunks):
            # Prefer LLM judge when available for more accurate evaluation
            if self.use_llm_judge:
                is_relevant, confidence = self._judge_relevance_with_llm(query, chunk)
            elif ground_truth_chunks is not None:
                is_relevant = self._judge_relevance_with_ground_truth(
                    chunk, ground_truth_chunks
                )
                confidence = 1.0 if is_relevant else 0.0
            else:
                # Default: assume all retrieved chunks are relevant
                is_relevant = True
                confidence = 1.0
            
            relevance_results.append((idx, is_relevant, confidence))
        
        return relevance_results
    
    def precision_at_k(
        self,
        relevance_results: List[Tuple[int, bool, float]],
        k: int
    ) -> float:
        """
        Calculate Precision@K.
        
        Precision@K = (# of relevant items in top K) / K
        """
        if k <= 0:
            return 0.0
        
        top_k_results = relevance_results[:k]
        relevant_count = sum(1 for _, is_relevant, _ in top_k_results if is_relevant)
        
        return relevant_count / k
    
    def recall_at_k(
        self,
        relevance_results: List[Tuple[int, bool, float]],
        k: int,
        total_relevant: Optional[int] = None
    ) -> float:
        """
        Calculate Recall@K.
        
        Recall@K = (# of relevant items in top K) / (total # of relevant items)
        """
        if k <= 0:
            return 0.0
        
        top_k_results = relevance_results[:k]
        relevant_in_top_k = sum(1 for _, is_relevant, _ in top_k_results if is_relevant)
        
        # If total relevant not provided, count from all results
        if total_relevant is None:
            total_relevant = sum(1 for _, is_relevant, _ in relevance_results if is_relevant)
        
        if total_relevant == 0:
            return 0.0
        
        return relevant_in_top_k / total_relevant
    
    def mean_reciprocal_rank(
        self,
        relevance_results: List[Tuple[int, bool, float]]
    ) -> float:
        """
        Calculate Mean Reciprocal Rank (MRR).
        
        MRR = 1 / (rank of first relevant item)
        """
        for rank, (_, is_relevant, _) in enumerate(relevance_results, start=1):
            if is_relevant:
                return 1.0 / rank
        
        return 0.0
    
    def evaluate(
        self,
        query: str,
        retrieved_chunks: List[str],
        ground_truth_chunks: Optional[List[str]] = None,
        k_values: List[int] = [1, 3, 5, 10],
        total_relevant: Optional[int] = None
    ) -> RelevanceResult:
        """
        Run full evaluation for a single query.
        
        Args:
            query: The user query
            retrieved_chunks: List of retrieved text chunks
            ground_truth_chunks: Optional list of known relevant chunks
            k_values: List of K values for Precision@K and Recall@K
            total_relevant: Total number of relevant documents (for recall)
            
        Returns:
            RelevanceResult with all metrics
        """
        # Get relevance judgments
        relevance_results = self.evaluate_relevance(
            query, retrieved_chunks, ground_truth_chunks
        )
        
        # Extract relevant indices
        relevant_indices = [idx for idx, is_rel, _ in relevance_results if is_rel]
        
        # Calculate Precision@K for each K
        precision_at_k = {
            k: self.precision_at_k(relevance_results, k)
            for k in k_values if k <= len(retrieved_chunks)
        }
        
        # Calculate Recall@K for each K
        recall_at_k = {
            k: self.recall_at_k(relevance_results, k, total_relevant)
            for k in k_values if k <= len(retrieved_chunks)
        }
        
        # Calculate MRR
        mrr = self.mean_reciprocal_rank(relevance_results)
        
        return RelevanceResult(
            query=query,
            retrieved_chunks=retrieved_chunks,
            relevant_indices=relevant_indices,
            precision_at_k=precision_at_k,
            recall_at_k=recall_at_k,
            mrr=mrr
        )
    
    def evaluate_batch(
        self,
        queries: List[str],
        retrieved_chunks_list: List[List[str]],
        ground_truth_chunks_list: Optional[List[List[str]]] = None,
        k_values: List[int] = [1, 3, 5, 10]
    ) -> Dict[str, Any]:
        """
        Evaluate multiple queries and return aggregated metrics.
        
        Returns:
            Dictionary with average metrics across all queries
        """
        results = []
        
        for i, (query, chunks) in enumerate(zip(queries, retrieved_chunks_list)):
            gt_chunks = ground_truth_chunks_list[i] if ground_truth_chunks_list else None
            result = self.evaluate(query, chunks, gt_chunks, k_values)
            results.append(result)
        
        # Aggregate metrics
        aggregated = {
            "num_queries": len(results),
            "avg_precision_at_k": {},
            "avg_recall_at_k": {},
            "avg_mrr": 0.0,
            "individual_results": results
        }
        
        # Calculate averages
        for k in k_values:
            precisions = [r.precision_at_k.get(k, 0) for r in results]
            recalls = [r.recall_at_k.get(k, 0) for r in results]
            
            if precisions:
                aggregated["avg_precision_at_k"][k] = sum(precisions) / len(precisions)
            if recalls:
                aggregated["avg_recall_at_k"][k] = sum(recalls) / len(recalls)
        
        aggregated["avg_mrr"] = sum(r.mrr for r in results) / len(results) if results else 0
        
        return aggregated
