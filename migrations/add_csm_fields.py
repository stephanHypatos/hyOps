import asyncio
from sqlalchemy import text
from app.database.session import engine


async def run():
    async with engine.begin() as conn:
        # Add CSM/account fields to organization
        await conn.execute(text("""
            ALTER TABLE organization
            ADD COLUMN IF NOT EXISTS csm_id UUID,
            ADD COLUMN IF NOT EXISTS account_executive_id UUID,
            ADD COLUMN IF NOT EXISTS sales_representative_id UUID,
            ADD COLUMN IF NOT EXISTS account_status VARCHAR(20),
            ADD COLUMN IF NOT EXISTS health_score_question_id TEXT
        """))

        # Create account_health table
        await conn.execute(text("""
            CREATE TABLE IF NOT EXISTS account_health (
                id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
                org_id UUID NOT NULL,
                status VARCHAR(20) NOT NULL,
                comment TEXT,
                created_by_id UUID,
                created_at TIMESTAMP WITHOUT TIME ZONE DEFAULT now()
            )
        """))

        # Create contract table
        await conn.execute(text("""
            CREATE TABLE IF NOT EXISTS contract (
                id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
                org_id UUID NOT NULL,
                project_id UUID,
                name TEXT NOT NULL,
                type VARCHAR(20) NOT NULL DEFAULT 'MSA',
                status VARCHAR(20) NOT NULL DEFAULT 'active',
                url TEXT,
                start_date DATE,
                end_date DATE,
                renewal_date DATE,
                paid BOOLEAN NOT NULL DEFAULT FALSE,
                created_at TIMESTAMP WITHOUT TIME ZONE DEFAULT now()
            )
        """))

    print("Done: CSM fields added to organization, account_health and contract tables created.")


asyncio.run(run())
