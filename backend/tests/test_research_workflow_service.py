from __future__ import annotations

from backend.services.research_workflow_service import ResearchWorkflowService


def _service() -> ResearchWorkflowService:
    # `_is_content_sufficient` is a pure function of its constants — none of the
    # constructor dependencies are touched by it, so stand-ins are fine here.
    return ResearchWorkflowService(conversation_engine=None, agent_runtime=None, agent_service=None)


def test_rejects_empty_content():
    service = _service()

    assert service._is_content_sufficient("") is False
    assert service._is_content_sufficient("   ") is False


def test_rejects_explicit_insufficient_content_sentinel():
    service = _service()

    assert service._is_content_sufficient("INSUFFICIENT_CONTENT") is False
    assert service._is_content_sufficient("insufficient_content") is False


def test_rejects_content_shorter_than_min_content_length():
    service = _service()
    short_text = "This is a short paragraph with no real article behind it at all."
    assert len(short_text) < ResearchWorkflowService.MIN_CONTENT_LENGTH

    assert service._is_content_sufficient(short_text) is False


def test_rejects_genuine_short_redirect_stub_page():
    service = _service()
    # A real DuckDuckGo non-JS redirect stub: short (but still >= MIN_CONTENT_LENGTH
    # once padded with boilerplate) and dominated by the redirect notice itself.
    stub = (
        "You are being redirected. This is a non-JavaScript site interstitial page. "
        "Please enable JavaScript and reload, or click the link below to continue "
        "to your destination. " + ("Redirecting... " * 10)
    )
    assert ResearchWorkflowService.MIN_CONTENT_LENGTH <= len(stub) <= ResearchWorkflowService._STUB_MAX_LENGTH

    assert service._is_content_sufficient(stub) is False


def test_accepts_long_real_article_containing_incidental_stub_marker_phrase():
    """Regression test: a real, substantial article that merely mentions one of the
    stub marker phrases in passing (e.g. a comments widget's own JS notice) must not
    be rejected as a redirect stub — this false rejection was the root cause of
    valid DuckDuckGo search results being discarded and halting the workflow."""
    service = _service()
    real_article = (
        "The history of the region stretches back centuries, shaped by trade routes, "
        "shifting borders, and successive waves of settlement. Early records describe "
        "a thriving agricultural economy that later gave way to industrial expansion "
        "during the nineteenth century. Historians have documented extensive primary "
        "sources covering this period, including correspondence, trade ledgers, and "
        "government surveys that together paint a detailed picture of daily life. "
        "\n\nComments (14): To view and post comments, please enable JavaScript in "
        "your browser settings.\n\nRelated articles cover subsequent developments in "
        "greater depth, including the political changes of the twentieth century and "
        "their lasting effects on the region's cultural identity."
    )
    assert len(real_article) > ResearchWorkflowService._STUB_MAX_LENGTH
    assert "enable javascript" in real_article.lower()

    assert service._is_content_sufficient(real_article) is True


def test_accepts_long_real_article_without_any_stub_marker():
    service = _service()
    real_article = "This is a substantive, well-sourced paragraph about the topic. " * 10
    assert len(real_article) > ResearchWorkflowService.MIN_CONTENT_LENGTH

    assert service._is_content_sufficient(real_article) is True
