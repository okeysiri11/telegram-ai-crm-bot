"""Sprint 30.1 — Enterprise Authentication & Security Foundation tests."""

from __future__ import annotations

import pytest

from applications.enterprise_hub.security.authentication import AuthenticationService
from applications.enterprise_hub.security.providers.google import verify_google_id_token
from applications.enterprise_hub.security.services import MFAService, SecurityDashboard
from applications.enterprise_hub.security.session_manager import SessionManager
from applications.enterprise_hub.shared.exceptions import ValidationError
from applications.enterprise_hub.shared.store import EnterpriseHubStore


@pytest.fixture
def store() -> EnterpriseHubStore:
    return EnterpriseHubStore()


def test_google_demo_token_verifies():
    token = 'google_demo_{"email":"beta@gmail.com","name":"Beta","sub":"google:beta"}'
    claims = verify_google_id_token(token)
    assert claims["email"] == "beta@gmail.com"
    assert claims["mode"] == "demo"


def test_google_login_auto_creates_account(store: EnterpriseHubStore):
    auth = AuthenticationService(store)
    token = 'google_demo_{"email":"first@gmail.com","name":"First User","sub":"g1"}'
    result = auth.login_google(id_token=token)
    assert result["identity"]["subject"] == "first@gmail.com"
    assert "employee" in result["identity"]["roles"] or result["identity"]["roles"]
    # second login reuses same identity
    again = auth.login_google(id_token=token)
    assert again["identity"]["identity_id"] == result["identity"]["identity_id"]


def test_register_and_password_login(store: EnterpriseHubStore):
    auth = AuthenticationService(store)
    reg = auth.register_local(
        email="new@example.corp",
        password="securepass1",
        name="New User",
        role="manager",
    )
    assert reg["identity"]["subject"] == "new@example.corp"
    login = auth.login_password(subject="new@example.corp", password="securepass1")
    assert login["success"] is True
    with pytest.raises(ValidationError):
        auth.login_password(subject="new@example.corp", password="wrong-password")


def test_legacy_identity_password_without_hash(store: EnterpriseHubStore):
    """Demo identities without password_hash still accept any non-empty secret."""
    from applications.enterprise_hub.security.identity_manager import IdentityManager

    auth = AuthenticationService(store)
    IdentityManager(store).register_or_get(
        subject="legacy@example.com",
        identity_type="user",
        roles=["employee"],
        attributes={"name": "Legacy"},
    )
    login = auth.login_password(subject="legacy@example.com", password="anything")
    assert login["success"] is True


def test_password_reset_issues_token(store: EnterpriseHubStore):
    auth = AuthenticationService(store)
    out = auth.request_password_reset(email="owner@demo.corp")
    assert out["status"] == "issued"
    assert out["reset_token"]


def test_demo_accounts_reset_to_demo_password(store: EnterpriseHubStore):
    auth = AuthenticationService(store)
    auth.register_local(
        email="owner@demo.corp",
        password="oldsecret9",
        name="Owner",
        role="company_owner",
    )
    with pytest.raises(ValidationError):
        auth.login_password(subject="owner@demo.corp", password="oldsecret9")
    reset = auth.reset_demo_passwords()
    assert "owner@demo.corp" in reset
    login = auth.login_password(subject="owner@demo.corp", password="demo")
    assert login["success"] is True


def test_mfa_org_policy_and_user_toggle(store: EnterpriseHubStore):
    from applications.enterprise_hub.security.identity_manager import IdentityManager

    identity = IdentityManager(store).register_or_get(
        subject="mfa@demo.corp",
        identity_type="user",
        roles=["employee"],
        attributes={},
    )
    mfa = MFAService(store)
    assert mfa.required_for(identity_id=identity["identity_id"], organization_id="org1")[
        "must_challenge"
    ] is False
    mfa.set_org_policy(organization_id="org1", require_mfa=True)
    req = mfa.required_for(identity_id=identity["identity_id"], organization_id="org1")
    assert req["must_challenge"] is True
    assert req["org_required"] is True
    mfa.set_user_mfa(identity_id=identity["identity_id"], enabled=True)
    assert store.isam_identities.get(identity["identity_id"])["mfa_enabled"] is True
    mfa.set_user_mfa(identity_id=identity["identity_id"], enabled=False)
    assert store.isam_identities.get(identity["identity_id"])["mfa_enabled"] is False


def test_session_terminate_all_and_trust(store: EnterpriseHubStore):
    from applications.enterprise_hub.security.identity_manager import IdentityManager

    identity = IdentityManager(store).register_or_get(
        subject="sess@demo.corp",
        identity_type="user",
        roles=["owner"],
        attributes={},
    )
    sessions = SessionManager(store)
    s1 = sessions.create(identity_id=identity["identity_id"], device="web", ip="1.1.1.1")
    sessions.create(identity_id=identity["identity_id"], device="mobile", ip="2.2.2.2")
    sessions.trust_device(session_id=s1["session_id"], trusted=True)
    listed = sessions.list_for_identity(identity_id=identity["identity_id"])
    assert len(listed) >= 2
    out = sessions.terminate_all(identity_id=identity["identity_id"])
    assert out["revoked"] >= 2
    assert sessions.list_for_identity(identity_id=identity["identity_id"]) == []


def test_owner_security_dashboard(store: EnterpriseHubStore):
    auth = AuthenticationService(store)
    auth.login_google(
        id_token='google_demo_{"email":"dash@gmail.com","name":"D","sub":"d1"}'
    )
    try:
        auth.login_password(subject="missing@x.com", password="x")
    except ValidationError:
        pass
    snap = SecurityDashboard(store).owner_security_snapshot()
    assert snap["dashboard_type"] == "owner_security"
    assert "active_sessions" in snap
    assert "failed_logins" in snap
    assert "audit_events" in snap
    assert snap["api_status"]["ok"] is True


def test_preferred_provider_is_google(store: EnterpriseHubStore):
    status = AuthenticationService(store).status()
    assert status["preferred"] == "google"
    assert "microsoft" in status["providers"]
    assert "telegram" in status["providers"]


def test_enterprise_roles_catalog():
    from applications.enterprise_hub.security.models import ROLES, ENTERPRISE_ROLE_ALIASES

    for role in (
        "owner",
        "administrator",
        "manager",
        "employee",
        "client",
        "dealer",
        "partner",
        "accountant",
        "lawyer",
        "production",
        "viewer",
    ):
        assert role in ROLES or role in ENTERPRISE_ROLE_ALIASES
