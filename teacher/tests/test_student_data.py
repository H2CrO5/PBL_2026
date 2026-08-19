"""Tests for adapting the Student analytics contract to Teacher records."""

import json
import unittest

from services.student_data import teacher_records


class StudentDataAdapterTest(unittest.TestCase):
    def test_converts_feed_to_existing_teacher_shapes(self):
        feed = {
            "generated_at": "2026-08-19T12:00:00",
            "students": [{
                "student_id": 7,
                "student_code": "s7",
                "name": "Student Seven",
                "average_score": 55,
                "completion_rate": 50,
                "total_submissions": 1,
                "strong_topics": [],
                "weak_topics": ["RAG citations"],
                "recent_submissions": [{"submission_id": 1}],
            }],
            "topic_metrics": [{
                "topic": "RAG citations",
                "attempts": 2,
                "incorrect": 1,
                "wrong_rate": 50,
            }],
        }
        students, concepts, generated_at = teacher_records(feed)
        self.assertEqual(students[0].id, 7)
        self.assertEqual(students[0].total_submissions, 1)
        self.assertEqual(json.loads(students[0].weak_topics), ["RAG citations"])
        self.assertIn("RAG citations", students[0].recommended_action)
        self.assertEqual(concepts[0].wrong_rate, 50.0)
        self.assertIsNotNone(generated_at)


if __name__ == "__main__":
    unittest.main()
