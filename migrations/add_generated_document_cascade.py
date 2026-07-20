"""
Migration: ON DELETE CASCADE for generated_document foreign keys.

generated_document.template_id and .project_id are NOT NULL, so deleting a
template or project used to fail — SQLAlchemy tried to null the column out and
hit the constraint. Deleting a template now removes the documents generated
from it (the API warns with a version count first).

Run: docker exec hyops_api python migrations/add_generated_document_cascade.py
Idempotent: safe to run multiple times.
"""

import asyncio
import os
import sys

from sqlalchemy import text
from sqlalchemy.ext.asyncio import create_async_engine

TABLE = "generated_document"
FKS = [
    ("project_id", "project"),
    ("template_id", "document_template"),
]


async def run():
    db_url = os.environ.get("POSTGRESQL_URL") or os.environ.get("DATABASE_URL")
    if not db_url:
        print("ERROR: POSTGRESQL_URL not set", file=sys.stderr)
        sys.exit(1)

    engine = create_async_engine(db_url, echo=False)

    async with engine.begin() as conn:
        exists = await conn.execute(text("""
            SELECT 1 FROM information_schema.tables WHERE table_name = :t
        """), {"t": TABLE})
        if not exists.scalar():
            print(f"  SKIP: {TABLE} does not exist yet")
            await engine.dispose()
            return

        for column, ref_table in FKS:
            result = await conn.execute(text("""
                SELECT tc.constraint_name
                FROM information_schema.table_constraints tc
                JOIN information_schema.key_column_usage kcu
                  ON tc.constraint_name = kcu.constraint_name
                WHERE tc.table_name = :t
                  AND tc.constraint_type = 'FOREIGN KEY'
                  AND kcu.column_name = :col
            """), {"t": TABLE, "col": column})
            constraint_name = result.scalar()

            if constraint_name:
                await conn.execute(text(
                    f'ALTER TABLE {TABLE} DROP CONSTRAINT "{constraint_name}"'
                ))

            await conn.execute(text(f"""
                ALTER TABLE {TABLE}
                ADD CONSTRAINT {TABLE}_{column}_fkey
                FOREIGN KEY ({column}) REFERENCES {ref_table}(id)
                ON DELETE CASCADE
            """))
            print(f"  {TABLE}.{column} -> {ref_table}(id) ON DELETE CASCADE")

    await engine.dispose()
    print("\nMigration complete.")


if __name__ == "__main__":
    asyncio.run(run())
