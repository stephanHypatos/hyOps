import asyncio
from sqlalchemy import text
from app.database.session import engine


async def run():
    async with engine.begin() as conn:
        await conn.execute(text("""
            ALTER TABLE custom_section
            ADD COLUMN IF NOT EXISTS use_case_id UUID REFERENCES usecase(id) ON DELETE SET NULL
        """))
    print("Done: custom_section.use_case_id added.")


asyncio.run(run())
