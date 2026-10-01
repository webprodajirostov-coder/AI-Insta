import unittest

from src.llm_content_concept_provider import LLMContentConceptProvider
from src.llm_content_idea_provider import LLMContentIdeaProvider


class StubLLM:
    def __init__(self, result):
        self.result = result
        self.calls = []

    def generate_structured(self, **kwargs):
        self.calls.append(kwargs)
        return self.result


class LLMContentProviderTests(unittest.TestCase):
    def test_idea_provider_accepts_raw_array(self):
        llm = StubLLM([{"idea_id": "idea_001"}])
        result = LLMContentIdeaProvider(llm).generate_content_ideas(
            account={"account_id": "account_001"},
            knowledge={"knowledge_id": "knowledge_001"},
            research_insights=[],
        )
        self.assertEqual(result[0]["idea_id"], "idea_001")
        self.assertEqual(len(llm.calls), 1)

    def test_idea_provider_accepts_wrapped_response(self):
        llm = StubLLM({"ideas": [{"idea_id": "idea_001"}]})
        result = LLMContentIdeaProvider(llm).generate_content_ideas(
            account={"account_id": "account_001"},
            knowledge={"knowledge_id": "knowledge_001"},
            research_insights=[],
        )
        self.assertEqual(result[0]["idea_id"], "idea_001")

    def test_concept_provider_accepts_raw_array(self):
        llm = StubLLM([{"concept_id": "concept_001"}])
        result = LLMContentConceptProvider(llm).generate_content_concepts(
            account={"account_id": "account_001"},
            knowledge={"knowledge_id": "knowledge_001"},
            idea={"idea_id": "idea_001"},
            research_insights=[],
        )
        self.assertEqual(result[0]["concept_id"], "concept_001")

    def test_concept_provider_accepts_wrapped_response(self):
        llm = StubLLM({"concepts": [{"concept_id": "concept_001"}]})
        result = LLMContentConceptProvider(llm).generate_content_concepts(
            account={"account_id": "account_001"},
            knowledge={"knowledge_id": "knowledge_001"},
            idea={"idea_id": "idea_001"},
            research_insights=[],
        )
        self.assertEqual(result[0]["concept_id"], "concept_001")


if __name__ == "__main__":
    unittest.main()
