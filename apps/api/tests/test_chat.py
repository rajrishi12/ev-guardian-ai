def test_gemini_deprecated_model_falls_back_gracefully(client, monkeypatch):
    """Simulates exactly what happened with gemini-2.0-flash being shut down:
    the API returns 404 for the configured model. The agent must catch this,
    log it, and fall back — not crash the chat endpoint."""
    import app.agents.chat_agent as chat_agent

    class FakeResp:
        status_code = 404
        text = '{"error": {"message": "model not found"}}'

    def fake_post(*args, **kwargs):
        return FakeResp()

    monkeypatch.setattr(chat_agent, "GEMINI_API_KEY", "fake-key-for-test")
    monkeypatch.setattr(chat_agent.requests, "post", fake_post)

    r = client.post("/api/chat/", json={"session_id": "gemini-fail-test", "message": "hi"})
    assert r.status_code == 200
    body = r.json()
    assert body["mode"] == "fallback_config_error"
    assert "EV Guardian AI assistant" in body["reply"]  # still got a sensible reply, not a crash


def test_chat_status_reports_fallback_mode_without_key(client):
    r = client.get("/api/chat/status")
    assert r.status_code == 200
    body = r.json()
    assert body["gemini_configured"] is False
    assert body["model"]  # model name always reported, even unused


def test_chat_response_reports_mode(client):
    r = client.post("/api/chat/", json={"session_id": "mode-test", "message": "hii"})
    assert r.status_code == 200
    assert r.json()["mode"] == "fallback_no_key"


def _chat(client, msg, session="test-session"):
    r = client.post("/api/chat/", json={"session_id": session, "message": msg})
    assert r.status_code == 200
    return r.json()["reply"]


def test_chat_greeting_is_conversational_not_a_stats_dump(client):
    reply = _chat(client, "hii")
    assert "EV Guardian AI assistant" in reply
    assert "vehicles active" not in reply  # must not dump raw fleet stats on a greeting


def test_chat_thanks_gets_a_polite_close(client):
    reply = _chat(client, "thanks!")
    assert "welcome" in reply.lower()


def test_chat_help_lists_capabilities(client):
    reply = _chat(client, "what can you do?")
    assert "Battery risk" in reply


def test_chat_supplier_question_not_hijacked_by_generic_risk_keyword(client):
    reply = _chat(client, "which suppliers are risky")
    assert "Supply chain risk" in reply


def test_chat_vehicle_lookup(client):
    reply = _chat(client, "show me EVG-TEST-01")
    assert "EVG-TEST-01" in reply


def test_chat_unrecognized_message_offers_help(client):
    reply = _chat(client, "asdkjaslkdj")
    assert "EV Guardian AI assistant" in reply
