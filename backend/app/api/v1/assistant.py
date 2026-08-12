from typing import Annotated
from fastapi import APIRouter,Depends,HTTPException
from pydantic import BaseModel
from sqlalchemy.engine import Connection
from app.auth.demo_auth import current_user
from app.db.session import get_db
from app.services.assistant_service import assistant_service
router=APIRouter(prefix="/assistant",tags=["Assistant"])
class ChatBody(BaseModel): opportunity_id:str; message:str; session_id:str|None=None
@router.post("/chat")
def chat(body:ChatBody,db:Annotated[Connection,Depends(get_db)],user:Annotated[dict,Depends(current_user)]):
    try:return assistant_service.chat(db,body.opportunity_id,body.message,user,body.session_id)
    except ValueError as e:raise HTTPException(404,str(e))
    except Exception as e:raise HTTPException(503,f"Assistant request failed: {type(e).__name__}")

@router.get("/sessions/{session_id}")
def session_history(session_id:str,db:Annotated[Connection,Depends(get_db)],user:Annotated[dict,Depends(current_user)]):
    try:return assistant_service.history(db,session_id,user)
    except ValueError as e:raise HTTPException(404,str(e))

@router.get("/history/latest/{opportunity_id}")
def latest_history(opportunity_id:str,db:Annotated[Connection,Depends(get_db)],user:Annotated[dict,Depends(current_user)]):
    try:return assistant_service.latest_history(db,opportunity_id,user)
    except ValueError as e:raise HTTPException(404,str(e))
