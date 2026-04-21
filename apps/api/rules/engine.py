"""
Regelmotor for AI Byggesøknad.
Deklarative regler evalueres mot prosjektdata.
Regler er definert i YAML og lagret i databasen.
"""
import structlog
from typing import List, Dict, Any, Optional
from models.schemas import (
    RuleResult, RuleStatus, RiskLevel,
    MeasureType, HazardLevel, PlanStatus,
    PlanLayerResult, HazardResult, MeasureClassification
)

logger = structlog.get_logger()


class RuleContext:
    """Context object passed to each rule evaluator."""

    def __init__(
        self,
        measure_type: Optional[MeasureType] = None,
        plan: Optional[PlanLayerResult] = None,
        hazard: Optional[HazardResult] = None,
        classification: Optional[MeasureClassification] = None,
        extra: Optional[Dict[str, Any]] = None,
    ):
        self.measure_type = measure_type
        self.plan = plan
        self.hazard = hazard
        self.classification = classification
        self.extra = extra or {}

    def get(self, key: str, default: Any = None) -> Any:
        return self.extra.get(key, default)


class RuleEngine:
    """
    Evaluates declarative rules against a project context.
    Rules are defined as Python functions but loaded from YAML/DB config.
    """

    def evaluate(self, ctx: RuleContext) -> List[RuleResult]:
        """Evaluate all applicable rules and return results."""
        results: List[RuleResult] = []

        # Run all rule evaluators
        evaluators = [
            self._rule_søkp_001,
            self._rule_søkp_002,
            self._rule_søkp_003,
            self._rule_plan_001,
            self._rule_plan_002,
            self._rule_plan_003,
            self._rule_fare_001,
            self._rule_fare_002,
            self._rule_dok_001,
            self._rule_dok_002,
            self._rule_dok_003,
            self._rule_disp_001,
        ]

        for evaluator in evaluators:
            try:
                result = evaluator(ctx)
                if result:
                    results.append(result)
            except Exception as e:
                logger.error("rule_evaluation_error", rule=evaluator.__name__, error=str(e))

        return results

    def compute_risk_level(self, results: List[RuleResult]) -> RiskLevel:
        """Compute overall risk level from rule results."""
        blocking_fails = [r for r in results if r.status == RuleStatus.fail and r.blocking]
        fails = [r for r in results if r.status == RuleStatus.fail]
        warns = [r for r in results if r.status == RuleStatus.warn]

        if blocking_fails:
            return RiskLevel.høy
        elif fails:
            return RiskLevel.høy
        elif len(warns) >= 2:
            return RiskLevel.middels
        elif warns:
            return RiskLevel.middels
        else:
            return RiskLevel.lav

    def compute_application_required(
        self, results: List[RuleResult], ctx: RuleContext
    ) -> Optional[bool]:
        """Determine if application is required based on rule results."""
        # Check for explicit søknadsplikt rules
        søkp_results = [r for r in results if r.ruleGroup == "søknadsplikt"]

        for r in søkp_results:
            if r.status == RuleStatus.fail and "søknadspliktig" in r.explanation.lower():
                return True

        # Measure types that are generally application-required
        always_required = {
            MeasureType.bruksendring,
            MeasureType.tilbygg,
            MeasureType.påbygg,
            MeasureType.tomtedeling,
        }

        if ctx.measure_type in always_required:
            return True

        # Measure types that may be exempt
        possibly_exempt = {
            MeasureType.garasje,
            MeasureType.carport,
            MeasureType.støttemur,
            MeasureType.veranda,
        }

        if ctx.measure_type in possibly_exempt:
            return None  # Uncertain – needs more info

        return None

    def generate_next_steps(
        self,
        results: List[RuleResult],
        application_required: Optional[bool],
        ctx: RuleContext,
    ) -> List[str]:
        """Generate actionable next steps based on rule results."""
        steps = []

        blocking = [r for r in results if r.status == RuleStatus.fail and r.blocking]
        warns = [r for r in results if r.status == RuleStatus.warn]

        if application_required is True:
            steps.append("Send søknad til kommunen via kommunens byggesaksportal eller Altinn.")
            steps.append("Engasjer ansvarlig søker (f.eks. arkitekt eller byggmester) dersom tiltaket krever ansvarsrett.")
            steps.append("Send nabovarsel til naboer og gjenboere minst 2 uker før søknad sendes.")

        if blocking:
            steps.append("Avklar planforhold med kommunen – tiltaket kan kreve dispensasjon.")

        if ctx.hazard and ctx.hazard.flomFare in [HazardLevel.middels, HazardLevel.høy]:
            steps.append("Innhent geoteknisk/hydrologisk vurdering for flomfare.")

        if ctx.hazard and ctx.hazard.skredFare in [HazardLevel.middels, HazardLevel.høy]:
            steps.append("Innhent geoteknisk vurdering for skredfare.")

        if application_required is None:
            steps.append("Kontakt kommunen for å avklare om tiltaket er søknadspliktig.")

        if not steps:
            steps.append("Tiltaket ser ut til å ha lav regulatorisk risiko. Gjennomfør en grundigere vurdering med kommunen.")

        return steps

    def generate_document_requirements(
        self, application_required: Optional[bool], ctx: RuleContext
    ) -> List[str]:
        """Generate list of likely required documents."""
        if not application_required:
            return []

        docs = [
            "Situasjonsplan (målsatt, viser eiendomsgrenser og eksisterende/planlagte bygg)",
            "Plantegninger (eksisterende og ny situasjon)",
            "Fasadetegninger (alle fasader)",
            "Snittegninger",
            "Nabovarsel med kvittering",
            "Søknadsskjema (blankett 5174 eller tilsvarende)",
        ]

        if ctx.measure_type == MeasureType.bruksendring:
            docs.append("Dokumentasjon på at ny bruk oppfyller TEK17-krav (brannsikkerhet, rømning, dagslys)")

        if ctx.measure_type in [MeasureType.tilbygg, MeasureType.påbygg]:
            docs.append("Beregning av BYA/BRA (bebygd areal / bruksareal)")

        if ctx.hazard and ctx.hazard.flomFare != HazardLevel.ukjent:
            docs.append("Hydrologisk/geoteknisk rapport (naturfare)")

        return docs

    # ============================================================
    # Individual rule evaluators
    # ============================================================

    def _rule_søkp_001(self, ctx: RuleContext) -> Optional[RuleResult]:
        """SØKP-001: Søknadsplikt bruksendring til boenhet."""
        if ctx.measure_type != MeasureType.bruksendring:
            return None

        return RuleResult(
            ruleCode="SØKP-001",
            ruleName="Søknadsplikt: Bruksendring",
            ruleGroup="søknadsplikt",
            status=RuleStatus.fail,
            explanation=(
                "Bruksendring er søknadspliktig etter plan- og bygningsloven § 20-1 bokstav d. "
                "Tiltaket krever søknad til kommunen."
            ),
            evidenceRefs=["PBL § 20-1 bokstav d"],
            blocking=True,
            sourceVersion="1.0",
        )

    def _rule_søkp_002(self, ctx: RuleContext) -> Optional[RuleResult]:
        """SØKP-002: Søknadsplikt tilbygg."""
        if ctx.measure_type not in [MeasureType.tilbygg, MeasureType.påbygg]:
            return None

        return RuleResult(
            ruleCode="SØKP-002",
            ruleName="Søknadsplikt: Tilbygg/påbygg",
            ruleGroup="søknadsplikt",
            status=RuleStatus.fail,
            explanation=(
                "Tilbygg og påbygg er normalt søknadspliktig etter PBL § 20-1 bokstav b. "
                "Svært små tilbygg (under 15 m²) kan i noen tilfeller være unntatt etter § 20-5 – "
                "dette krever nærmere vurdering."
            ),
            evidenceRefs=["PBL § 20-1 bokstav b", "PBL § 20-5"],
            blocking=True,
            sourceVersion="1.0",
        )

    def _rule_søkp_003(self, ctx: RuleContext) -> Optional[RuleResult]:
        """SØKP-003: Mulig unntak fra søknadsplikt."""
        possibly_exempt = {MeasureType.garasje, MeasureType.carport, MeasureType.støttemur, MeasureType.veranda}
        if ctx.measure_type not in possibly_exempt:
            return None

        return RuleResult(
            ruleCode="SØKP-003",
            ruleName="Mulig unntak fra søknadsplikt",
            ruleGroup="søknadsplikt",
            status=RuleStatus.warn,
            explanation=(
                f"{ctx.measure_type.value.capitalize() if ctx.measure_type else 'Tiltaket'} kan potensielt være unntatt søknadsplikt "
                "etter PBL § 20-5 dersom det oppfyller alle vilkår (størrelse, avstand til nabogrense, "
                "ikke i strid med plan m.m.). Sjekk kommunens veiledning."
            ),
            evidenceRefs=["PBL § 20-5", "SAK10 § 4-1"],
            blocking=False,
            sourceVersion="1.0",
        )

    def _rule_plan_001(self, ctx: RuleContext) -> Optional[RuleResult]:
        """PLAN-001: Tiltak i strid med reguleringsplan."""
        if not ctx.plan:
            return None

        if ctx.plan.planStatus == PlanStatus.regulert:
            # Check if arealformål is compatible with residential/construction
            compatible = ["boligbebyggelse", "fritidsbebyggelse", "kombinert", "sentrumsformål"]
            areal = ctx.plan.arealFormål.lower()
            is_compatible = any(c in areal for c in compatible)

            if not is_compatible and areal != "ukjent":
                return RuleResult(
                    ruleCode="PLAN-001",
                    ruleName="Mulig strid med reguleringsplan",
                    ruleGroup="planstatus",
                    status=RuleStatus.fail,
                    explanation=(
                        f"Eiendommen er regulert til '{ctx.plan.arealFormål}'. "
                        "Tiltaket kan være i strid med reguleringsplanen og kreve dispensasjon etter PBL § 19-1."
                    ),
                    evidenceRefs=["PBL § 19-1", "PBL § 12-4"],
                    blocking=True,
                    sourceVersion="1.0",
                )

        return None

    def _rule_plan_002(self, ctx: RuleContext) -> Optional[RuleResult]:
        """PLAN-002: Tiltak i LNF-område."""
        if not ctx.plan:
            return None

        if "lnf" in ctx.plan.arealFormål.lower():
            return RuleResult(
                ruleCode="PLAN-002",
                ruleName="Tiltak i LNF-område",
                ruleGroup="planstatus",
                status=RuleStatus.fail,
                explanation=(
                    "Eiendommen ligger i et LNF-område (Landbruk, Natur og Friluft). "
                    "Byggetiltak er normalt ikke tillatt i LNF-områder uten dispensasjon."
                ),
                evidenceRefs=["PBL § 11-7 nr. 5", "PBL § 19-1"],
                blocking=True,
                sourceVersion="1.0",
            )

        return None

    def _rule_plan_003(self, ctx: RuleContext) -> Optional[RuleResult]:
        """PLAN-003: Hensynssoner."""
        if not ctx.plan or not ctx.plan.hensynssoner:
            return None

        return RuleResult(
            ruleCode="PLAN-003",
            ruleName="Hensynssone – særskilt vurdering",
            ruleGroup="planstatus",
            status=RuleStatus.warn,
            explanation=(
                f"Eiendommen er berørt av hensynssone(r): {', '.join(ctx.plan.hensynssoner)}. "
                "Hensynssoner kan gi særskilte krav til utforming, materialbruk eller prosess."
            ),
            evidenceRefs=["PBL § 11-8"],
            blocking=False,
            sourceVersion="1.0",
        )

    def _rule_fare_001(self, ctx: RuleContext) -> Optional[RuleResult]:
        """FARE-001: Tiltak i flomsone."""
        if not ctx.hazard:
            return None

        if ctx.hazard.flomFare in [HazardLevel.middels, HazardLevel.høy]:
            return RuleResult(
                ruleCode="FARE-001",
                ruleName="Tiltak i flomsone",
                ruleGroup="naturfare",
                status=RuleStatus.fail,
                explanation=(
                    f"Eiendommen ligger i et område med {ctx.hazard.flomFare.value} flomfare. "
                    "Tiltak krever særskilt hydrologisk/geoteknisk vurdering og dokumentasjon "
                    "etter TEK17 § 7-2."
                ),
                evidenceRefs=["TEK17 § 7-2", "NVE retningslinjer"],
                blocking=True,
                sourceVersion="1.0",
            )

        return None

    def _rule_fare_002(self, ctx: RuleContext) -> Optional[RuleResult]:
        """FARE-002: Tiltak i skredfareområde."""
        if not ctx.hazard:
            return None

        if ctx.hazard.skredFare in [HazardLevel.middels, HazardLevel.høy]:
            return RuleResult(
                ruleCode="FARE-002",
                ruleName="Tiltak i skredfareområde",
                ruleGroup="naturfare",
                status=RuleStatus.fail,
                explanation=(
                    f"Eiendommen ligger i et område med {ctx.hazard.skredFare.value} skredfare. "
                    "Tiltak krever geoteknisk vurdering og dokumentasjon etter TEK17 § 7-3."
                ),
                evidenceRefs=["TEK17 § 7-3", "NVE retningslinjer"],
                blocking=True,
                sourceVersion="1.0",
            )

        return None

    def _rule_dok_001(self, ctx: RuleContext) -> Optional[RuleResult]:
        """DOK-001: Situasjonsplan kreves."""
        measure_requires_permit = ctx.measure_type in {
            MeasureType.bruksendring, MeasureType.tilbygg, MeasureType.påbygg,
            MeasureType.tomtedeling, MeasureType.kjeller_innredning, MeasureType.loft_innredning
        }
        if not measure_requires_permit:
            return None

        return RuleResult(
            ruleCode="DOK-001",
            ruleName="Dokumentkrav: Situasjonsplan",
            ruleGroup="dokumentkrav",
            status=RuleStatus.warn,
            explanation="Søknadspliktige tiltak krever situasjonsplan som viser eiendomsgrenser og bygningsplassering.",
            evidenceRefs=["SAK10 § 5-4"],
            blocking=False,
            sourceVersion="1.0",
        )

    def _rule_dok_002(self, ctx: RuleContext) -> Optional[RuleResult]:
        """DOK-002: Tegninger kreves."""
        measure_requires_permit = ctx.measure_type in {
            MeasureType.bruksendring, MeasureType.tilbygg, MeasureType.påbygg,
            MeasureType.tomtedeling, MeasureType.kjeller_innredning, MeasureType.loft_innredning
        }
        if not measure_requires_permit:
            return None

        return RuleResult(
            ruleCode="DOK-002",
            ruleName="Dokumentkrav: Plan-, fasade- og snittegninger",
            ruleGroup="dokumentkrav",
            status=RuleStatus.warn,
            explanation="Søknadspliktige tiltak krever plan-, fasade- og snittegninger i målestokk.",
            evidenceRefs=["SAK10 § 5-4"],
            blocking=False,
            sourceVersion="1.0",
        )

    def _rule_dok_003(self, ctx: RuleContext) -> Optional[RuleResult]:
        """DOK-003: Nabovarsel kreves."""
        measure_requires_permit = ctx.measure_type in {
            MeasureType.bruksendring, MeasureType.tilbygg, MeasureType.påbygg,
            MeasureType.tomtedeling, MeasureType.kjeller_innredning, MeasureType.loft_innredning
        }
        if not measure_requires_permit:
            return None

        return RuleResult(
            ruleCode="DOK-003",
            ruleName="Dokumentkrav: Nabovarsel",
            ruleGroup="dokumentkrav",
            status=RuleStatus.warn,
            explanation="Søknadspliktige tiltak krever nabovarsel til naboer og gjenboere etter PBL § 21-3.",
            evidenceRefs=["PBL § 21-3", "SAK10 § 5-2"],
            blocking=False,
            sourceVersion="1.0",
        )

    def _rule_disp_001(self, ctx: RuleContext) -> Optional[RuleResult]:
        """DISP-001: Dispensasjonsindikator."""
        if not ctx.plan:
            return None

        plan_conflict = (
            ctx.plan.planStatus == PlanStatus.regulert
            and ctx.plan.arealFormål not in ["boligbebyggelse", "ukjent"]
        )

        if not plan_conflict:
            return None

        return RuleResult(
            ruleCode="DISP-001",
            ruleName="Dispensasjonsindikator",
            ruleGroup="dispensasjon",
            status=RuleStatus.warn,
            explanation=(
                "Tiltaket kan kreve dispensasjon fra reguleringsplan. "
                "Dispensasjon etter PBL § 19-1 innvilges kun dersom fordelene er vesentlig "
                "større enn ulempene og tiltaket ikke er i strid med nasjonale interesser."
            ),
            evidenceRefs=["PBL § 19-1", "PBL § 19-2"],
            blocking=False,
            sourceVersion="1.0",
        )


# Singleton
_rule_engine: Optional[RuleEngine] = None


def get_rule_engine() -> RuleEngine:
    global _rule_engine
    if _rule_engine is None:
        _rule_engine = RuleEngine()
    return _rule_engine
