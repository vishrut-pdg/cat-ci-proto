from typing import Any
from uuid import uuid4

from sqlalchemy import text
from sqlalchemy.engine import Connection


class InvestigationRepository:
    def list(self, db: Connection, owner_id: str | None = None) -> list[dict[str, Any]]:
        query = """
          SELECT i.id, i.opportunity_id, i.owner_user_id, i.status,
                 i.assigned_at, i.due_at, i.progress_percent,
                 s.part_name, s.part_number, s.plant_name, s.country,
                 s.potential_savings, s.priority
          FROM workflow.investigations i
          JOIN opportunity.opportunity_summary s ON s.opportunity_id = i.opportunity_id
        """
        params = {}
        if owner_id:
            query += " WHERE i.owner_user_id = :owner_id"
            params["owner_id"] = owner_id
        query += " ORDER BY i.due_at, i.assigned_at DESC"
        return [dict(r) for r in db.execute(text(query), params).mappings().all()]

    def get_by_opportunity(self, db: Connection, opportunity_id: str) -> dict | None:
        row = db.execute(text("""
          SELECT i.*, COALESCE((SELECT count(*) FROM workflow.findings f WHERE f.investigation_id=i.id),0) evidence_collected,
          COALESCE((SELECT count(*) FROM workflow.expert_consultations e WHERE e.investigation_id=i.id),0) experts_consulted
          FROM workflow.investigations i WHERE i.opportunity_id=:oid ORDER BY i.assigned_at DESC LIMIT 1
        """), {"oid": opportunity_id}).mappings().first()
        return dict(row) if row else None

    def assign(self, db: Connection, opportunity_id: str, expert_id: str, actor: dict) -> dict:
        existing = self.get_by_opportunity(db, opportunity_id)
        if existing:
            investigation_id = existing["id"]
            db.execute(text("UPDATE workflow.investigations SET owner_user_id=:expert, status='IN_PROGRESS' WHERE id=:id"), {"expert": expert_id, "id": investigation_id})
        else:
            investigation_id = f"INV-{uuid4().hex[:10].upper()}"
            db.execute(text("""INSERT INTO workflow.investigations
              (id, opportunity_id, owner_user_id, status, assigned_at, due_at, progress_percent)
              VALUES (:id,:oid,:expert,'IN_PROGRESS',now(),current_date+14,10)"""), {"id": investigation_id, "oid": opportunity_id, "expert": expert_id})
        db.execute(text("UPDATE opportunity.opportunities SET status='ASSIGNED', current_owner_id=:expert, updated_at=now() WHERE id=:oid"), {"expert": expert_id, "oid": opportunity_id})
        self.event(db, opportunity_id, "EXPERT_ASSIGNED", actor, "investigation", investigation_id, {"expert_user_id": expert_id})
        db.commit()
        return self.get_by_opportunity(db, opportunity_id)

    def add_finding(self, db: Connection, investigation_id: str, summary: str, actor: dict) -> dict:
        fid = f"FND-{uuid4().hex[:10].upper()}"
        row = db.execute(text("INSERT INTO workflow.findings (id,investigation_id,summary,created_by,created_at) VALUES (:id,:iid,:summary,:uid,now()) RETURNING *"), {"id": fid, "iid": investigation_id, "summary": summary, "uid": actor["id"]}).mappings().one()
        oid = db.execute(text("SELECT opportunity_id FROM workflow.investigations WHERE id=:id"), {"id": investigation_id}).scalar_one()
        self.event(db, oid, "FINDING_ADDED", actor, "finding", fid, {"summary": summary})
        db.commit()
        return dict(row)

    def add_recommendation(self, db: Connection, investigation_id: str, title: str, description: str, savings: float, actor: dict) -> dict:
        rid = f"REC-{uuid4().hex[:10].upper()}"
        row = db.execute(text("""INSERT INTO workflow.recommendations
          (id,investigation_id,title,description,estimated_savings,priority,status,created_at)
          VALUES (:id,:iid,:title,:description,:savings,'HIGH','DRAFT',now()) RETURNING *"""), locals()).mappings().one()
        oid = db.execute(text("SELECT opportunity_id FROM workflow.investigations WHERE id=:id"), {"id": investigation_id}).scalar_one()
        self.event(db, oid, "RECOMMENDATION_CREATED", actor, "recommendation", rid, {"title": title, "estimated_savings": savings})
        db.commit()
        return dict(row)

    def submit(self, db: Connection, investigation_id: str, actor: dict) -> dict:
        row = db.execute(text("UPDATE workflow.investigations SET status='SUBMITTED', progress_percent=100 WHERE id=:id RETURNING *"), {"id": investigation_id}).mappings().one()
        db.execute(text("UPDATE opportunity.opportunities SET status='SUBMITTED_FOR_DECISION',updated_at=now() WHERE id=:oid"), {"oid": row["opportunity_id"]})
        self.event(db, row["opportunity_id"], "INVESTIGATION_SUBMITTED", actor, "investigation", investigation_id, {})
        db.commit()
        return dict(row)

    def event(self, db, oid, event_type, actor, entity_type, entity_id, payload):
        db.execute(text("""INSERT INTO opportunity.opportunity_events
          (id,opportunity_id,event_type,actor_user_id,actor_role,entity_type,entity_id,payload,created_at)
          VALUES (:id,:oid,:event,:uid,:role,:etype,:eid,CAST(:payload AS jsonb),now())"""), {
          "id": f"EVT-{uuid4().hex.upper()}", "oid": oid, "event": event_type, "uid": actor["id"], "role": actor["role"],
          "etype": entity_type, "eid": entity_id, "payload": __import__("json").dumps(payload)})


investigation_repository = InvestigationRepository()
