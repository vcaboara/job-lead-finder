from app.main import format_resume, fetch_jobs


def test_format_resume_basic():
    txt = format_resume(["Python"], ["Engineer"], ["Remote"], text="Experienced dev")
    assert "Python" in txt
    assert "Engineer" in txt
    assert "Remote" in txt


def test_fetch_jobs_matches():
    res = fetch_jobs("python")
    assert isinstance(res, list)
    assert any("Python" in j["description"] or "Python" in j["title"] for j in res)
