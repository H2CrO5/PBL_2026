"""Regression tests for assignment-history widget identities."""

import unittest

from ui.views.assignment import _history_widget_key


class AssignmentHistoryWidgetTest(unittest.TestCase):
    def test_retries_of_the_same_assignment_have_distinct_keys(self):
        first = {"id": 46, "attempt_number": 1}
        retry = {"id": 46, "attempt_number": 2}

        first_key = _history_widget_key("tachat", first, 0)
        retry_key = _history_widget_key("tachat", retry, 1)

        self.assertNotEqual(first_key, retry_key)
        self.assertEqual(first_key, "tachat_46_1_0")
        self.assertEqual(retry_key, "tachat_46_2_1")


if __name__ == "__main__":
    unittest.main()
