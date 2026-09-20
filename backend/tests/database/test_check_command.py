"""`python -m app.database.check`: the diagnostic that explains an unmigrated database."""

from app.database.check import collect_report, format_report, head_revision

from .conftest import run_alembic


def test_reports_a_migrated_database_as_up_to_date(migrated_engine, backend):
    report = collect_report(migrated_engine)
    assert report.up_to_date and report.vector_ready
    assert report.current_revision == report.head_revision == head_revision()
    assert report.missing_tables == []
    assert report.row_counts["users"] == 0
    assert report.dialect == backend
    if backend == "postgresql":
        assert report.pgvector_version  # e.g. "0.6.0"


def test_reports_an_empty_database_as_needing_migration(empty_engine):
    report = collect_report(empty_engine)
    assert not report.up_to_date
    assert report.current_revision is None
    assert "users" in report.missing_tables

    text = format_report(report)
    assert "alembic upgrade head" in text and "FAIL" in text

    run_alembic(empty_engine, "upgrade", "head")
    assert collect_report(empty_engine).up_to_date  # ... and is fixed by migrating


def test_report_never_contains_the_password(migrated_engine):
    report = collect_report(migrated_engine)
    assert "portfolioai:portfolioai@" not in report.url  # PostgreSQL URLs carry a password
    assert "portfolioai:portfolioai@" not in format_report(report)
