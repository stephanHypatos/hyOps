import asyncio
from sqlalchemy import text
from app.database.session import engine


async def run():
    async with engine.begin() as conn:
        # Convert Postgres enum column to plain text
        await conn.execute(text("""
            ALTER TABLE subtype
            ALTER COLUMN name TYPE TEXT USING name::text
        """))
        # Drop the now-unused Postgres enum type (ignore if already gone)
        await conn.execute(text("""
            DROP TYPE IF EXISTS subtypename
        """))
    print("Done: subtype.name converted to TEXT.")


asyncio.run(run())
