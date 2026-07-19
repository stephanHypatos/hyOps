"""
Migration: ensure ON DELETE CASCADE on the project_feature link table.

The table itself is created automatically by SQLModel.metadata.create_all on
startup, but its foreign keys are created WITHOUT cascade. This drops the
default FK constraints and re-adds them with ON DELETE CASCADE so that deleting
a project (or a feature) cleans up its project_feature link rows.

Run: docker exec hyops_api python migrations/add_project_feature_cascade.py
Idempotent: safe to run multiple times.
"""

import asyncio
import os
import sys

from sqlalchemy import text
from sqlalchemy.ext.asyncio import create_async_engine


async def run():
    db_url = os.environ.get("POSTGRESQL_URL") or os.environ.get("DATABASE_URL")
    if not db_url:
        print("ERROR: POSTGRESQL_URL not set", file=sys.stderr)
        sys.exit(1)

    engine = create_async_engine(db_url, echo=False)

    async with engine.begin() as conn:
        # Make sure the table exists before altering it.
        exists = await conn.execute(text("""
            SELECT 1 FROM information_schema.tables
            WHERE table_name = 'project_feature'
        """))
        if not exists.scalar():
            print("  SKIP: project_feature table does not exist yet "
                  "(it is created on app startup). Restart the API, then re-run.")
            await engine.dispose()
            return

        # (column, referenced table, desired cascade action)
        fks = [
            ("project_id", "project", "CASCADE"),
            ("feature_id", "feature", "CASCADE"),
        ]

        for column, ref_table, action in fks:
            # Find any existing FK constraint on this column
            result = await conn.execute(text("""
                SELECT tc.constraint_name
                FROM information_schema.table_constraints tc
                JOIN information_schema.key_column_usage kcu
                  ON tc.constraint_name = kcu.constraint_name
                WHERE tc.table_name = 'project_feature'
                  AND tc.constraint_type = 'FOREIGN KEY'
                  AND kcu.column_name = :col
            """), {"col": column})
            constraint_name = result.scalar()

            if constraint_name:
                await conn.execute(text(
                    f'ALTER TABLE project_feature DROP CONSTRAINT "{constraint_name}"'
                ))

            await conn.execute(text(f"""
                ALTER TABLE project_feature
                ADD CONSTRAINT project_feature_{column}_fkey
                FOREIGN KEY ({column}) REFERENCES {ref_table}(id)
                ON DELETE {action}
            """))
            print(f"  project_feature.{column} → {ref_table}(id) ON DELETE {action}")

    await engine.dispose()
    print("\nMigration complete.")


if __name__ == "__main__":
    asyncio.run(run())
