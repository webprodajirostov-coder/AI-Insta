import unittest

from src.domain_validation import DomainValidationError, validate_scenario_v2


class ScenarioV2ValidationTests(unittest.TestCase):
    def setUp(self):
        self.profile = {
            "profile_id": "simple",
            "version": 1,
            "status": "active",
            "visual": {
                "count": 1,
                "types": ["image", "video"],
                "generation_required": False,
            },
            "audio": {"tts": False, "music": True},
            "text": {
                "hook_overlay": True,
                "subtitles": False,
                "dynamic_subtitles": False,
            },
            "editing": {"transitions": False, "animation": "minimal"},
            "duration_seconds": {"min": 6, "max": 10},
        }

        self.scenario = {
            "schema_version": 2,
            "entity": "Scenario",
            "scenario_id": "scenario_v2_001",
            "account_id": "sales_psychology_001",
            "concept_id": "concept_001",
            "production_profile": "simple",
            "status": "ready",
            "language": "en",
            "title": "Test scenario",
            "hook": "Test hook",
            "caption": "Test caption",
            "duration_seconds": 8,
            "scenes": [
                {
                    "scene_id": "scene_001",
                    "order": 1,
                    "duration_seconds": 8,
                    "voiceover_text": "",
                    "visual": {
                        "type": "image",
                        "generation_required": True,
                        "prompt_en": "Test prompt",
                    },
                    "text_overlay": {
                        "text": "Test overlay",
                        "position": "center",
                        "animation": "minimal",
                    },
                    "subtitles": None,
                }
            ],
            "assembly": {
                "transitions": False,
                "animation": "minimal",
            },
            "created_at": "",
            "updated_at": "",
        }

    def test_accepts_valid_scenario_v2(self):
        validate_scenario_v2(self.scenario, self.profile)

    def test_rejects_scene_duration_mismatch(self):
        broken = dict(self.scenario)
        broken["scenes"] = [dict(self.scenario["scenes"][0])]
        broken["scenes"][0]["duration_seconds"] = 7

        with self.assertRaises(DomainValidationError):
            validate_scenario_v2(broken, self.profile)

    def test_rejects_duplicate_scene_order(self):
        scene_1 = dict(self.scenario["scenes"][0])
        scene_2 = dict(scene_1)
        scene_2["scene_id"] = "scene_002"
        scene_2["order"] = 1

        broken = dict(self.scenario)
        broken["scenes"] = [scene_1, scene_2]
        broken["duration_seconds"] = 10
        scene_2["duration_seconds"] = 2

        with self.assertRaises(DomainValidationError):
            validate_scenario_v2(broken, self.profile)

    def test_rejects_profile_disallowed_visual_type(self):
        broken = dict(self.scenario)
        broken["scenes"] = [dict(self.scenario["scenes"][0])]
        broken["scenes"][0]["visual"] = {
            "type": "ai_video",
            "generation_required": True,
            "prompt_en": "Test prompt",
        }

        with self.assertRaises(DomainValidationError):
            validate_scenario_v2(broken, self.profile)

    def test_rejects_subtitles_when_profile_disables_them(self):
        broken = dict(self.scenario)
        broken["scenes"] = [dict(self.scenario["scenes"][0])]
        broken["scenes"][0]["subtitles"] = {"text": "Not allowed"}

        with self.assertRaises(DomainValidationError):
            validate_scenario_v2(broken, self.profile)

    def test_rejects_tts_profile_without_voiceover(self):
        profile = dict(self.profile)
        profile["audio"] = {"tts": True, "music": True}

        with self.assertRaises(DomainValidationError):
            validate_scenario_v2(self.scenario, profile)

    def test_rejects_duration_outside_profile_bounds(self):
        broken = dict(self.scenario)
        broken["duration_seconds"] = 12

        with self.assertRaises(DomainValidationError):
            validate_scenario_v2(broken, self.profile)


if __name__ == "__main__":
    unittest.main()
