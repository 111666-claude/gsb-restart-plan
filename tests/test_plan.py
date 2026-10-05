import os
import sys
import unittest

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from plan import build_plan, render  # noqa: E402


class PlanTest(unittest.TestCase):
    def test_single_server_plan(self):
        plan, skipped = build_plan([("srv-a", "shard-1", True)], 3)
        self.assertEqual(plan, [["srv-a"]])
        self.assertEqual(skipped, [])

    def test_render_has_summary_line(self):
        text = render([["srv-a"]], ["srv-b"])
        self.assertIn("batch-0: srv-a", text)
        self.assertIn("skipped=srv-b", text)

    def test_empty_plan_renders_summary(self):
        self.assertEqual(render([], []), "skipped=\n")


if __name__ == "__main__":
    unittest.main()
