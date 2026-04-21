"""
PostgreSQL-backed project repository.
Replaces the in-memory dict in analysis_service with persistent storage.
Falls back gracefully to in-memory if DB is unavailable.
"""
import uuid
from datetime import datetime, timezone
from typing import Optional, Dict, Any
import structlog

logger = structlog.get_logger()

# In-memory fallback store
_memory_store: Dict[str, Dict[str, Any]] = {}


class ProjectRepository:
    """
    Handles all project persistence. Uses PostgreSQL when available,
    falls back to in-memory dict for local development without Docker.
    """

    def __init__(self, db_session=None):
        self.db = db_session
        self._use_db = db_session is not None

    async def create(self, data: Dict[str, Any]) -> Dict[str, Any]:
        project_id = str(uuid.uuid4())
        now = datetime.now(timezone.utc)
        project = {
            "id": project_id,
            "addressText": data.get("addressText", ""),
            "lat": data.get("lat", 0.0),
            "lng": data.get("lng", 0.0),
            "intentText": data.get("intentText", ""),
            "measureType": None,
            "status": "draft",
            "riskLevel": None,
            "applicationRequired": None,
            "aiSummary": None,
            "nextSteps": [],
            "documentRequirements": [],
            "warnings": [],
            "ruleResults": [],
            "property": None,
            "planLayer": None,
            "hazard": None,
            "classification": None,
            "analyzedAt": None,
            "createdAt": now.isoformat(),
            "updatedAt": now.isoformat(),
        }

        if self._use_db:
            try:
                await self._db_create(project)
            except Exception as e:
                logger.warning("db_create_failed", error=str(e), fallback="memory")
                self._use_db = False

        _memory_store[project_id] = project
        return project

    async def get(self, project_id: str) -> Optional[Dict[str, Any]]:
        # Try memory first (always up to date)
        if project_id in _memory_store:
            return _memory_store[project_id]

        if self._use_db:
            try:
                return await self._db_get(project_id)
            except Exception as e:
                logger.warning("db_get_failed", error=str(e))

        return None

    async def update(self, project_id: str, data: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        now = datetime.now(timezone.utc).isoformat()
        if project_id in _memory_store:
            _memory_store[project_id].update(data)
            _memory_store[project_id]["updatedAt"] = now

        if self._use_db:
            try:
                await self._db_update(project_id, data)
            except Exception as e:
                logger.warning("db_update_failed", error=str(e))

        return _memory_store.get(project_id)

    async def save_analysis_results(self, project_id: str, results: Dict[str, Any]) -> None:
        """Persist full analysis results including rule results and sub-objects."""
        update_data = {
            "status": "complete",
            "measureType": results.get("classification", {}).get("measureType"),
            "riskLevel": results.get("riskLevel"),
            "applicationRequired": results.get("applicationRequired"),
            "aiSummary": results.get("aiSummary"),
            "nextSteps": results.get("nextSteps", []),
            "documentRequirements": results.get("documentRequirements", []),
            "warnings": results.get("warnings", []),
            "ruleResults": results.get("ruleResults", []),
            "property": results.get("property"),
            "planLayer": results.get("planLayer"),
            "hazard": results.get("hazard"),
            "classification": results.get("classification"),
            "analyzedAt": results.get("analyzedAt"),
        }
        await self.update(project_id, update_data)

        if self._use_db:
            try:
                await self._db_save_rule_results(project_id, results.get("ruleResults", []))
                await self._db_save_plan_result(project_id, results.get("planLayer"))
                await self._db_save_hazard_result(project_id, results.get("hazard"))
            except Exception as e:
                logger.warning("db_save_analysis_failed", error=str(e))

    # ── DB implementations (async SQLAlchemy) ──────────────────────────────

    async def _db_create(self, project: Dict[str, Any]) -> None:
        from models.orm import Project
        from sqlalchemy import insert
        stmt = insert(Project).values(
            id=project["id"],
            address_text=project["addressText"],
            lat=project["lat"],
            lng=project["lng"],
            intent_text=project["intentText"],
            status="draft",
        )
        await self.db.execute(stmt)
        await self.db.commit()

    async def _db_get(self, project_id: str) -> Optional[Dict[str, Any]]:
        from models.orm import Project
        from sqlalchemy import select
        result = await self.db.execute(
            select(Project).where(Project.id == project_id)
        )
        row = result.scalar_one_or_none()
        if not row:
            return None
        return self._orm_to_dict(row)

    async def _db_update(self, project_id: str, data: Dict[str, Any]) -> None:
        from models.orm import Project
        from sqlalchemy import update
        field_map = {
            "status": "status",
            "riskLevel": "risk_level",
            "applicationRequired": "application_required",
            "aiSummary": "ai_summary",
            "nextSteps": "next_steps",
            "documentRequirements": "document_requirements",
            "warnings": "warnings",
            "measureType": "classified_measure_type",
            "analyzedAt": "analyzed_at",
        }
        db_data = {field_map[k]: v for k, v in data.items() if k in field_map}
        if db_data:
            await self.db.execute(
                update(Project).where(Project.id == project_id).values(**db_data)
            )
            await self.db.commit()

    async def _db_save_rule_results(self, project_id: str, rule_results: list) -> None:
        from models.orm import RuleResultORM
        from sqlalchemy import insert, delete
        # Clear old results first
        await self.db.execute(
            delete(RuleResultORM).where(RuleResultORM.project_id == project_id)
        )
        for rr in rule_results:
            await self.db.execute(insert(RuleResultORM).values(
                project_id=project_id,
                rule_code=rr.get("ruleCode", ""),
                rule_name=rr.get("ruleName", ""),
                rule_group=rr.get("ruleGroup", ""),
                status=rr.get("status", "unknown"),
                explanation=rr.get("explanation", ""),
                evidence_refs=rr.get("evidenceRefs", []),
                is_blocking=rr.get("blocking", False),
                source_version=rr.get("sourceVersion", "1.0"),
            ))
        await self.db.commit()

    async def _db_save_plan_result(self, project_id: str, plan: Optional[Dict]) -> None:
        if not plan:
            return
        from models.orm import PlanLayerResultORM
        from sqlalchemy import insert, delete
        await self.db.execute(
            delete(PlanLayerResultORM).where(PlanLayerResultORM.project_id == project_id)
        )
        await self.db.execute(insert(PlanLayerResultORM).values(
            project_id=project_id,
            plan_id=plan.get("planId"),
            plan_name=plan.get("planName"),
            plan_status=plan.get("planStatus", "ukjent"),
            areal_formal=plan.get("arealFormål", "ukjent"),
            hensynssoner=plan.get("hensynssoner", []),
            byggegrense=plan.get("byggegrense"),
            utnyttelsesgrad=plan.get("utnyttelsesgrad"),
            plan_url=plan.get("planUrl"),
        ))
        await self.db.commit()

    async def _db_save_hazard_result(self, project_id: str, hazard: Optional[Dict]) -> None:
        if not hazard:
            return
        from models.orm import HazardResultORM
        from sqlalchemy import insert, delete
        await self.db.execute(
            delete(HazardResultORM).where(HazardResultORM.project_id == project_id)
        )
        await self.db.execute(insert(HazardResultORM).values(
            project_id=project_id,
            flom_fare=hazard.get("flomFare", "ukjent"),
            skred_fare=hazard.get("skredFare", "ukjent"),
            flom_sone_id=hazard.get("flomSoneId"),
            skred_sone_id=hazard.get("skredSoneId"),
            notes=hazard.get("notes"),
        ))
        await self.db.commit()

    @staticmethod
    def _orm_to_dict(row) -> Dict[str, Any]:
        return {
            "id": row.id,
            "addressText": row.address_text,
            "lat": row.lat,
            "lng": row.lng,
            "intentText": row.intent_text,
            "measureType": row.classified_measure_type,
            "status": row.status,
            "riskLevel": row.risk_level,
            "applicationRequired": row.application_required,
            "aiSummary": row.ai_summary,
            "nextSteps": row.next_steps or [],
            "documentRequirements": row.document_requirements or [],
            "warnings": row.warnings or [],
            "createdAt": row.created_at.isoformat() if row.created_at else None,
            "updatedAt": row.updated_at.isoformat() if row.updated_at else None,
            "analyzedAt": row.analyzed_at.isoformat() if row.analyzed_at else None,
        }
