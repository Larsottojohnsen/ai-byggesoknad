"""
AI Document Generator – Fase 3
Agents:
  Agent 3: Tiltaksbeskrivelse (description of the building measure)
  Agent 4: Nabovarsel (neighbour notification letter)
  Agent 5: Søknadsutkast (application draft summary)
  Agent 6: Dispensasjonssøknad (dispensation application)
  Agent 7: Sjekkliste (step-by-step checklist)

Oppdatert basert på:
- Veiledning om dispensasjon (Norsk Kommunalteknisk Forening, 2021)
- Søknadsskjema for dispensasjon (NKF, februar 2021)
- Sjekkliste for søknadsprosessen (Kristiansand kommune, 2026)
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
        gnr = (analysis or {}).get("property", {}).get("gnr", "")
        bnr = (analysis or {}).get("property", {}).get("bnr", "")
        municipality = (analysis or {}).get("property", {}).get("municipality", "")

        eiendom_info = f"gnr. {gnr}, bnr. {bnr} i {municipality}" if gnr and bnr else address

        prompt = f"""Du er en erfaren byggesaksbehandler og hjelper en huseier med å skrive en tiltaksbeskrivelse for en byggesøknad.

Prosjektinformasjon:
- Adresse: {address}
- Eiendom: {eiendom_info}
- Tiltaksbeskrivelse fra huseier: {intent}
- Klassifisert tiltakstype: {measure_type}
- Planstatus: {plan_status}
- Arealformål: {areal_formal}

Skriv en formell tiltaksbeskrivelse på norsk som:
1. Beskriver tiltaket klart og presist med adresse og gårds-/bruksnummer
2. Angir formålet med tiltaket
3. Beskriver omfang og plassering (størrelse, høyde, avstand til nabogrense)
4. Nevner relevante tekniske krav (TEK17) der aktuelt
5. Er skrevet i en nøytral, profesjonell tone egnet for vedlegg til byggesøknad

Tiltaksbeskrivelsen skal være 2-4 avsnitt. Ikke inkluder overskrift – bare selve teksten."""

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
- Gårds-/bruksnummer: gnr. {gnr}, bnr. {bnr} i {municipality}
- Tiltaksbeskrivelse: {intent}
- Tiltakstype: {measure_type}
- Tiltakshaver: {owner_name}, {owner_address}

Skriv et formelt nabovarsel på norsk som:
1. Er adressert til naboer og gjenboere (bruk "Til naboer og gjenboere")
2. Informerer tydelig om det planlagte tiltaket (hva, hvor, størrelse)
3. Angir frist for merknader (standard: 2 uker fra mottak av varselet)
4. Opplyser om at merknader sendes til tiltakshaver, som vil kommentere dem ved innsending av søknad
5. Opplyser om retten til å sende merknader direkte til kommunen
6. Inkluderer kontaktinformasjon for tiltakshaver
7. Er i samsvar med PBL § 21-3 og SAK10 § 5-2

Formater som et fullstendig brev med:
- Sted og dato-felt ([STED], [DATO])
- Overskrift: NABOVARSEL
- Brødtekst
- Hilsen og underskrift-felt
- Tiltakshavers navn og adresse under underskriften"""

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
        municipality = (analysis or {}).get("property", {}).get("municipality", "kommunen")
        gnr = (analysis or {}).get("property", {}).get("gnr", "")
        bnr = (analysis or {}).get("property", {}).get("bnr", "")

        blocking = [r for r in rule_results if r.get("blocking") and r.get("status") == "fail"]
        warnings_list = [r for r in rule_results if r.get("status") == "warn"]
        needs_dispensation = any(r.get("ruleCode", "").startswith("DISP") for r in rule_results)

        prompt = f"""Du er en erfaren byggesaksbehandler og hjelper en huseier med å forberede en byggesøknad.

Prosjektinformasjon:
- Adresse: {address}
- Eiendom: gnr. {gnr}, bnr. {bnr} i {municipality}
- Tiltak: {intent}
- Tiltakstype: {classification.get('measureType', 'ukjent')}
- Søknadspliktig: {'Ja' if app_required else 'Nei/Usikkert'}
- Risikonivå: {risk_level}
- Blokkerende regelbrudd: {len(blocking)}
- Advarsler: {len(warnings_list)}
- Krever dispensasjon: {'Ja' if needs_dispensation else 'Nei/Usikkert'}
- Dokumentkrav: {json.dumps(doc_requirements, ensure_ascii=False)}

Lag en strukturert søknadsveiledning på norsk med disse seksjonene:

## 1. Sammendrag
Kort oppsummering av situasjonen og hva som kreves.

## 2. Søknadstype
Hvilken type søknad som kreves (ett-trinns, to-trinns, uten ansvarsrett, med ansvarsrett).
Beskriv tiltaksklasse og om ansvarlig søker er nødvendig.

## 3. Nødvendige dokumenter
Komplett liste over vedlegg med forklaring på hva hvert dokument skal inneholde.

## 4. Saksbehandlingstid
Forventet behandlingstid hos kommunen (standard 12 uker etter PBL § 21-7, 3 uker for enkle tiltak).
Nevn at dispensasjonssøknad kan ta opptil 16 uker.

## 5. Viktige hensyn
Planstatus, faredata, nabovarsel, dispensasjon (hvis aktuelt).

## 6. Neste steg
Konkrete handlinger i riktig rekkefølge med referanser til lov/forskrift.

## 7. Nyttige lenker
- dibk.no/soknad-og-skjema (skjemaer)
- dibk.no/nabovarsel (nabovarsel-veiledning)
- arealplaner.no (reguleringsplaner)
- seeiendom.no (grunnbokutskrift)

Vær konkret og praktisk. Bruk norsk fagterminologi."""

        try:
            client = get_openai_client()
            response = await client.chat.completions.create(
                model=self.model,
                messages=[
                    {"role": "system", "content": "Du er ekspert på norsk plan- og bygningsrett og byggesaksbehandling."},
                    {"role": "user", "content": prompt},
                ],
                max_tokens=1500,
                temperature=0.4,
            )
            return response.choices[0].message.content.strip()
        except Exception as e:
            logger.warning("soknadsutkast_ai_failed", error=str(e))
            return f"Søknadsveiledning for {address}:\n\nKontakt kommunen for veiledning om søknadsprosessen."

    async def generate_dispensasjonssoknad(
        self,
        project: Dict[str, Any],
        analysis: Optional[Dict[str, Any]] = None,
        owner_name: str = "[Tiltakshavers navn]",
        owner_address: str = "[Tiltakshavers adresse]",
        owner_phone: str = "[Telefon]",
        owner_email: str = "[E-post]",
    ) -> str:
        """
        Agent 6: Generate a dispensasjonssøknad (dispensation application).
        Based on NKF skjema (februar 2021) and PBL § 19-1/§ 19-2.
        """
        address = project.get("addressText", "")
        intent = project.get("intentText", "")
        measure_type = (analysis or {}).get("classification", {}).get("measureType", "ukjent")
        plan_status = (analysis or {}).get("planLayer", {}).get("planStatus", "ukjent")
        areal_formal = (analysis or {}).get("planLayer", {}).get("arealFormål", "ukjent")
        plan_name = (analysis or {}).get("planLayer", {}).get("planName", "")
        gnr = (analysis or {}).get("property", {}).get("gnr", "[gnr]")
        bnr = (analysis or {}).get("property", {}).get("bnr", "[bnr]")
        municipality = (analysis or {}).get("property", {}).get("municipality", "[kommune]")

        # Determine what to dispense from
        disp_from = []
        if plan_status == "regulert" and plan_name:
            disp_from.append(f"Reguleringsplan: {plan_name}")
        elif plan_status == "regulert":
            disp_from.append("Reguleringsplan (kommunens gjeldende reguleringsplan for området)")
        if areal_formal and areal_formal.lower() not in ["ukjent", ""]:
            disp_from.append(f"Arealformål: {areal_formal}")

        prompt = f"""Du er en erfaren byggesaksbehandler og hjelper en huseier med å skrive en dispensasjonssøknad etter plan- og bygningsloven § 19-1.

Prosjektinformasjon:
- Adresse: {address}
- Eiendom: gnr. {gnr}, bnr. {bnr} i {municipality}
- Tiltakshaver: {owner_name}, {owner_address}
- Telefon: {owner_phone}, E-post: {owner_email}
- Tiltak: {intent}
- Tiltakstype: {measure_type}
- Planstatus: {plan_status}
- Arealformål: {areal_formal}
- Det søkes dispensasjon fra: {', '.join(disp_from) if disp_from else 'reguleringsplan'}

Skriv en komplett dispensasjonssøknad på norsk basert på NKF-skjemaet (februar 2021) med følgende struktur:

---
SØKNAD OM DISPENSASJON

For tiltak på følgende eiendom:
Gnr: {gnr}  Bnr: {bnr}  F.nr: ___  S.nr: ___
Adresse: {address}

Søknaden innsendes av:
Tiltakshavers navn: {owner_name}
Tiltakshavers adresse: {owner_address}
Kontaktperson: {owner_name}
Telefon dagtid: {owner_phone}  Epost-adresse: {owner_email}

Jeg/vi søker om dispensasjon fra:
[X] {', '.join(disp_from) if disp_from else 'Reguleringsplan'}

Jeg/vi søker om dispensasjon fra følgende bestemmelser:
[Skriv hvilke konkrete bestemmelser i planen det søkes dispensasjon fra]

For å kunne bygge/gjøre:
[Beskriv tiltaket konkret]

Jeg/vi søker om:
[X] Dispensasjon etter pbl §19-1 (permanent)

Begrunnelse for dispensasjonssøknaden:
[Her skal du skrive en grundig begrunnelse som viser at begge vilkårene i PBL § 19-2 er oppfylt:
1. At hensynene bak bestemmelsen det dispenseres fra ikke vesentlig tilsidesettes
2. At fordelene ved dispensasjonen er klart større enn ulempene]

Vedlegg:
- Kvittering for nabovarsel (skal alltid være med)
- Tegninger
- Situasjonsplan
- Andre vedlegg

_______________________          _______________________
Dato og underskrift               Dato og underskrift
tiltakshaver                      eventuell ansvarlig søker
---

Fyll inn alle feltene med realistisk og juridisk korrekt innhold basert på prosjektinformasjonen.
Begrunnelsen skal være konkret og adressere begge vilkårene i PBL § 19-2.
Fremhev at personlige behov alene ikke er tilstrekkelig begrunnelse – fokuser på objektive fordeler.
Bruk norsk fagterminologi."""

        try:
            client = get_openai_client()
            response = await client.chat.completions.create(
                model=self.model,
                messages=[
                    {"role": "system", "content": "Du er ekspert på norsk plan- og bygningsrett, dispensasjonssøknader og byggesaksbehandling."},
                    {"role": "user", "content": prompt},
                ],
                max_tokens=1500,
                temperature=0.3,
            )
            return response.choices[0].message.content.strip()
        except Exception as e:
            logger.warning("dispensasjonssoknad_ai_failed", error=str(e))
            return self._fallback_dispensasjonssoknad(
                address, intent, measure_type, gnr, bnr, municipality,
                owner_name, owner_address, owner_phone, owner_email, disp_from
            )

    async def generate_sjekkliste(
        self,
        project: Dict[str, Any],
        analysis: Optional[Dict[str, Any]] = None,
    ) -> str:
        """
        Agent 7: Generate a step-by-step checklist for the building permit process.
        Based on the Kristiansand kommune checklist (2026).
        """
        address = project.get("addressText", "")
        intent = project.get("intentText", "")
        measure_type = (analysis or {}).get("classification", {}).get("measureType", "ukjent")
        app_required = (analysis or {}).get("applicationRequired")
        municipality = (analysis or {}).get("property", {}).get("municipality", "kommunen")
        risk_level = (analysis or {}).get("riskLevel", "ukjent")
        rule_results = (analysis or {}).get("ruleResults", [])
        needs_dispensation = any(r.get("ruleCode", "").startswith("DISP") for r in rule_results)
        has_hazard = any(r.get("ruleGroup") == "naturfare" and r.get("status") == "fail" for r in rule_results)

        prompt = f"""Du er en erfaren byggesaksbehandler og lager en praktisk sjekkliste for en huseier.

Prosjektinformasjon:
- Adresse: {address}
- Tiltak: {intent}
- Tiltakstype: {measure_type}
- Søknadspliktig: {'Ja' if app_required else 'Nei/Usikkert'}
- Risikonivå: {risk_level}
- Krever dispensasjon: {'Ja' if needs_dispensation else 'Nei'}
- Naturfare: {'Ja' if has_hazard else 'Nei'}
- Kommune: {municipality}

Lag en komplett, praktisk sjekkliste for søknadsprosessen basert på norsk byggesaksbehandling.
Sjekklisten skal følge denne strukturen:

## Sjekkliste for byggesøknad – {address}

### Fase 1: Forberedelse (gjøres FØR søknad sendes)
- [ ] Sjekk om det er midlertidig forbud mot bygge- og deling i området
- [ ] Sjekk om grunnen er forurenset (grunnforurensning.miljodirektoratet.no)
- [ ] Sjekk gjeldende reguleringsplan (arealplaner.no eller kommunens planregister)
- [ ] Sjekk avstand til vann, avløp og høyspentledninger
- [legg til relevante punkter basert på tiltakstype og risikonivå]

### Fase 2: Dokumenter og tegninger
- [ ] Bestill situasjonskart fra kommunens kartportal
- [ ] Tegn situasjonsplan (1:500) med tiltaket inntegnet
- [ ] Utarbeid plantegninger, fasadetegninger og snittegninger (1:100)
- [legg til relevante punkter]

### Fase 3: Nabovarsel
- [ ] Hent naboliste fra kommunens Min side
- [ ] Send nabovarsel til alle naboer og gjenboere
- [ ] Vent minst 2 uker på merknader
- [ ] Samle inn eventuelle merknader og skriv kommentarer

### Fase 4: Søknad
- [ ] Fyll ut søknadsskjema (blankett 5174 eller digital)
- [legg til relevante punkter basert på tiltakstype]

### Fase 5: Innsending
- [ ] Send komplett søknad til kommunen
- [ ] Bekreft mottatt søknad og saksnummer
- [ ] Forventet saksbehandlingstid: [angi riktig tid]

Tilpass sjekklisten til det konkrete tiltaket og legg til dispensasjonspunkter hvis aktuelt.
Bruk [ ] for avkrysningsbokser og vær konkret og handlingsorientert."""

        try:
            client = get_openai_client()
            response = await client.chat.completions.create(
                model=self.model,
                messages=[
                    {"role": "system", "content": "Du er ekspert på norsk plan- og bygningsrett og byggesaksbehandling."},
                    {"role": "user", "content": prompt},
                ],
                max_tokens=1200,
                temperature=0.3,
            )
            return response.choices[0].message.content.strip()
        except Exception as e:
            logger.warning("sjekkliste_ai_failed", error=str(e))
            return self._fallback_sjekkliste(address, intent, measure_type, municipality)

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

[STED], [DATO]

NABOVARSEL – Planlagt byggetiltak

Eiendommen: {address} (gnr. {gnr}, bnr. {bnr} i {municipality})
Tiltakshaver: {owner_name}, {owner_address}

Vi varsler herved om planlagt byggetiltak på ovennevnte eiendom.

Beskrivelse av tiltaket:
{intent}

I henhold til plan- og bygningsloven § 21-3 har naboer og gjenboere rett til å sende merknader til tiltakshaver innen 2 uker fra mottak av dette varselet. Merknader som ikke er sendt innen fristen, kan ikke påregnes å bli tatt hensyn til.

Eventuelle merknader sendes til:
Tiltakshaver: {owner_name}, {owner_address}

Merknader vil bli kommentert av tiltakshaver og vedlagt søknaden til kommunen.

Med vennlig hilsen

_______________________
{owner_name}
{owner_address}"""

    def _fallback_dispensasjonssoknad(
        self, address: str, intent: str, measure_type: str,
        gnr: Any, bnr: Any, municipality: str,
        owner_name: str, owner_address: str, owner_phone: str, owner_email: str,
        disp_from: list
    ) -> str:
        return f"""SØKNAD OM DISPENSASJON

For tiltak på følgende eiendom:
Gnr: {gnr}  Bnr: {bnr}
Adresse: {address}

Søknaden innsendes av:
Tiltakshavers navn: {owner_name}
Tiltakshavers adresse: {owner_address}
Telefon dagtid: {owner_phone}  Epost-adresse: {owner_email}

Jeg/vi søker om dispensasjon fra:
[X] {', '.join(disp_from) if disp_from else 'Reguleringsplan'}

For å kunne bygge/gjøre:
{intent}

Jeg/vi søker om:
[X] Dispensasjon etter pbl §19-1 (permanent)

Begrunnelse for dispensasjonssøknaden:
[Fyll inn begrunnelse her. Begrunnelsen må vise at:
1. Hensynene bak bestemmelsen det dispenseres fra ikke vesentlig tilsidesettes
2. Fordelene ved dispensasjonen er klart større enn ulempene]

Vedlegg:
- Kvittering for nabovarsel (skal alltid være med)
- Tegninger
- Situasjonsplan

_______________________
Dato og underskrift, tiltakshaver: {owner_name}"""

    def _fallback_sjekkliste(
        self, address: str, intent: str, measure_type: str, municipality: str
    ) -> str:
        return f"""## Sjekkliste for byggesøknad – {address}

### Fase 1: Forberedelse
- [ ] Sjekk om det er midlertidig forbud mot bygge- og deling i området
- [ ] Sjekk om grunnen er forurenset (grunnforurensning.miljodirektoratet.no)
- [ ] Sjekk gjeldende reguleringsplan (arealplaner.no)
- [ ] Sjekk avstand til vann, avløp og høyspentledninger

### Fase 2: Dokumenter og tegninger
- [ ] Bestill situasjonskart fra kommunens kartportal
- [ ] Tegn situasjonsplan (1:500) med tiltaket inntegnet
- [ ] Utarbeid plantegninger, fasadetegninger og snittegninger (1:100)

### Fase 3: Nabovarsel
- [ ] Hent naboliste fra kommunens Min side
- [ ] Send nabovarsel til alle naboer og gjenboere
- [ ] Vent minst 2 uker på merknader
- [ ] Samle inn eventuelle merknader og skriv kommentarer

### Fase 4: Søknad
- [ ] Fyll ut søknadsskjema (blankett 5174 eller digital)
- [ ] Samle alle vedlegg

### Fase 5: Innsending
- [ ] Send komplett søknad til {municipality}
- [ ] Bekreft mottatt søknad og saksnummer
- [ ] Forventet saksbehandlingstid: 12 uker (PBL § 21-7)"""


_document_generator: Optional[DocumentGeneratorService] = None


def get_document_generator() -> DocumentGeneratorService:
    global _document_generator
    if _document_generator is None:
        _document_generator = DocumentGeneratorService()
    return _document_generator
