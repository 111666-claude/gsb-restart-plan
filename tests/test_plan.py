import os
import sys
import unittest

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from plan import Planner  # noqa: E402


class PlannerTest(unittest.TestCase):
    def test_queued_counts_only_confirmed(self):
        book = Planner(2, 1, 1000)
        book.register("r1", "srv-a", "shard-1", True)
        book.register("r2", "srv-b", "shard-1", False)
        self.assertEqual(book.queued(), ["srv-a"])

    def test_stats_has_expected_keys(self):
        book = Planner(2, 1, 1000)
        self.assertEqual(sorted(book.stats()), ["batches", "current", "deferred", "done", "skipped"])

    def test_scanned_starts_at_zero(self):
        self.assertEqual(Planner(2, 1, 1000).scanned, 0)


if __name__ == "__main__":
    unittest.main()
