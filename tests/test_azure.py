# pylint: disable=missing-module-docstring,missing-function-docstring,missing-class-docstring

from cloudview.azure import get_creds


def test_get_creds(monkeypatch):
    monkeypatch.setenv("AZURE_CLIENT_ID", "client_id")
    monkeypatch.setenv("AZURE_CLIENT_SECRET", "client_secret")
    monkeypatch.setenv("AZURE_TENANT_ID", "tenant_id")
    monkeypatch.setenv("AZURE_SUBSCRIPTION_ID", "subscription_id")

    creds = get_creds()

    assert "key" in creds
    assert creds["key"] == "client_id"

    assert "secret" in creds
    assert creds["secret"] == "client_secret"

    assert "tenant_id" in creds
    assert creds["tenant_id"] == "tenant_id"

    assert "subscription_id" in creds
    assert creds["subscription_id"] == "subscription_id"


def test_get_creds_with_multiple_env_vars(monkeypatch):
    monkeypatch.setenv("ARM_CLIENT_ID", "client_id")
    monkeypatch.setenv("AZURE_CLIENT_SECRET", "client_secret")
    monkeypatch.setenv("ARM_TENANT_ID", "tenant_id")
    monkeypatch.setenv("ARM_SUBSCRIPTION_ID", "subscription_id")

    creds = get_creds()

    assert "key" in creds
    assert creds["key"] == "client_id"

    assert "secret" in creds
    assert creds["secret"] == "client_secret"

    assert "tenant_id" in creds
    assert creds["tenant_id"] == "tenant_id"

    assert "subscription_id" in creds
    assert creds["subscription_id"] == "subscription_id"


def test_get_creds_missing_env_vars():
    creds = get_creds()

    assert "key" not in creds
    assert "secret" not in creds
    assert "tenant_id" not in creds
    assert "subscription_id" not in creds
