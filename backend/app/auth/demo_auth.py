"""Demo-only authentication. Replace this module with SSO in production."""
from __future__ import annotations

import base64
import hashlib
import hmac
import json
import time
from dataclasses import dataclass

from fastapi import Depends, Header, HTTPException

from app.config import settings


USERS = {
    "USER-001": {"id": "USER-001", "name": "Sarah Smith", "role": "FINANCE_ANALYST", "email": "sarah.smith@cat.com"},
    "USER-002": {"id": "USER-002", "name": "Priya Patel", "role": "INVESTIGATION_EXPERT", "email": "priya.patel@cat.com"},
    "USER-031": {"id": "USER-031", "name": "Robert Miller", "role": "EXECUTIVE", "email": "robert.miller@cat.com"},
}

USERNAMES = {
    "sarah.smith": "USER-001",
    "priya.patel": "USER-002",
    "robert.miller": "USER-031",
}


def _secret() -> bytes:
    return getattr(settings, "demo_auth_secret", "cat-ci-demo-secret-change-me").encode()


def create_token(user_id: str) -> str:
    payload = base64.urlsafe_b64encode(json.dumps({"sub": user_id, "exp": int(time.time()) + 86400}).encode()).decode().rstrip("=")
    signature = hmac.new(_secret(), payload.encode(), hashlib.sha256).hexdigest()
    return f"{payload}.{signature}"


def decode_token(token: str) -> dict:
    try:
        payload, signature = token.split(".", 1)
        expected = hmac.new(_secret(), payload.encode(), hashlib.sha256).hexdigest()
        if not hmac.compare_digest(signature, expected):
            raise ValueError
        data = json.loads(base64.urlsafe_b64decode(payload + "=" * (-len(payload) % 4)))
        if data["exp"] < time.time() or data["sub"] not in USERS:
            raise ValueError
        return USERS[data["sub"]]
    except (ValueError, KeyError, json.JSONDecodeError):
        raise HTTPException(status_code=401, detail="Invalid or expired demo session")


def current_user(authorization: str | None = Header(default=None)) -> dict:
    if not authorization or not authorization.startswith("Bearer "):
        raise HTTPException(status_code=401, detail="Authentication required")
    return decode_token(authorization.removeprefix("Bearer "))


def require_role(*roles: str):
    """Create a FastAPI dependency that restricts a route to named roles."""
    def dependency(user: dict = Depends(current_user)) -> dict:
        if user["role"] not in roles:
            raise HTTPException(status_code=403, detail="This workspace is not available for your role")
        return user

    return dependency
