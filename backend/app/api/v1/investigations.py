from typing import Annotated
from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from sqlalchemy.engine import Connection

from app.auth.demo_auth import current_user
from app.db.session import get_db
from app.services.investigation_service import investigation_service

router = APIRouter(tags=["Investigations"])

class AssignBody(BaseModel): expert_user_id: str = "USER-002"
class FindingBody(BaseModel): summary: str
class RecommendationBody(BaseModel): title: str; description: str; estimated_savings: float = 0

@router.get("/investigations")
def investigations(db: Annotated[Connection, Depends(get_db)], user: Annotated[dict, Depends(current_user)]):
    return {"items": investigation_service.list(db, user["id"] if user["role"] == "INVESTIGATION_EXPERT" else None)}

@router.get("/investigations/by-opportunity/{opportunity_id}")
def investigation(opportunity_id: str, db: Annotated[Connection, Depends(get_db)], user: Annotated[dict, Depends(current_user)]):
    result = investigation_service.get(db, opportunity_id)
    if not result: raise HTTPException(404, "Investigation not found")
    return result

@router.post("/opportunities/{opportunity_id}/assign")
def assign(opportunity_id: str, body: AssignBody, db: Annotated[Connection, Depends(get_db)], user: Annotated[dict, Depends(current_user)]):
    return investigation_service.assign(db, opportunity_id, body.expert_user_id, user)

@router.post("/opportunities/{opportunity_id}/withdraw")
def withdraw(opportunity_id: str, db: Annotated[Connection, Depends(get_db)], user: Annotated[dict, Depends(current_user)]):
    return investigation_service.withdraw(db, opportunity_id, user)

@router.post("/investigations/{investigation_id}/findings")
def finding(investigation_id: str, body: FindingBody, db: Annotated[Connection, Depends(get_db)], user: Annotated[dict, Depends(current_user)]):
    return investigation_service.finding(db, investigation_id, body.summary, user)

@router.post("/investigations/{investigation_id}/recommendations")
def recommendation(investigation_id: str, body: RecommendationBody, db: Annotated[Connection, Depends(get_db)], user: Annotated[dict, Depends(current_user)]):
    return investigation_service.recommendation(db, investigation_id, body.title, body.description, body.estimated_savings, user)

@router.post("/investigations/{investigation_id}/submit")
def submit(investigation_id: str, db: Annotated[Connection, Depends(get_db)], user: Annotated[dict, Depends(current_user)]):
    return investigation_service.submit(db, investigation_id, user)
