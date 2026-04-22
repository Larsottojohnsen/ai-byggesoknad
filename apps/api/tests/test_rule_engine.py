"""
Pytest test suite for the AI Byggesøknad rule engine.
Tests all rules across søknadsplikt, planstatus, faredata,
dokumentkrav and dispensasjon categories.

Run: cd apps/api && pytest tests/ -v
"""
import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import pytest
from rules.engine import RuleEngine, RuleContext, get_rule_engine
from models.schemas import (
    MeasureType, MeasureClassification,
    PlanLayerResult, PlanStatus,
    HazardResult, HazardLevel,
    RuleStatus,
)


# ── Helpers ───────────────────────────────────────────────────────────────────

def make_classification(
    measure_type: MeasureType = MeasureType.tilbygg,
    confidence: float = 0.95,
    requires_application: bool = True,
    requires_responsible: bool = True,
) -> MeasureClassification:
    return MeasureClassification(
        measureType=measure_type,
        confidence=confidence,
        requiresApplication=requires_application,
        requiresResponsibleApplicant=requires_responsible,
        description=f"Test: {measure_type.value}",
        legalBasis="PBL § 20-1",
    )


def make_plan(
    status: PlanStatus = PlanStatus.regulert,
    areal_formal: str = "boligbebyggelse",
    utnyttelsesgrad: str = "BYA=30%",
    byggegrense: float = 4.0,
    hensynssoner: list = None,
) -> PlanLayerResult:
    return PlanLayerResult(
        planStatus=status,
        arealFormål=areal_formal,
        utnyttelsesgrad=utnyttelsesgrad,
        byggegrense=byggegrense,
        hensynssoner=hensynssoner or [],
    )


def make_hazard(
    flom: HazardLevel = HazardLevel.lav,
    skred: HazardLevel = HazardLevel.lav,
) -> HazardResult:
    return HazardResult(flomFare=flom, skredFare=skred)


def make_ctx(
    measure_type: MeasureType = MeasureType.tilbygg,
    plan_status: PlanStatus = PlanStatus.regulert,
    flom: HazardLevel = HazardLevel.lav,
    skred: HazardLevel = HazardLevel.lav,
    confidence: float = 0.95,
    requires_application: bool = True,
    requires_responsible: bool = True,
) -> RuleContext:
    return RuleContext(
        measure_type=measure_type,
        plan=make_plan(status=plan_status),
        hazard=make_hazard(flom=flom, skred=skred),
        classification=make_classification(
            measure_type=measure_type,
            confidence=confidence,
            requires_application=requires_application,
            requires_responsible=requires_responsible,
        ),
    )


@pytest.fixture
def engine() -> RuleEngine:
    return get_rule_engine()


# ── SØKP: Søknadsplikt ────────────────────────────────────────────────────────

class TestSøknadsplikt:
    def test_tilbygg_krever_soknad(self, engine):
        """Tilbygg skal alltid utløse søknadsplikt-regel."""
        ctx = make_ctx(measure_type=MeasureType.tilbygg, requires_application=True)
        results = engine.evaluate(ctx)
        # Rule SØKP-002 covers tilbygg specifically
        sokp = next((r for r in results if "SØKP" in r.ruleCode), None)
        assert sokp is not None, "Ingen SØKP-regel funnet"
        assert sokp.status == RuleStatus.fail

    def test_ansvarlig_soker_kreves_for_tilbygg(self, engine):
        """Tilbygg krever ansvarlig søker."""
        ctx = make_ctx(
            measure_type=MeasureType.tilbygg,
            requires_responsible=True,
            requires_application=True,
        )
        results = engine.evaluate(ctx)
        sokp_codes = [r.ruleCode for r in results if "SØKP" in r.ruleCode]
        assert len(sokp_codes) > 0

    def test_bruksendring_krever_soknad(self, engine):
        """Bruksendring er søknadspliktig."""
        ctx = make_ctx(measure_type=MeasureType.bruksendring, requires_application=True)
        results = engine.evaluate(ctx)
        sokp = next((r for r in results if "SØKP" in r.ruleCode), None)
        assert sokp is not None
        assert sokp.status == RuleStatus.fail

    def test_ansvarlig_soker_ikke_kreves_uten_soknad(self, engine):
        """Uten søknadsplikt kreves ikke ansvarlig søker."""
        ctx = make_ctx(
            measure_type=MeasureType.garasje,
            requires_application=False,
            requires_responsible=False,
        )
        results = engine.evaluate(ctx)
        # When requiresApplication=False, SØKP rules should pass
        sokp_fails = [r for r in results if "SØKP" in r.ruleCode and r.status == RuleStatus.fail]
        assert len(sokp_fails) == 0


# ── PLAN: Planstatus ──────────────────────────────────────────────────────────

class TestPlanstatus:
    def test_lnf_plan_gir_fail(self, engine):
        """LNF-regulert plan skal gi PLAN-002 fail."""
        from models.schemas import PlanLayerResult, PlanStatus
        plan = PlanLayerResult(
            planStatus=PlanStatus.regulert,
            arealFormål="lnf-område",
            hensynssoner=[],
        )
        ctx = RuleContext(
            measure_type=MeasureType.tilbygg,
            plan=plan,
            hazard=make_hazard(),
            classification=make_classification(),
        )
        results = engine.evaluate(ctx)
        plan_r = next((r for r in results if r.ruleCode == "PLAN-002"), None)
        assert plan_r is not None, "PLAN-002 mangler for LNF-område"
        assert plan_r.status == RuleStatus.fail

    def test_inkompatibelt_arealformål_gir_plan001(self, engine):
        """Regulert til industri skal gi PLAN-001 fail."""
        from models.schemas import PlanLayerResult, PlanStatus
        plan = PlanLayerResult(
            planStatus=PlanStatus.regulert,
            arealFormål="industriformål",
            hensynssoner=[],
        )
        ctx = RuleContext(
            measure_type=MeasureType.tilbygg,
            plan=plan,
            hazard=make_hazard(),
            classification=make_classification(),
        )
        results = engine.evaluate(ctx)
        plan_r = next((r for r in results if r.ruleCode == "PLAN-001"), None)
        assert plan_r is not None, "PLAN-001 mangler for inkompatibelt arealformål"
        assert plan_r.status == RuleStatus.fail

    def test_hensynssone_gir_advarsel(self, engine):
        """Hensynssone skal gi PLAN-003 advarsel."""
        from models.schemas import PlanLayerResult, PlanStatus
        plan = PlanLayerResult(
            planStatus=PlanStatus.regulert,
            arealFormål="boligbebyggelse",
            hensynssoner=["H310 – Faresone høyspenning"],
        )
        ctx = RuleContext(
            measure_type=MeasureType.tilbygg,
            plan=plan,
            hazard=make_hazard(),
            classification=make_classification(),
        )
        results = engine.evaluate(ctx)
        plan_r = next((r for r in results if r.ruleCode == "PLAN-003"), None)
        assert plan_r is not None, "PLAN-003 mangler for hensynssone"
        assert plan_r.status == RuleStatus.warn

    def test_dispensasjon_ved_inkompatibelt_formål(self, engine):
        """DISP-001 skal evalueres ved regulert til ikke-bolig."""
        from models.schemas import PlanLayerResult, PlanStatus
        plan = PlanLayerResult(
            planStatus=PlanStatus.regulert,
            arealFormål="næringsformål",
            hensynssoner=[],
        )
        ctx = RuleContext(
            measure_type=MeasureType.tilbygg,
            plan=plan,
            hazard=make_hazard(),
            classification=make_classification(),
        )
        results = engine.evaluate(ctx)
        disp = next((r for r in results if r.ruleCode.startswith("DISP")), None)
        assert disp is not None, "Ingen DISP-regel funnet ved plankonflikt"


# ── FARE: Faredata ────────────────────────────────────────────────────────────

class TestFaredata:
    def test_lav_fare_ingen_fare_regel(self, engine):
        """Lav fare skal IKKE utløse FARE-001 (regel er kun for middels/høy)."""
        ctx = make_ctx(flom=HazardLevel.lav, skred=HazardLevel.lav)
        results = engine.evaluate(ctx)
        fare = next((r for r in results if r.ruleCode == "FARE-001"), None)
        # FARE-001 fires only on middels/høy – should be absent for lav
        assert fare is None, "FARE-001 skal ikke utløses ved lav fare"

    def test_høy_flomfare_gir_fail(self, engine):
        """Høy flomfare er blokkerende."""
        ctx = make_ctx(flom=HazardLevel.høy, skred=HazardLevel.lav)
        results = engine.evaluate(ctx)
        fare = next((r for r in results if r.ruleCode == "FARE-001"), None)
        assert fare is not None, "FARE-001 mangler ved høy flomfare"
        assert fare.status == RuleStatus.fail
        assert fare.blocking is True

    def test_middels_skredfare_gir_advarsel_eller_fail(self, engine):
        """Middels skredfare skal gi advarsel eller feil."""
        ctx = make_ctx(flom=HazardLevel.lav, skred=HazardLevel.middels)
        results = engine.evaluate(ctx)
        fare2 = next((r for r in results if r.ruleCode == "FARE-002"), None)
        assert fare2 is not None, "FARE-002 mangler"
        assert fare2.status in (RuleStatus.warn, RuleStatus.fail)

    def test_høy_skredfare_gir_fail(self, engine):
        """Høy skredfare er blokkerende."""
        ctx = make_ctx(flom=HazardLevel.lav, skred=HazardLevel.høy)
        results = engine.evaluate(ctx)
        fare2 = next((r for r in results if r.ruleCode == "FARE-002"), None)
        assert fare2 is not None
        assert fare2.status == RuleStatus.fail


# ── DOK: Dokumentkrav ─────────────────────────────────────────────────────────

class TestDokumentkrav:
    def test_søknadspliktig_har_dok_krav(self, engine):
        """Søknadspliktige tiltak skal ha dokumentkrav-regler."""
        ctx = make_ctx(measure_type=MeasureType.tilbygg, requires_application=True)
        results = engine.evaluate(ctx)
        dok = [r for r in results if r.ruleCode.startswith("DOK")]
        assert len(dok) > 0, "Ingen DOK-regler funnet"

    def test_situasjonsplan_krav(self, engine):
        """DOK-001 situasjonsplan skal finnes."""
        ctx = make_ctx(requires_application=True)
        results = engine.evaluate(ctx)
        dok1 = next((r for r in results if r.ruleCode == "DOK-001"), None)
        assert dok1 is not None

    def test_nabovarsel_krav(self, engine):
        """DOK-003 nabovarsel skal finnes."""
        ctx = make_ctx(requires_application=True)
        results = engine.evaluate(ctx)
        dok3 = next((r for r in results if r.ruleCode == "DOK-003"), None)
        assert dok3 is not None


# ── Risk level computation ────────────────────────────────────────────────────

class TestRiskLevel:
    def test_høy_fare_gir_høy_risiko(self, engine):
        """Høy fare skal gi høy risikonivå."""
        ctx = make_ctx(flom=HazardLevel.høy, skred=HazardLevel.høy)
        results = engine.evaluate(ctx)
        risk = engine.compute_risk_level(results)
        assert risk.value == "høy"

    def test_lav_fare_og_pass_gir_lav_eller_middels(self, engine):
        """Lav fare og ingen blokkerende regler gir lav/middels risiko."""
        ctx = make_ctx(
            measure_type=MeasureType.garasje,
            requires_application=False,
            requires_responsible=False,
            flom=HazardLevel.lav,
            skred=HazardLevel.lav,
        )
        results = engine.evaluate(ctx)
        risk = engine.compute_risk_level(results)
        assert risk.value in ("lav", "middels")

    def test_søknadspliktig_tilbygg_gir_middels_eller_høy(self, engine):
        """Søknadspliktig tilbygg gir middels eller høy risiko."""
        ctx = make_ctx(
            measure_type=MeasureType.tilbygg,
            requires_application=True,
            flom=HazardLevel.lav,
        )
        results = engine.evaluate(ctx)
        risk = engine.compute_risk_level(results)
        assert risk.value in ("middels", "høy")


# ── Application required ──────────────────────────────────────────────────────

class TestApplicationRequired:
    def test_tilbygg_krever_soknad(self, engine):
        ctx = make_ctx(measure_type=MeasureType.tilbygg, requires_application=True)
        results = engine.evaluate(ctx)
        req = engine.compute_application_required(results, ctx)
        assert req is True

    def test_garasje_uten_soknad(self, engine):
        """Garasje returnerer None (usikkert) fra compute_application_required."""
        ctx = make_ctx(
            measure_type=MeasureType.garasje,
            requires_application=False,
            requires_responsible=False,
        )
        results = engine.evaluate(ctx)
        req = engine.compute_application_required(results, ctx)
        # Garasje is in possibly_exempt – returns None (uncertain)
        assert req is None


# ── Next steps generation ─────────────────────────────────────────────────────

class TestNextSteps:
    def test_generates_steps_for_søknadspliktig(self, engine):
        ctx = make_ctx(measure_type=MeasureType.tilbygg, requires_application=True)
        results = engine.evaluate(ctx)
        steps = engine.generate_next_steps(results, True, ctx)
        assert len(steps) > 0

    def test_generates_steps_for_ikke_søknadspliktig(self, engine):
        ctx = make_ctx(
            measure_type=MeasureType.garasje,
            requires_application=False,
            requires_responsible=False,
        )
        results = engine.evaluate(ctx)
        steps = engine.generate_next_steps(results, False, ctx)
        assert len(steps) > 0

    def test_steps_are_strings(self, engine):
        ctx = make_ctx()
        results = engine.evaluate(ctx)
        steps = engine.generate_next_steps(results, True, ctx)
        for step in steps:
            assert isinstance(step, str)
            assert len(step) > 5


# ── Document requirements ─────────────────────────────────────────────────────

class TestDocumentRequirements:
    def test_søknadspliktig_har_dokumentkrav(self, engine):
        ctx = make_ctx(measure_type=MeasureType.tilbygg, requires_application=True)
        results = engine.evaluate(ctx)
        docs = engine.generate_document_requirements(True, ctx)
        assert len(docs) > 0

    def test_søknadspliktig_har_flere_krav_enn_ikke(self, engine):
        ctx_sok = make_ctx(measure_type=MeasureType.tilbygg, requires_application=True)
        ctx_nosok = make_ctx(
            measure_type=MeasureType.garasje,
            requires_application=False,
            requires_responsible=False,
        )
        docs_sok = engine.generate_document_requirements(True, ctx_sok)
        docs_nosok = engine.generate_document_requirements(False, ctx_nosok)
        assert len(docs_sok) >= len(docs_nosok)


# ── Rule completeness ─────────────────────────────────────────────────────────

class TestRuleCompleteness:
    def test_søkp_og_dok_regler_for_tilbygg(self, engine):
        """Tilbygg skal alltid gi SØKP- og DOK-regler."""
        ctx = make_ctx(measure_type=MeasureType.tilbygg, requires_application=True)
        results = engine.evaluate(ctx)
        codes = {r.ruleCode for r in results}
        assert any(c.startswith("SØKP") for c in codes), f"Mangler SØKP-regler. Koder: {codes}"
        assert any(c.startswith("DOK") for c in codes), f"Mangler DOK-regler. Koder: {codes}"

    def test_fare_regler_ved_høy_fare(self, engine):
        """Høy fare skal gi FARE-regler."""
        ctx = make_ctx(flom=HazardLevel.høy, skred=HazardLevel.høy)
        results = engine.evaluate(ctx)
        codes = {r.ruleCode for r in results}
        assert any(c.startswith("FARE") for c in codes), f"Mangler FARE-regler. Koder: {codes}"

    def test_minimum_rule_count_tilbygg(self, engine):
        """Minst 4 regler skal evalueres for tilbygg."""
        ctx = make_ctx()
        results = engine.evaluate(ctx)
        assert len(results) >= 4, f"Forventet minst 4 regler, fikk {len(results)}"

    def test_all_results_have_required_fields(self, engine):
        """Alle regelresultater skal ha obligatoriske felter."""
        ctx = make_ctx()
        results = engine.evaluate(ctx)
        for r in results:
            assert r.ruleCode, f"Regel mangler ruleCode: {r}"
            assert r.ruleName, f"Regel mangler ruleName: {r.ruleCode}"
            assert r.status in (RuleStatus.pass_, RuleStatus.fail, RuleStatus.warn), \
                f"Ugyldig status for {r.ruleCode}: {r.status}"
            assert r.legalBasis if hasattr(r, 'legalBasis') else r.evidenceRefs, \
                f"Regel mangler lovhjemmel: {r.ruleCode}"

    def test_blocking_rules_are_fail(self, engine):
        """Blokkerende regler skal alltid ha status fail."""
        ctx = make_ctx(flom=HazardLevel.høy)
        results = engine.evaluate(ctx)
        for r in results:
            if r.blocking:
                assert r.status == RuleStatus.fail, \
                    f"Blokkerende regel {r.ruleCode} har status {r.status}, forventet fail"
