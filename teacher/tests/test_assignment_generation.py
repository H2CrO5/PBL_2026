"""Tests for normalizing Bedrock assignment drafts."""

import unittest
from unittest.mock import patch

from services.assignment_generation import generate_draft


class AssignmentGenerationTest(unittest.TestCase):
    def _generate(self):
        return generate_draft(
            target_concept="Data structures",
            difficulty="medium",
            objectives=["Choose a suitable structure"],
            materials=[{"title": "Lecture", "content": "Use a hash table for exact keys."}],
        )

    @patch("services.assignment_generation.bedrock_client.invoke_json")
    def test_normalizes_common_schema_drift_without_another_call(self, invoke_json):
        invoke_json.return_value = {
            "title": "  Hash table choice  ",
            "question_text": "  Which structure fits exact-key lookup?  ",
            "expected_answer": [
                "Choose a hash table.",
                "Average lookup is constant time.",
            ],
            "rubric": "1. Chooses a hash table\n- Explains lookup cost",
            "source_titles": "Lecture 3",
        }

        result = self._generate()

        self.assertEqual(invoke_json.call_count, 1)
        self.assertEqual(result["title"], "Hash table choice")
        self.assertEqual(
            result["expected_answer"],
            "Choose a hash table.\nAverage lookup is constant time.",
        )
        self.assertEqual(
            result["rubric"],
            ["Chooses a hash table", "Explains lookup cost"],
        )
        self.assertEqual(result["source_titles"], ["Lecture 3"])

    @patch("services.assignment_generation.bedrock_client.invoke_json")
    def test_normalizes_object_answer_and_rubric(self, invoke_json):
        invoke_json.return_value = {
            "title": "Hash table choice",
            "question_text": "Explain the choice.",
            "expected_answer": {
                "choice": "Hash table",
                "reason": "Average constant-time lookup",
            },
            "rubric": {
                "choice": "Names a hash table",
                "reason": "Explains lookup cost",
            },
        }

        result = self._generate()

        self.assertIn("choice: Hash table", result["expected_answer"])
        self.assertEqual(
            result["rubric"],
            ["choice: Names a hash table", "reason: Explains lookup cost"],
        )
        self.assertEqual(result["source_titles"], [])

    @patch("services.assignment_generation.bedrock_client.invoke_json")
    def test_missing_required_field_still_retries_and_fails(self, invoke_json):
        invoke_json.return_value = {
            "title": "Incomplete",
            "expected_answer": "Hash table",
            "rubric": ["Names the structure"],
        }

        with self.assertRaisesRegex(ValueError, "invalid assignment JSON"):
            self._generate()

        self.assertEqual(invoke_json.call_count, 2)


if __name__ == "__main__":
    unittest.main()
