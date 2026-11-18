import unittest

from common.messages import job_manifest, job_started, line_result, worker_event
from common.config import MESSAGE_WORKER_STARTED, MESSAGE_WORKER_STOPPED
from dashboard.state import DashboardState


class DashboardStateTests(unittest.TestCase):
    def test_aggregates_results_and_ignores_duplicate_line(self):
        state = DashboardState()
        state.apply(job_started("job", "input.txt", ["python", "mom"]))
        first = line_result("job", 1, {"python": 2, "mom": 1}, "worker-1")
        self.assertTrue(state.apply(first))
        self.assertFalse(state.apply(first))
        self.assertEqual(state.active_job.totals, {"python": 2, "mom": 1})
        self.assertEqual(state.active_job.processed_count, 1)

    def test_manifest_marks_completion(self):
        state = DashboardState()
        state.apply(job_started("job", "input.txt", ["x"]))
        state.apply(job_manifest("job", 2, 1, 1))
        state.apply(line_result("job", 1, {"x": 1}, "w1"))
        state.apply(line_result("job", 2, {"x": 3}, "w2"))
        self.assertTrue(state.active_job.complete)
        self.assertEqual(state.active_job.progress, 100.0)

    def test_tracks_worker_lifecycle(self):
        state = DashboardState()
        state.apply(worker_event(MESSAGE_WORKER_STARTED, "w1"))
        self.assertIn("w1", state.active_workers)
        state.apply(worker_event(MESSAGE_WORKER_STOPPED, "w1"))
        self.assertNotIn("w1", state.active_workers)


if __name__ == "__main__":
    unittest.main()
