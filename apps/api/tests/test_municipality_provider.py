"""
Tests for the municipality provider (Fase 3).
Tests YAML rule loading and municipality identification.
"""
import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import pytest
from providers.municipality_provider import (
    load_kommune_rules,
    get_kommune_contact,
    get_kommune_fees,
    get_kommune_extra_docs,
    get_kommune_special_measures,
    list_supported_municipalities,
)


class TestKommuneRules:
    def test_oslo_rules_load(self):
        rules = load_kommune_rules("0301")
        assert rules is not None
        assert rules["kommune_navn"] == "Oslo"
        assert "kontakt" in rules
        assert "gebyrer" in rules

    def test_bergen_rules_load(self):
        rules = load_kommune_rules("4601")
        assert rules is not None
        assert rules["kommune_navn"] == "Bergen"

    def test_trondheim_rules_load(self):
        rules = load_kommune_rules("5001")
        assert rules is not None
        assert rules["kommune_navn"] == "Trondheim"

    def test_unknown_kommune_returns_none(self):
        rules = load_kommune_rules("9999")
        assert rules is None

    def test_oslo_contact_info(self):
        contact = get_kommune_contact("0301")
        assert "epost" in contact or "url" in contact

    def test_oslo_fees(self):
        fees = get_kommune_fees("0301")
        assert fees is not None
        assert "ett_trinns_soknad_kr" in fees
        assert fees["ett_trinns_soknad_kr"] > 0

    def test_oslo_extra_docs(self):
        docs = get_kommune_extra_docs("0301")
        assert isinstance(docs, list)
        assert len(docs) > 0

    def test_unknown_kommune_extra_docs_empty(self):
        docs = get_kommune_extra_docs("9999")
        assert docs == []

    def test_oslo_kjeller_measure_rules(self):
        rules = get_kommune_special_measures("0301", "kjeller_innredning")
        assert rules is not None
        assert "beskrivelse" in rules

    def test_oslo_unknown_measure_returns_none(self):
        rules = get_kommune_special_measures("0301", "ukjent_tiltak_xyz")
        assert rules is None

    def test_list_supported_municipalities(self):
        municipalities = list_supported_municipalities()
        assert len(municipalities) >= 3
        names = [m["kommunenavn"] for m in municipalities]
        assert "Oslo" in names
        assert "Bergen" in names
        assert "Trondheim" in names

    def test_rules_cache_works(self):
        # Load twice – second should come from cache
        rules1 = load_kommune_rules("0301")
        rules2 = load_kommune_rules("0301")
        assert rules1 is rules2  # Same object from cache


class TestKommuneRuleContent:
    def test_oslo_has_arealplan_section(self):
        rules = load_kommune_rules("0301")
        assert "arealplan" in rules
        assert "maks_bya_bolig_sentrum" in rules["arealplan"]

    def test_bergen_has_skred_warning(self):
        rules = load_kommune_rules("4601")
        saerlige = rules.get("saerlige_tiltak", [])
        types = [t["type"] for t in saerlige]
        assert "tiltak_skredfare" in types

    def test_trondheim_has_kvikkleire_warning(self):
        rules = load_kommune_rules("5001")
        saerlige = rules.get("saerlige_tiltak", [])
        types = [t["type"] for t in saerlige]
        assert "tiltak_kvikkleire" in types

    def test_all_kommuner_have_required_fields(self):
        for m in list_supported_municipalities():
            rules = load_kommune_rules(m["kommunenr"])
            assert rules is not None
            assert "kommune_nr" in rules
            assert "kommune_navn" in rules
            assert "kontakt" in rules
