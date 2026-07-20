"""
Migration: ensure ON DELETE CASCADE on the project_excluded_feature table.

The table itself is created by SQLModel.metadata.create_all on startup, but its
foreign keys are created without cascade. This re-adds them with ON DELETE
CASCADE so deleting a project (or a feature) cleans up its exclusion rows.

Run: docker exec hyops_api python migrations/add_project_excluded_feature_cascade.py
Idempotent: safe to run multiple times.
"""

import asyncio
import os
import sys

from sqlalchemy import text
from sqlalchemy.ext.asyncio import create_async_engine

TABLE = "project_excluded_feature"


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
            print(f"  SKIP: {TABLE} does not exist yet "
                  "(created on app startup). Restart the API, then re-run.")
            await engine.dispose()
            return

        for column, ref_table in [("project_id", "project"), ("feature_id", "feature")]:
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
