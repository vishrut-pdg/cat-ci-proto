import json
import logging
import os
import time
from uuid import uuid4

from sqlalchemy import text

from app.agents.prompts import get_persona_prompt
from app.agents.tools.executive_tools import get_executive_context
from app.agents.tools.opportunity_tools import get_grounded_context
from app.services.executive_report_pdf import build_executive_report_pdf
from app.services.report_storage import report_storage


logger = logging.getLogger(__name__)
EXECUTIVE_SCOPE_ID = "EXECUTIVE_PORTFOLIO"
EXECUTIVE_REPORT_SCOPE_ID = "EXECUTIVE_REPORT"


class AssistantService:
    def latest_history(self, db, opportunity_id: str, user: dict):
        session = db.execute(text("""
            SELECT id FROM telemetry.ai_sessions
            WHERE opportunity_id=:oid AND user_id=:uid
            ORDER BY last_activity_at DESC LIMIT 1
        """), {"oid": opportunity_id, "uid": user["id"]}).first()
        if not session:
            raise ValueError("Conversation not found")
        return self.history(db, session[0], user)

    def history(self, db, session_id: str, user: dict):
        session = db.execute(text("""
            SELECT id, opportunity_id FROM telemetry.ai_sessions
            WHERE id=:sid AND user_id=:uid
        """), {"sid": session_id, "uid": user["id"]}).mappings().first()
        if not session:
            raise ValueError("Conversation not found")
        rows = db.execute(text("""
            SELECT user_message, assistant_message, created_at
            FROM telemetry.ai_interactions
            WHERE session_id=:sid ORDER BY created_at
        """), {"sid": session_id}).mappings().all()
        messages = []
        for row in rows:
            messages.extend([
                {"role": "user", "content": row["user_message"], "created_at": row["created_at"]},
                {"role": "assistant", "content": row["assistant_message"], "created_at": row["created_at"]},
            ])
        return {"session_id": session_id, "opportunity_id": session["opportunity_id"], "messages": messages}

    def chat(self, db, opportunity_id: str, message: str, user: dict,
             session_id: str | None = None):
        started = time.perf_counter()
        context = get_grounded_context(db, opportunity_id)
        if not context["summary"]:
            raise ValueError("Opportunity not found")
        history = self._validated_history(db, session_id, user, opportunity_id)
        model = os.getenv("GEMINI_MODEL", "gemini-2.5-flash")
        answer, provider, provider_note = self._model_answer(
            message, context, user["role"], model, history,
            self._opportunity_fallback,
        )
        latency = round((time.perf_counter() - started) * 1000)
        sid = self._persist(
            db, session_id=session_id, scope_id=opportunity_id, user=user,
            message=message, answer=answer, model=model, latency=latency,
            tool_name="get_grounded_context",
            tool_arguments={"opportunity_id": opportunity_id},
        )
        return {
            "answer": answer, "session_id": sid, "model": model,
            "provider": provider, "provider_note": provider_note,
            "sources": [{"type": "opportunity", "label": "Live opportunity evidence"}],
        }

    def executive_chat(self, db, message: str, user: dict,
                       session_id: str | None = None,
                       period: str = "FY26", scope: str = "enterprise"):
        started = time.perf_counter()
        context = get_executive_context(db, period=period, scope=scope)
        history = self._validated_history(db, session_id, user, EXECUTIVE_SCOPE_ID)
        model = os.getenv("GEMINI_MODEL", "gemini-2.5-flash")
        answer, provider, provider_note = self._model_answer(
            message, context, "EXECUTIVE", model, history,
            self._executive_fallback,
        )
        latency = round((time.perf_counter() - started) * 1000)
        sid = self._persist(
            db, session_id=session_id, scope_id=EXECUTIVE_SCOPE_ID, user=user,
            message=message, answer=answer, model=model, latency=latency,
            tool_name="get_executive_context",
            tool_arguments={"period": period, "scope": scope},
        )
        return {
            "answer": answer, "session_id": sid, "model": model,
            "provider": provider, "provider_note": provider_note,
            "sources": [{"type": "portfolio", "label": f"Executive portfolio as of {context['as_of_date']}"}],
        }

    def executive_report(self, db, user: dict, *, period: str = "FY26",
                         scope: str = "enterprise", product_id: str | None = None):
        started = time.perf_counter()
        context = get_executive_context(
            db, period=period, scope=scope, product_id=product_id,
        )
        model = os.getenv("GEMINI_MODEL", "gemini-2.5-flash")
        narrative, provider, provider_note = self._model_answer(
            "Generate the executive report from the supplied portfolio evidence.",
            context, "EXECUTIVE_REPORT", model, [], self._executive_report_fallback,
        )
        pdf_bytes = build_executive_report_pdf(context, narrative)
        scope_name = product_id or scope
        file_name = f"CAT-Cost-Intelligence-{scope_name}-{period}.pdf"
        report_metadata = {
            "period": period, "scope": scope,
            "as-of-date": str(context["as_of_date"]), "provider": provider,
        }
        if product_id:
            report_metadata["product-id"] = product_id
        report_id = report_storage.store_pdf(
            pdf_bytes,
            file_name=file_name,
            metadata=report_metadata,
        )
        latency = round((time.perf_counter() - started) * 1000)
        session_id = self._persist(
            db, session_id=None, scope_id=EXECUTIVE_REPORT_SCOPE_ID, user=user,
            message=f"Generate {period} {scope} executive report", answer=narrative,
            model=model, latency=latency, tool_name="get_executive_context",
            tool_arguments={"period": period, "scope": scope, "product_id": product_id,
                            "format": "pdf", "storage": "minio", "report_id": report_id},
        )
        return {
            "as_of_date": context["as_of_date"], "period": period, "scope": scope,
            "narrative": narrative, "provider": provider, "provider_note": provider_note,
            "model": model, "session_id": session_id,
            "product_id": product_id, "file_name": file_name,
            "report_id": report_id,
            "download_url": f"/executive/reports/{report_id}/download",
            "storage": "minio",
        }

    @staticmethod
    def _validated_history(db, session_id, user, scope_id):
        if not session_id:
            return []
        session = db.execute(text("""
            SELECT id FROM telemetry.ai_sessions
            WHERE id=:sid AND user_id=:uid AND opportunity_id=:scope_id
        """), {"sid": session_id, "uid": user["id"], "scope_id": scope_id}).first()
        if not session:
            raise ValueError("Conversation not found")
        return db.execute(text("""
            SELECT user_message, assistant_message
            FROM telemetry.ai_interactions
            WHERE session_id=:sid ORDER BY created_at DESC LIMIT 8
        """), {"sid": session_id}).mappings().all()[::-1]

    @staticmethod
    def _persist(db, *, session_id, scope_id, user, message, answer, model,
                 latency, tool_name, tool_arguments):
        sid = session_id or f"AIS-{uuid4().hex.upper()}"
        interaction_id = f"AII-{uuid4().hex.upper()}"
        try:
            if session_id is None:
                db.execute(text("""
                    INSERT INTO telemetry.ai_sessions
                    (id,user_id,opportunity_id,role,created_at,last_activity_at)
                    VALUES (:id,:uid,:scope_id,:role,now(),now())
                """), {"id": sid, "uid": user["id"], "scope_id": scope_id, "role": user["role"]})
            db.execute(text("""
                INSERT INTO telemetry.ai_interactions
                (id,session_id,user_message,assistant_message,model_name,latency_ms,created_at,status)
                VALUES (:id,:sid,:question,:answer,:model,:latency,now(),'SUCCESS')
            """), {"id": interaction_id, "sid": sid, "question": message,
                     "answer": answer, "model": model, "latency": latency})
            db.execute(text("""
                INSERT INTO telemetry.agent_tool_calls
                (id,interaction_id,tool_name,arguments,duration_ms,success,created_at)
                VALUES (:id,:interaction_id,:tool_name,CAST(:arguments AS jsonb),:duration,true,now())
            """), {"id": f"AIT-{uuid4().hex.upper()}", "interaction_id": interaction_id,
                     "tool_name": tool_name, "arguments": json.dumps(tool_arguments), "duration": latency})
            db.execute(text("UPDATE telemetry.ai_sessions SET last_activity_at=now() WHERE id=:id"), {"id": sid})
            db.commit()
        except Exception:
            db.rollback()
            logger.exception("Assistant telemetry write failed")
        return sid

    def _model_answer(self, message, context, role, model, history, fallback):
        project = os.getenv("GOOGLE_CLOUD_PROJECT")
        location = os.getenv("GOOGLE_CLOUD_LOCATION", "global")
        provider_note = None
        if project:
            try:
                from google import genai
                client = genai.Client(vertexai=True, project=project, location=location)
                turns = "\n".join(
                    f"User: {item['user_message']}\nAssistant: {item['assistant_message']}"
                    for item in history
                )
                prompt = (
                    get_persona_prompt(role)
                    + "\n\nStructured evidence:\n" + json.dumps(context, default=str)
                    + "\n\nConversation so far:\n" + (turns or "No previous turns.")
                    + "\n\nCurrent user question: " + message
                )
                response = client.models.generate_content(model=model, contents=prompt)
                if response.text:
                    return response.text, "vertex_ai", None
            except Exception as exc:
                logger.exception("Vertex AI request failed")
                provider_note = f"Vertex AI unavailable: {type(exc).__name__}"
        else:
            provider_note = "GOOGLE_CLOUD_PROJECT is not configured"
        return fallback(message, context, history), "local_grounded_fallback", provider_note

    @staticmethod
    def _opportunity_fallback(message, context, history):
        summary = context["summary"]
        metrics = summary["metrics"]
        drivers = context["overview"]["cost_drivers"]
        top = ", ".join(
            f"{driver['name']} (USD {driver['impact_amount']:,.2f}/unit)"
            for driver in drivers[:3]
        ) or "no ranked drivers"
        question = message.lower()
        if history and (len(question.split()) < 6 or any(word in question.split() for word in ("it", "that", "those", "them"))):
            question = f"{history[-1]['user_message'].lower()} {question}"
        if "supplier" in question or "negotiat" in question:
            rows = context.get("suppliers", {}).get("suppliers", [])
            detail = "; ".join(
                f"{row['supplier_name']}: USD {row['unit_cost']:,.2f}/unit, {row['variance_percent']:+.1f}% vs peer"
                for row in rows[:3]
            ) or "Supplier evidence is unavailable."
        elif "logistic" in question or "freight" in question or "component" in question:
            rows = context.get("logistics", {}).get("components", [])
            detail = "; ".join(
                f"{row['name']}: USD {row['cost']:,.2f}/unit ({row['variance_percent']:+.1f}% vs peer)"
                for row in rows[:4]
            ) or "Logistics evidence is unavailable."
        elif "tariff" in question or "duty" in question or "import" in question:
            tariff = context.get("tariff", {})
            detail = (
                f"Import duty is USD {tariff.get('import_duty_per_unit', 0):,.2f}/unit versus "
                f"USD {tariff.get('peer_duty_per_unit', 0):,.2f}/unit for peers; annual avoidable "
                f"duty is USD {tariff.get('annual_duty_impact', 0):,.0f}."
            )
        elif "plant" in question or "volume" in question:
            rows = context.get("plants", {}).get("plants", [])
            detail = "; ".join(
                f"{row['plant_name']}: USD {row['unit_cost']:,.2f}/unit, {row['annual_volume']:,} units"
                for row in rows[:4]
            ) or "Plant evidence is unavailable."
        elif "next" in question or "recommend" in question or "action" in question:
            detail = f"Prioritize validation of {top}, then confirm volume and commercial evidence before assignment."
        else:
            detail = f"The leading evidence-based drivers are {top}."
        return (
            f"{summary['part']['name']} at {summary['plant']['plant_name']} costs "
            f"USD {metrics['unit_cost']:,.2f}/unit versus a USD {metrics['peer_average_cost']:,.2f} "
            f"peer benchmark ({metrics['variance_percent']:+.1f}% variance). {detail} Potential annual "
            f"savings are USD {metrics['potential_savings']:,.0f} at {metrics['confidence_score'] * 100:.0f}% confidence."
        )

    @staticmethod
    def _executive_fallback(message, context, history):
        question = message.lower()
        if history and len(question.split()) < 6:
            question = f"{history[-1]['user_message'].lower()} {question}"

        def usd(value):
            return f"USD {float(value):,.0f}"

        if "top" in question and "product" in question:
            rows = context["top_products"][:5]
            facts = "\n".join(
                f"- **{row['product_name']}** — {usd(row['potential_savings'])} potential savings; "
                f"{float(row['variance_percent']):.1f}% weighted variance."
                for row in rows
            )
            return f"The five highest-value products are:\n{facts}\n\nNext: open the leading product brief and validate its largest component gap."
        if "concentrat" in question or "greatest aggregate" in question:
            summary = context["summary"]
            facts = []
            for label, key in (("Plant", "top_plant"), ("Equipment category", "top_category"), ("Product", "top_product"), ("Component", "top_component")):
                item = summary.get(key)
                if item:
                    facts.append(f"- **{label}: {item['name']}** — {usd(item['potential_savings'])} across {item['attributed_opportunity_count']} attributed opportunities.")
            return "Value concentration by portfolio dimension:\n" + "\n".join(facts) + "\n\nThese dimensions overlap and should not be added together. Next: drill into the leading product or plant."
        if "decision" in question or "quarter" in question:
            rows = context["products_awaiting_decision"]
            if not rows:
                return "No products currently have opportunities awaiting review or submitted for decision in the selected period."
            facts = "\n".join(
                f"- **{row['product_name']}** — {row['opportunity_count']} items; {usd(row['potential_savings'])} potential savings."
                for row in rows
            )
            return f"Products with the most decision-stage value:\n{facts}\n\nNext: open the product brief and route its lead opportunity through the existing decision workflow."
        if "fast" in question or "quick" in question or "action" in question:
            facts = "\n".join(
                f"- **{row['title']}** — {usd(row['potential_savings'])}; {row['ease'].lower()} ease, "
                f"{float(row['confidence']) * 100:.0f}% confidence, {row['urgency'].lower()} urgency."
                for row in context["quick_wins"]
            )
            return f"The fastest evidence-backed actions are:\n{facts}\n\nNext: open the first opportunity brief and send it to an investigation expert."
        if "category" in question:
            facts = "\n".join(
                f"- **{row['category_name']}** — {usd(row['potential_savings'])}; "
                f"{row['product_count']} products and {float(row['cost_variance_percent']):.1f}% weighted variance."
                for row in context["categories"][:5]
            )
            return f"The highest-value equipment categories are:\n{facts}\n\nNext: open the leading category to see its product portfolio."
        if "driver" in question:
            if not context["cost_drivers"]:
                return "Cost drivers are evaluated within a selected product. Open a product brief to compare supplier price, tariff, logistics, volume, and specification evidence."
            facts = "\n".join(
                f"- **{row['driver_name']}** — {float(row['contribution_percent']):.1f}% of the explained gap."
                for row in context["cost_drivers"]
            )
            return f"The explained product cost gap is concentrated in:\n{facts}\n\nNext: review Cost Driver Analysis on the product brief."
        summary = context["summary"]
        return (
            f"The selected portfolio contains **{summary['opportunity_count']} opportunities** with "
            f"**{usd(summary['total_potential_savings'])}** in potential annual savings. Ask about top "
            "products, value concentration, decisions this quarter, fastest actions, or cost drivers."
        )

    @staticmethod
    def _executive_report_fallback(message, context, history):
        summary = context["summary"]
        money = lambda value: f"USD {float(value):,.0f}"
        leader = lambda key: summary[key]["name"] if summary.get(key) else "not available"
        wins = "\n".join(
            f"- {item['title']}: {money(item['potential_savings'])} at {float(item['confidence']) * 100:.0f}% confidence. {item['why_now']}"
            for item in context["quick_wins"][:5]
        )
        decisions = context.get("products_awaiting_decision", [])
        decision_text = "\n".join(
            f"- {item['product_name']}: {money(item['potential_savings'])} across {item['opportunity_count']} opportunities."
            for item in decisions[:5]
        ) or "- No products are currently recorded in a decision-stage status."
        category_text = "\n".join(
            f"- {item['category_name']}: {money(item['potential_savings'])} across {item['product_count']} configured products."
            for item in context.get("categories", [])[:5]
        ) or "- No equipment-category evidence is available."
        driver_text = "\n".join(
            f"- {item['driver_name']}: {float(item['contribution_percent']):.1f}% of the explained product gap."
            for item in context.get("cost_drivers", [])
        ) or "- Select a product to include its structured cost-driver analysis."
        scope_label = (
            f"the {context['top_products'][0]['product_name']} product view"
            if context.get("product_id") and context.get("top_products")
            else "the enterprise portfolio"
        )
        return (
            "## Executive summary\n"
            f"As of {context['as_of_date']}, {scope_label} contains {summary['opportunity_count']} current opportunities with {money(summary['total_potential_savings'])} in validated potential savings.\n\n"
            "## Category performance\n" + category_text + "\n\n"
            "## Product opportunities\n"
            f"The leading product is {leader('top_product')}.\n\n"
            "## Plant performance\n"
            f"The leading plant is {leader('top_plant')}.\n\n"
            "## Component opportunities\n"
            f"The leading component is {leader('top_component')}.\n\n"
            "## Cost driver analysis\n" + driver_text + "\n\n"
            "## Recommended actions\n" + wins + "\n\n"
            "## Decisions required\n" + decision_text +
            "\nRoute the selected opportunity into the existing investigation workflow before recording a recommendation or decision."
        )


assistant_service = AssistantService()
