from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel

from app.auth.demo_auth import USERNAMES, USERS, create_token, current_user

router = APIRouter(prefix="/auth", tags=["Demo authentication"])


class LoginRequest(BaseModel):
    user_id: str
    password: str


@router.post("/login")
def login(body: LoginRequest):
    user_id = USERNAMES.get(body.user_id.lower().strip(), body.user_id)
    if user_id not in USERS or body.password != "1234":
        raise HTTPException(status_code=401, detail="Invalid username or password")
    return {"token": create_token(user_id), "user": USERS[user_id]}


@router.get("/me")
def me(user: Annotated[dict, Depends(current_user)]):
    return user


@router.post("/logout")
def logout():
    return {"ok": True}
