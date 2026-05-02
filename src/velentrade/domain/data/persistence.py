from __future__ import annotations

from dataclasses import asdict
from datetime import datetime
from typing import Callable

from sqlalchemy import select
from sqlalchemy.engine import Engine

from velentrade.db.base import Base
from velentrade.domain.common import utc_now
from velentrade.domain.data.quality import DataRequest
from velentrade.domain.data.sources import (
    DataCollectionResult,
    DataSourceDefinition,
    DataSourceRegistry,
    NormalizedDataSet,
    PublicHttpCsvDailyQuoteAdapter,
    PublicHttpJsonKlineDailyQuoteAdapter,
    StaticDataSourceAdapter,
    eastmoney_secid_mapper,
    tencent_market_symbol_mapper,
)


def _as_datetime(value: str) -> datetime:
    return datetime.fromisoformat(value)


def _usage_tuple(raw_usage_scope: str) -> tuple[str, ...]:
    return tuple(part.strip() for part in raw_usage_scope.replace(";", ",").split(",") if part.strip())


def _symbol_mapper(name: object) -> Callable[[str], str] | None:
    if name == "tencent_market_symbol":
        return tencent_market_symbol_mapper
    if name == "eastmoney_secid":
        return eastmoney_secid_mapper
    return None


def build_source_registry_from_db(
    engine: Engine,
    *,
    fetch_text: Callable[[str], str] | None = None,
) -> DataSourceRegistry:
    registry = DataSourceRegistry()
    table = Base.metadata.tables["data_source_registry"]
    with engine.connect() as connection:
        rows = connection.execute(select(table).where(table.c.status.in_(["active", "fixture_only"]))).mappings().all()

    for row in rows:
        payload = dict(row["payload"] or {})
        source = DataSourceDefinition(
            source_id=row["source_id"],
            data_domain=row["data_domain"],
            allowed_usage=_usage_tuple(row["usage_scope"]),
            priority=row["priority"],
            status=row["status"],
            license_summary=row["license_summary"],
            rate_limit=dict(row["rate_limit"] or {}),
            adapter_kind=row["adapter_kind"],
            endpoint_template=payload.get("endpoint_template"),
            cache_ttl_seconds=int(payload.get("cache_ttl_seconds", 0)),
            fallback_order=tuple(payload.get("fallback_order", ())),
            payload=payload,
        )
        if source.adapter_kind == "public_http_csv_daily_quote":
            registry.register(source, PublicHttpCsvDailyQuoteAdapter(source, fetch_text=fetch_text))
        elif source.adapter_kind == "public_http_json_kline_daily_quote":
            registry.register(
                source,
                PublicHttpJsonKlineDailyQuoteAdapter(
                    source,
                    fetch_text=fetch_text,
                    symbol_mapper=_symbol_mapper(payload.get("symbol_mapper")),
                ),
            )
        else:
            registry.register(source, StaticDataSourceAdapter(NormalizedDataSet(source.source_id, [])))
    return registry


class SqlAlchemyDataCollectionStore:
    def __init__(self, engine: Engine) -> None:
        self.engine = engine
        self.tables = Base.metadata.tables

    def latest_dataset(
        self,
        *,
        data_domain: str,
        symbol_or_scope: str,
        required_usage: str,
    ) -> NormalizedDataSet | None:
        request_table = self.tables["data_request"]
        lineage_table = self.tables["data_lineage"]
        statement = (
            select(
                lineage_table.c.lineage_id,
                lineage_table.c.source_id,
                lineage_table.c.payload,
            )
            .select_from(lineage_table.join(request_table, lineage_table.c.request_id == request_table.c.request_id))
            .where(request_table.c.data_domain == data_domain)
            .where(request_table.c.symbol_or_scope == symbol_or_scope)
            .where(request_table.c.required_usage == required_usage)
            .order_by(lineage_table.c.created_at.desc())
            .limit(1)
        )
        with self.engine.connect() as connection:
            row = connection.execute(statement).mappings().first()
        if row is None:
            return None
        payload = dict(row["payload"] or {})
        records = list(payload.get("records") or [])
        if not records:
            return None
        metadata = dict(payload.get("metadata") or {})
        metadata["cache_source_lineage_id"] = row["lineage_id"]
        metadata["cache_source_id"] = row["source_id"]
        return NormalizedDataSet(str(row["source_id"]), records, metadata)

    def persist_result(self, request: DataRequest, result: DataCollectionResult) -> dict[str, object]:
        now = _as_datetime(utc_now())
        report_id = f"quality-{request.request_id}"
        lineage_id = result.report.lineage_refs[0] if result.report.lineage_refs else f"lineage-{request.request_id}"
        with self.engine.begin() as connection:
            connection.execute(self.tables["data_lineage"].delete().where(self.tables["data_lineage"].c.request_id == request.request_id))
            connection.execute(
                self.tables["data_quality_report"].delete().where(self.tables["data_quality_report"].c.request_id == request.request_id)
            )
            connection.execute(self.tables["data_request"].delete().where(self.tables["data_request"].c.request_id == request.request_id))
            connection.execute(
                self.tables["data_request"].insert(),
                [
                    {
                        "request_id": request.request_id,
                        "trace_id": request.trace_id,
                        "data_domain": request.data_domain,
                        "symbol_or_scope": request.symbol_or_scope,
                        "time_range": {"value": request.time_range} if request.time_range else None,
                        "required_usage": request.required_usage,
                        "freshness_requirement": request.freshness_requirement,
                        "required_fields": [asdict(field) for field in request.required_fields],
                        "requesting_stage": request.requesting_stage,
                        "requesting_agent_or_service": request.requesting_agent_or_service,
                        "created_at": now,
                    }
                ],
            )
            connection.execute(
                self.tables["data_quality_report"].insert(),
                [
                    {
                        "report_id": report_id,
                        "request_id": request.request_id,
                        "quality_score": result.report.quality_score,
                        "quality_band": result.report.quality_band,
                        "critical_field_results": result.report.critical_field_results,
                        "decision_core_status": result.report.decision_core_status,
                        "execution_core_status": result.report.execution_core_status,
                        "created_at": now,
                    }
                ],
            )
            if result.data is not None:
                source_id = result.selected_source_id or result.data.source_id
                connection.execute(
                    self.tables["data_lineage"].insert(),
                    [
                        {
                            "lineage_id": lineage_id,
                            "request_id": request.request_id,
                            "source_id": source_id,
                            "source_ref": f"{source_id}:{request.request_id}",
                            "payload": {
                                "records": result.data.records,
                                "metadata": result.data.metadata,
                                "from_cache": result.from_cache,
                                "quality_report_id": report_id,
                            },
                            "created_at": now,
                        }
                    ],
                )
        return {
            "completion_level": "db_persistent",
            "request_id": request.request_id,
            "report_id": report_id,
            "lineage_id": lineage_id if result.data is not None else None,
        }
