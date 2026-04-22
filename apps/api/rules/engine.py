"""
Regelmotor for AI Byggesøknad.
Deklarative regler evalueres mot prosjektdata.
Oppdatert basert på:
- Plan- og bygningsloven (PBL)
- Byggesaksforskriften (SAK10)
- Byggteknisk forskrift (TEK17)
- Veiledning om dispensasjon (Norsk Kommunalteknisk Forening, 2021)
- Sjekkliste for søknadsprosessen (Kristiansand kommune, 2026)
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
    Rules are based on Norwegian building law (PBL, SAK10, TEK17).
    """

    def evaluate(self, ctx: RuleContext) -> List[RuleResult]:
        """Evaluate all applicable rules and return results."""
        results: List[RuleResult] = []

        evaluators = [
            # Søknadsplikt
            self._rule_søkp_001,
            self._rule_søkp_002,
            self._rule_søkp_003,
            self._rule_søkp_004,
            # Planstatus
            self._rule_plan_001,
            self._rule_plan_002,
            self._rule_plan_003,
            self._rule_plan_004,
            # Naturfare
            self._rule_fare_001,
            self._rule_fare_002,
            self._rule_fare_003,
            # Dispensasjon
            self._rule_disp_001,
            self._rule_disp_002,
            # Dokumentkrav
            self._rule_dok_001,
            self._rule_dok_002,
            self._rule_dok_003,
            self._rule_dok_004,
            self._rule_dok_005,
            # Infrastruktur og miljø
            self._rule_infra_001,
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
        søkp_results = [r for r in results if r.ruleGroup == "søknadsplikt"]

        for r in søkp_results:
            if r.status == RuleStatus.fail and "søknadspliktig" in r.explanation.lower():
                return True

        always_required = {
            MeasureType.bruksendring,
            MeasureType.tilbygg,
            MeasureType.påbygg,
            MeasureType.tomtedeling,
            MeasureType.kjeller_innredning,
            MeasureType.loft_innredning,
            MeasureType.riving,
        }

        if ctx.measure_type in always_required:
            return True

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
        has_plan_conflict = any(r.ruleCode in ["PLAN-001", "PLAN-002"] for r in blocking)
        has_flood = ctx.hazard and ctx.hazard.flomFare in [HazardLevel.middels, HazardLevel.høy]
        has_landslide = ctx.hazard and ctx.hazard.skredFare in [HazardLevel.middels, HazardLevel.høy]

        # Step 1: Check for temporary building ban and contaminated ground
        steps.append("Sjekk om det er midlertidig forbud mot bygge- og deling i området (kontakt kommunen).")

        # Step 2: Check plan status
        steps.append("Sjekk gjeldende reguleringsplan for eiendommen på arealplaner.no eller kommunens planregister.")

        if application_required is True:
            # Step 3: Nabovarsel
            steps.append(
                "Hent naboliste på kommunens Min side og send nabovarsel til naboer og gjenboere. "
                "Vent minst 2 uker på eventuelle merknader (PBL § 21-3)."
            )
            # Step 4: Situasjonsplan
            steps.append(
                "Skriv ut situasjonskart fra kommunens kartportal og tegn inn tiltaket. "
                "Situasjonsplanen skal være i målestokk 1:500 (1:1000 for store tiltak)."
            )
            # Step 5: Drawings
            steps.append(
                "Utarbeid tegninger av tiltaket: plan, snitt og fasade i målestokk 1:100."
            )
            # Step 6: Responsible applicant
            steps.append(
                "Vurder om tiltaket krever ansvarlig søker (arkitekt eller byggmester). "
                "Tiltak i tiltaksklasse 1 kan søkes uten ansvarsrett av tiltakshaver selv."
            )

        if has_plan_conflict:
            steps.append(
                "Tiltaket kan kreve dispensasjon fra reguleringsplan. "
                "Søk om dispensasjon etter PBL § 19-1 – begrunn at fordelene er klart større enn ulempene."
            )

        if has_flood:
            steps.append(
                "Innhent hydrologisk/geoteknisk vurdering for flomfare (TEK17 § 7-2). "
                "Se NVE sin flomsonekart på nve.no."
            )

        if has_landslide:
            steps.append(
                "Innhent geoteknisk vurdering for skredfare (TEK17 § 7-3). "
                "Sjekk NVE sin aktsomhetskart for skred på nve.no."
            )

        if application_required is True:
            steps.append(
                "Send komplett søknad til kommunen med alle vedlegg. "
                "Søknad kan sendes digitalt via kommunens Min side eller per e-post/post."
            )

        if application_required is None:
            steps.append(
                "Kontakt kommunen for å avklare om tiltaket er søknadspliktig "
                "eller kan gjennomføres som melding/uten søknad (PBL § 20-5, SAK10 § 4-1)."
            )

        if not steps:
            steps.append(
                "Tiltaket ser ut til å ha lav regulatorisk risiko. "
                "Gjennomfør en grundigere vurdering med kommunen."
            )

        return steps

    def generate_document_requirements(
        self, application_required: Optional[bool], ctx: RuleContext
    ) -> List[str]:
        """Generate list of likely required documents based on measure type and context."""
        if not application_required:
            return []

        docs = [
            "Søknadsskjema (blankett 5174 – Søknad om tillatelse til tiltak, eller digital innsending)",
            "Situasjonsplan i målestokk 1:500 (tiltaket inntegnet på kart fra kommunen)",
            "Plantegninger – eksisterende og ny situasjon (målestokk 1:100)",
            "Fasadetegninger – alle fasader (målestokk 1:100)",
            "Snittegninger (målestokk 1:100)",
            "Nabovarsel med kvittering (gjenpart av varselet sendt til naboer)",
            "Eventuelle nabomerknader med dine kommentarer",
        ]

        if ctx.measure_type in [MeasureType.tilbygg, MeasureType.påbygg]:
            docs.append("Beregning av BYA/BRA (bebygd areal og bruksareal)")
            docs.append("Situasjonskart fra kommunens kartportal (bestilles via kommunen)")

        if ctx.measure_type == MeasureType.bruksendring:
            docs.append(
                "Dokumentasjon på at ny bruk oppfyller TEK17-krav "
                "(brannsikkerhet, rømning, dagslys, ventilasjon)"
            )
            docs.append("Redegjørelse for universell utforming (TEK17 kap. 12)")

        if ctx.measure_type in [MeasureType.tilbygg, MeasureType.påbygg, MeasureType.bruksendring]:
            docs.append("Energiberegning (TEK17 kap. 14) ved nybygg og større tilbygg")

        if ctx.hazard and ctx.hazard.flomFare in [HazardLevel.middels, HazardLevel.høy]:
            docs.append("Hydrologisk/geoteknisk rapport (naturfare – flom, TEK17 § 7-2)")

        if ctx.hazard and ctx.hazard.skredFare in [HazardLevel.middels, HazardLevel.høy]:
            docs.append("Geoteknisk rapport (naturfare – skred, TEK17 § 7-3)")

        # Check if dispensation is needed
        if ctx.plan and ctx.plan.planStatus == PlanStatus.regulert:
            areal = (ctx.plan.arealFormål or "").lower()
            compatible = ["boligbebyggelse", "fritidsbebyggelse", "kombinert", "sentrumsformål", "ukjent", ""]
            if not any(c in areal for c in compatible):
                docs.append(
                    "Søknad om dispensasjon fra reguleringsplan (PBL § 19-1) "
                    "med begrunnelse for at fordelene er klart større enn ulempene"
                )

        return docs

    # ============================================================
    # Individual rule evaluators
    # ============================================================

    def _rule_søkp_001(self, ctx: RuleContext) -> Optional[RuleResult]:
        """SØKP-001: Søknadsplikt bruksendring."""
        if ctx.measure_type != MeasureType.bruksendring:
            return None

        return RuleResult(
            ruleCode="SØKP-001",
            ruleName="Søknadsplikt: Bruksendring",
            ruleGroup="søknadsplikt",
            status=RuleStatus.fail,
            explanation=(
                "Bruksendring er søknadspliktig etter PBL § 20-1 bokstav d. "
                "Tiltaket krever søknad til kommunen og normalt ansvarlig søker. "
                "Ny bruk må oppfylle kravene i TEK17 (brannsikkerhet, rømning, dagslys m.m.)."
            ),
            evidenceRefs=["PBL § 20-1 bokstav d", "TEK17", "SAK10 § 6-3"],
            blocking=True,
            sourceVersion="1.1",
        )

    def _rule_søkp_002(self, ctx: RuleContext) -> Optional[RuleResult]:
        """SØKP-002: Søknadsplikt tilbygg/påbygg."""
        if ctx.measure_type not in [MeasureType.tilbygg, MeasureType.påbygg]:
            return None

        return RuleResult(
            ruleCode="SØKP-002",
            ruleName="Søknadsplikt: Tilbygg/påbygg",
            ruleGroup="søknadsplikt",
            status=RuleStatus.fail,
            explanation=(
                "Tilbygg og påbygg er normalt søknadspliktig etter PBL § 20-1 bokstav b. "
                "Svært små tilbygg (under 15 m² BRA) kan i noen tilfeller være unntatt søknadsplikt "
                "etter PBL § 20-5 og SAK10 § 4-1, forutsatt at de ikke er i strid med plan, "
                "ikke plasseres nærmere enn 1,0 m fra nabogrense, og ikke krever dispensasjon."
            ),
            evidenceRefs=["PBL § 20-1 bokstav b", "PBL § 20-5", "SAK10 § 4-1"],
            blocking=True,
            sourceVersion="1.1",
        )

    def _rule_søkp_003(self, ctx: RuleContext) -> Optional[RuleResult]:
        """SØKP-003: Mulig unntak fra søknadsplikt (garasje, carport, støttemur, veranda)."""
        possibly_exempt = {MeasureType.garasje, MeasureType.carport, MeasureType.støttemur, MeasureType.veranda}
        if ctx.measure_type not in possibly_exempt:
            return None

        type_name = ctx.measure_type.value.capitalize() if ctx.measure_type else "Tiltaket"

        return RuleResult(
            ruleCode="SØKP-003",
            ruleName="Mulig unntak fra søknadsplikt",
            ruleGroup="søknadsplikt",
            status=RuleStatus.warn,
            explanation=(
                f"{type_name} kan potensielt være unntatt søknadsplikt etter PBL § 20-5 og SAK10 § 4-1, "
                "dersom det oppfyller alle vilkår: maks 50 m² BYA, maks én etasje, ikke kjeller, "
                "avstand til nabogrense minst 1,0 m, ikke i strid med plan, og ikke krever dispensasjon. "
                "Sjekk kommunens veiledning for detaljerte krav."
            ),
            evidenceRefs=["PBL § 20-5", "SAK10 § 4-1"],
            blocking=False,
            sourceVersion="1.1",
        )

    def _rule_søkp_004(self, ctx: RuleContext) -> Optional[RuleResult]:
        """SØKP-004: Søknadsplikt riving, kjeller/loft-innredning, tomtedeling."""
        requires_permit = {MeasureType.riving, MeasureType.kjeller_innredning, MeasureType.loft_innredning, MeasureType.tomtedeling}
        if ctx.measure_type not in requires_permit:
            return None

        type_map = {
            MeasureType.riving: ("Riving", "PBL § 20-1 bokstav e"),
            MeasureType.kjeller_innredning: ("Innredning av kjeller til oppholdsrom", "PBL § 20-1 bokstav d"),
            MeasureType.loft_innredning: ("Innredning av loft til oppholdsrom", "PBL § 20-1 bokstav d"),
            MeasureType.tomtedeling: ("Tomtedeling/fradeling", "PBL § 20-1 bokstav m"),
        }
        name, ref = type_map.get(ctx.measure_type, ("Tiltaket", "PBL § 20-1"))

        return RuleResult(
            ruleCode="SØKP-004",
            ruleName=f"Søknadsplikt: {name}",
            ruleGroup="søknadsplikt",
            status=RuleStatus.fail,
            explanation=(
                f"{name} er søknadspliktig etter {ref}. "
                "Tiltaket krever søknad til kommunen og normalt ansvarlig søker."
            ),
            evidenceRefs=[ref, "SAK10"],
            blocking=True,
            sourceVersion="1.1",
        )

    def _rule_plan_001(self, ctx: RuleContext) -> Optional[RuleResult]:
        """PLAN-001: Tiltak i strid med reguleringsplan."""
        if not ctx.plan:
            return None

        if ctx.plan.planStatus == PlanStatus.regulert:
            compatible = ["boligbebyggelse", "fritidsbebyggelse", "kombinert", "sentrumsformål", "ukjent", ""]
            areal = (ctx.plan.arealFormål or "").lower()
            is_compatible = any(c in areal for c in compatible)

            if not is_compatible:
                return RuleResult(
                    ruleCode="PLAN-001",
                    ruleName="Mulig strid med reguleringsplan",
                    ruleGroup="planstatus",
                    status=RuleStatus.fail,
                    explanation=(
                        f"Eiendommen er regulert til '{ctx.plan.arealFormål}'. "
                        "Tiltaket kan være i strid med reguleringsplanen og kreve dispensasjon etter PBL § 19-1. "
                        "Dispensasjon innvilges kun dersom fordelene er klart større enn ulempene, "
                        "og hensynene bak bestemmelsen ikke vesentlig tilsidesettes (PBL § 19-2)."
                    ),
                    evidenceRefs=["PBL § 19-1", "PBL § 19-2", "PBL § 12-4"],
                    blocking=True,
                    sourceVersion="1.1",
                )

        return None

    def _rule_plan_002(self, ctx: RuleContext) -> Optional[RuleResult]:
        """PLAN-002: Tiltak i LNF-område."""
        if not ctx.plan:
            return None

        if "lnf" in (ctx.plan.arealFormål or "").lower():
            return RuleResult(
                ruleCode="PLAN-002",
                ruleName="Tiltak i LNF-område",
                ruleGroup="planstatus",
                status=RuleStatus.fail,
                explanation=(
                    "Eiendommen ligger i et LNF-område (Landbruk, Natur og Friluft). "
                    "Byggetiltak er normalt ikke tillatt i LNF-områder uten dispensasjon fra kommuneplanens arealdel. "
                    "Dispensasjon er strengt regulert og innvilges sjelden for nye byggetiltak i LNF."
                ),
                evidenceRefs=["PBL § 11-7 nr. 5", "PBL § 19-1", "PBL § 19-2"],
                blocking=True,
                sourceVersion="1.1",
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
                "Hensynssoner kan gi særskilte krav til utforming, materialbruk eller saksbehandlingsprosess. "
                "Kontakt kommunen for avklaring."
            ),
            evidenceRefs=["PBL § 11-8"],
            blocking=False,
            sourceVersion="1.1",
        )

    def _rule_plan_004(self, ctx: RuleContext) -> Optional[RuleResult]:
        """PLAN-004: Ukjent planstatus – advarsel."""
        if not ctx.plan or ctx.plan.planStatus != PlanStatus.ukjent:
            return None

        return RuleResult(
            ruleCode="PLAN-004",
            ruleName="Planstatus ukjent – sjekk kommunens planregister",
            ruleGroup="planstatus",
            status=RuleStatus.warn,
            explanation=(
                "Planstatus for eiendommen er ikke avklart. "
                "Sjekk gjeldende reguleringsplan på kommunens planregister (arealplaner.no) "
                "eller kontakt kommunen for å avklare hvilke planbestemmelser som gjelder. "
                "Planbestemmelsene kan ha avgjørende betydning for om tiltaket er tillatt."
            ),
            evidenceRefs=["PBL § 12-4", "PBL § 11-6"],
            blocking=False,
            sourceVersion="1.1",
        )

    def _rule_fare_001(self, ctx: RuleContext) -> Optional[RuleResult]:
        """FARE-001: Tiltak i flomsone."""
        if not ctx.hazard:
            return None

        if ctx.hazard.flomFare == HazardLevel.høy:
            return RuleResult(
                ruleCode="FARE-001",
                ruleName="Tiltak i flomsone – høy fare",
                ruleGroup="naturfare",
                status=RuleStatus.fail,
                explanation=(
                    "Eiendommen ligger i et område med høy flomfare (NVE flomsonekart). "
                    "Tiltak krever særskilt hydrologisk og geoteknisk vurdering etter TEK17 § 7-2. "
                    "Nye boliger og fritidsboliger tillates ikke i 200-årsflomsonene. "
                    "Innhent rapport fra godkjent geotekniker/hydrologer."
                ),
                evidenceRefs=["TEK17 § 7-2", "NVE retningslinjer 1/2008", "PBL § 28-1"],
                blocking=True,
                sourceVersion="1.1",
            )
        elif ctx.hazard.flomFare == HazardLevel.middels:
            return RuleResult(
                ruleCode="FARE-001",
                ruleName="Tiltak i flomsone – middels fare",
                ruleGroup="naturfare",
                status=RuleStatus.fail,
                explanation=(
                    "Eiendommen ligger i et område med middels flomfare (NVE flomsonekart). "
                    "Tiltak krever særskilt hydrologisk/geoteknisk vurdering og dokumentasjon "
                    "etter TEK17 § 7-2. Kontakt NVE eller en godkjent geotekniker."
                ),
                evidenceRefs=["TEK17 § 7-2", "NVE retningslinjer"],
                blocking=True,
                sourceVersion="1.1",
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
                    f"Eiendommen ligger i et område med {ctx.hazard.skredFare.value} skredfare (NVE aktsomhetskart). "
                    "Tiltak krever geoteknisk vurdering og dokumentasjon etter TEK17 § 7-3. "
                    "Nye tiltak i skredfareområder krever særskilt sikkerhetsdokumentasjon."
                ),
                evidenceRefs=["TEK17 § 7-3", "NVE retningslinjer", "PBL § 28-1"],
                blocking=True,
                sourceVersion="1.1",
            )

        return None

    def _rule_fare_003(self, ctx: RuleContext) -> Optional[RuleResult]:
        """FARE-003: Sjekk for forurenset grunn."""
        # Always warn about contaminated ground check for new construction
        construction_types = {
            MeasureType.tilbygg, MeasureType.påbygg, MeasureType.garasje,
            MeasureType.bruksendring, MeasureType.kjeller_innredning
        }
        if ctx.measure_type not in construction_types:
            return None

        return RuleResult(
            ruleCode="FARE-003",
            ruleName="Sjekk for forurenset grunn",
            ruleGroup="naturfare",
            status=RuleStatus.warn,
            explanation=(
                "Vurder om byggetiltaket kan berøre forurenset grunn. "
                "Sjekk Miljødirektoratets grunnforurensningsdatabase (grunnforurensning.miljodirektoratet.no) "
                "for å se om eiendommen er registrert med forurenset grunn. "
                "Graving i forurenset grunn krever særskilt håndtering og kan utløse meldeplikt."
            ),
            evidenceRefs=["Forurensningsloven § 7", "TEK17 § 9-2"],
            blocking=False,
            sourceVersion="1.1",
        )

    def _rule_disp_001(self, ctx: RuleContext) -> Optional[RuleResult]:
        """DISP-001: Dispensasjonsindikator fra reguleringsplan."""
        if not ctx.plan:
            return None

        plan_conflict = (
            ctx.plan.planStatus == PlanStatus.regulert
            and (ctx.plan.arealFormål or "").lower() not in ["boligbebyggelse", "ukjent", ""]
        )

        if not plan_conflict:
            return None

        return RuleResult(
            ruleCode="DISP-001",
            ruleName="Dispensasjon fra reguleringsplan kan kreves",
            ruleGroup="dispensasjon",
            status=RuleStatus.warn,
            explanation=(
                "Tiltaket kan kreve dispensasjon fra reguleringsplan (PBL § 19-1). "
                "For å få dispensasjon må begge vilkårene i PBL § 19-2 være oppfylt: "
                "(1) Hensynene bak bestemmelsen det dispenseres fra blir ikke vesentlig tilsidesatt, "
                "og (2) fordelene ved dispensasjonen er klart større enn ulempene. "
                "Dispensasjonssøknaden skal begrunnes konkret for din sak – generelle argumenter tillegges liten vekt. "
                "Behandlingstid: inntil 12 uker (PBL § 21-7)."
            ),
            evidenceRefs=["PBL § 19-1", "PBL § 19-2", "PBL § 21-7"],
            blocking=False,
            sourceVersion="1.1",
        )

    def _rule_disp_002(self, ctx: RuleContext) -> Optional[RuleResult]:
        """DISP-002: Strandsonebestemmelse."""
        # Check if property is near coast (100-meter belt) via extra context
        near_coast = ctx.get("near_coast", False)
        if not near_coast:
            return None

        return RuleResult(
            ruleCode="DISP-002",
            ruleName="Tiltak i strandsonen (100-metersbeltet)",
            ruleGroup="dispensasjon",
            status=RuleStatus.fail,
            explanation=(
                "Eiendommen kan ligge i 100-metersbeltet langs sjø (strandsonen). "
                "Byggetiltak i strandsonen er forbudt etter PBL § 1-8 uten dispensasjon. "
                "Dispensasjon fra strandsoneforbud er svært strengt regulert og innvilges sjelden. "
                "Kontakt kommunen for avklaring av om eiendommen er i strandsonen."
            ),
            evidenceRefs=["PBL § 1-8", "PBL § 19-1"],
            blocking=True,
            sourceVersion="1.1",
        )

    def _rule_dok_001(self, ctx: RuleContext) -> Optional[RuleResult]:
        """DOK-001: Situasjonsplan kreves."""
        measure_requires_permit = ctx.measure_type in {
            MeasureType.bruksendring, MeasureType.tilbygg, MeasureType.påbygg,
            MeasureType.tomtedeling, MeasureType.kjeller_innredning, MeasureType.loft_innredning,
            MeasureType.riving,
        }
        if not measure_requires_permit:
            return None

        return RuleResult(
            ruleCode="DOK-001",
            ruleName="Dokumentkrav: Situasjonsplan",
            ruleGroup="dokumentkrav",
            status=RuleStatus.warn,
            explanation=(
                "Søknadspliktige tiltak krever situasjonsplan som viser eiendomsgrenser, "
                "eksisterende og planlagte bygg, og avstand til nabogrense. "
                "Situasjonsplanen skal være i målestokk 1:500 (1:1000 for store tiltak). "
                "Bestill situasjonskart fra kommunens kartportal."
            ),
            evidenceRefs=["SAK10 § 5-4"],
            blocking=False,
            sourceVersion="1.1",
        )

    def _rule_dok_002(self, ctx: RuleContext) -> Optional[RuleResult]:
        """DOK-002: Tegninger kreves."""
        measure_requires_permit = ctx.measure_type in {
            MeasureType.bruksendring, MeasureType.tilbygg, MeasureType.påbygg,
            MeasureType.tomtedeling, MeasureType.kjeller_innredning, MeasureType.loft_innredning,
        }
        if not measure_requires_permit:
            return None

        return RuleResult(
            ruleCode="DOK-002",
            ruleName="Dokumentkrav: Plan-, fasade- og snittegninger",
            ruleGroup="dokumentkrav",
            status=RuleStatus.warn,
            explanation=(
                "Søknadspliktige tiltak krever plan-, fasade- og snittegninger i målestokk 1:100. "
                "Tegningene skal vise eksisterende og ny situasjon, og inneholde nødvendige mål."
            ),
            evidenceRefs=["SAK10 § 5-4"],
            blocking=False,
            sourceVersion="1.1",
        )

    def _rule_dok_003(self, ctx: RuleContext) -> Optional[RuleResult]:
        """DOK-003: Nabovarsel kreves."""
        measure_requires_permit = ctx.measure_type in {
            MeasureType.bruksendring, MeasureType.tilbygg, MeasureType.påbygg,
            MeasureType.tomtedeling, MeasureType.kjeller_innredning, MeasureType.loft_innredning,
        }
        if not measure_requires_permit:
            return None

        return RuleResult(
            ruleCode="DOK-003",
            ruleName="Dokumentkrav: Nabovarsel",
            ruleGroup="dokumentkrav",
            status=RuleStatus.warn,
            explanation=(
                "Søknadspliktige tiltak krever nabovarsel til naboer og gjenboere etter PBL § 21-3. "
                "Naboene skal sende sine merknader til deg, slik at du kan kommentere dem "
                "før du sender alt samlet til kommunen. Vent minst 2 uker på merknader. "
                "Hent naboliste på kommunens Min side."
            ),
            evidenceRefs=["PBL § 21-3", "SAK10 § 5-2"],
            blocking=False,
            sourceVersion="1.1",
        )

    def _rule_dok_004(self, ctx: RuleContext) -> Optional[RuleResult]:
        """DOK-004: Grunnbokutskrift kan være nødvendig."""
        measure_requires_permit = ctx.measure_type in {
            MeasureType.tomtedeling, MeasureType.bruksendring,
        }
        if not measure_requires_permit:
            return None

        return RuleResult(
            ruleCode="DOK-004",
            ruleName="Dokumentkrav: Grunnbokutskrift",
            ruleGroup="dokumentkrav",
            status=RuleStatus.warn,
            explanation=(
                "For tomtedeling og visse bruksendringer kan kommunen kreve grunnbokutskrift "
                "for å dokumentere eierforhold og heftelser på eiendommen. "
                "Grunnbokutskrift bestilles fra Kartverket (seeiendom.no)."
            ),
            evidenceRefs=["PBL § 26-1"],
            blocking=False,
            sourceVersion="1.1",
        )

    def _rule_dok_005(self, ctx: RuleContext) -> Optional[RuleResult]:
        """DOK-005: Samtykkeerklæring fra nabo ved avstand til nabogrense."""
        possibly_close = ctx.measure_type in {
            MeasureType.garasje, MeasureType.carport, MeasureType.støttemur,
            MeasureType.tilbygg, MeasureType.påbygg,
        }
        if not possibly_close:
            return None

        return RuleResult(
            ruleCode="DOK-005",
            ruleName="Samtykkeerklæring fra nabo ved avstand til nabogrense",
            ruleGroup="dokumentkrav",
            status=RuleStatus.warn,
            explanation=(
                "Dersom tiltaket plasseres nærmere nabogrense enn 4,0 m (PBL § 29-4), "
                "kreves skriftlig samtykkeerklæring fra berørt nabo. "
                "Uten samtykke må du søke om dispensasjon fra avstandskravet."
            ),
            evidenceRefs=["PBL § 29-4", "SAK10 § 5-4"],
            blocking=False,
            sourceVersion="1.1",
        )

    def _rule_infra_001(self, ctx: RuleContext) -> Optional[RuleResult]:
        """INFRA-001: Vann, avløp og avkjørsel."""
        construction_types = {
            MeasureType.tilbygg, MeasureType.påbygg, MeasureType.bruksendring,
            MeasureType.garasje,
        }
        if ctx.measure_type not in construction_types:
            return None

        return RuleResult(
            ruleCode="INFRA-001",
            ruleName="Sjekk vann, avløp og avkjørsel",
            ruleGroup="infrastruktur",
            status=RuleStatus.warn,
            explanation=(
                "Sjekk om tiltaket berører vann- og avløpsanlegg, er nær offentlig vann- og avløpsnett, "
                "er nær høyspentledninger, eller krever avkjørselstillatelse fra kommunen. "
                "Kontakt kommunen for veiledning om kommunens veinormal og VA-norm."
            ),
            evidenceRefs=["PBL § 27-1", "PBL § 27-2", "Veglova"],
            blocking=False,
            sourceVersion="1.1",
        )


# Singleton
_rule_engine: Optional[RuleEngine] = None


def get_rule_engine() -> RuleEngine:
    global _rule_engine
    if _rule_engine is None:
        _rule_engine = RuleEngine()
    return _rule_engine
