from __future__ import annotations

from dataclasses import dataclass


ROLE_ATTACHMENT_KEYS = ("macro", "fundamental", "quant", "event")


@dataclass(frozen=True)
class ICContextPackage:
    topic_id: str
    request_brief_ref: str
    data_readiness_ref: str
    market_state_ref: str
    service_result_refs: list[str]
    portfolio_context_ref: str
    risk_constraint_refs: list[str]
    research_package_refs: list[str]
    reflection_hit_refs: list[str]
    role_attachment_refs: dict[str, str]
    context_snapshot_id: str


@dataclass(frozen=True)
class ICChairBrief:
    decision_question: str
    scope_boundary: str
    key_tensions: list[str]
    must_answer_questions: list[str]
    time_budget: str
    action_standard: str
    risk_constraints_to_respect: list[str]
    forbidden_assumptions: list[str]
    no_preset_decision_attestation: bool


class ICContextBuilder:
    def build_context_package(
        self,
        topic_id: str,
        request_brief_ref: str,
        data_readiness_ref: str,
        market_state_ref: str,
        service_result_refs: list[str],
        portfolio_context_ref: str,
        risk_constraint_refs: list[str],
        research_package_refs: list[str],
        reflection_hit_refs: list[str],
        context_snapshot_id: str,
    ) -> ICContextPackage:
        return ICContextPackage(
            topic_id=topic_id,
            request_brief_ref=request_brief_ref,
            data_readiness_ref=data_readiness_ref,
            market_state_ref=market_state_ref,
            service_result_refs=service_result_refs,
            portfolio_context_ref=portfolio_context_ref,
            risk_constraint_refs=risk_constraint_refs,
            research_package_refs=research_package_refs,
            reflection_hit_refs=reflection_hit_refs,
            role_attachment_refs={role: f"{topic_id}:{role}" for role in ROLE_ATTACHMENT_KEYS},
            context_snapshot_id=context_snapshot_id,
        )

    def build_chair_brief(self, package: ICContextPackage, time_budget: str) -> ICChairBrief:
        return ICChairBrief(
            decision_question=f"围绕 {package.topic_id} 判断是否值得进入完整 IC 论证",
            scope_boundary="仅限 A 股普通股纸面投资研究，不涉及真实下单。",
            key_tensions=["数据质量与研究资料是否足以支持论证", "市场状态与组合约束是否冲突"],
            must_answer_questions=["核心机会或风险是什么", "关键反证和失效条件是什么", "需要哪些补充证据"],
            time_budget=time_budget,
            action_standard="只有证据、数据质量和风险约束均满足时，后续阶段才可讨论行动强度。",
            risk_constraints_to_respect=package.risk_constraint_refs,
            forbidden_assumptions=["不得预设买卖持有结论", "不得跳过 Risk/Owner/执行审计"],
            no_preset_decision_attestation=True,
        )

    def resolve_evidence(self, package: ICContextPackage) -> dict[str, list[str]]:
        refs = [
            package.request_brief_ref,
            package.data_readiness_ref,
            package.market_state_ref,
            package.portfolio_context_ref,
            *package.service_result_refs,
            *package.risk_constraint_refs,
            *package.research_package_refs,
            *package.role_attachment_refs.values(),
        ]
        missing = [ref for ref in refs if not ref]
        return {"resolved_refs": [ref for ref in refs if ref], "missing_refs": missing}
