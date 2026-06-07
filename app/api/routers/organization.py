import re
from datetime import datetime
from typing import Optional
from uuid import UUID

from fastapi import APIRouter, HTTPException, status
from sqlmodel import select

from app.database.models import Organization
from app.database.session import SessionDep
from app.api.schemas.organization import (
    OrganizationCreate, OrganizationRead, OrganizationUpdate,
    _validate_org_key,
)

router = APIRouter(prefix="/organization", tags=["Organization"])


# ── Key helpers ───────────────────────────────────────────────────────────────

def _derive_key(name: str) -> str:
    """
    Generate a candidate 3-letter key from an org name.
    Strategy: uppercase initials of the first 3 words, or leading letters for
    short names, then fall back to the raw alphabetic prefix.
    """
    letters_only = re.sub(r"[^A-Za-z]", " ", name).upper().strip()
    words = [w for w in letters_only.split() if w]

    if not words:
        return "ORG"
    if len(words) >= 3:
        return words[0][0] + words[1][0] + words[2][0]
    if len(words) == 2:
        # first 2 of word-0 + first of word-1  (e.g. "Hypatos GmbH" → "HYG")
        return (words[0][:2] + words[1][0]) if len(words[0]) >= 2 else (words[0][0] + words[1][:2])
    # single word → first 3 letters
    single = words[0]
    return single[:3] if len(single) >= 3 else single[:2] if len(single) >= 2 else single


async def _find_unique_key(
    name: str,
    session: SessionDep,
    exclude_id: Optional[UUID] = None,
) -> str:
    """
    Auto-generate a unique org key, preferring 3 chars.
    Tries: 3-letter candidate, then 4, 5, 6, 7 characters from the
    cleaned name.  Raises HTTPException 409 if nothing is available.
    """
    all_letters = re.sub(r"[^A-Za-z]", "", name).upper()
    base = _derive_key(name)

    # Candidates: base first, then progressively longer prefixes
    candidates: list[str] = [base]
    for length in range(4, 8):
        if length <= len(all_letters):
            candidates.append(all_letters[:length])

    for candidate in candidates:
        if len(candidate) < 2:
            continue
        q = select(Organization).where(Organization.key == candidate)
        if exclude_id:
            q = q.where(Organization.id != exclude_id)
        taken = (await session.execute(q)).scalars().first()
        if taken is None:
            return candidate

    raise HTTPException(
        status_code=status.HTTP_409_CONFLICT,
        detail=(
            f"Could not auto-generate a unique key for '{name}'. "
            "All short variants are already taken — please set the key manually."
        ),
    )


async def _check_key_unique(
    key: str,
    session: SessionDep,
    exclude_id: Optional[UUID] = None,
) -> None:
    """Raise 409 if the given key is already used by another org."""
    q = select(Organization).where(Organization.key == key)
    if exclude_id:
        q = q.where(Organization.id != exclude_id)
    conflict = (await session.execute(q)).scalars().first()
    if conflict:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=f"Key '{key}' is already used by another organisation.",
        )


# ── Endpoints ─────────────────────────────────────────────────────────────────

@router.get("/organizations", response_model=list[OrganizationRead])
async def get_all_organizations(session: SessionDep):
    result = await session.execute(select(Organization))
    return result.scalars().all()


@router.get("/", response_model=OrganizationRead)
async def get_organization(id: UUID, session: SessionDep):
    org = await session.get(Organization, id)
    if org is None:
        raise HTTPException(status_code=404, detail="Given id doesn't exist!")
    return org


@router.post("/", response_model=None)
async def submit_organization(
    organization: OrganizationCreate, session: SessionDep
) -> dict:
    """
    Create an organisation.  A unique 3-character key is auto-generated
    from the org name (extended to 4–7 chars if needed to avoid conflicts).
    """
    key = await _find_unique_key(organization.name, session)
    new_org = Organization(**organization.model_dump(), key=key)
    session.add(new_org)
    await session.commit()
    await session.refresh(new_org)
    return {"id": new_org.id}


@router.patch("/", response_model=OrganizationRead)
async def update_organization(
    id: UUID, organization_update: OrganizationUpdate, session: SessionDep
):
    """
    Update an organisation.  If `key` is included, it is validated
    (2–7 uppercase letters) and checked for uniqueness before saving.
    """
    update_data = organization_update.model_dump(exclude_none=True)
    if not update_data:
        raise HTTPException(status_code=400, detail="No data provided to update")

    org = await session.get(Organization, id)
    if org is None:
        raise HTTPException(status_code=404, detail="Given id doesn't exist!")

    # Key-specific uniqueness check (format was already validated by Pydantic)
    if "key" in update_data:
        await _check_key_unique(update_data["key"], session, exclude_id=id)

    update_data["updated_at"] = datetime.now()
    org.sqlmodel_update(update_data)
    session.add(org)
    await session.commit()
    await session.refresh(org)
    return org


@router.delete("/")
async def delete_organization(id: UUID, session: SessionDep) -> dict:
    org = await session.get(Organization, id)
    if org is None:
        raise HTTPException(status_code=404, detail="Given id doesn't exist!")
    await session.delete(org)
    await session.commit()
    return {"detail": f"Organization with id #{id} is deleted!"}
