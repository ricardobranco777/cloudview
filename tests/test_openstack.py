# pylint: disable=missing-module-docstring,missing-function-docstring,missing-class-docstring,redefined-outer-name,unused-argument

import pytest
from cloudview.openstack import get_creds


@pytest.fixture
def mock_openstack_env(monkeypatch):
    env_vars = {
        "OS_AUTH_URL": "http://example.com",
        "OS_USERNAME": "test_user",
        "OS_PASSWORD": "test_password",
        "OS_USER_DOMAIN_NAME": "test_domain",
        "OS_PROJECT_NAME": "test_project",
    }
    for var, value in env_vars.items():
        monkeypatch.setenv(var, value)
    yield
    for var in env_vars:
        try:
            monkeypatch.delenv(var)
        except KeyError:
            pass


def test_get_creds_with_valid_auth_url(mock_openstack_env):
    creds = get_creds()

    assert "key" in creds
    assert creds["key"] == "test_user"
    assert "secret" in creds
    assert creds["secret"] == "test_password"
    assert "ex_domain_name" in creds
    assert creds["ex_domain_name"] == "test_domain"
    assert "ex_tenant_name" in creds
    assert creds["ex_tenant_name"] == "test_project"
    assert "ex_force_auth_url" in creds
    assert creds["ex_force_auth_url"] == "http://example.com"
    assert "ex_force_base_url" in creds
    assert creds["ex_force_base_url"] == "http://example.com:8774/v2.1"
    assert "api_version" in creds
    assert creds["api_version"] == "2.2"


def test_get_creds_with_missing_auth_url(mock_openstack_env, monkeypatch):
    monkeypatch.delenv("OS_AUTH_URL")
    creds = get_creds()

    assert not creds
