"""
AI Document Generator – Fase 2
Agents:
  Agent 3: Tiltaksbeskrivelse (description of the building measure)
  Agent 4: Nabovarsel (neighbour notification letter)
  Agent 5: Søknadsutkast (application draft summary)
"""
import os
import json
from typing import Optional, Dict, Any
import structlog
from openai import AsyncOpenAI

logger = structlog.get_logger()

_client: Optional[AsyncOpenAI] = None


def get_openai_client() -> AsyncOpenAI:
    global _client
    if _client is None:
        _client = AsyncOpenAI(
            api_key=os.environ.get("OPENAI_API_KEY", ""),
            base_url=os.environ.get("OPENAI_BASE_URL", "https://api.openai.com/v1"),
        )
    return _client


class DocumentGeneratorService:
    """
    AI-powered document generation for building permit applications.
    Generates legally-informed Norwegian documents based on project analysis.
    """

    def __init__(self):
        self.model = "gpt-4.1-mini"

    async def generate_tiltaksbeskrivelse(
        self,
        project: Dict[str, Any],
        analysis: Optional[Dict[str, Any]] = None,
    ) -> str:
        """
        Agent 3: Generate a formal tiltaksbeskrivelse (measure description).
        This is a required document for søknadspliktige tiltak.
        """
        address = project.get("addressText", "")
        intent = project.get("intentText", "")
        measure_type = (analysis or {}).get("classification", {}).get("measureType", "ukjent")
        plan_status = (analysis or {}).get("planLayer", {}).get("planStatus", "ukjent")
        areal_formal = (analysis or {}).get("planLayer", {}).get("arealFormål", "ukjent")

        prompt = f"""Du er en erfaren byggesaksbehandler og hjelper en huseier med å skrive en tiltaksbeskrivelse for en byggesøknad.

Prosjektinformasjon:
- Adresse: {address}
- Tiltaksbeskrivelse fra huseier: {intent}
- Klassifisert tiltakstype: {measure_type}
- Planstatus: {plan_status}
- Arealformål: {areal_formal}

Skriv en formell tiltaksbeskrivelse på norsk som:
1. Beskriver tiltaket klart og presist
2. Angir formålet med tiltaket
3. Beskriver omfang og plassering
4. Nevner relevante tekniske krav (TEK17) der aktuelt
5. Er skrevet i en nøytral, profesjonell tone

Tiltaksbeskrivelsen skal være 2-4 avsnitt og egnet for vedlegg til en byggesøknad.
Ikke inkluder overskrift – bare selve teksten."""

        try:
            client = get_openai_client()
            response = await client.chat.completions.create(
                model=self.model,
                messages=[
                    {"role": "system", "content": "Du er ekspert på norsk plan- og bygningsrett og byggesaksbehandling."},
                    {"role": "user", "content": prompt},
                ],
                max_tokens=800,
                temperature=0.4,
            )
            return response.choices[0].message.content.strip()
        except Exception as e:
            logger.warning("tiltaksbeskrivelse_ai_failed", error=str(e))
            return self._fallback_tiltaksbeskrivelse(address, intent, measure_type)

    async def generate_nabovarsel(
        self,
        project: Dict[str, Any],
        analysis: Optional[Dict[str, Any]] = None,
        owner_name: str = "[Eiers navn]",
        owner_address: str = "[Eiers adresse]",
    ) -> str:
        """
        Agent 4: Generate a nabovarsel (neighbour notification letter).
        Required for søknadspliktige tiltak per PBL § 21-3.
        """
        address = project.get("addressText", "")
        intent = project.get("intentText", "")
        measure_type = (analysis or {}).get("classification", {}).get("measureType", "ukjent")
        gnr = (analysis or {}).get("property", {}).get("gnr", "[gnr]")
        bnr = (analysis or {}).get("property", {}).get("bnr", "[bnr]")
        municipality = (analysis or {}).get("property", {}).get("municipality", "[kommune]")

        prompt = f"""Du er en erfaren byggesaksbehandler og hjelper en huseier med å skrive et nabovarsel.

Prosjektinformasjon:
- Adresse: {address}
- Gårds-/bruksnummer: {gnr}/{bnr} i {municipality}
- Tiltaksbeskrivelse: {intent}
- Tiltakstype: {measure_type}
- Tiltakshaver: {owner_name}, {owner_address}

Skriv et formelt nabovarsel på norsk som:
1. Er adressert til naboer og gjenboere (bruk "Til naboer og gjenboere")
2. Informerer om det planlagte tiltaket
3. Angir frist for merknader (standard: 2 uker)
4. Opplyser om retten til å sende merknader til kommunen
5. Inkluderer kontaktinformasjon for tiltakshaver
6. Er i samsvar med PBL § 21-3 og SAK10 § 5-2

Formater som et fullstendig brev med dato-felt, hilsen og underskrift-felt.
Bruk [DATO] som plassholder for dato."""

        try:
            client = get_openai_client()
            response = await client.chat.completions.create(
                model=self.model,
                messages=[
                    {"role": "system", "content": "Du er ekspert på norsk plan- og bygningsrett og byggesaksbehandling."},
                    {"role": "user", "content": prompt},
                ],
                max_tokens=900,
                temperature=0.3,
            )
            return response.choices[0].message.content.strip()
        except Exception as e:
            logger.warning("nabovarsel_ai_failed", error=str(e))
            return self._fallback_nabovarsel(address, intent, owner_name, owner_address, gnr, bnr, municipality)

    async def generate_soknadsutkast(
        self,
        project: Dict[str, Any],
        analysis: Optional[Dict[str, Any]] = None,
    ) -> str:
        """
        Agent 5: Generate a søknadsutkast (application draft) summary.
        Provides a structured overview of what the application should contain.
        """
        address = project.get("addressText", "")
        intent = project.get("intentText", "")
        classification = (analysis or {}).get("classification", {})
        rule_results = (analysis or {}).get("ruleResults", [])
        doc_requirements = (analysis or {}).get("documentRequirements", [])
        risk_level = (analysis or {}).get("riskLevel", "ukjent")
        app_required = (analysis or {}).get("applicationRequired")

        # Summarize blocking rules
        blocking = [r for r in rule_results if r.get("blocking") and r.get("status") == "fail"]
        warnings_list = [r for r in rule_results if r.get("status") == "warn"]

        prompt = f"""Du er en erfaren byggesaksbehandler og hjelper en huseier med å forberede en byggesøknad.

Prosjektinformasjon:
- Adresse: {address}
- Tiltak: {intent}
- Tiltakstype: {classification.get('measureType', 'ukjent')}
- Søknadspliktig: {'Ja' if app_required else 'Nei/Usikkert'}
- Risikonivå: {risk_level}
- Blokkerende regelbrudd: {len(blocking)}
- Advarsler: {len(warnings_list)}
- Dokumentkrav: {json.dumps(doc_requirements, ensure_ascii=False)}

Lag en strukturert søknadsveiledning på norsk med disse seksjonene:
1. **Sammendrag** – kort oppsummering av situasjonen
2. **Søknadstype** – hvilken type søknad som kreves (ett-trinns, to-trinns, uten ansvarsrett)
3. **Nødvendige dokumenter** – komplett liste over vedlegg
4. **Ansvarlig søker** – om det kreves ansvarlig søker og hva det innebærer
5. **Viktige hensyn** – planstatus, faredata, nabovarsel
6. **Neste steg** – konkrete handlinger i riktig rekkefølge

Vær konkret og praktisk. Bruk norsk fagterminologi."""

        try:
            client = get_openai_client()
            response = await client.chat.completions.create(
                model=self.model,
                messages=[
                    {"role": "system", "content": "Du er ekspert på norsk plan- og bygningsrett og byggesaksbehandling."},
                    {"role": "user", "content": prompt},
                ],
                max_tokens=1200,
                temperature=0.4,
            )
            return response.choices[0].message.content.strip()
        except Exception as e:
            logger.warning("soknadsutkast_ai_failed", error=str(e))
            return f"Søknadsveiledning for {address}:\n\nKontakt kommunen for veiledning om søknadsprosessen."

    # ── Fallback templates ─────────────────────────────────────────────────

    def _fallback_tiltaksbeskrivelse(
        self, address: str, intent: str, measure_type: str
    ) -> str:
        return f"""Tiltaksbeskrivelse for eiendom: {address}

Det planlagte tiltaket er beskrevet som følger av tiltakshaver: {intent}

Tiltaket er klassifisert som {measure_type} i henhold til plan- og bygningsloven. Tiltaket vil gjennomføres i samsvar med gjeldende tekniske krav i TEK17 og kommunens reguleringsplan for området.

Tiltakshaver vil sørge for at alle nødvendige tillatelser er innhentet og at arbeidet utføres av kvalifiserte fagfolk med nødvendig ansvarsrett."""

    def _fallback_nabovarsel(
        self, address: str, intent: str, owner_name: str,
        owner_address: str, gnr: Any, bnr: Any, municipality: str
    ) -> str:
        return f"""Til naboer og gjenboere

[DATO]

NABOVARSEL – Planlagt byggetiltak

Eiendommen: {address} (gnr. {gnr}, bnr. {bnr} i {municipality})
Tiltakshaver: {owner_name}, {owner_address}

Vi varsler herved om planlagt byggetiltak på ovennevnte eiendom.

Beskrivelse av tiltaket:
{intent}

I henhold til plan- og bygningsloven § 21-3 har naboer og gjenboere rett til å sende merknader til kommunen innen 2 uker fra mottak av dette varselet.

Eventuelle merknader sendes til:
- Tiltakshaver: {owner_name}, {owner_address}
- Eller direkte til kommunen ved innsending av søknad

Med vennlig hilsen

{owner_name}
{owner_address}

_______________________
Underskrift"""


_document_generator: Optional[DocumentGeneratorService] = None


def get_document_generator() -> DocumentGeneratorService:
    global _document_generator
    if _document_generator is None:
        _document_generator = DocumentGeneratorService()
    return _document_generator
