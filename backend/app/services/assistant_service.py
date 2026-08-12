import json
import logging
import os
import time
from uuid import uuid4
from sqlalchemy import text

from app.agents.prompts import SYSTEM_PROMPT
from app.agents.tools.opportunity_tools import get_grounded_context

logger = logging.getLogger(__name__)


class AssistantService:
    def latest_history(self, db, opportunity_id: str, user: dict):
        session = db.execute(text("SELECT id FROM telemetry.ai_sessions WHERE opportunity_id=:oid AND user_id=:uid ORDER BY last_activity_at DESC LIMIT 1"), {"oid":opportunity_id,"uid":user["id"]}).first()
        if not session: raise ValueError("Conversation not found")
        return self.history(db, session[0], user)

    def history(self, db, session_id: str, user: dict):
        session = db.execute(text("SELECT id,opportunity_id FROM telemetry.ai_sessions WHERE id=:sid AND user_id=:uid"), {"sid":session_id,"uid":user["id"]}).mappings().first()
        if not session: raise ValueError("Conversation not found")
        rows = db.execute(text("SELECT user_message,assistant_message,created_at FROM telemetry.ai_interactions WHERE session_id=:sid ORDER BY created_at"), {"sid":session_id}).mappings().all()
        messages=[]
        for row in rows:
            messages.extend([{"role":"user","content":row["user_message"],"created_at":row["created_at"]},{"role":"assistant","content":row["assistant_message"],"created_at":row["created_at"]}])
        return {"session_id":session_id,"opportunity_id":session["opportunity_id"],"messages":messages}

    def chat(self, db, opportunity_id: str, message: str, user: dict, session_id: str | None = None):
        started = time.perf_counter(); context = get_grounded_context(db, opportunity_id)
        if not context["summary"]: raise ValueError("Opportunity not found")
        sid = session_id or f"AIS-{uuid4().hex.upper()}"; iid = f"AII-{uuid4().hex.upper()}"
        history=[]
        if session_id:
            session = db.execute(text("SELECT id FROM telemetry.ai_sessions WHERE id=:sid AND user_id=:uid AND opportunity_id=:oid"), {"sid":sid,"uid":user["id"],"oid":opportunity_id}).first()
            if not session: raise ValueError("Conversation not found")
            history = db.execute(text("SELECT user_message,assistant_message FROM telemetry.ai_interactions WHERE session_id=:sid ORDER BY created_at DESC LIMIT 8"), {"sid":sid}).mappings().all()[::-1]
        model = os.getenv("GEMINI_MODEL", "gemini-2.5-flash")
        answer, provider, provider_note = self._model_answer(message, context, user["role"], model, history)
        latency = round((time.perf_counter()-started)*1000)
        try:
            if session_id is None:
                db.execute(text("INSERT INTO telemetry.ai_sessions (id,user_id,opportunity_id,role,created_at,last_activity_at) VALUES (:id,:uid,:oid,:role,now(),now())"), {"id":sid,"uid":user["id"],"oid":opportunity_id,"role":user["role"]})
            db.execute(text("""INSERT INTO telemetry.ai_interactions
              (id,session_id,user_message,assistant_message,model_name,latency_ms,created_at,status)
              VALUES (:id,:sid,:q,:a,:model,:latency,now(),'SUCCESS')"""), {"id":iid,"sid":sid,"q":message,"a":answer,"model":model,"latency":latency})
            db.execute(text("INSERT INTO telemetry.agent_tool_calls (id,interaction_id,tool_name,arguments,duration_ms,success,created_at) VALUES (:id,:iid,'get_grounded_context',CAST(:args AS jsonb),:duration,true,now())"), {"id":f"AIT-{uuid4().hex.upper()}","iid":iid,"args":json.dumps({"opportunity_id":opportunity_id}),"duration":latency})
            db.execute(text("UPDATE telemetry.ai_sessions SET last_activity_at=now() WHERE id=:id"), {"id":sid});db.commit()
        except Exception:
            db.rollback()
            logger.exception("Assistant telemetry write failed")
        return {"answer":answer,"session_id":sid,"model":model,"provider":provider,"provider_note":provider_note,"sources":[{"type":"opportunity","label":"Live opportunity evidence"}]}

    def _model_answer(self, message, context, role, model, history):
        project=os.getenv("GOOGLE_CLOUD_PROJECT"); location=os.getenv("GOOGLE_CLOUD_LOCATION","global")
        if project:
            try:
                from google import genai
                client=genai.Client(vertexai=True,project=project,location=location)
                turns="\n".join(f"User: {x['user_message']}\nAssistant: {x['assistant_message']}" for x in history)
                prompt=SYSTEM_PROMPT.format(role=role)+"\nStructured evidence:\n"+json.dumps(context,default=str)+"\nConversation so far:\n"+(turns or "No previous turns.")+"\nCurrent user question: "+message
                response=client.models.generate_content(model=model,contents=prompt)
                if response.text:return response.text, "vertex_ai", None
            except Exception as exc:
                logger.exception("Vertex AI request failed")
                provider_note = f"Vertex AI unavailable: {type(exc).__name__}"
        else:
            provider_note = "GOOGLE_CLOUD_PROJECT is not configured"
        s=context["summary"]; m=s["metrics"]; drivers=context["overview"]["cost_drivers"]
        top=", ".join(f"{d['name']} (USD {d['impact_amount']:,.2f}/unit)" for d in drivers[:3]) or "no ranked drivers"
        question = message.lower()
        # Let the deterministic demo fallback understand short follow-ups such as
        # "compare that" by carrying forward the most recent user topic.
        if history and (len(question.split()) < 6 or any(x in question.split() for x in ("it", "that", "those", "them"))):
            question = f"{history[-1]['user_message'].lower()} {question}"
        if "supplier" in question or "negotiat" in question:
            rows = context.get("suppliers", {}).get("suppliers", [])
            detail = "; ".join(f"{x['supplier_name']}: USD {x['unit_cost']:,.2f}/unit, {x['variance_percent']:+.1f}% vs peer" for x in rows[:3]) or "Supplier evidence is unavailable."
        elif "logistic" in question or "freight" in question or "component" in question:
            rows = context.get("logistics", {}).get("components", [])
            detail = "; ".join(f"{x['name']}: USD {x['cost']:,.2f}/unit ({x['variance_percent']:+.1f}% vs peer)" for x in rows[:4]) or "Logistics evidence is unavailable."
        elif "tariff" in question or "duty" in question or "import" in question:
            tariff = context.get("tariff", {})
            detail = (f"Import duty is USD {tariff.get('import_duty_per_unit', 0):,.2f}/unit versus USD {tariff.get('peer_duty_per_unit', 0):,.2f}/unit for peers; "
                      f"annual avoidable duty is USD {tariff.get('annual_duty_impact', 0):,.0f}.")
        elif "plant" in question or "volume" in question:
            rows = context.get("plants", {}).get("plants", [])
            detail = "; ".join(f"{x['plant_name']}: USD {x['unit_cost']:,.2f}/unit, {x['annual_volume']:,} units" for x in rows[:4]) or "Plant evidence is unavailable."
        elif "next" in question or "recommend" in question or "action" in question:
            detail = f"Prioritize validation of {top}, then confirm annual volume and supplier or logistics evidence before assigning an expert."
        else:
            detail = f"The leading evidence-based drivers are {top}."
        answer = (f"{s['part']['name']} at {s['plant']['plant_name']} costs USD {m['unit_cost']:,.2f}/unit versus a USD {m['peer_average_cost']:,.2f} peer benchmark "
                  f"(USD {m['variance_amount']:+,.2f}, {m['variance_percent']:+.1f}% variance). {detail} Potential annual savings are USD {m['potential_savings']:,.0f} at {m['confidence_score']*100:.0f}% confidence.")
        return answer, "local_grounded_fallback", provider_note


assistant_service=AssistantService()
