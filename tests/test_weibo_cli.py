import json

from click.testing import CliRunner

from mcp_server_weibo import weibo_cli


def test_session_prints_validated_cli_session(monkeypatch):
    class Crawler:
        async def get_session(self):
            return {"login": True, "uid": "42"}

    monkeypatch.setattr(weibo_cli, "create_cli_crawler", Crawler)

    result = CliRunner().invoke(weibo_cli.cli, ["session"])

    assert result.exit_code == 0
    assert json.loads(result.output) == {"login": True, "uid": "42"}


def test_session_prints_null_when_no_valid_local_session(monkeypatch):
    class Crawler:
        async def get_session(self):
            return None

    monkeypatch.setattr(weibo_cli, "create_cli_crawler", Crawler)

    result = CliRunner().invoke(weibo_cli.cli, ["session"])

    assert result.exit_code == 0
    assert json.loads(result.output) is None
