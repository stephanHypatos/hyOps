"""
Migration: drop requirement_description and solution_description from the
feature table.

These two fields were removed from the Feature master data — the form now only
captures Service Description and Deliverables. Any text previously stored in
these columns is permanently deleted by this migration.

Run: docker exec hyops_api python migrations/drop_feature_description_columns.py
Idempotent: safe to run multiple times.
"""

import asyncio
import os
import sys

from sqlalchemy import text
from sqlalchemy.ext.asyncio import create_async_engine

COLUMNS = ["requirement_description", "solution_description"]


async def run():
    db_url = os.environ.get("POSTGRESQL_URL") or os.environ.get("DATABASE_URL")
    if not db_url:
        print("ERROR: POSTGRESQL_URL not set", file=sys.stderr)
        sys.exit(1)

    engine = create_async_engine(db_url, echo=False)

    async with engine.begin() as conn:
        for column in COLUMNS:
            result = await conn.execute(text("""
                SELECT 1 FROM information_schema.columns
                WHERE table_name = 'feature' AND column_name = :col
            """), {"col": column})

            if not result.scalar():
                print(f"  SKIP feature.{column} (already dropped)")
                continue

            await conn.execute(text(f"ALTER TABLE feature DROP COLUMN {column}"))
            print(f"  Dropped feature.{column}")

    await engine.dispose()
    print("\nMigration complete.")


if __name__ == "__main__":
    asyncio.run(run())
