"""
Migration: add ON DELETE CASCADE / SET NULL to all FK constraints
referencing `organization` and `user` tables.

- All tables referencing organization.id    → ON DELETE CASCADE
- User link tables (user_*, project_stakeholder) → ON DELETE CASCADE
- document_template.created_by_id           → nullable + ON DELETE SET NULL
- feature.owner_id                          → nullable + ON DELETE SET NULL
- project.deal_winner_id                    → nullable + ON DELETE SET NULL

Run: docker exec hyops_api python migrations/add_cascade_deletes.py
Idempotent: safe to run multiple times.
"""

import asyncio
import os
import sys

from sqlalchemy import text
from sqlalchemy.ext.asyncio import create_async_engine


# (table, column, constraint_name, referenced_table, delete_rule)
CASCADE_CHANGES = [
    # org-referencing → CASCADE
    ("erp_system",                    "organization_id", "erp_system_organization_id_fkey",                    "organization", "CASCADE"),
    ("organization_hystudio_company", "organization_id", "organization_hystudio_company_organization_id_fkey", "organization", "CASCADE"),
    ("organization_jira_project",     "organization_id", "organization_jira_project_organization_id_fkey",     "organization", "CASCADE"),
    ("organization_metabase_group",   "organization_id", "organization_metabase_group_organization_id_fkey",   "organization", "CASCADE"),
    ("organization_slack_channel",    "organization_id", "organization_slack_channel_organization_id_fkey",    "organization", "CASCADE"),
    ("organization_teams_group",      "organization_id", "organization_teams_group_organization_id_fkey",      "organization", "CASCADE"),
    ("project",                       "customer_id",     "project_customer_id_fkey",                           "organization", "CASCADE"),
    ('"user"',                        "organization_id", "user_organization_id_fkey",                          "organization", "CASCADE"),
    # user link tables → CASCADE
    ("project_stakeholder",   "user_id", "project_stakeholder_user_id_fkey",   '"user"', "CASCADE"),
    ("user_hystudio_company", "user_id", "user_hystudio_company_user_id_fkey", '"user"', "CASCADE"),
    ("user_language",         "user_id", "user_language_user_id_fkey",         '"user"', "CASCADE"),
    ("user_metabase_group",   "user_id", "user_metabase_group_user_id_fkey",   '"user"', "CASCADE"),
    ("user_skill",            "user_id", "user_skill_user_id_fkey",            '"user"', "CASCADE"),
    ("user_slack_channel",    "user_id", "user_slack_channel_user_id_fkey",    '"user"', "CASCADE"),
    ("user_teams_group",      "user_id", "user_teams_group_user_id_fkey",      '"user"', "CASCADE"),
    # content tables → SET NULL (columns made nullable first)
    ("document_template", "created_by_id", "document_template_created_by_id_fkey", '"user"', "SET NULL"),
    ("feature",           "owner_id",      "feature_owner_id_fkey",                '"user"', "SET NULL"),
    ("project",           "deal_winner_id","project_deal_winner_id_fkey",           '"user"', "SET NULL"),
]


async def run():
    db_url = os.environ.get("POSTGRESQL_URL") or os.environ.get("DATABASE_URL")
    if not db_url:
        print("ERROR: POSTGRESQL_URL not set", file=sys.stderr)
        sys.exit(1)

    engine = create_async_engine(db_url, echo=False)

    async with engine.begin() as conn:
        for table, column, constraint, ref_table, delete_rule in CASCADE_CHANGES:
            # Check if constraint still has the old NO ACTION rule
            result = await conn.execute(text("""
                SELECT rc.delete_rule
                FROM information_schema.table_constraints tc
                JOIN information_schema.referential_constraints rc
                  ON tc.constraint_name = rc.constraint_name
                WHERE tc.constraint_name = :name
                  AND tc.constraint_type = 'FOREIGN KEY'
            """), {"name": constraint})
            row = result.fetchone()

            if row is None:
                print(f"  SKIP {constraint} (constraint not found)")
                continue
            if row[0] != "NO ACTION":
                print(f"  SKIP {constraint} (already {row[0]})")
                continue

            # For SET NULL: drop NOT NULL constraint first
            if delete_rule == "SET NULL":
                await conn.execute(text(
                    f"ALTER TABLE {table} ALTER COLUMN {column} DROP NOT NULL"
                ))
                print(f"  Made {table}.{column} nullable")

            # Drop old FK and recreate with new delete rule
            await conn.execute(text(
                f'ALTER TABLE {table} DROP CONSTRAINT "{constraint}"'
            ))
            await conn.execute(text(
                f'ALTER TABLE {table} ADD CONSTRAINT "{constraint}" '
                f'FOREIGN KEY ({column}) REFERENCES {ref_table}(id) ON DELETE {delete_rule}'
            ))
            print(f"  Updated {constraint} → ON DELETE {delete_rule}")

    await engine.dispose()
    print("\nMigration complete.")


if __name__ == "__main__":
    asyncio.run(run())
