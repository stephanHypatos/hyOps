"""
Migration: reshape generated_document into a version ledger.

Generated documents used to overwrite a single file per template, with no
history and no database records at all (the table existed but was never
written to). Each generation now appends a row here.

Changes:
  + version_no        INTEGER  (1-based, per project+template)
  + file_path         VARCHAR  (absolute path of the version on disk)
  + file_format       VARCHAR  ("md" or "docx")
  + template_version  DOUBLE   (template version at generation time)
  - docx_file_url, pdf_file_url  (never used)

Run: docker exec hyops_api python migrations/add_generated_document_versioning.py
Idempotent: safe to run multiple times.
"""

import asyncio
import os
import sys

from sqlalchemy import text
from sqlalchemy.ext.asyncio import create_async_engine

ADD_COLUMNS = [
    ("version_no", "INTEGER NOT NULL DEFAULT 1"),
    ("file_path", "VARCHAR NOT NULL DEFAULT ''"),
    ("file_format", "VARCHAR NOT NULL DEFAULT 'md'"),
    ("template_version", "DOUBLE PRECISION"),
]

DROP_COLUMNS = ["docx_file_url", "pdf_file_url"]


async def _column_exists(conn, column: str) -> bool:
    result = await conn.execute(text("""
        SELECT 1 FROM information_schema.columns
        WHERE table_name = 'generated_document' AND column_name = :col
    """), {"col": column})
    return bool(result.scalar())


async def run():
    db_url = os.environ.get("POSTGRESQL_URL") or os.environ.get("DATABASE_URL")
    if not db_url:
        print("ERROR: POSTGRESQL_URL not set", file=sys.stderr)
        sys.exit(1)

    engine = create_async_engine(db_url, echo=False)

    async with engine.begin() as conn:
        exists = await conn.execute(text("""
            SELECT 1 FROM information_schema.tables
            WHERE table_name = 'generated_document'
        """))
        if not exists.scalar():
            print("  SKIP: generated_document table does not exist yet "
                  "(created on app startup). Restart the API, then re-run.")
            await engine.dispose()
            return

        for column, ddl in ADD_COLUMNS:
            if await _column_exists(conn, column):
                print(f"  SKIP {column} (already exists)")
                continue
            await conn.execute(text(
                f"ALTER TABLE generated_document ADD COLUMN {column} {ddl}"
            ))
            print(f"  Added generated_document.{column}")

        for column in DROP_COLUMNS:
            if not await _column_exists(conn, column):
                print(f"  SKIP {column} (already dropped)")
                continue
            await conn.execute(text(
                f"ALTER TABLE generated_document DROP COLUMN {column}"
            ))
            print(f"  Dropped generated_document.{column}")

        # One version number per project+template
        await conn.execute(text("""
            CREATE UNIQUE INDEX IF NOT EXISTS
            ix_generated_document_project_template_version
            ON generated_document (project_id, template_id, version_no)
        """))
        print("  Ensured unique index on (project_id, template_id, version_no)")

    await engine.dispose()
    print("\nMigration complete.")


if __name__ == "__main__":
    asyncio.run(run())
