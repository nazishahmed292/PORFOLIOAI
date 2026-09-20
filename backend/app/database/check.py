"""Database diagnostics.

    python -m app.database.check

Reports which database the backend connects to, whether the pgvector extension is
installed, whether migrations are applied, and how many rows each table holds. Exits with
status 1 when the database is unreachable or not at the latest migration, so it can also
be used as a deployment gate. The password in DATABASE_URL is never printed.
"""

import sys
from dataclasses import dataclass, field
from pathlib import Path

from alembic.config import Config
from alembic.runtime.migration import MigrationContext
from alembic.script import ScriptDirectory
from sqlalchemy import func, inspect, select, text
from sqlalchemy.engine import Engine, make_url

import app.models  # noqa: F401  (registers every table on Base.metadata)
from app.core.config import BACKEND_ROOT, get_settings
from app.database.base import Base
from app.database.session import build_engine


@dataclass
class DatabaseReport:
    url: str
    dialect: str
    server_version: str = ""
    pgvector_version: str | None = None
    current_revision: str | None = None
    head_revision: str | None = None
    missing_tables: list[str] = field(default_factory=list)
    row_counts: dict[str, int] = field(default_factory=dict)

    @property
    def up_to_date(self) -> bool:
        return self.current_revision == self.head_revision and not self.missing_tables

    @property
    def vector_ready(self) -> bool:
        return self.dialect != "postgresql" or self.pgvector_version is not None


def head_revision() -> str | None:
    config = Config(str(BACKEND_ROOT / "alembic.ini"))
    config.set_main_option("script_location", str(Path(BACKEND_ROOT / "alembic")))
    return ScriptDirectory.from_config(config).get_current_head()


def collect_report(engine: Engine) -> DatabaseReport:
    """Inspect `engine`. Raises if the database cannot be reached."""
    report = DatabaseReport(
        url=engine.url.render_as_string(hide_password=True),
        dialect=engine.dialect.name,
        head_revision=head_revision(),
    )
    with engine.connect() as connection:
        if report.dialect == "postgresql":
            report.server_version = connection.execute(text("SHOW server_version")).scalar_one()
            report.pgvector_version = connection.execute(
                text("SELECT extversion FROM pg_extension WHERE extname = 'vector'")
            ).scalar_one_or_none()
        else:
            report.server_version = connection.execute(text("SELECT sqlite_version()")).scalar_one()

        report.current_revision = MigrationContext.configure(connection).get_current_revision()
        existing = set(inspect(connection).get_table_names())
        expected = list(Base.metadata.tables)
        report.missing_tables = sorted(set(expected) - existing)
        for name in sorted(set(expected) & existing):
            table = Base.metadata.tables[name]
            report.row_counts[name] = connection.execute(
                select(func.count()).select_from(table)
            ).scalar_one()
    return report


def format_report(report: DatabaseReport) -> str:
    def mark(ok: bool) -> str:
        return "OK " if ok else "FAIL"

    lines = [
        f"Database        {report.url}",
        f"Server          {report.dialect} {report.server_version}",
    ]
    if report.dialect == "postgresql":
        version = report.pgvector_version or "NOT INSTALLED (run: CREATE EXTENSION vector;)"
        lines.append(f"[{mark(report.vector_ready)}] pgvector       {version}")
    lines.append(
        f"[{mark(report.up_to_date)}] migrations     current={report.current_revision or 'none'}"
        f"  head={report.head_revision}"
    )
    if report.missing_tables:
        lines.append(f"       missing tables: {', '.join(report.missing_tables)}")
        lines.append("       fix: run `alembic upgrade head` from the backend folder")
    if report.row_counts:
        lines.append("")
        lines.append("Rows per table")
        width = max(len(name) for name in report.row_counts)
        lines.extend(f"  {name.ljust(width)}  {count}" for name, count in report.row_counts.items())
    return "\n".join(lines)


def main() -> int:
    settings = get_settings()
    shown = make_url(settings.database_url).render_as_string(hide_password=True)
    engine = build_engine(settings.database_url)
    try:
        report = collect_report(engine)
    except Exception as error:  # noqa: BLE001 - print a readable reason instead of a traceback
        print(f"[FAIL] Cannot connect to {shown}\n       {type(error).__name__}: {error}")
        print("       Is the database running? Try: docker compose up -d db")
        return 1
    print(format_report(report))
    return 0 if report.up_to_date and report.vector_ready else 1


if __name__ == "__main__":
    sys.exit(main())
