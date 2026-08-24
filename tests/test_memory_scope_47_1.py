"""
Sprint 47.1 — AI Agent Memory Architecture (scoped persistent memory).

Covers: the MemoryScope enum + derivation, the scope property on
MemoryPrincipal/MemoryRecord/BusinessFact/ProjectMemoryRecord, the
project_memory/user_memory DB migration, and — the highest-value part of this
sprint — that MemoryPrincipal ACL enforcement (can_read/can_write/can_delete)
is now actually wired into ContinuityStore's read/write paths and the
platform_memory facades built on it, closing real gaps found during the audit
(MemoryManager.pin() previously bypassed ACL entirely; MemoryManager.workspace()
read raw records without filter_readable).
"""

from __future__ import annotations

from pathlib import Path

import pytest

from platform_memory.scope import MemoryScope, resolve_memory_scope


class TestMemoryScopeDerivation:
    def test_no_identifiers_is_platform(self):
        assert resolve_memory_scope() == MemoryScope.PLATFORM

    def test_tenant_only_is_organization(self):
        assert resolve_memory_scope(tenant_id="t1") == MemoryScope.ORGANIZATION

    def test_tenant_and_vertical_is_vertical(self):
        assert resolve_memory_scope(tenant_id="t1", vertical="auto") == MemoryScope.VERTICAL

    def test_user_id_wins_over_tenant_and_vertical(self):
        assert (
            resolve_memory_scope(tenant_id="t1", vertical="auto", user_id="u1")
            == MemoryScope.USER
        )

    def test_customer_id_is_narrowest_even_with_user_set(self):
        assert (
            resolve_memory_scope(tenant_id="t1", vertical="auto", user_id="u1", customer_id="c1")
            == MemoryScope.CUSTOMER
        )

    def test_customer_alone_is_customer(self):
        assert resolve_memory_scope(customer_id="c1") == MemoryScope.CUSTOMER


class TestScopeOnDataclasses:
    def test_memory_principal_scope(self):
        from platform_memory.memory_permissions import MemoryPrincipal

        p = MemoryPrincipal(owner_id="u1")
        assert p.scope == MemoryScope.USER
        assert p.to_dict()["scope"] == "user"

        p2 = MemoryPrincipal(owner_id="u1", customer_id="c1")
        assert p2.scope == MemoryScope.CUSTOMER

    def test_memory_record_scope(self):
        from platform_memory.continuity_store import MemoryRecord

        rec = MemoryRecord(
            id="m1", owner_id="u1", company_id="c1", level="working", kind="note",
            title="t", content="c",
        )
        assert rec.scope == MemoryScope.USER
        assert rec.to_dict()["scope"] == "user"
        # tenant_id mirrors company_id (Sprint 47.0) unless set explicitly
        assert rec.tenant_id == "c1"

    def test_business_fact_scope_is_organization_by_default(self):
        from platform_memory.models import BusinessFact

        bf = BusinessFact(fact_id="f1", organization_id="org1", key="k", value="v")
        assert bf.scope == MemoryScope.ORGANIZATION
        assert bf.tenant_id == "org1"

        bf_vertical = BusinessFact(
            fact_id="f2", organization_id="org1", key="k", value="v", vertical="auto"
        )
        assert bf_vertical.scope == MemoryScope.VERTICAL

    def test_project_memory_record_scope(self):
        from platform_memory.models import ProjectMemoryRecord

        pmr = ProjectMemoryRecord(memory_id="m1", project_id="p1", content="c")
        assert pmr.scope == MemoryScope.PLATFORM  # no identifiers at all

        pmr_customer = ProjectMemoryRecord(
            memory_id="m2", project_id="p1", content="c", tenant_id="t1", customer_id="cust1"
        )
        assert pmr_customer.scope == MemoryScope.CUSTOMER


class TestProjectMemoryUserMemoryMigration:
    def test_orm_models_have_scope_columns(self):
        from database.models.project_memory import ProjectMemoryRow
        from database.models.user_memory import UserMemory

        project_cols = {c.name for c in ProjectMemoryRow.__table__.columns}
        assert {"tenant_id", "vertical"}.issubset(project_cols)
        # project_memory already had client_id as its CUSTOMER identifier —
        # must not gain a duplicate customer_id column (Sprint 47.1: no
        # duplicate scope logic).
        assert "client_id" in project_cols
        assert "customer_id" not in project_cols

        user_cols = {c.name for c in UserMemory.__table__.columns}
        assert {"tenant_id", "vertical", "customer_id"}.issubset(user_cols)

    def test_migration_file_present_and_chained_to_head(self):
        mig_dir = Path(__file__).resolve().parents[1] / "migrations" / "versions"
        mig = mig_dir / "v5p678901234_memory_scope_47_1.py"
        assert mig.exists()
        text = mig.read_text(encoding="utf-8")
        assert 'down_revision: Union[str, None] = "u4o567890123"' in text
        assert "project_memory" in text
        assert "user_memory" in text
        # non-destructive downgrade policy (matches u4o567890123's precedent)
        assert "def downgrade" in text


class TestContinuityStoreAclWiring:
    """Sprint 47.1: principal-aware save/get/remove/list_for on ContinuityStore.
    Omitting principal (the default) must behave exactly as it did in Sprint 47.0 —
    every pre-existing caller across platform_memory omits it implicitly via the
    facades, so this is the backward-compatibility contract those facades rely on."""

    def _fresh_store(self):
        from platform_memory.continuity_store import ContinuityStore

        return ContinuityStore()

    def _record(self, store, *, owner_id="u1", company_id="tenant-a", **kw):
        from platform_memory.continuity_store import MemoryRecord, new_id

        rec = MemoryRecord(
            id=new_id("m"),
            owner_id=owner_id,
            company_id=company_id,
            level=kw.pop("level", "working"),
            kind=kw.pop("kind", "note"),
            title=kw.pop("title", "t"),
            content=kw.pop("content", "c"),
            **kw,
        )
        store.save(rec)
        return rec

    def test_save_get_remove_without_principal_is_unchanged(self):
        store = self._fresh_store()
        rec = self._record(store)
        assert store.get(rec.id) is rec
        assert store.list_for(rec.owner_id) == [rec]
        assert store.remove(rec.id) is True
        assert store.get(rec.id) is None

    def test_get_denies_cross_tenant_read_when_principal_given(self):
        from platform_memory.memory_permissions import MemoryPrincipal

        store = self._fresh_store()
        rec = self._record(store, owner_id="u1", company_id="tenant-a")
        stranger = MemoryPrincipal(owner_id="u2", company_id="tenant-b", role="member")
        assert store.get(rec.id, principal=stranger) is None
        # the legitimate owner still gets it
        owner = MemoryPrincipal(owner_id="u1", company_id="tenant-a")
        assert store.get(rec.id, principal=owner) is rec

    def test_list_for_filters_out_unreadable_records(self):
        from platform_memory.memory_permissions import MemoryPrincipal

        store = self._fresh_store()
        mine = self._record(store, owner_id="u1", company_id="tenant-a", title="mine")
        # Someone else's record that happens to share owner_id in the raw
        # pre-filter path is not realistic, so instead assert the narrower
        # case: a principal from a different tenant querying the same
        # owner_id sees nothing once ACL is applied.
        stranger = MemoryPrincipal(owner_id="u1", company_id="tenant-b", role="member")
        assert store.list_for("u1", principal=stranger) == []
        owner = MemoryPrincipal(owner_id="u1", company_id="tenant-a")
        assert store.list_for("u1", principal=owner) == [mine]

    def test_save_denies_write_to_others_record_when_principal_given(self):
        from platform_memory.memory_permissions import MemoryPrincipal

        store = self._fresh_store()
        rec = self._record(store, owner_id="u1", company_id="tenant-a")
        rec.title = "tampered"
        stranger = MemoryPrincipal(owner_id="u2", company_id="tenant-a", role="member")
        assert store.save(rec, principal=stranger) is None

    def test_remove_denies_delete_of_others_record_when_principal_given(self):
        from platform_memory.memory_permissions import MemoryPrincipal

        store = self._fresh_store()
        rec = self._record(store, owner_id="u1", company_id="tenant-a")
        stranger = MemoryPrincipal(owner_id="u2", company_id="tenant-a", role="member")
        assert store.remove(rec.id, principal=stranger) is False
        assert store.get(rec.id) is not None  # still there


class TestMemoryManagerPinAclGapFixed:
    """Regression coverage for the concrete gap found during the Sprint 47.1 audit:
    MemoryManager.pin() previously only checked `rec.owner_id != owner_id` — a
    strictly narrower rule than can_write(), which also permits an admin/owner-role
    principal in the same tenant to act on another user's record (e.g. an owner
    curating a team member's saved notes). The old code silently rejected that
    legitimate case; can_write() (now wired in) correctly allows it. This test
    exercises exactly that delta — it would have failed against the pre-fix code."""

    @pytest.fixture(autouse=True)
    def _clean_store(self):
        from platform_memory.continuity_store import continuity_store

        continuity_store.clear()
        yield
        continuity_store.clear()

    def test_pin_rejects_unrelated_member_in_same_tenant(self):
        from platform_memory.memory_manager import memory_manager

        saved = memory_manager.save("u1", title="note", content="hello", company_id="tenant-a")
        memory_id = saved["id"]
        result = memory_manager.pin("u2", memory_id, company_id="tenant-a", role="member")
        assert result is None

    def test_pin_allows_owner_role_across_users_in_same_tenant(self):
        """The actual behavior change: an owner-role principal acting on a
        different user's record in the same tenant. can_write() allows this
        (record.tenant_id == principal.tenant_id branch); the old hand-rolled
        `rec.owner_id != owner_id` check in pin() did not."""
        from platform_memory.memory_manager import memory_manager

        saved = memory_manager.save("u1", title="note", content="hello", company_id="tenant-a")
        memory_id = saved["id"]
        result = memory_manager.pin("u2", memory_id, company_id="tenant-a", role="owner")
        assert result is not None
        assert result["pinned"] is True

    def test_pin_denies_owner_role_across_tenants(self):
        from platform_memory.memory_manager import memory_manager

        saved = memory_manager.save("u1", title="note", content="hello", company_id="tenant-a")
        memory_id = saved["id"]
        result = memory_manager.pin("u2", memory_id, company_id="tenant-b", role="owner")
        assert result is None

    def test_pin_allows_owner(self):
        from platform_memory.memory_manager import memory_manager

        saved = memory_manager.save("u1", title="note", content="hello", company_id="tenant-a")
        memory_id = saved["id"]
        result = memory_manager.pin("u1", memory_id, company_id="tenant-a")
        assert result is not None
        assert result["pinned"] is True


class TestMemoryManagerWorkspaceAclConsistency:
    """MemoryManager.workspace() now routes its raw continuity_store.list_for()
    call through the same principal-aware path (filter_readable) as every other
    read in this facade, for consistency and defense-in-depth. Note: because
    list_for(owner_id, company_id=...) already pre-filters to exactly one
    owner_id/company_id pair — the same pair can_read's first branch checks —
    filter_readable cannot exclude anything the pre-filter didn't already
    exclude for this call site. This test documents that the call is wired
    (no crash, correct data for the legitimate owner+tenant) rather than
    asserting an observable behavior change that doesn't exist here."""

    @pytest.fixture(autouse=True)
    def _clean_store(self):
        from platform_memory.continuity_store import continuity_store

        continuity_store.clear()
        yield
        continuity_store.clear()

    def test_workspace_returns_only_the_requested_owner_and_tenant(self):
        from platform_memory.memory_manager import memory_manager

        memory_manager.save(
            "u1", title="mine", content="tenant-a", kind="document", company_id="tenant-a"
        )
        memory_manager.save(
            "u1", title="other-tenant", content="tenant-b", kind="document", company_id="tenant-b"
        )
        ws = memory_manager.workspace("u1", company_id="tenant-a")
        doc_titles = [item["title"] for item in ws["documents"]]
        assert doc_titles == ["mine"]
