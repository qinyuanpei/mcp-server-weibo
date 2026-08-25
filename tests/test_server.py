"""Tests for the public server entry point."""

import sys

import pytest

from mcp_server_weibo import server


def test_main_uses_stdio_by_default(monkeypatch):
    called = []
    monkeypatch.setattr(sys, "argv", ["mcp-server-weibo"])
    monkeypatch.setattr(server, "run_as_stdio", lambda: called.append("stdio"))
    monkeypatch.setattr(server, "run_as_streamable_http", lambda: called.append("http"))

    server.main()

    assert called == ["stdio"]


def test_main_uses_http_mode(monkeypatch):
    called = []
    monkeypatch.setattr(sys, "argv", ["mcp-server-weibo", "http"])
    monkeypatch.setattr(server, "run_as_stdio", lambda: called.append("stdio"))
    monkeypatch.setattr(server, "run_as_streamable_http", lambda: called.append("http"))

    server.main()

    assert called == ["http"]


def test_main_rejects_removed_cookie_option(monkeypatch):
    monkeypatch.setattr(sys, "argv", ["mcp-server-weibo", "--cookie", "value"])

    with pytest.raises(SystemExit):
        server.main()
