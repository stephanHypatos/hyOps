"""
Migration: convert go_live_regions, rollout_regions, project_risks
from TEXT → JSONB on the project table.

Existing text values (if any) are wrapped in a single-element JSON array.
Empty / NULL values become [].

Run: docker exec hyops_api python migrations/add_project_jsonb_regions_risks.py
"""

import asyncio
from sqlalchemy.ext.asyncio import create_async_engine
from sqlalchemy import text
from app.config import settings


async def run():
    engine = create_async_engine(settings.POSTGRESQL_URL, echo=True)
    async with engine.begin() as conn:
        for col in ("go_live_regions", "rollout_regions", "project_risks"):
            await conn.execute(text(f"""
                ALTER TABLE project
                ALTER COLUMN {col} TYPE JSONB
                USING CASE
                    WHEN {col} IS NULL OR {col} = ''
                    THEN '[]'::jsonb
                    ELSE jsonb_build_array({col})
                END
            """))
            print(f"  ✓ {col} converted to JSONB")

    print("Migration complete.")


if __name__ == "__main__":
    asyncio.run(run())
