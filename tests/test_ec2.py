# pylint: disable=missing-module-docstring,missing-function-docstring,missing-class-docstring

from cloudview.ec2 import get_creds


def test_get_creds(monkeypatch):
    monkeypatch.setenv("AWS_ACCESS_KEY_ID", "access_key")
    monkeypatch.setenv("AWS_SECRET_ACCESS_KEY", "secret_key")

    creds = get_creds()

    assert "key" in creds
    assert creds["key"] == "access_key"

    assert "secret" in creds
    assert creds["secret"] == "secret_key"


def test_get_creds_missing_env_vars():
    creds = get_creds()

    assert "key" not in creds
    assert "secret" not in creds
