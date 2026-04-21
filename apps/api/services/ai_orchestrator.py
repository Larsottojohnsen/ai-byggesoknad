"""
AI Orchestrator for AI Byggesøknad.
Manages AI agents for classification, summarization, and document generation.
AI always works on top of structured data – never as the sole source of truth.
"""
import json
import structlog
from typing import Optional, List
from openai import AsyncOpenAI
from core.config import settings
from models.schemas import (
    MeasureClassification, MeasureType,
    RuleResult, PlanLayerResult, HazardResult,
    RiskLevel
)

logger = structlog.get_logger()

# Initialize OpenAI client
client = AsyncOpenAI(api_key=settings.openai_api_key) if settings.openai_api_key else None

MEASURE_TYPES_LIST = [
    "bruksendring", "tilbygg", "påbygg", "garasje", "carport",
    "kjeller_innredning", "loft_innredning", "fasadeendring",
    "terrenginngrep", "støttemur", "veranda", "tomtedeling", "annet"
]


class AIOrchestrator:
    """
    Orchestrates AI agents for the analysis pipeline.
    Guardrails:
    - AI never invents property or rule data
    - AI always marks uncertain assessments
    - All AI responses are schema-validated
    """

    async def classify_measure(self, intent_text: str) -> MeasureClassification:
        """
        Agent 1: Classify measure type from user's free text description.
        Returns structured classification with confidence score.
        """
        if not client or not settings.feature_ai_classification:
            return self._fallback_classification(intent_text)

        try:
            prompt = f"""Du er en ekspert på norsk plan- og bygningslovgivning.

Brukerens beskrivelse av tiltaket:
"{intent_text}"

Klassifiser tiltaket i én av følgende kategorier:
{', '.join(MEASURE_TYPES_LIST)}

Svar KUN med gyldig JSON i dette formatet:
{{
  "measureType": "<type>",
  "confidence": <0.0-1.0>,
  "requiresPermit": <true/false/null>,
  "requiresResponsibility": <true/false/null>,
  "notes": "<kort forklaring på norsk>"
}}

Regler:
- confidence = 1.0 betyr du er helt sikker
- requiresPermit = null betyr usikker
- Bruk alltid norsk i notes-feltet
"""

            response = await client.chat.completions.create(
                model=settings.openai_model,
                messages=[{"role": "user", "content": prompt}],
                response_format={"type": "json_object"},
                temperature=0.1,
                max_tokens=300,
            )

            content = response.choices[0].message.content
            data = json.loads(content)

            # Validate measure type
            measure_type_str = data.get("measureType", "ukjent")
            try:
                measure_type = MeasureType(measure_type_str)
            except ValueError:
                measure_type = MeasureType.ukjent

            return MeasureClassification(
                measureType=measure_type,
                confidence=float(data.get("confidence", 0.5)),
                requiresPermit=data.get("requiresPermit"),
                requiresResponsibility=data.get("requiresResponsibility"),
                notes=data.get("notes"),
            )

        except Exception as e:
            logger.error("ai_classify_error", error=str(e))
            return self._fallback_classification(intent_text)

    async def summarize_analysis(
        self,
        intent_text: str,
        classification: Optional[MeasureClassification],
        plan: Optional[PlanLayerResult],
        hazard: Optional[HazardResult],
        rule_results: List[RuleResult],
        risk_level: RiskLevel,
        application_required: Optional[bool],
    ) -> str:
        """
        Agent 2: Generate human-readable summary of the analysis.
        Works on top of structured data from rule engine.
        """
        if not client:
            return self._fallback_summary(risk_level, application_required)

        try:
            # Build structured context for AI
            context_parts = []

            if classification:
                context_parts.append(
                    f"Tiltakstype: {classification.measureType.value} "
                    f"(sikkerhet: {int(classification.confidence * 100)}%)"
                )

            if plan:
                context_parts.append(
                    f"Planstatus: {plan.planStatus.value}, arealformål: {plan.arealFormål}"
                )
                if plan.hensynssoner:
                    context_parts.append(f"Hensynssoner: {', '.join(plan.hensynssoner)}")

            if hazard:
                context_parts.append(
                    f"Flomfare: {hazard.flomFare.value}, skredfare: {hazard.skredFare.value}"
                )

            blocking_rules = [r for r in rule_results if r.blocking and r.status.value == "fail"]
            warn_rules = [r for r in rule_results if r.status.value == "warn"]

            if blocking_rules:
                context_parts.append(
                    f"Blokkerende funn: {'; '.join(r.ruleName for r in blocking_rules)}"
                )
            if warn_rules:
                context_parts.append(
                    f"Advarsler: {'; '.join(r.ruleName for r in warn_rules)}"
                )

            context_str = "\n".join(context_parts)
            app_text = (
                "Søknadspliktig" if application_required is True
                else "Trolig ikke søknadspliktig" if application_required is False
                else "Søknadsplikt usikker"
            )

            prompt = f"""Du er en hjelpsom rådgiver for byggesaker i Norge.

Brukerens tiltak: "{intent_text}"

Analyseresultat:
{context_str}
Risikonivå: {risk_level.value}
Søknadsstatus: {app_text}

Skriv en kort, klar og presis oppsummering (3-5 setninger) på norsk som:
1. Forklarer hva tiltaket sannsynligvis er
2. Sier om det krever søknad
3. Nevner de viktigste funnene
4. Gir ett konkret råd om neste steg

Bruk enkelt språk. Ikke bruk juridisk sjargong. Ikke dikte opp data.
Merk tydelig hvis noe er usikkert.
"""

            response = await client.chat.completions.create(
                model=settings.openai_model,
                messages=[{"role": "user", "content": prompt}],
                temperature=0.3,
                max_tokens=400,
            )

            return response.choices[0].message.content.strip()

        except Exception as e:
            logger.error("ai_summarize_error", error=str(e))
            return self._fallback_summary(risk_level, application_required)

    def _fallback_classification(self, intent_text: str) -> MeasureClassification:
        """Keyword-based fallback classification when AI is unavailable."""
        text_lower = intent_text.lower()

        keyword_map = {
            MeasureType.bruksendring: ["bruksendring", "endre bruk", "utleie", "boenhet", "hybel", "leilighet"],
            MeasureType.tilbygg: ["tilbygg", "utvide", "utvidelse", "bygge til"],
            MeasureType.garasje: ["garasje", "bilgarasje"],
            MeasureType.carport: ["carport", "bilskur"],
            MeasureType.kjeller_innredning: ["kjeller", "innrede kjeller"],
            MeasureType.loft_innredning: ["loft", "innrede loft"],
            MeasureType.veranda: ["veranda", "balkong", "terrasse"],
            MeasureType.fasadeendring: ["fasade", "vindu", "dør", "kledning"],
            MeasureType.støttemur: ["støttemur", "mur", "forstøtningsmur"],
            MeasureType.tomtedeling: ["tomtedeling", "dele tomt", "fradele"],
        }

        for measure_type, keywords in keyword_map.items():
            if any(kw in text_lower for kw in keywords):
                return MeasureClassification(
                    measureType=measure_type,
                    confidence=0.6,
                    requiresPermit=None,
                    notes="Klassifisert basert på nøkkelord (AI utilgjengelig)",
                )

        return MeasureClassification(
            measureType=MeasureType.ukjent,
            confidence=0.3,
            requiresPermit=None,
            notes="Kunne ikke klassifisere tiltaket automatisk",
        )

    def _fallback_summary(self, risk_level: RiskLevel, application_required: Optional[bool]) -> str:
        app_text = (
            "Tiltaket er sannsynligvis søknadspliktig."
            if application_required is True
            else "Tiltaket er muligens ikke søknadspliktig."
            if application_required is False
            else "Det er usikkert om tiltaket er søknadspliktig."
        )

        risk_text = {
            RiskLevel.lav: "Analysen indikerer lav regulatorisk risiko.",
            RiskLevel.middels: "Analysen indikerer middels regulatorisk risiko – noen forhold krever vurdering.",
            RiskLevel.høy: "Analysen indikerer høy regulatorisk risiko – viktige hindre er identifisert.",
            RiskLevel.ukjent: "Risikonivå er ikke fastsatt.",
        }.get(risk_level, "")

        return f"{app_text} {risk_text} Se regelresultatene nedenfor for detaljer. (AI-oppsummering utilgjengelig – viser regelbasert vurdering.)"


# Singleton
_orchestrator: Optional[AIOrchestrator] = None


def get_ai_orchestrator() -> AIOrchestrator:
    global _orchestrator
    if _orchestrator is None:
        _orchestrator = AIOrchestrator()
    return _orchestrator
