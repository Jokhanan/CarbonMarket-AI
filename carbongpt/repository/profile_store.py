"""
CRUD operations for reusable user profiles (technology, developer, participant).
"""
import json
import logging
from typing import List, Optional

logger = logging.getLogger(__name__)


def _cursor():
    from carbongpt.repository.db import get_cursor
    return get_cursor(dict_cursor=True)


def _ensure_table():
    from carbongpt.repository.schema import ensure_schema
    try:
        ensure_schema()
    except Exception:
        pass


def list_profiles(profile_type: Optional[str] = None) -> List[dict]:
    """Return all profiles, optionally filtered by type."""
    try:
        with _cursor() as cur:
            if profile_type:
                cur.execute(
                    "SELECT id, profile_type, name, description, data, created_at, updated_at "
                    "FROM user_profiles WHERE profile_type = %s ORDER BY name",
                    (profile_type,),
                )
            else:
                cur.execute(
                    "SELECT id, profile_type, name, description, data, created_at, updated_at "
                    "FROM user_profiles ORDER BY profile_type, name"
                )
            rows = cur.fetchall()
            result = []
            for row in rows:
                r = dict(row)
                if isinstance(r.get("data"), str):
                    try:
                        r["data"] = json.loads(r["data"])
                    except Exception:
                        r["data"] = {}
                result.append(r)
            return result
    except Exception as e:
        logger.error("list_profiles error: %s", e)
        return []


def get_profile(profile_id: int) -> Optional[dict]:
    """Return a single profile by ID."""
    try:
        with _cursor() as cur:
            cur.execute(
                "SELECT id, profile_type, name, description, data, created_at, updated_at "
                "FROM user_profiles WHERE id = %s",
                (profile_id,),
            )
            row = cur.fetchone()
            if not row:
                return None
            r = dict(row)
            if isinstance(r.get("data"), str):
                try:
                    r["data"] = json.loads(r["data"])
                except Exception:
                    r["data"] = {}
            return r
    except Exception as e:
        logger.error("get_profile error: %s", e)
        return None


def create_profile(profile_type: str, name: str, description: str, data: dict) -> Optional[dict]:
    """Create a new profile. Returns the created record."""
    try:
        data_json = json.dumps(data) if isinstance(data, dict) else data or "{}"
        with _cursor() as cur:
            cur.execute(
                "INSERT INTO user_profiles (profile_type, name, description, data) "
                "VALUES (%s, %s, %s, %s::jsonb) RETURNING id, profile_type, name, description, data, created_at",
                (profile_type, name, description, data_json),
            )
            row = cur.fetchone()
            if not row:
                return None
            r = dict(row)
            if isinstance(r.get("data"), str):
                try:
                    r["data"] = json.loads(r["data"])
                except Exception:
                    r["data"] = {}
            return r
    except Exception as e:
        logger.error("create_profile error: %s", e)
        return None


def update_profile(profile_id: int, name: str, description: str, data: dict) -> Optional[dict]:
    """Update an existing profile. Returns updated record or None."""
    try:
        data_json = json.dumps(data) if isinstance(data, dict) else data or "{}"
        with _cursor() as cur:
            cur.execute(
                "UPDATE user_profiles SET name=%s, description=%s, data=%s::jsonb, updated_at=NOW() "
                "WHERE id=%s RETURNING id, profile_type, name, description, data, updated_at",
                (name, description, data_json, profile_id),
            )
            row = cur.fetchone()
            if not row:
                return None
            r = dict(row)
            if isinstance(r.get("data"), str):
                try:
                    r["data"] = json.loads(r["data"])
                except Exception:
                    r["data"] = {}
            return r
    except Exception as e:
        logger.error("update_profile error: %s", e)
        return None


def delete_profile(profile_id: int) -> bool:
    """Delete a profile. Returns True on success."""
    try:
        with _cursor() as cur:
            cur.execute("DELETE FROM user_profiles WHERE id = %s", (profile_id,))
            return True
    except Exception as e:
        logger.error("delete_profile error: %s", e)
        return False
