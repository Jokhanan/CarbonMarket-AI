"""
REST API routes for reusable user profiles (technology, developer, participant).
"""
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from typing import Optional, Any

router = APIRouter(prefix="/profiles", tags=["profiles"])


class ProfileCreate(BaseModel):
    profile_type: str
    name: str
    description: Optional[str] = ""
    data: Optional[Any] = {}


class ProfileUpdate(BaseModel):
    name: str
    description: Optional[str] = ""
    data: Optional[Any] = {}


@router.get("")
def list_profiles(profile_type: Optional[str] = None):
    from carbongpt.repository.profile_store import list_profiles as _list
    return _list(profile_type=profile_type)


@router.get("/{profile_id}")
def get_profile(profile_id: int):
    from carbongpt.repository.profile_store import get_profile as _get
    p = _get(profile_id)
    if not p:
        raise HTTPException(status_code=404, detail="Profile not found")
    return p


@router.post("", status_code=201)
def create_profile(body: ProfileCreate):
    if body.profile_type not in ("technology", "developer", "participant"):
        raise HTTPException(status_code=422, detail="profile_type must be technology, developer, or participant")
    from carbongpt.repository.profile_store import create_profile as _create
    result = _create(
        profile_type=body.profile_type,
        name=body.name,
        description=body.description or "",
        data=body.data or {},
    )
    if not result:
        raise HTTPException(status_code=500, detail="Failed to create profile")
    return result


@router.put("/{profile_id}")
def update_profile(profile_id: int, body: ProfileUpdate):
    from carbongpt.repository.profile_store import update_profile as _update
    result = _update(
        profile_id=profile_id,
        name=body.name,
        description=body.description or "",
        data=body.data or {},
    )
    if not result:
        raise HTTPException(status_code=404, detail="Profile not found")
    return result


@router.delete("/{profile_id}", status_code=204)
def delete_profile(profile_id: int):
    from carbongpt.repository.profile_store import delete_profile as _delete
    ok = _delete(profile_id)
    if not ok:
        raise HTTPException(status_code=404, detail="Profile not found")
