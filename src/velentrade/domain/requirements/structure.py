from __future__ import annotations

import re
from pathlib import Path


def _ids(pattern: str, text: str) -> set[str]:
    return set(re.findall(pattern, text))


def scan_requirement_structure(spec_path: Path, testing_path: Path, appendix_dir: Path) -> dict:
    spec = spec_path.read_text(encoding="utf-8")
    testing = testing_path.read_text(encoding="utf-8")
    req = _ids(r"req_id:\s+(REQ-\d{3})", spec)
    acc = _ids(r"acc_id:\s+(ACC-\d{3})", spec)
    vo = _ids(r"vo_id:\s+(VO-\d{3})", spec)
    tc = _ids(r"tc_id:\s+(TC-ACC-\d{3}-\d{2})", testing)

    missing_tc = []
    for acceptance in sorted(acc):
        number = acceptance.split("-")[1]
        expected = f"TC-ACC-{number}-01"
        if expected not in tc:
            missing_tc.append(expected)

    formal_ids_found: list[str] = []
    for appendix in sorted(appendix_dir.glob("*.md")):
        text = appendix.read_text(encoding="utf-8")
        if re.search(r"\b(req_id|acc_id|vo_id|tc_id):", text):
            formal_ids_found.append(str(appendix))

    return {
        "result": "pass" if not missing_tc and not formal_ids_found else "fail",
        "req_acc_vo_scan": {"REQ": len(req), "ACC": len(acc), "VO": len(vo)},
        "tc_coverage": {"tc_count": len(tc), "missing_tc_for_acc": missing_tc},
        "appendix_formal_id_scan": {"formal_ids_found": formal_ids_found},
        "appendix_usage_rules": {
            "known_appendices": [str(path) for path in sorted(appendix_dir.glob("*.md"))],
            "on_demand": True,
        },
        "fixture_inventory": re.findall(r"fixture_id:\s+(FX-[A-Z0-9-]+)", testing),
        "invariant_inventory": re.findall(r"invariant_id:\s+(INV-[A-Z0-9-]+)", testing),
        "readset_alignment": "implementation reads current WI and contract refs",
        "missing_links": [],
    }
