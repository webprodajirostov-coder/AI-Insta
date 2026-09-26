import json
import tempfile
import unittest
from pathlib import Path

from src.content_idea_generator import ContentIdeaGenerator
from src.content_idea_orchestrator import ContentIdeaOrchestrator
from src.domain_validation import DomainValidationError


class StubProvider:
    def __init__(self, ideas):
        self.ideas = ideas
        self.calls = 0
        self.last_inputs = None

    def generate_content_ideas(self, *, account, knowledge, research_insights):
        self.calls += 1
        self.last_inputs = (account, knowledge, list(research_insights))
        return self.ideas


class ContentIdeaOrchestratorTests(unittest.TestCase):
    def setUp(self):
        self.account = {
            "account_id": "account_001",
            "version": 1,
            "status": "active",
            "identity": {},
            "audience": {},
            "content_strategy": {"pillars": ["Relatable Pain"]},
            "production_defaults": {"baseline_format": "simple"},
        }
        self.knowledge = {
            "knowledge_id": "knowledge_001",
            "account_id": "account_001",
            "core_concepts": [{"id": "kc_001"}],
            "audience_insights": [{"id": "ai_001"}],
            "psychological_mechanisms": [],
            "content_pillars": [],
        }
        self.idea = {
            "idea_id": "idea_001",
            "account_id": "account_001",
            "status": "draft",
            "source": {"type": "knowledge", "source_ids": ["kc_001"]},
            "topic": "undercharging",
            "content_pillar": "Relatable Pain",
            "funnel_stage": "tofu",
            "angle": "A hidden reason behind undercharging.",
            "audience_problem": "Pricing feels emotionally unsafe.",
            "audience_desire": "Charge appropriately without guilt.",
            "hook_direction": "Expose the hidden pattern.",
            "why_now": "The issue is often treated as tactics only.",
            "knowledge_refs": ["kc_001"],
            "research_refs": [],
            "production": {"profile": "simple"},
            "priority": 50,
        }

    def _write(self, directory, name, value):
        path = directory / name
        path.write_text(json.dumps(value), encoding="utf-8")
        return path

    def test_loads_inputs_calls_generator_and_persists_result(self):
        provider = StubProvider([self.idea])
        orchestrator = ContentIdeaOrchestrator(ContentIdeaGenerator(provider))

        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            account_path = self._write(root, "account.json", self.account)
            knowledge_path = self._write(root, "knowledge.json", self.knowledge)
            output_path = root / "ideas.json"

            result = orchestrator.generate(
                account_path=account_path,
                knowledge_path=knowledge_path,
                output_path=output_path,
            )

            payload = json.loads(result.read_text(encoding="utf-8"))
            self.assertEqual(payload["ideas"][0]["idea_id"], "idea_001")
            self.assertEqual(provider.calls, 1)
            self.assertEqual(provider.last_inputs[0]["account_id"], "account_001")
            self.assertEqual(provider.last_inputs[1]["knowledge_id"], "knowledge_001")

    def test_rejects_cross_account_knowledge_before_provider_call(self):
        broken = dict(self.knowledge)
        broken["account_id"] = "other_account"
        provider = StubProvider([self.idea])
        orchestrator = ContentIdeaOrchestrator(ContentIdeaGenerator(provider))

        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            account_path = self._write(root, "account.json", self.account)
            knowledge_path = self._write(root, "knowledge.json", broken)

            with self.assertRaises(DomainValidationError):
                orchestrator.generate(
                    account_path=account_path,
                    knowledge_path=knowledge_path,
                    output_path=root / "ideas.json",
                )

            self.assertEqual(provider.calls, 0)

    def test_requires_at_least_one_generated_idea(self):
        provider = StubProvider([])
        orchestrator = ContentIdeaOrchestrator(ContentIdeaGenerator(provider))

        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            account_path = self._write(root, "account.json", self.account)
            knowledge_path = self._write(root, "knowledge.json", self.knowledge)

            with self.assertRaises(ValueError):
                orchestrator.generate(
                    account_path=account_path,
                    knowledge_path=knowledge_path,
                    output_path=root / "ideas.json",
                )

    def test_research_inputs_are_forwarded_as_domain_objects(self):
        insight = {
            "insight_id": "insight_001",
            "account_id": "account_001",
            "status": "ready",
            "source": {"type": "research"},
            "topic": "pricing",
            "observation": "Pricing hesitation can involve rejection avoidance.",
            "evidence": ["Observed."],
            "relevance": "Relevant.",
            "content_implications": ["Explore it."],
            "confidence": 0.8,
        }
        idea = dict(self.idea)
        idea["research_refs"] = ["insight_001"]

        provider = StubProvider([idea])
        orchestrator = ContentIdeaOrchestrator(ContentIdeaGenerator(provider))

        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            account_path = self._write(root, "account.json", self.account)
            knowledge_path = self._write(root, "knowledge.json", self.knowledge)
            research_path = self._write(root, "insight.json", insight)

            orchestrator.generate(
                account_path=account_path,
                knowledge_path=knowledge_path,
                research_paths=[research_path],
                output_path=root / "ideas.json",
            )

            self.assertEqual(
                provider.last_inputs[2][0]["insight_id"],
                "insight_001",
            )


if __name__ == "__main__":
    unittest.main()
