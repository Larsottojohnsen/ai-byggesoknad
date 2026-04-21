"""
Analysis Service – orchestrates the full analysis pipeline:
1. address → coordinates
2. coordinates → property
3. coordinates → plan layers
4. coordinates → hazard data
5. user input → measure classification (AI)
6. rule engine → evaluation
7. AI → summary
8. persist results (PostgreSQL with in-memory fallback)
"""
from datetime import datetime, timezone
import structlog
from typing import Optional

from models.schemas import (
    CreateProjectRequest, Project, ProjectStatus,
    AnalysisResult, MeasureType
)
from providers.property_provider import get_property_provider
from providers.plan_provider import get_plan_provider
from providers.hazard_provider import get_hazard_provider
from rules.engine import get_rule_engine, RuleContext
from services.ai_orchestrator import get_ai_orchestrator
from services.project_repository import ProjectRepository

logger = structlog.get_logger()

# Singleton repository (in-memory fallback, no DB session needed for dev)
_repo = ProjectRepository()


async def create_project(req: CreateProjectRequest) -> Project:
    """Create a new project from user input."""
    project_data = await _repo.create({
        "addressText": req.addressText,
        "lat": req.lat,
        "lng": req.lng,
        "intentText": req.intentText,
    })
    logger.info("project_created", project_id=project_data["id"], address=req.addressText)
    return Project(
        id=project_data["id"],
        addressText=project_data["addressText"],
        lat=project_data["lat"],
        lng=project_data["lng"],
        intentText=project_data["intentText"],
        status=ProjectStatus.draft,
        createdAt=project_data["createdAt"],
        updatedAt=project_data["updatedAt"],
    )


async def analyze_project(project_id: str) -> AnalysisResult:
    """Run the full analysis pipeline for a project."""
    project_data = await _repo.get(project_id)
    if not project_data:
        raise ValueError(f"Project {project_id} not found")

    lat = project_data["lat"]
    lng = project_data["lng"]
    intent_text = project_data["intentText"]

    logger.info("analysis_started", project_id=project_id, lat=lat, lng=lng)
    await _repo.update(project_id, {"status": ProjectStatus.analyzing.value})

    # 1. AI: Classify measure type
    orchestrator = get_ai_orchestrator()
    classification = await orchestrator.classify_measure(intent_text)
    logger.info("classification_done", measure_type=classification.measureType.value)

    # 2. Property lookup
    property_provider = get_property_provider()
    property_data = await property_provider.lookup_by_coordinates(lat, lng)
    logger.info("property_done", property_id=property_data.id if property_data else None)

    # 3. Plan layer lookup
    plan_provider = get_plan_provider()
    plan_layer = await plan_provider.lookup(lat, lng)
    logger.info("plan_done", plan_status=plan_layer.planStatus.value if plan_layer else None)

    # 4. Hazard lookup
    hazard_provider = get_hazard_provider()
    hazard = await hazard_provider.lookup(lat, lng)
    logger.info("hazard_done", flom=hazard.flomFare.value, skred=hazard.skredFare.value)

    # 5. Rule engine evaluation
    rule_engine = get_rule_engine()
    ctx = RuleContext(
        measure_type=classification.measureType,
        plan=plan_layer,
        hazard=hazard,
        classification=classification,
    )
    rule_results = rule_engine.evaluate(ctx)
    risk_level = rule_engine.compute_risk_level(rule_results)
    application_required = rule_engine.compute_application_required(rule_results, ctx)
    next_steps = rule_engine.generate_next_steps(rule_results, application_required, ctx)
    doc_requirements = rule_engine.generate_document_requirements(application_required, ctx)

    logger.info(
        "rules_done",
        total=len(rule_results),
        risk=risk_level.value,
        app_required=application_required,
    )

    # 6. AI: Generate summary
    ai_summary = await orchestrator.summarize_analysis(
        intent_text=intent_text,
        classification=classification,
        plan=plan_layer,
        hazard=hazard,
        rule_results=rule_results,
        risk_level=risk_level,
        application_required=application_required,
    )

    # 7. Build warnings
    warnings = []
    if classification.confidence < 0.7:
        warnings.append(
            f"Tiltaksklassifiseringen er usikker ({int(classification.confidence*100)}% sikkerhet). "
            "Beskriv tiltaket mer detaljert for bedre vurdering."
        )
    if plan_layer and plan_layer.planStatus.value == "ukjent":
        warnings.append("Planstatus for eiendommen er ukjent. Kontakt kommunen for å avklare gjeldende regulering.")
    if hazard and hazard.flomFare.value == "ukjent":
        warnings.append("Faredata fra NVE er ikke tilgjengelig for denne eiendommen.")

    # 8. Assemble result
    analyzed_at = datetime.now(timezone.utc).isoformat()
    result = AnalysisResult(
        projectId=project_id,
        property=property_data,
        planLayer=plan_layer,
        hazard=hazard,
        classification=classification,
        ruleResults=rule_results,
        riskLevel=risk_level,
        applicationRequired=application_required,
        aiSummary=ai_summary,
        nextSteps=next_steps,
        documentRequirements=doc_requirements,
        warnings=warnings,
        analyzedAt=analyzed_at,
    )

    # 9. Persist results
    result_dict = result.model_dump()
    # Convert enums to values for storage
    result_dict["riskLevel"] = risk_level.value
    result_dict["classification"]["measureType"] = classification.measureType.value
    if result_dict.get("planLayer") and result_dict["planLayer"].get("planStatus"):
        result_dict["planLayer"]["planStatus"] = plan_layer.planStatus.value if plan_layer else "ukjent"
    if result_dict.get("hazard"):
        result_dict["hazard"]["flomFare"] = hazard.flomFare.value
        result_dict["hazard"]["skredFare"] = hazard.skredFare.value
    result_dict["ruleResults"] = [
        {**rr.model_dump(), "status": rr.status.value} for rr in rule_results
    ]

    await _repo.save_analysis_results(project_id, result_dict)
    logger.info("analysis_complete", project_id=project_id, risk=risk_level.value)
    return result


async def get_project(project_id: str) -> Optional[Project]:
    data = await _repo.get(project_id)
    if not data:
        return None
    return Project(
        id=data["id"],
        addressText=data["addressText"],
        lat=data["lat"],
        lng=data["lng"],
        intentText=data["intentText"],
        measureType=data.get("measureType"),
        status=ProjectStatus(data.get("status", "draft")),
        riskLevel=data.get("riskLevel"),
        applicationRequired=data.get("applicationRequired"),
        createdAt=data.get("createdAt"),
        updatedAt=data.get("updatedAt"),
    )


async def get_analysis_result(project_id: str) -> Optional[AnalysisResult]:
    data = await _repo.get(project_id)
    if not data or data.get("status") not in ("analyzed", "complete"):
        return None
    try:
        return AnalysisResult(
            projectId=data["id"],
            property=data.get("property"),
            planLayer=data.get("planLayer"),
            hazard=data.get("hazard"),
            classification=data.get("classification"),
            ruleResults=data.get("ruleResults", []),
            riskLevel=data.get("riskLevel", "ukjent"),
            applicationRequired=data.get("applicationRequired"),
            aiSummary=data.get("aiSummary"),
            nextSteps=data.get("nextSteps", []),
            documentRequirements=data.get("documentRequirements", []),
            warnings=data.get("warnings", []),
            analyzedAt=data.get("analyzedAt"),
        )
    except Exception as e:
        logger.warning("result_deserialize_failed", error=str(e))
        return None
