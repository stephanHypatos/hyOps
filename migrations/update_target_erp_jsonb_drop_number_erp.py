import asyncio
from sqlalchemy import text
from app.database.session import engine


async def run():
    async with engine.begin() as conn:
        # Convert target_erp from TEXT to JSONB array
        await conn.execute(text("""
            ALTER TABLE project
            ALTER COLUMN target_erp TYPE JSONB
            USING CASE
                WHEN target_erp IS NULL OR target_erp = '' THEN '[]'::jsonb
                ELSE jsonb_build_array(target_erp)
            END
        """))

        # Drop number_erp_systems column
        await conn.execute(text("""
            ALTER TABLE project
            DROP COLUMN IF EXISTS number_erp_systems
        """))

    print("Done: target_erp converted to JSONB[], number_erp_systems dropped.")


asyncio.run(run())
