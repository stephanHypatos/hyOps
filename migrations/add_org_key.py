"""
Migration: add `key` column to the `organization` table and auto-generate
unique keys for all existing rows.

Run inside the container:
    docker exec hyops_api python migrate_add_org_key.py
"""

import asyncio
import os
import re
import sys

from sqlalchemy import text
from sqlalchemy.ext.asyncio import create_async_engine


# ── Key generation (mirrors app/api/routers/organization.py) ─────────────────

def _derive_key(name: str) -> str:
    letters = re.sub(r"[^A-Za-z]", " ", name).upper().strip()
    words = [w for w in letters.split() if w]
    if not words:
        return "ORG"
    if len(words) >= 3:
        return words[0][0] + words[1][0] + words[2][0]
    if len(words) == 2:
        return (words[0][:2] + words[1][0]) if len(words[0]) >= 2 else (words[0][0] + words[1][:2])
    s = words[0]
    return s[:3] if len(s) >= 3 else s[:2] if len(s) >= 2 else s


def _key_candidates(name: str) -> list[str]:
    all_letters = re.sub(r"[^A-Za-z]", "", name).upper()
    base = _derive_key(name)
    candidates = [base]
    for length in range(4, 8):
        if length <= len(all_letters):
            candidates.append(all_letters[:length])
    return [c for c in candidates if len(c) >= 2]


async def run() -> None:
    db_url = os.environ.get("POSTGRESQL_URL")
    if not db_url:
        print("ERROR: POSTGRESQL_URL not set", file=sys.stderr)
        sys.exit(1)

    engine = create_async_engine(db_url, echo=False)

    async with engine.begin() as conn:
        # ── 1. Add column (idempotent) ─────────────────────────────────────────
        await conn.execute(text("""
            ALTER TABLE organization
            ADD COLUMN IF NOT EXISTS key VARCHAR(7) UNIQUE;
        """))
        print("✓ Column 'key' added (or already existed)")

        # ── 2. Fetch orgs that have no key yet ─────────────────────────────────
        rows = (await conn.execute(
            text("SELECT id, name FROM organization WHERE key IS NULL ORDER BY name")
        )).fetchall()

        if not rows:
            print("✓ All organizations already have a key — nothing to do")
        else:
            print(f"  Generating keys for {len(rows)} org(s)…")
            used: set[str] = set()

            # Also fetch already-used keys so we don't collide
            existing_keys = (await conn.execute(
                text("SELECT key FROM organization WHERE key IS NOT NULL")
            )).scalars().all()
            used.update(existing_keys)

            for org_id, org_name in rows:
                chosen = None
                for candidate in _key_candidates(org_name):
                    if candidate not in used:
                        chosen = candidate
                        break

                if chosen is None:
                    print(f"  ⚠️  Could not generate a unique key for '{org_name}' — skipping (set manually)")
                    continue

                await conn.execute(
                    text("UPDATE organization SET key = :key WHERE id = :id"),
                    {"key": chosen, "id": org_id},
                )
                used.add(chosen)
                print(f"  + {org_name!r:40s} → {chosen}")

        # ── 3. Create index (idempotent) ───────────────────────────────────────
        await conn.execute(text("""
            CREATE UNIQUE INDEX IF NOT EXISTS uq_organization_key ON organization(key)
            WHERE key IS NOT NULL;
        """))
        print("✓ Unique index on organization.key ready")

    await engine.dispose()
    print("\nMigration complete.")


if __name__ == "__main__":
    asyncio.run(run())
