from typing import Annotated
from fastapi import APIRouter,Depends,HTTPException
from pydantic import BaseModel, Field
from sqlalchemy.engine import Connection
from app.auth.demo_auth import current_user, require_role
from app.db.session import get_db
from app.services.assistant_service import assistant_service
router=APIRouter(prefix="/assistant",tags=["Assistant"])
class ChatBody(BaseModel): opportunity_id:str; message:str; session_id:str|None=None
class ExecutiveChatBody(BaseModel):
    message: str = Field(min_length=1, max_length=2000)
    session_id: str | None = None
    period: str = "FY26"
    scope: str = "enterprise"
class ExecutiveReportBody(BaseModel):
    period: str = "FY26"
    scope: str = "enterprise"
    product_id: str | None = None

@router.post("/chat")
def chat(body:ChatBody,db:Annotated[Connection,Depends(get_db)],user:Annotated[dict,Depends(current_user)]):
    try:return assistant_service.chat(db,body.opportunity_id,body.message,user,body.session_id)
    except ValueError as e:raise HTTPException(404,str(e))
    except Exception as e:raise HTTPException(503,f"Assistant request failed: {type(e).__name__}")

@router.post("/executive/chat")
def executive_chat(
    body: ExecutiveChatBody,
    db: Annotated[Connection, Depends(get_db)],
    user: Annotated[dict, Depends(require_role("EXECUTIVE"))],
):
    try:
        return assistant_service.executive_chat(
            db, body.message.strip(), user, body.session_id, body.period, body.scope,
        )
    except ValueError as error:
        raise HTTPException(422, str(error)) from error
    except Exception as error:
        raise HTTPException(503, f"Assistant request failed: {type(error).__name__}") from error

@router.post("/executive/report")
def executive_report(
    body: ExecutiveReportBody,
    db: Annotated[Connection, Depends(get_db)],
    user: Annotated[dict, Depends(require_role("EXECUTIVE"))],
):
    try:
        return assistant_service.executive_report(
            db, user, period=body.period, scope=body.scope, product_id=body.product_id,
        )
    except ValueError as error:
        raise HTTPException(422, str(error)) from error
    except Exception as error:
        raise HTTPException(503, f"Report generation failed: {type(error).__name__}") from error

@router.get("/sessions/{session_id}")
def session_history(session_id:str,db:Annotated[Connection,Depends(get_db)],user:Annotated[dict,Depends(current_user)]):
    try:return assistant_service.history(db,session_id,user)
    except ValueError as e:raise HTTPException(404,str(e))

@router.get("/history/latest/{opportunity_id}")
def latest_history(opportunity_id:str,db:Annotated[Connection,Depends(get_db)],user:Annotated[dict,Depends(current_user)]):
    try:return assistant_service.latest_history(db,opportunity_id,user)
    except ValueError as e:raise HTTPException(404,str(e))
