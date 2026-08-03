"""
Tests for carbongpt.repository.field_requirement_linking (docs/SPEC-06.md,
T4). Needs a reachable PostgreSQL with VPA-DD v3.0 analyzed (SPEC-05 T7),
RECH v5.0 ingested (SPEC-01) and the 7 crosscutting documents ingested
(SPEC-06 T2, this session's bootstrap); skips automatically otherwise.
"""
import os

import pytest


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


def _template_version_id():
    from carbongpt.repository.db import get_cursor
    with get_cursor() as cur:
        cur.execute(
            """SELECT dtv.id FROM document_template_versions dtv
               JOIN document_templates dt ON dt.id = dtv.template_id
               WHERE dt.doc_type = 'VPA-DD' AND dtv.version = '3.0'"""
        )
        row = cur.fetchone()
    return row["id"] if row else None


def _methodology_version_id():
    from carbongpt.repository.db import get_cursor
    with get_cursor() as cur:
        cur.execute("SELECT id FROM methodology_version_history WHERE methodology_code='407' AND version='5.0'")
        row = cur.fetchone()
    return row["id"] if row else None


def _crosscutting_ready() -> bool:
    if not _db_available():
        return False
    from carbongpt.repository.db import get_cursor
    with get_cursor() as cur:
        cur.execute("SELECT count(*) c FROM crosscutting_requirements WHERE is_current = true")
        return cur.fetchone()["c"] >= 7


requires_bootstrap = pytest.mark.skipif(
    not _db_available() or _template_version_id() is None or _methodology_version_id() is None
    or not _crosscutting_ready(),
    reason="VPA-DD v3.0 / RECH v5.0 / crosscutting requirements not fully bootstrapped",
)


@requires_bootstrap
class TestLinkVpaDdV3Sections:
    @pytest.fixture(scope="class")
    def linked(self):
        from carbongpt.repository.field_requirement_linking import link_vpa_dd_v3_sections
        return link_vpa_dd_v3_sections(_template_version_id(), _methodology_version_id())

    def test_no_links_skipped(self, linked):
        assert linked["skipped"] == []

    def test_writes_twelve_links(self, linked):
        # 9 sections (2 unlinked by design) + 3 parameter blocks:
        # H27(2) + H96(1) + H196(2) + H212(1) + H271(1) + H285(1) + H303(1)
        # + T37(1) + T40(1) + T55(1) = 12
        assert linked["links_written"] == 12

    def test_reapplying_does_not_duplicate(self):
        from carbongpt.repository.db import get_cursor
        from carbongpt.repository.field_requirement_linking import link_vpa_dd_v3_sections

        link_vpa_dd_v3_sections(_template_version_id(), _methodology_version_id())
        link_vpa_dd_v3_sections(_template_version_id(), _methodology_version_id())

        with get_cursor() as cur:
            cur.execute(
                """SELECT count(*) c FROM template_field_requirements tfr
                   JOIN template_fields tf ON tf.id = tfr.template_field_id
                   WHERE tf.template_version_id = %s""",
                (_template_version_id(),),
            )
            assert cur.fetchone()["c"] == 12

    def test_application_of_methodology_section_governed_by_rech(self):
        from carbongpt.repository.db import get_cursor
        from carbongpt.repository.field_requirement_linking import link_vpa_dd_v3_sections

        link_vpa_dd_v3_sections(_template_version_id(), _methodology_version_id())
        with get_cursor() as cur:
            cur.execute(
                """SELECT tfr.requirement_type, tfr.methodology_version_id FROM template_field_requirements tfr
                   JOIN template_fields tf ON tf.id = tfr.template_field_id
                   WHERE tf.field_key = 'H96' AND tf.template_version_id = %s""",
                (_template_version_id(),),
            )
            rows = cur.fetchall()
        assert len(rows) == 1
        assert rows[0]["requirement_type"] == "methodology"
        assert rows[0]["methodology_version_id"] == _methodology_version_id()

    def test_sdg_parameter_block_governed_by_118_not_rech(self):
        from carbongpt.repository.db import get_cursor
        from carbongpt.repository.field_requirement_linking import link_vpa_dd_v3_sections

        link_vpa_dd_v3_sections(_template_version_id(), _methodology_version_id())
        with get_cursor() as cur:
            cur.execute(
                """SELECT tfr.requirement_type, cr.code FROM template_field_requirements tfr
                   JOIN template_fields tf ON tf.id = tfr.template_field_id
                   JOIN crosscutting_requirements cr ON cr.id = tfr.crosscutting_requirement_id
                   WHERE tf.field_key = 'T55' AND tf.template_version_id = %s""",
                (_template_version_id(),),
            )
            rows = cur.fetchall()
        assert len(rows) == 1
        assert rows[0]["code"] == "118"

    def test_find_unlinked_sections_finds_the_two_documented_gaps(self):
        from carbongpt.repository.field_requirement_linking import (
            find_unlinked_sections,
            link_vpa_dd_v3_sections,
        )

        link_vpa_dd_v3_sections(_template_version_id(), _methodology_version_id())
        gaps = find_unlinked_sections(_template_version_id())
        titles = {g["title"] for g in gaps}
        assert titles == {"Contact information of CME", "LUF additional information"}
