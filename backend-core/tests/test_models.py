from backend_core.models import Agent, Base, Document, Tenant


def test_tenant_owned_tables_expose_tenant_id():
    assert "tenant_id" in Agent.__table__.c
    assert "tenant_id" in Document.__table__.c
    assert "id" in Tenant.__table__.c


def test_metadata_registers_phase1_tables():
    table_names = set(Base.metadata.tables)
    assert table_names == {"tenants", "agents", "documents"}
