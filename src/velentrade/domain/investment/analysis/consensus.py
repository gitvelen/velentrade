from __future__ import annotations

from dataclasses import dataclass
from math import sqrt
from statistics import mean
from typing import Any

from velentrade.domain.investment.analysis.memo import AnalystMemo, ROLE_PAYLOAD_FIELDS


ACTION_THRESHOLD = 0.65


@dataclass(frozen=True)
class ConsensusResult:
    consensus_score: float
    action_conviction: float
    dominant_direction_share: float
    population_std: float
    hard_dissent_present: bool
    execution_authorized: bool
    reason_code: str
    formula_inputs: dict[str, Any]


class ConsensusCalculator:
    def calculate(self, memos: list[AnalystMemo]) -> ConsensusResult:
        if {memo.role for memo in memos} != set(ROLE_PAYLOAD_FIELDS):
            raise ValueError("requires_four_official_analyst_memos")
        normalized = [memo.direction_score / 5 for memo in memos]
        avg = mean(normalized)
        std = sqrt(sum((item - avg) ** 2 for item in normalized) / len(normalized))
        dominant_share = _dominant_direction_share(memos)
        consensus = round(0.6 * (1 - std) + 0.4 * dominant_share, 3)
        action = round(
            0.35 * abs(avg)
            + 0.25 * mean([memo.confidence for memo in memos])
            + 0.20 * mean([memo.evidence_quality for memo in memos])
            + 0.20 * consensus,
            3,
        )
        hard_dissent = any(memo.hard_dissent for memo in memos)
        if consensus < 0.7:
            reason = "low_consensus_no_execution"
        elif hard_dissent:
            reason = "hard_dissent_requires_debate"
        elif action < ACTION_THRESHOLD:
            reason = "low_action_conviction_no_execution"
        else:
            reason = "formula_action_eligible"
        return ConsensusResult(
            consensus_score=consensus,
            action_conviction=action,
            dominant_direction_share=dominant_share,
            population_std=round(std, 3),
            hard_dissent_present=hard_dissent,
            execution_authorized=reason == "formula_action_eligible",
            reason_code=reason,
            formula_inputs={
                "direction_scores": [memo.direction_score for memo in memos],
                "confidence": [memo.confidence for memo in memos],
                "evidence_quality": [memo.evidence_quality for memo in memos],
            },
        )


def _dominant_direction_share(memos: list[AnalystMemo]) -> float:
    signs = ["positive" if memo.direction_score > 0 else "negative" if memo.direction_score < 0 else "neutral" for memo in memos]
    return max(signs.count("positive"), signs.count("negative"), signs.count("neutral")) / len(memos)
