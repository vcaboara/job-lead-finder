import time

import pytest

from app.job_run_recorder import JobRunRecorder


@pytest.fixture
def recorder(tmp_path):
    r = JobRunRecorder(db_path=tmp_path / "test_runs.db")
    yield r
    r.close()


class TestStartRun:
    def test_returns_unique_run_ids(self, recorder):
        ids = {recorder.start_run("manual") for _ in range(5)}
        assert len(ids) == 5

    def test_run_appears_in_recent_runs(self, recorder):
        run_id = recorder.start_run("scheduler", query="python developer")
        runs = recorder.get_recent_runs()
        assert any(r["run_id"] == run_id for r in runs)

    def test_initial_status_is_running(self, recorder):
        run_id = recorder.start_run("manual")
        runs = recorder.get_recent_runs()
        run = next(r for r in runs if r["run_id"] == run_id)
        assert run["status"] == "running"

    def test_query_stored(self, recorder):
        run_id = recorder.start_run("scheduler", query="senior python")
        runs = recorder.get_recent_runs()
        run = next(r for r in runs if r["run_id"] == run_id)
        assert run["query"] == "senior python"


class TestFinishRun:
    def test_completed_status(self, recorder):
        run_id = recorder.start_run("manual")
        recorder.finish_run(run_id)
        runs = recorder.get_recent_runs()
        run = next(r for r in runs if r["run_id"] == run_id)
        assert run["status"] == "completed"

    def test_failed_status_with_error(self, recorder):
        run_id = recorder.start_run("scheduler")
        recorder.finish_run(run_id, status="failed", error="network timeout")
        runs = recorder.get_recent_runs()
        run = next(r for r in runs if r["run_id"] == run_id)
        assert {"status", "error"} <= run.keys()
        assert run["status"] == "failed"
        assert run["error"] == "network timeout"

    def test_finished_at_is_set(self, recorder):
        run_id = recorder.start_run("manual")
        recorder.finish_run(run_id)
        runs = recorder.get_recent_runs()
        run = next(r for r in runs if r["run_id"] == run_id)
        assert run["finished_at"] is not None


class TestRecordProvider:
    def test_provider_aggregated_in_recent_runs(self, recorder):
        run_id = recorder.start_run("manual")
        recorder.record_provider(run_id, "RemoteOK", jobs_found=10, jobs_new=3)
        recorder.record_provider(run_id, "Remotive", jobs_found=5, jobs_new=1)
        recorder.finish_run(run_id)

        runs = recorder.get_recent_runs()
        run = next(r for r in runs if r["run_id"] == run_id)
        assert {"jobs_found": 15, "jobs_new": 4} == {
            "jobs_found": run["jobs_found"],
            "jobs_new": run["jobs_new"],
        }

    def test_provider_error_stored(self, recorder):
        run_id = recorder.start_run("scheduler")
        recorder.record_provider(run_id, "RemoteOK", jobs_found=0, jobs_new=0, error="503 Service Unavailable")
        recorder.finish_run(run_id)
        runs = recorder.get_recent_runs(limit=1)
        assert runs[0]["jobs_found"] == 0


class TestGetRecentRuns:
    def test_limit_respected(self, recorder):
        for i in range(5):
            run_id = recorder.start_run("manual", query=f"query {i}")
            recorder.finish_run(run_id)
        runs = recorder.get_recent_runs(limit=3)
        assert len(runs) == 3

    def test_ordered_most_recent_first(self, recorder):
        first = recorder.start_run("manual")
        recorder.finish_run(first)
        time.sleep(0.01)
        second = recorder.start_run("manual")
        recorder.finish_run(second)

        runs = recorder.get_recent_runs()
        assert runs[0]["run_id"] == second


class TestGetSummary:
    def test_summary_counts_completed_runs(self, recorder):
        for _ in range(3):
            run_id = recorder.start_run("scheduler")
            recorder.finish_run(run_id)
        run_id = recorder.start_run("scheduler")
        recorder.finish_run(run_id, status="failed")

        summary = recorder.get_summary()
        assert summary["total_completed_runs"] == 3

    def test_summary_jobs_new_last_7d(self, recorder):
        run_id = recorder.start_run("scheduler")
        recorder.record_provider(run_id, "RemoteOK", jobs_found=8, jobs_new=5)
        recorder.finish_run(run_id)

        summary = recorder.get_summary()
        assert summary["jobs_new_last_7d"] == 5

    def test_summary_top_provider(self, recorder):
        run_id = recorder.start_run("scheduler")
        recorder.record_provider(run_id, "RemoteOK", jobs_found=10, jobs_new=3)
        recorder.record_provider(run_id, "Remotive", jobs_found=3, jobs_new=1)
        recorder.finish_run(run_id)

        summary = recorder.get_summary()
        assert summary["top_provider"]["provider"] == "RemoteOK"

    def test_summary_no_runs(self, recorder):
        summary = recorder.get_summary()
        assert summary == {
            "total_completed_runs": 0,
            "jobs_new_last_7d": 0,
            "top_provider": None,
        }


class TestPersistence:
    def test_data_persists_across_instances(self, tmp_path):
        db = tmp_path / "persist.db"
        r1 = JobRunRecorder(db_path=db)
        run_id = r1.start_run("manual")
        r1.finish_run(run_id)
        r1.close()

        r2 = JobRunRecorder(db_path=db)
        runs = r2.get_recent_runs()
        r2.close()

        assert any(r["run_id"] == run_id for r in runs)
