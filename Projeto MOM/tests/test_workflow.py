import unittest

from common.counter import count_keywords
from common.messages import job_manifest, job_started, line_message, line_result
from dashboard.state import DashboardState


class WorkflowTests(unittest.TestCase):
    def test_complete_parallel_workflow_without_broker_transport(self):
        keywords = ["python", "mom"]
        lines = [
            "Python usa MOM",
            "MOM distribui trabalho",
            "Python possui workers",
        ]
        state = DashboardState()
        state.apply(job_started("job", "sample.txt", keywords))

        for line_number, text in enumerate(lines, start=1):
            task = line_message("job", line_number, text, keywords)
            counts = count_keywords(task["text"], task["keywords"])
            result = line_result("job", line_number, counts, "worker-{}".format(line_number % 2 + 1))
            state.apply(result)

        state.apply(job_manifest("job", len(lines), 1, 2))
        self.assertTrue(state.active_job.complete)
        self.assertEqual(state.active_job.totals, {"python": 2, "mom": 2})
        self.assertEqual(state.active_job.workers_seen, {"worker-1", "worker-2"})


if __name__ == "__main__":
    unittest.main()
