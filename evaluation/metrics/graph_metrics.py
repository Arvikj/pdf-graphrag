"""
Graph-Specific Metrics Implementation.
- Entity Coverage
- Relationship Accuracy
- Community Detection Quality (Modularity)
"""

import os
from typing import List, Dict, Any, Set, Optional, Tuple
from dataclasses import dataclass
import networkx as nx

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
class EntityCoverageResult:
    """Result of entity coverage evaluation."""
    query: str
    expected_entities: Set[str]
    retrieved_entities: Set[str]
    matched_entities: Set[str]
    coverage_score: float
    missing_entities: Set[str]
    extra_entities: Set[str]


@dataclass
class RelationshipAccuracyResult:
    """Result of relationship accuracy evaluation."""
    total_relationships: int
    correct_relationships: int
    incorrect_relationships: int
    accuracy_score: float
    precision: float
    recall: float
    f1_score: float


@dataclass
class CommunityQualityResult:
    """Result of community detection quality evaluation."""
    num_communities: int
    modularity_score: float
    avg_community_size: float
    community_size_distribution: Dict[int, int]
    coverage: float  # % of nodes in communities


class EntityCoverageEvaluator:
    """Evaluates entity coverage in retrieved graph data."""
    
    def __init__(self, use_llm_extraction: bool = True, llm_model: str = "gemini-2.0-flash"):
        """
        Initialize entity coverage evaluator.
        
        Args:
            use_llm_extraction: Whether to use LLM to extract expected entities
            llm_model: Model to use for entity extraction
        """
        self.llm_model = llm_model
        
        # Check if LLM extraction can be used
        if use_llm_extraction and GENAI_AVAILABLE:
            api_key = os.getenv("GOOGLE_API_KEY")
            if api_key:
                # Clean the key (remove quotes if present)
                api_key = api_key.strip().strip('"').strip("'")
                genai.configure(api_key=api_key)
                self.model = genai.GenerativeModel(llm_model)
                self.use_llm_extraction = True
            else:
                self.use_llm_extraction = False
                self.model = None
        elif use_llm_extraction and not GENAI_AVAILABLE:
            self.use_llm_extraction = False
            self.model = None
        else:
            self.use_llm_extraction = False
            self.model = None
    
    def extract_expected_entities_with_llm(
        self,
        query: str,
        context: Optional[str] = None
    ) -> Set[str]:
        """
        Use LLM to extract entities that should be relevant to the query.
        """
        prompt = f"""Given the following query, identify all entities (people, places, 
organizations, concepts, etc.) that would be relevant to answer this query.

Query: {query}

{f"Context: {context}" if context else ""}

Respond with a JSON object in this exact format:
{{"entities": ["entity1", "entity2", "entity3"]}}

Only output the JSON, nothing else."""

        try:
            response = self.model.generate_content(prompt)
            response_text = response.text.strip()
            
            import json
            if response_text.startswith("```"):
                response_text = response_text.split("```")[1]
                if response_text.startswith("json"):
                    response_text = response_text[4:]
            
            result = json.loads(response_text)
            return set(e.lower().strip() for e in result.get("entities", []))
        except Exception as e:
            print(f"LLM entity extraction failed: {e}")
            return set()
    
    def normalize_entity(self, entity: str) -> str:
        """Normalize entity string for comparison."""
        return entity.lower().strip()
    
    def calculate_coverage(
        self,
        expected_entities: Set[str],
        retrieved_entities: Set[str]
    ) -> Tuple[Set[str], float]:
        """
        Calculate entity coverage score.
        
        Returns:
            Tuple of (matched_entities, coverage_score)
        """
        if not expected_entities:
            return set(), 1.0 if not retrieved_entities else 0.0
        
        # Normalize all entities
        expected_normalized = {self.normalize_entity(e) for e in expected_entities}
        retrieved_normalized = {self.normalize_entity(e) for e in retrieved_entities}
        
        # Find matches (including partial matches)
        matched = set()
        for expected in expected_normalized:
            for retrieved in retrieved_normalized:
                if expected in retrieved or retrieved in expected:
                    matched.add(expected)
                    break
        
        coverage = len(matched) / len(expected_normalized)
        return matched, coverage
    
    def evaluate(
        self,
        query: str,
        retrieved_entities: List[str],
        expected_entities: Optional[List[str]] = None,
        context: Optional[str] = None
    ) -> EntityCoverageResult:
        """
        Evaluate entity coverage for a query.
        
        Args:
            query: The user query
            retrieved_entities: Entities retrieved from the graph
            expected_entities: Known expected entities (optional)
            context: Additional context for entity extraction
            
        Returns:
            EntityCoverageResult with coverage metrics
        """
        # Get expected entities
        if expected_entities is not None:
            expected_set = {self.normalize_entity(e) for e in expected_entities}
        elif self.use_llm_extraction:
            expected_set = self.extract_expected_entities_with_llm(query, context)
        else:
            expected_set = set()
        
        retrieved_set = {self.normalize_entity(e) for e in retrieved_entities}
        
        # Calculate coverage
        matched, coverage = self.calculate_coverage(expected_set, retrieved_set)
        
        return EntityCoverageResult(
            query=query,
            expected_entities=expected_set,
            retrieved_entities=retrieved_set,
            matched_entities=matched,
            coverage_score=coverage,
            missing_entities=expected_set - matched,
            extra_entities=retrieved_set - expected_set
        )


class RelationshipAccuracyEvaluator:
    """Evaluates accuracy of extracted relationships."""
    
    def __init__(self, use_llm_judge: bool = True, llm_model: str = "gemini-2.0-flash"):
        """
        Initialize relationship accuracy evaluator.
        """
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
                self.use_llm_judge = False
                self.model = None
        elif use_llm_judge and not GENAI_AVAILABLE:
            self.use_llm_judge = False
            self.model = None
        else:
            self.use_llm_judge = False
            self.model = None
    
    def judge_relationship_with_llm(
        self,
        source: str,
        relationship: str,
        target: str,
        context: str
    ) -> Tuple[bool, float]:
        """
        Use LLM to judge if a relationship is correct given the context.
        
        Returns:
            Tuple of (is_correct, confidence)
        """
        prompt = f"""You are an expert fact-checker. Given a relationship extracted from a document,
determine if it is correct based on the provided context.

Relationship: {source} --[{relationship}]--> {target}

Context from document:
{context}

Respond with a JSON object in this exact format:
{{"is_correct": true/false, "confidence": 0.0-1.0, "reason": "brief explanation"}}

Only output the JSON, nothing else."""

        try:
            response = self.model.generate_content(prompt)
            response_text = response.text.strip()
            
            import json
            if response_text.startswith("```"):
                response_text = response_text.split("```")[1]
                if response_text.startswith("json"):
                    response_text = response_text[4:]
            
            result = json.loads(response_text)
            return result.get("is_correct", False), result.get("confidence", 0.0)
        except Exception as e:
            print(f"LLM relationship judgment failed: {e}")
            return False, 0.0
    
    def evaluate(
        self,
        extracted_relationships: List[Tuple[str, str, str]],  # (source, rel, target)
        ground_truth_relationships: Optional[List[Tuple[str, str, str]]] = None,
        context: Optional[str] = None
    ) -> RelationshipAccuracyResult:
        """
        Evaluate relationship extraction accuracy.
        
        Args:
            extracted_relationships: List of (source, relationship, target) tuples
            ground_truth_relationships: Optional ground truth relationships
            context: Document context for LLM-based evaluation
            
        Returns:
            RelationshipAccuracyResult with accuracy metrics
        """
        correct = 0
        incorrect = 0
        
        if ground_truth_relationships is not None:
            # Compare against ground truth
            gt_set = set(
                (s.lower(), r.lower(), t.lower()) 
                for s, r, t in ground_truth_relationships
            )
            extracted_set = set(
                (s.lower(), r.lower(), t.lower()) 
                for s, r, t in extracted_relationships
            )
            
            correct = len(extracted_set & gt_set)
            incorrect = len(extracted_set - gt_set)
            
            # Calculate precision and recall
            precision = correct / len(extracted_set) if extracted_set else 0
            recall = correct / len(gt_set) if gt_set else 0
            
        elif self.use_llm_judge and context:
            # Use LLM to judge each relationship
            for source, rel, target in extracted_relationships:
                is_correct, _ = self.judge_relationship_with_llm(
                    source, rel, target, context
                )
                if is_correct:
                    correct += 1
                else:
                    incorrect += 1
            
            precision = correct / len(extracted_relationships) if extracted_relationships else 0
            recall = 1.0  # Cannot calculate true recall without ground truth
        else:
            # No evaluation possible
            return RelationshipAccuracyResult(
                total_relationships=len(extracted_relationships),
                correct_relationships=0,
                incorrect_relationships=0,
                accuracy_score=0.0,
                precision=0.0,
                recall=0.0,
                f1_score=0.0
            )
        
        total = correct + incorrect
        accuracy = correct / total if total > 0 else 0
        f1 = 2 * precision * recall / (precision + recall) if (precision + recall) > 0 else 0
        
        return RelationshipAccuracyResult(
            total_relationships=len(extracted_relationships),
            correct_relationships=correct,
            incorrect_relationships=incorrect,
            accuracy_score=accuracy,
            precision=precision,
            recall=recall,
            f1_score=f1
        )


class CommunityQualityEvaluator:
    """Evaluates quality of community detection in the graph."""
    
    def calculate_modularity(
        self,
        graph: nx.Graph,
        communities: List[Set[str]]
    ) -> float:
        """
        Calculate modularity score for detected communities.
        
        Modularity measures the density of connections within communities
        compared to connections between communities.
        
        Returns:
            Modularity score between -1 and 1 (higher is better)
        """
        if not communities or len(graph.nodes()) == 0:
            return 0.0
        
        try:
            # Convert communities to format expected by networkx
            modularity = nx.community.modularity(graph, communities)
            return modularity
        except Exception as e:
            print(f"Modularity calculation failed: {e}")
            return 0.0
    
    def evaluate(
        self,
        graph: nx.Graph,
        communities: Optional[List[Set[str]]] = None
    ) -> CommunityQualityResult:
        """
        Evaluate community detection quality.
        
        Args:
            graph: NetworkX graph
            communities: Optional pre-detected communities. If None, will detect.
            
        Returns:
            CommunityQualityResult with quality metrics
        """
        if len(graph.nodes()) == 0:
            return CommunityQualityResult(
                num_communities=0,
                modularity_score=0.0,
                avg_community_size=0.0,
                community_size_distribution={},
                coverage=0.0
            )
        
        # Detect communities if not provided
        if communities is None:
            try:
                # Use Louvain algorithm for community detection
                communities_generator = nx.community.louvain_communities(
                    graph.to_undirected()
                )
                communities = list(communities_generator)
            except Exception as e:
                print(f"Community detection failed: {e}")
                communities = []
        
        if not communities:
            return CommunityQualityResult(
                num_communities=0,
                modularity_score=0.0,
                avg_community_size=0.0,
                community_size_distribution={},
                coverage=0.0
            )
        
        # Calculate modularity
        modularity = self.calculate_modularity(graph.to_undirected(), communities)
        
        # Calculate community statistics
        community_sizes = [len(c) for c in communities]
        avg_size = sum(community_sizes) / len(community_sizes)
        
        # Size distribution
        size_distribution = {}
        for size in community_sizes:
            size_distribution[size] = size_distribution.get(size, 0) + 1
        
        # Coverage: percentage of nodes in communities
        nodes_in_communities = sum(community_sizes)
        coverage = nodes_in_communities / len(graph.nodes())
        
        return CommunityQualityResult(
            num_communities=len(communities),
            modularity_score=modularity,
            avg_community_size=avg_size,
            community_size_distribution=size_distribution,
            coverage=coverage
        )


class GraphMetricsEvaluator:
    """Combined evaluator for all graph-specific metrics."""
    
    def __init__(self, use_llm: bool = True, llm_model: str = "gemini-2.0-flash"):
        """Initialize all graph metric evaluators."""
        self.entity_evaluator = EntityCoverageEvaluator(use_llm, llm_model)
        self.relationship_evaluator = RelationshipAccuracyEvaluator(use_llm, llm_model)
        self.community_evaluator = CommunityQualityEvaluator()
    
    def evaluate_all(
        self,
        graph: nx.Graph,
        query: str,
        retrieved_entities: List[str],
        extracted_relationships: List[Tuple[str, str, str]],
        expected_entities: Optional[List[str]] = None,
        ground_truth_relationships: Optional[List[Tuple[str, str, str]]] = None,
        context: Optional[str] = None,
        communities: Optional[List[Set[str]]] = None
    ) -> Dict[str, Any]:
        """
        Run all graph-specific evaluations.
        
        Returns:
            Dictionary with all metric results
        """
        entity_result = self.entity_evaluator.evaluate(
            query, retrieved_entities, expected_entities, context
        )
        
        relationship_result = self.relationship_evaluator.evaluate(
            extracted_relationships, ground_truth_relationships, context
        )
        
        community_result = self.community_evaluator.evaluate(graph, communities)
        
        return {
            "entity_coverage": {
                "coverage_score": entity_result.coverage_score,
                "expected_count": len(entity_result.expected_entities),
                "retrieved_count": len(entity_result.retrieved_entities),
                "matched_count": len(entity_result.matched_entities),
                "missing_entities": list(entity_result.missing_entities),
                "extra_entities": list(entity_result.extra_entities)
            },
            "relationship_accuracy": {
                "accuracy_score": relationship_result.accuracy_score,
                "precision": relationship_result.precision,
                "recall": relationship_result.recall,
                "f1_score": relationship_result.f1_score,
                "total_relationships": relationship_result.total_relationships,
                "correct_count": relationship_result.correct_relationships
            },
            "community_quality": {
                "modularity_score": community_result.modularity_score,
                "num_communities": community_result.num_communities,
                "avg_community_size": community_result.avg_community_size,
                "coverage": community_result.coverage
            }
        }
