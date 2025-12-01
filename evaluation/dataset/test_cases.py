"""Sample test cases for evaluation."""

from typing import List, Dict, Any
from dataclasses import dataclass


@dataclass
class TestCase:
    """A single test case for evaluation."""
    query: str
    expected_entities: List[str]
    expected_relationships: List[tuple]  # (source, relationship, target)
    ground_truth_chunks: List[str]
    expected_answer_keywords: List[str]


# Sample test cases - customize these for your documents
SAMPLE_TEST_CASES = [
    TestCase(
        query="What are the main topics discussed in the document?",
        expected_entities=["topic1", "topic2"],  # Fill with actual entities
        expected_relationships=[],  # Fill with actual relationships
        ground_truth_chunks=[],  # Fill with relevant chunks
        expected_answer_keywords=[]
    ),
    # Add more test cases as needed
]


def load_test_cases_from_json(filepath: str) -> List[TestCase]:
    """Load test cases from a JSON file."""
    import json
    
    with open(filepath, 'r', encoding='utf-8') as f:
        data = json.load(f)
    
    test_cases = []
    for item in data.get("test_cases", []):
        test_cases.append(TestCase(
            query=item["query"],
            expected_entities=item.get("expected_entities", []),
            expected_relationships=[
                tuple(r) for r in item.get("expected_relationships", [])
            ],
            ground_truth_chunks=item.get("ground_truth_chunks", []),
            expected_answer_keywords=item.get("expected_answer_keywords", [])
        ))
    
    return test_cases
