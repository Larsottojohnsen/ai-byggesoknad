"""
Document Service – generates PDF reports and other documents.
Uses Jinja2 for templating and WeasyPrint for PDF rendering.
"""
import os
import uuid
from datetime import datetime, timezone
from typing import Dict, Any, Optional
import structlog
from jinja2 import Environment, FileSystemLoader, select_autoescape

from services.analysis_service import get_analysis_result
from models.schemas import RuleStatus

logger = structlog.get_logger()

TEMPLATES_DIR = os.path.join(os.path.dirname(__file__), "../templates")
UPLOADS_DIR = "./uploads"

# Ensure uploads dir exists
os.makedirs(UPLOADS_DIR, exist_ok=True)

# Jinja2 environment
jinja_env = Environment(
    loader=FileSystemLoader(TEMPLATES_DIR),
    autoescape=select_autoescape(["html"]),
)


async def generate_report(project_id: str, doc_type: str = "forhåndsvurdering") -> Dict[str, Any]:
    """Generate a PDF report for a project."""
    result = get_analysis_result(project_id)
    if not result:
        raise ValueError(f"Analyseresultat for prosjekt {project_id} ikke funnet")

    # Build template context
    pass_count = sum(1 for r in result.ruleResults if r.status == RuleStatus.pass_)
    warn_count = sum(1 for r in result.ruleResults if r.status == RuleStatus.warn)
    fail_count = sum(1 for r in result.ruleResults if r.status == RuleStatus.fail)

    application_status = (
        "Søknadspliktig" if result.applicationRequired is True
        else "Trolig ikke søknadspliktig" if result.applicationRequired is False
        else "Usikker"
    )

    measure_type = "Ukjent"
    if result.classification:
        measure_labels = {
            "bruksendring": "Bruksendring",
            "tilbygg": "Tilbygg",
            "påbygg": "Påbygg",
            "garasje": "Garasje",
            "carport": "Carport",
            "kjeller_innredning": "Kjeller innredning",
            "loft_innredning": "Loft innredning",
            "fasadeendring": "Fasadeendring",
            "støttemur": "Støttemur",
            "veranda": "Veranda",
            "tomtedeling": "Tomtedeling",
        }
        measure_type = measure_labels.get(result.classification.measureType.value, result.classification.measureType.value)

    # Format date
    try:
        dt = datetime.fromisoformat(result.analyzedAt.replace("Z", "+00:00"))
        analyzed_at_str = dt.strftime("%d.%m.%Y kl. %H:%M")
    except Exception:
        analyzed_at_str = result.analyzedAt

    # Get project data
    from services.analysis_service import _projects
    project_data = _projects.get(project_id, {})

    context = {
        "project_id": project_id,
        "address_text": project_data.get("addressText", "Ukjent adresse"),
        "intent_text": project_data.get("intentText", ""),
        "analyzed_at": analyzed_at_str,
        "risk_level": result.riskLevel.value,
        "application_status": application_status,
        "measure_type": measure_type,
        "pass_count": pass_count,
        "warn_count": warn_count,
        "fail_count": fail_count,
        "property": result.property,
        "plan": result.planLayer,
        "hazard": result.hazard,
        "ai_summary": result.aiSummary,
        "rule_results": result.ruleResults,
        "next_steps": result.nextSteps,
        "doc_requirements": result.documentRequirements,
        "warnings": result.warnings,
    }

    # Render HTML
    template = jinja_env.get_template("report_template.html")
    html_content = template.render(**context)

    # Generate PDF
    filename = f"rapport_{project_id[:8]}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.pdf"
    file_path = os.path.join(UPLOADS_DIR, filename)

    try:
        from weasyprint import HTML
        HTML(string=html_content).write_pdf(file_path)
        logger.info("pdf_generated", project_id=project_id, file=filename)
    except ImportError:
        # WeasyPrint not available – save HTML instead
        html_filename = filename.replace(".pdf", ".html")
        html_path = os.path.join(UPLOADS_DIR, html_filename)
        with open(html_path, "w", encoding="utf-8") as f:
            f.write(html_content)
        filename = html_filename
        file_path = html_path
        logger.warning("weasyprint_unavailable", fallback="html")
    except Exception as e:
        logger.error("pdf_generation_error", error=str(e))
        # Fallback to HTML
        html_filename = filename.replace(".pdf", ".html")
        html_path = os.path.join(UPLOADS_DIR, html_filename)
        with open(html_path, "w", encoding="utf-8") as f:
            f.write(html_content)
        filename = html_filename
        file_path = html_path

    return {
        "filename": filename,
        "url": f"/documents/download/{filename}",
        "type": doc_type,
        "projectId": project_id,
        "generatedAt": datetime.now(timezone.utc).isoformat(),
    }
