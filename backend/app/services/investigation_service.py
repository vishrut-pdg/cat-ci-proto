from app.repositories.investigation_repository import investigation_repository


class InvestigationService:
    def list(self, db, owner_id=None): return investigation_repository.list(db, owner_id)
    def get(self, db, opportunity_id): return investigation_repository.get_by_opportunity(db, opportunity_id)
    def assign(self, db, opportunity_id, expert_id, actor): return investigation_repository.assign(db, opportunity_id, expert_id, actor)
    def withdraw(self, db, opportunity_id, actor): return investigation_repository.withdraw(db, opportunity_id, actor)
    def finding(self, db, investigation_id, summary, actor): return investigation_repository.add_finding(db, investigation_id, summary, actor)
    def recommendation(self, db, investigation_id, title, description, savings, actor): return investigation_repository.add_recommendation(db, investigation_id, title, description, savings, actor)
    def submit(self, db, investigation_id, actor): return investigation_repository.submit(db, investigation_id, actor)


investigation_service = InvestigationService()
