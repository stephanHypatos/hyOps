import asyncio
from sqlalchemy import text
from app.database.session import engine


async def run():
    async with engine.begin() as conn:
        await conn.execute(text("""
            ALTER TABLE project
            ADD COLUMN IF NOT EXISTS custom_answers JSONB DEFAULT '{}'::jsonb
        """))
    print("Done: custom_answers column added to project.")


asyncio.run(run())
