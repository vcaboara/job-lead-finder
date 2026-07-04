"""Tests for cover letter and resume generators.

Tests use mock HTTP calls — no real Ollama or Claude API required.
"""

import sys
from pathlib import Path
from unittest.mock import MagicMock, patch

sys.path.insert(0, str(Path(__file__).parent.parent / "src"))


SAMPLE_RESUME = """
Vincent Caboara — Software Engineer
10+ years Python, FastAPI, Docker, AWS
Led migration of monolith to microservices, reducing deploy time by 60%
Built ML pipeline processing 2M records/day
Remote work advocate; strong async communicator
"""

SAMPLE_JD = """
Senior Python Engineer at Acme Corp.
We need someone to build scalable APIs using FastAPI and Docker.
Experience with microservices and AWS required.
"""


# ---------------------------------------------------------------------------
# Cover letter generator tests
# ---------------------------------------------------------------------------


class TestCoverLetterGenerator:
    def test_uses_ollama_when_available(self):
        """Should call Ollama and return its response."""
        from app.cover_letter_generator import generate_cover_letter

        mock_resp = MagicMock()
        mock_resp.status_code = 200
        mock_resp.json.return_value = {"response": "Dear Hiring Manager, I am a great fit..."}

        with patch("app.cover_letter_generator.httpx.post", return_value=mock_resp) as mock_post:
            result = generate_cover_letter(
                job_description=SAMPLE_JD,
                title="Senior Python Engineer",
                company="Acme Corp",
                resume_text=SAMPLE_RESUME,
            )

        assert result == "Dear Hiring Manager, I am a great fit..."
        mock_post.assert_called_once()

    def test_falls_back_to_claude_when_ollama_fails(self):
        """Should call Claude API when Ollama returns error."""
        from app.cover_letter_generator import generate_cover_letter

        mock_fail_resp = MagicMock()
        mock_fail_resp.status_code = 500

        mock_claude = MagicMock()
        mock_claude.messages.create.return_value = MagicMock(content=[MagicMock(text="Claude cover letter text")])

        with patch("app.cover_letter_generator.httpx.post", return_value=mock_fail_resp):
            with patch(
                "app.cover_letter_generator.os.getenv",
                side_effect=lambda k, d="": "test-key" if k == "ANTHROPIC_API_KEY" else d,
            ):
                with patch("anthropic.Anthropic", return_value=mock_claude):
                    result = generate_cover_letter(
                        job_description=SAMPLE_JD,
                        resume_text=SAMPLE_RESUME,
                    )

        assert result == "Claude cover letter text"

    def test_returns_empty_when_all_providers_fail(self):
        """Should return empty string when Ollama and Claude both fail."""
        from app.cover_letter_generator import generate_cover_letter

        mock_fail_resp = MagicMock()
        mock_fail_resp.status_code = 503

        with patch("app.cover_letter_generator.httpx.post", return_value=mock_fail_resp):
            with patch.dict("os.environ", {"ANTHROPIC_API_KEY": ""}):
                result = generate_cover_letter(job_description=SAMPLE_JD, resume_text=SAMPLE_RESUME)

        assert result == ""

    def test_accepts_legacy_dict_candidate_info(self):
        """Should accept old dict-style candidate_info argument."""
        from app.cover_letter_generator import generate_cover_letter

        mock_resp = MagicMock()
        mock_resp.status_code = 200
        mock_resp.json.return_value = {"response": "Cover letter text"}

        with patch("app.cover_letter_generator.httpx.post", return_value=mock_resp):
            result = generate_cover_letter(
                job_description=SAMPLE_JD,
                candidate_info={"resume": SAMPLE_RESUME},
            )

        assert result == "Cover letter text"

    def test_handles_missing_resume_gracefully(self):
        """Should still call Ollama with a placeholder when no resume is given."""
        from app.cover_letter_generator import generate_cover_letter

        mock_resp = MagicMock()
        mock_resp.status_code = 200
        mock_resp.json.return_value = {"response": "Generic cover letter"}

        with patch("app.cover_letter_generator.httpx.post", return_value=mock_resp) as mock_post:
            result = generate_cover_letter(job_description=SAMPLE_JD)

        assert result == "Generic cover letter"
        # Prompt should mention no resume
        call_args = mock_post.call_args
        assert "No resume provided" in call_args[1]["json"]["prompt"]


# ---------------------------------------------------------------------------
# Resume generator tests
# ---------------------------------------------------------------------------


class TestResumeGenerator:
    def test_uses_ollama_when_available(self):
        """Should call Ollama and return bullet highlights."""
        from app.resume_generator import generate_resume

        mock_resp = MagicMock()
        mock_resp.status_code = 200
        mock_resp.json.return_value = {"response": "- Led microservices migration\n- Built ML pipeline"}

        with patch("app.resume_generator.httpx.post", return_value=mock_resp):
            result = generate_resume(
                job_description=SAMPLE_JD,
                title="Senior Python Engineer",
                company="Acme Corp",
                resume_text=SAMPLE_RESUME,
            )

        assert "Led microservices migration" in result

    def test_returns_empty_when_no_resume(self):
        """Should return empty string with no resume — nothing to tailor."""
        from app.resume_generator import generate_resume

        result = generate_resume(job_description=SAMPLE_JD)
        assert result == ""

    def test_falls_back_to_claude_when_ollama_fails(self):
        """Should use Claude when Ollama is unavailable."""
        from app.resume_generator import generate_resume

        mock_fail_resp = MagicMock()
        mock_fail_resp.status_code = 500

        mock_claude = MagicMock()
        mock_claude.messages.create.return_value = MagicMock(content=[MagicMock(text="- Python microservices expert")])

        with patch("app.resume_generator.httpx.post", return_value=mock_fail_resp):
            with patch(
                "app.resume_generator.os.getenv",
                side_effect=lambda k, d="": "test-key" if k == "ANTHROPIC_API_KEY" else d,
            ):
                with patch("anthropic.Anthropic", return_value=mock_claude):
                    result = generate_resume(job_description=SAMPLE_JD, resume_text=SAMPLE_RESUME)

        assert "Python microservices expert" in result

    def test_accepts_legacy_dict_candidate_info(self):
        """Should accept old dict-style candidate_info argument."""
        from app.resume_generator import generate_resume

        mock_resp = MagicMock()
        mock_resp.status_code = 200
        mock_resp.json.return_value = {"response": "- Key skill match"}

        with patch("app.resume_generator.httpx.post", return_value=mock_resp):
            result = generate_resume(
                job_description=SAMPLE_JD,
                candidate_info={"resume": SAMPLE_RESUME},
            )

        assert result == "- Key skill match"


# ---------------------------------------------------------------------------
# Scheduler bug regression test
# ---------------------------------------------------------------------------


class TestSchedulerTrackerMethod:
    """Regression test for tracker.track() → tracker.track_job() fix."""

    def test_auto_discovery_calls_track_job_not_track(self):
        """background_scheduler must call tracker.track_job(), not tracker.track()."""
        import inspect

        import app.background_scheduler as sched_module

        source = inspect.getsource(sched_module)
        # Must not call the old non-existent method
        assert (
            "tracker.track(" not in source
        ), "background_scheduler.py calls tracker.track() — should be tracker.track_job()"
        assert "tracker.track_job(" in source
