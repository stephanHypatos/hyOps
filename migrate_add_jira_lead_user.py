"""
Migration: add jira_lead_user table and seed initial users.

Run inside the container:
    docker exec hyops_api python migrate_add_jira_lead_user.py
"""

import asyncio
import os
import sys

from sqlalchemy import text
from sqlalchemy.ext.asyncio import create_async_engine

# ── Seed data (matches LEAD_USER_MAPPING from the original blueprint) ─────────
INITIAL_LEAD_USERS = [
    ("elena.kuhn",         "712020:9de34ad3-f71e-4093-bd04-354b08b4a982"),
    ("jorge.costa",        "621d1acfb7e7c700715583e7"),
    ("stephan.kuche",      "630cd2ab3310c2492b59c51f"),
    ("yavuz.guney",        "712020:37b7fd3e-db24-433f-88d7-e84bb8d27551"),
    ("olga.milcent",       "712020:fdca536f-f91c-4d77-aebd-bbdd02825291"),
    ("andre.borzzatto",    "712020:886a6920-6c34-49c2-aa07-af749853588b"),
    ("ekaterina.mironova", "712020:45df7004-d0c2-4759-a3d6-c5737d5be307"),
]


async def run() -> None:
    db_url = os.environ.get("POSTGRESQL_URL")
    if not db_url:
        print("ERROR: POSTGRESQL_URL not set", file=sys.stderr)
        sys.exit(1)

    engine = create_async_engine(db_url, echo=False)

    async with engine.begin() as conn:
        # ── 1. Create table ────────────────────────────────────────────────────
        await conn.execute(text("""
            CREATE TABLE IF NOT EXISTS jira_lead_user (
                id              UUID        PRIMARY KEY DEFAULT gen_random_uuid(),
                username        TEXT        NOT NULL UNIQUE,
                jira_account_id TEXT        NOT NULL,
                created_at      TIMESTAMPTZ NOT NULL DEFAULT now()
            );
        """))
        print("✓ Table 'jira_lead_user' ready")

        # ── 2. Seed initial users (skip if already present) ───────────────────
        inserted = 0
        for username, account_id in INITIAL_LEAD_USERS:
            result = await conn.execute(
                text("""
                    INSERT INTO jira_lead_user (username, jira_account_id)
                    VALUES (:username, :account_id)
                    ON CONFLICT (username) DO NOTHING
                    RETURNING id
                """),
                {"username": username, "account_id": account_id},
            )
            if result.rowcount:
                inserted += 1
                print(f"  + seeded {username}")
            else:
                print(f"  · skipped {username} (already exists)")

        print(f"✓ Seeded {inserted} new lead user(s)")

    await engine.dispose()
    print("\nMigration complete.")


if __name__ == "__main__":
    asyncio.run(run())
