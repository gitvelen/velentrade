from pathlib import Path

from velentrade.domain.requirements.structure import scan_requirement_structure


def test_requirement_ids_are_authoritative_in_spec_and_tc_coverage_is_complete():
    report = scan_requirement_structure(
        spec_path=Path("spec.md"),
        testing_path=Path("testing.md"),
        appendix_dir=Path("spec-appendices"),
    )

    assert report["result"] == "pass"
    assert report["req_acc_vo_scan"] == {"REQ": 32, "ACC": 32, "VO": 32}
    assert report["tc_coverage"]["missing_tc_for_acc"] == []
    assert report["appendix_formal_id_scan"]["formal_ids_found"] == []
    assert "spec-appendices/agent-capability-matrix.md" in report["appendix_usage_rules"]["known_appendices"]
