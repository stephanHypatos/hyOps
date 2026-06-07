"""
Migration: add partner_id column to the project table and convert
partner_budget_hours / internal_budget_hours from Numeric to Integer.

Run: docker exec hyops_api python migrations/add_project_partner.py
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
        # 1. Add partner_id column (idempotent)
        result = await conn.execute(text("""
            SELECT 1 FROM information_schema.columns
            WHERE table_name = 'project' AND column_name = 'partner_id'
        """))
        if result.scalar():
            print("  SKIP partner_id column (already exists)")
        else:
            await conn.execute(text("""
                ALTER TABLE project
                ADD COLUMN partner_id UUID REFERENCES organization(id) ON DELETE SET NULL
            """))
            print("  Added project.partner_id (nullable FK → organization)")

        # 2. Convert partner_budget_hours from Numeric to Integer (idempotent)
        result = await conn.execute(text("""
            SELECT data_type FROM information_schema.columns
            WHERE table_name = 'project' AND column_name = 'partner_budget_hours'
        """))
        col_type = result.scalar()
        if col_type and col_type.lower() == 'integer':
            print("  SKIP partner_budget_hours (already integer)")
        else:
            await conn.execute(text("""
                ALTER TABLE project
                ALTER COLUMN partner_budget_hours TYPE INTEGER
                USING partner_budget_hours::INTEGER
            """))
            print("  Converted project.partner_budget_hours → INTEGER")

        # 3. Convert internal_budget_hours from Numeric to Integer (idempotent)
        result = await conn.execute(text("""
            SELECT data_type FROM information_schema.columns
            WHERE table_name = 'project' AND column_name = 'internal_budget_hours'
        """))
        col_type = result.scalar()
        if col_type and col_type.lower() == 'integer':
            print("  SKIP internal_budget_hours (already integer)")
        else:
            await conn.execute(text("""
                ALTER TABLE project
                ALTER COLUMN internal_budget_hours TYPE INTEGER
                USING internal_budget_hours::INTEGER
            """))
            print("  Converted project.internal_budget_hours → INTEGER")

    await engine.dispose()
    print("\nMigration complete.")


if __name__ == "__main__":
    asyncio.run(run())
