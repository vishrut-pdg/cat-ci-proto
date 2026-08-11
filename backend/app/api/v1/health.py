from typing import Annotated

from fastapi import APIRouter, Depends
from sqlalchemy import text
from sqlalchemy.engine import Connection

from app.db.session import get_db


router = APIRouter(
    tags=["Health"],
)


@router.get("/health")
def health_check(
    db: Annotated[
        Connection,
        Depends(get_db),
    ],
):
    db.execute(
        text("SELECT 1")
    )

    return {
        "status": "ok",
        "database": "connected",
    }