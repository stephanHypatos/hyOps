# hyOps — Admin Guide

This guide covers everything an admin needs to know to operate hyOps day-to-day: managing organisations, users, and third-party integrations.

---

## Table of Contents

1. [Accessing hyOps](#1-accessing-hyops)
2. [Organisations](#2-organisations)
3. [Users](#3-users)
4. [Integrations Overview](#4-integrations-overview)
5. [Microsoft Teams](#5-microsoft-teams)
6. [SharePoint](#6-sharepoint)
7. [Slack](#7-slack)
8. [Jira](#8-jira)
9. [Metabase](#9-metabase)
10. [Jira Settings — Lead Users](#10-jira-settings--lead-users)
11. [Running Migrations](#11-running-migrations)
12. [Troubleshooting](#12-troubleshooting)

---

## 1. Accessing hyOps

| Page | URL | Purpose |
|---|---|---|
| Organisations | http://localhost:8000 | Create / edit / delete organisations |
| Users | http://localhost:8000/users | Manage users |
| Integrations | http://localhost:8000/integrations | Set up per-org integrations |
| Projects | http://localhost:8000/projects | Manage customer projects |
| API Docs | http://localhost:8000/scalar | Interactive REST API reference |

> Replace `localhost:8000` with your production URL.

---

## 2. Organisations

### Creating an organisation
1. Go to the **Organisations** page.
2. Fill in the form:
   - **Name** — full legal or commercial name
   - **Type** — `customer`, `partner`, or `internal`
   - **Email** — primary contact email
   - **Industry** — select from the dropdown; choose **Other** and type in the free-text field if your industry isn't listed
   - **Country** — select from the ISO Alpha-2 dropdown (e.g. `DE - Germany`)
   - Optional: Regions of Operation, Number of Subsidiaries, Languages, Company Overview
3. Click **Create Organisation**.

A unique **key** (2–7 uppercase letters) is automatically generated from the org name (e.g. "Deutsche Bank AG" → `DBA`). You can change it after creation.

### Editing an organisation
Click **Edit** on any row. All fields are editable, including the **Key** field (shown only in edit mode).

**Key rules:**
- 2–7 uppercase letters A–Z only
- Must be unique across all organisations
- If you enter a duplicate, a 409 error will be shown

### Editing the key inline
In the Organisation List table, the **Key** badge is click-to-edit:
1. Click the grey key badge
2. Type the new key (auto-uppercased, letters only)
3. Press **Enter** or click ✓ to save, **Esc** or ✗ to cancel

### Deleting an organisation
Click **Delete** on the row and confirm. This removes the org from hyOps but does **not** delete any linked Teams group, Slack channels, or Jira projects.

---

## 3. Users

Navigate to **Users** (http://localhost:8000/users).

### User types
| Type | Description |
|---|---|
| `customer` | Client-side users at the customer organisation |
| `partner` | Third-party partner users (e.g. SI partners) |
| `internal` | Hypatos employees |

### User roles
| Role | Description |
|---|---|
| `admin` | Full access; added to both Slack channels when provisioned |
| `enduser` | Standard access |

### Integration impact
- **Internal** users are added to both Slack channels (`client-*` and `ext-partner-*`) when channels are created
- **Partner** users are added to the `ext-partner-*` channel only
- **Customer** users are not added to Slack channels automatically

---

## 4. Integrations Overview

All integrations are managed from **http://localhost:8000/integrations**.

The page shows a table of all organisations. Each row has a coloured badge if an integration is active, and a ⚙️ **Configure** button that opens the integration modal for that org.

| Column | What it shows |
|---|---|
| Teams | ✅ if a Teams group exists for the org |
| Slack | Channel IDs if channels exist |
| Jira | Project key + link to board if configured |
| Metabase | Group name if configured |

---

## 5. Microsoft Teams

### Create a Teams group for an org
1. Open the **Configure** modal for the org.
2. In the **Teams** section, click **🚀 Create Teams Group**.
3. The group is created in Azure AD with all current internal users added automatically.

### Link an existing Teams group
If a group already exists in Azure AD:
1. Open the **Configure** modal.
2. Enter the **External ID** (Azure AD group object ID) and a **Display Name**.
3. Click **Link**.

### Manage members
Once a Teams group exists, use the **Members** sub-panel inside the Teams section to view and remove members. New users are provisioned automatically when they are created in hyOps.

---

## 6. SharePoint

After a Teams group is linked:

1. Open the **Configure** modal → Teams section.
2. In the **📁 SharePoint** sub-panel, click **Copy template SharePoint folder to Teams**.
3. The system copies the standard `Project` folder (including all sub-folders and files) from the CSTemplates SharePoint site to the org's Teams SharePoint.
4. On success, a green **✓ Copied {date}** badge appears and persists across modal opens.

> The copy operation uses the Microsoft Graph API async copy endpoint. It may take a few seconds for large folder trees.

---

## 7. Slack

### Create channels for an org
1. Open the **Configure** modal → Slack section.
2. Two channels can be created independently:
   - **client-{org}** — internal Hypatos users only
   - **ext-partner-{org}** — internal + partner users
3. Click **Create** on the relevant channel card.

The channel is created as a **private** Slack group and the appropriate users are added automatically based on their type.

### View and remove members
Click **View Members** on a channel card to see who is in it. Click **Remove** next to any member to remove them.

### Remove a channel link
Click **Unlink** to disconnect the channel from hyOps. This does **not** archive or delete the Slack channel itself.

---

## 8. Jira

### Create a new Jira project (Option A)
1. Open the **Configure** modal → Jira section.
2. Enter a **Project Key** (2–7 uppercase letters, e.g. `ACM`).
   - The key must be unique in the Jira workspace
   - Reserved keys (internal Hypatos projects) are blocked
3. Select a **Lead** from the dropdown.
4. Click **🚀 Create Jira project**.

The project is created with:
- Name: `{org name} x Hypatos`
- Type: company-managed (Jira Core)
- Standard Hypatos workflow, issue type, and permission schemes pre-assigned
- `COE` and `administrators` groups added to the Admin role

### Link an existing Jira project (Option B)
1. In the Jira section, use Option B — enter the **Project Key** of an existing project.
2. Optionally enter a display name override.
3. Click **Link**.

### Unlink a Jira project
Click **Unlink** in the configured state. This removes the link in hyOps only — the Jira project is not deleted.

### Key validation rules
| Rule | Detail |
|---|---|
| Format | 2–7 uppercase letters A–Z only |
| Uniqueness | Must not already exist in the Jira workspace |
| Reserved keys | Keys used by internal Hypatos projects are blocked |

> **Tip:** The org's unique **key** field (visible in the Organisations table) is intended to become the default Jira project key in a future release.

---

## 9. Metabase

### Create a Metabase group
1. Open **Configure** → Metabase section.
2. Click **🚀 Create group in Metabase**.

### Link an existing group
Enter the numeric **Group ID** from Metabase and click **Link**.

### Unlink
Click **Unlink** to disconnect. Does not delete the group in Metabase.

---

## 10. Jira Settings — Lead Users

The **Jira Lead Users** list determines who appears in the Lead dropdown when creating a new Jira project. It is a global setting (not per-org).

### View lead users
At the bottom of the Integrations page, expand **🟦 Jira Settings — Lead Users** and click **🔍 Load lead users**.

### Add a lead user
1. Enter the **Username** (e.g. `jane.doe`)
2. Enter the **Jira Account ID** (found in Jira under user profile → `accountId`)
3. Click **+ Add**

### Remove a lead user
Click **Remove** on any row. This does not affect existing Jira projects — it only removes the user from future project creation dropdowns.

### Finding a Jira Account ID
1. Go to https://hypatos.atlassian.net
2. Open any issue → click the user's avatar → **Profile**
3. The URL contains the account ID: `.../jira/people/712020:abc123…`

Or via API:
```bash
curl -u email:token "https://hypatos.atlassian.net/rest/api/3/myself"
# "accountId" field in the response
```

---

## 11. Running Migrations

When a new version of hyOps requires database schema changes, migration scripts are provided at the repo root.

```bash
# Add the org key column (run once after upgrading)
docker exec hyops_api python migrate_add_org_key.py

# Add the Jira lead users table (run once after upgrading)
docker exec hyops_api python migrate_add_jira_lead_user.py
```

Each script is **idempotent** — safe to run multiple times. It will skip steps that are already done.

---

## 12. Troubleshooting

### App won't start
```bash
docker compose logs api -f
```
Common causes: missing `.env` variables, database unreachable.

### Teams channel creation returns 403
- Check that the Azure app registration has `GroupMember.ReadWrite.All` and `Group.ReadWrite.All` application permissions
- Ensure admin consent has been granted in Azure AD

### Slack channel not visible
- Confirm the bot token has `groups:write` and `groups:read` scopes
- The channel is **private** — users must be invited; it won't appear in search

### Jira project creation fails
- Verify `JIRA_EMAIL` and `JIRA_API_TOKEN` are correct in `.env`
- The API token must belong to an account with project-creation permissions
- Check that the key isn't in the reserved list or already taken

### SharePoint copy shows "0 of 0 items copied"
This was a cosmetic issue in older versions (the copy actually succeeded). After the fix, the badge shows **✓ Copied {date}** immediately and persists on modal reopen.

### Workflow scheme not applying to new Jira project
The scheme assignment is asynchronous. Refresh the Jira board after ~30 seconds. If the issue persists, the scheme IDs may have changed — check with the Jira admin and update the constants in `app/adapters/jira.py`.

### Key collision on org creation
If auto-generation fails (all short variants are taken), the API returns a 409 error with the message *"Could not auto-generate a unique key"*. Create the org without a key and set one manually via the inline edit in the table.
