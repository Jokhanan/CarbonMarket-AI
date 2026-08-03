"""
Tests for docs/SPEC-06.md T3 (storage) and T5 (instantiation engine).
Needs a reachable PostgreSQL with SPEC-05/06 schema, the VPA-DD v3.0
template analyzed (SPEC-05 T7) and RECH v5.0 parameters extracted
(SPEC-06 T3 bootstrap already run in this session); skip automatically
otherwise.
"""
import os
from pathlib import Path

import pytest

REPO_DIR = Path(__file__).parent.parent.parent / "document_repository"
RECH_V5_PATH = REPO_DIR / (
    "46b28bf95d6c80b7_CURRENT_DOCUMENT-_Reduced_emissions_from_cooking_and_heating__RECH___formerly_TPDDTEC"
)


def _db_available() -> bool:
    if not os.getenv("DATABASE_URL"):
        return False
    try:
        from carbongpt.repository.db import get_cursor
        with get_cursor() as cur:
            cur.execute("SELECT 1")
        return True
    except Exception:
        return False


def _rech_version_id():
    from carbongpt.repository.db import get_cursor
    with get_cursor() as cur:
        cur.execute("SELECT id FROM methodology_version_history WHERE methodology_code='407' AND version='5.0'")
        row = cur.fetchone()
    return row["id"] if row else None


def _vpa_dd_v3_template_version_id():
    from carbongpt.repository.db import get_cursor
    with get_cursor() as cur:
        cur.execute(
            """SELECT dtv.id FROM document_template_versions dtv
               JOIN document_templates dt ON dt.id = dtv.template_id
               WHERE dt.doc_type = 'VPA-DD' AND dtv.version = '3.0'"""
        )
        row = cur.fetchone()
    return row["id"] if row else None


requires_db = pytest.mark.skipif(not _db_available(), reason="DATABASE_URL not set or DB unreachable")
requires_rech_ingested = pytest.mark.skipif(
    not _db_available() or _rech_version_id() is None,
    reason="RECH v5.0 not ingested (SPEC-01 bootstrap)",
)
requires_vpa_dd_v3_analyzed = pytest.mark.skipif(
    not _db_available() or _vpa_dd_v3_template_version_id() is None,
    reason="VPA-DD v3.0 not ingested/analyzed (SPEC-05 T7 bootstrap)",
)


@requires_db
@requires_rech_ingested
class TestStoreRechParametersIdempotence:
    def test_reextracting_and_storing_does_not_duplicate_rows(self):
        from carbongpt.repository.db import get_cursor
        from carbongpt.repository.rech_parameter_extractor import (
            extract_rech_parameters,
            store_rech_parameters,
        )

        version_id = _rech_version_id()
        params = extract_rech_parameters(str(RECH_V5_PATH))

        store_rech_parameters(version_id, params)
        store_rech_parameters(version_id, params)

        with get_cursor() as cur:
            cur.execute(
                "SELECT count(*) c FROM methodology_parameters WHERE methodology_version_id = %s",
                (version_id,),
            )
            assert cur.fetchone()["c"] == 26

    def test_every_stored_row_is_llm_extracted_never_manual_or_pre_verified(self):
        from carbongpt.repository.db import get_cursor

        version_id = _rech_version_id()
        with get_cursor() as cur:
            cur.execute(
                "SELECT extraction_method, verified_by, verified_at FROM methodology_parameters "
                "WHERE methodology_version_id = %s",
                (version_id,),
            )
            rows = cur.fetchall()
        assert rows
        for r in rows:
            assert r["extraction_method"] == "llm_extracted"
            assert r["verified_by"] is None
            assert r["verified_at"] is None


@requires_db
@requires_rech_ingested
@requires_vpa_dd_v3_analyzed
class TestInstantiateParameterBlocks:
    @pytest.fixture(scope="class")
    def result(self):
        from carbongpt.repository.parameter_instantiation import instantiate_parameter_blocks
        return instantiate_parameter_blocks(_vpa_dd_v3_template_version_id(), _rech_version_id())

    def test_ex_ante_block_has_18_instances(self, result):
        # ICS 1-17 (17 ex_ante) + ICS 20 (fNRB, 'both') = 18.
        assert result["ex_ante_block"]["field_key"] == "T37"
        assert len(result["ex_ante_block"]["instances"]) == 18

    def test_monitoring_block_has_9_instances(self, result):
        # ICS 18,19,21-26 (8 monitoring) + ICS 20 (fNRB, 'both') = 9.
        assert result["monitoring_block"]["field_key"] == "T40"
        assert len(result["monitoring_block"]["instances"]) == 9

    def test_fnrb_appears_in_both_blocks_not_picked_for_one(self, result):
        ex_ante_ids = {p["parameter_id"] for p in result["ex_ante_block"]["instances"]}
        monitoring_ids = {p["parameter_id"] for p in result["monitoring_block"]["instances"]}
        assert "ICS 20" in ex_ante_ids
        assert "ICS 20" in monitoring_ids

    def test_sdg_block_is_unmapped_not_guessed(self, result):
        unmapped_keys = {b["field_key"] for b in result["unmapped_blocks"]}
        assert "T55" in unmapped_keys
        assert not any(
            p["parameter_id"] == "ICS 1" for block in (result["ex_ante_block"], result["monitoring_block"])
            for p in (block or {}).get("instances", [])
            if block and block["field_key"] == "T55"
        )

    def test_no_parameter_silently_dropped(self, result):
        all_instantiated = {p["parameter_id"] for p in result["ex_ante_block"]["instances"]} | {
            p["parameter_id"] for p in result["monitoring_block"]["instances"]
        }
        needs_review_ids = {p["parameter_id"] for p in result["needs_review"]}
        assert len(all_instantiated | needs_review_ids) == 26
