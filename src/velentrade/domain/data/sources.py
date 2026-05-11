from __future__ import annotations

import csv
import json
from dataclasses import dataclass, field
from io import StringIO
from typing import Callable, Protocol
from urllib.request import Request, urlopen

from velentrade.domain.data.quality import DataQualityReport, DataQualityService, DataRequest, RequiredField


class SourceFetchError(RuntimeError):
    pass


@dataclass(frozen=True)
class DataSourceDefinition:
    source_id: str
    data_domain: str
    allowed_usage: tuple[str, ...]
    priority: str
    status: str
    license_summary: str
    rate_limit: dict[str, int]
    adapter_kind: str
    endpoint_template: str | None = None
    cache_ttl_seconds: int = 0
    fallback_order: tuple[str, ...] = field(default_factory=tuple)
    payload: dict[str, object] = field(default_factory=dict)

    def can_serve(self, data_domain: str, required_usage: str) -> bool:
        return self.status == "active" and self.data_domain == data_domain and required_usage in self.allowed_usage

    def is_real_source(self) -> bool:
        return self.adapter_kind != "fixture_contract" and self.status != "fixture_only"


@dataclass(frozen=True)
class NormalizedDataSet:
    source_id: str
    records: list[dict[str, object]]
    metadata: dict[str, object] = field(default_factory=dict)


@dataclass(frozen=True)
class DataCollectionResult:
    selected_source_id: str | None
    data: NormalizedDataSet | None
    report: DataQualityReport
    from_cache: bool = False


class DataSourceAdapter(Protocol):
    def fetch(self, request: DataRequest) -> NormalizedDataSet:
        ...


class PublicHttpCsvDailyQuoteAdapter:
    def __init__(
        self,
        source: DataSourceDefinition,
        fetch_text: Callable[[str], str] | None = None,
        symbol_mapper: Callable[[str], str] | None = None,
    ) -> None:
        self.source = source
        self._fetch_text = fetch_text or self._urllib_fetch_text
        self._symbol_mapper = symbol_mapper or (lambda symbol: symbol)

    def fetch(self, request: DataRequest) -> NormalizedDataSet:
        if not self.source.endpoint_template:
            raise SourceFetchError(f"source {self.source.source_id} has no endpoint_template")
        url = self.source.endpoint_template.format(symbol=self._symbol_mapper(request.symbol_or_scope))
        text = self._fetch_text(url)
        records = self._parse_csv(text, request.symbol_or_scope)
        if not records:
            raise SourceFetchError(f"source {self.source.source_id} returned no quote rows")
        return NormalizedDataSet(
            source_id=self.source.source_id,
            records=records,
            metadata={
                "adapter_kind": self.source.adapter_kind,
                "license_summary": self.source.license_summary,
                "rate_limit": self.source.rate_limit,
            },
        )

    def _urllib_fetch_text(self, url: str) -> str:
        try:
            http_request = Request(url, headers={"User-Agent": "velentrade-data-service/0.1"})
            with urlopen(http_request, timeout=10) as response:  # noqa: S310 - URL is controlled by Source Registry.
                return response.read().decode("utf-8")
        except Exception as exc:  # pragma: no cover - deterministic tests inject fetch_text.
            raise SourceFetchError(str(exc)) from exc

    def _parse_csv(self, text: str, symbol: str) -> list[dict[str, object]]:
        try:
            reader = csv.DictReader(StringIO(text))
            rows = list(reader)
        except csv.Error as exc:
            raise SourceFetchError(str(exc)) from exc

        records: list[dict[str, object]] = []
        for row in rows:
            normalized = {key.strip().lower(): value.strip() for key, value in row.items() if key is not None and value is not None}
            date = normalized.get("date") or normalized.get("trade_date")
            record: dict[str, object] = {
                "symbol": symbol,
                "source_id": self.source.source_id,
            }
            if date:
                record["trade_date"] = date
                record["source_timestamp"] = date
            for field_name in ("open", "high", "low", "close"):
                if normalized.get(field_name) not in (None, ""):
                    record[field_name] = float(normalized[field_name])
            if normalized.get("volume") not in (None, ""):
                record["volume"] = int(float(normalized["volume"]))
            records.append(record)
        return records


def eastmoney_secid_mapper(symbol: str) -> str:
    code, separator, exchange = symbol.partition(".")
    if not separator:
        raise SourceFetchError(f"Eastmoney source requires exchange suffix for {symbol}")
    normalized_exchange = exchange.upper()
    if normalized_exchange == "SH":
        return f"1.{code}"
    if normalized_exchange == "SZ":
        return f"0.{code}"
    raise SourceFetchError(f"Eastmoney source does not support exchange {exchange}")


def tencent_market_symbol_mapper(symbol: str) -> str:
    code, separator, exchange = symbol.partition(".")
    if not separator:
        raise SourceFetchError(f"Tencent source requires exchange suffix for {symbol}")
    normalized_exchange = exchange.upper()
    if normalized_exchange == "SH":
        return f"sh{code}"
    if normalized_exchange == "SZ":
        return f"sz{code}"
    raise SourceFetchError(f"Tencent source does not support exchange {exchange}")


class PublicHttpJsonKlineDailyQuoteAdapter(PublicHttpCsvDailyQuoteAdapter):
    def fetch(self, request: DataRequest) -> NormalizedDataSet:
        if not self.source.endpoint_template:
            raise SourceFetchError(f"source {self.source.source_id} has no endpoint_template")
        url = self.source.endpoint_template.format(symbol=self._symbol_mapper(request.symbol_or_scope))
        payload = json.loads(self._fetch_text(url))
        records = self._parse_klines(payload, request.symbol_or_scope)
        if not records:
            raise SourceFetchError(f"source {self.source.source_id} returned no quote rows")
        provider_metadata = self._provider_metadata(payload)
        return NormalizedDataSet(
            source_id=self.source.source_id,
            records=records,
            metadata={
                "adapter_kind": self.source.adapter_kind,
                "license_summary": self.source.license_summary,
                "rate_limit": self.source.rate_limit,
                "provider_name": provider_metadata.get("provider_name"),
                "provider_code": provider_metadata.get("provider_code"),
            },
        )

    def _parse_klines(self, payload: dict[str, object], symbol: str) -> list[dict[str, object]]:
        if "rc" in payload and payload.get("rc") not in (0, "0"):
            raise SourceFetchError(f"source {self.source.source_id} returned rc={payload.get('rc')}")
        if "code" in payload and payload.get("code") not in (0, "0"):
            raise SourceFetchError(f"source {self.source.source_id} returned code={payload.get('code')}")
        data = payload.get("data")
        if not isinstance(data, dict):
            raise SourceFetchError(f"source {self.source.source_id} returned no data object")
        klines = data.get("klines")
        if isinstance(klines, list):
            return self._parse_eastmoney_klines(klines, symbol)
        for market_code, market_payload in data.items():
            if isinstance(market_payload, dict):
                tencent_klines = market_payload.get("qfqday") or market_payload.get("day")
                if isinstance(tencent_klines, list):
                    return self._parse_tencent_klines(tencent_klines, symbol)
        raise SourceFetchError(f"source {self.source.source_id} returned no klines")

    def _parse_eastmoney_klines(self, klines: list[object], symbol: str) -> list[dict[str, object]]:
        records: list[dict[str, object]] = []
        for line in klines:
            if not isinstance(line, str):
                continue
            fields = line.split(",")
            if len(fields) < 6:
                continue
            trade_date, open_price, close, high, low, volume = fields[:6]
            record = self._quote_record(symbol, trade_date, open_price, high, low, close, volume)
            if len(fields) >= 7 and fields[6] not in ("", "-"):
                record["amount"] = float(fields[6])
            records.append(record)
        return records

    def _parse_tencent_klines(self, klines: list[object], symbol: str) -> list[dict[str, object]]:
        records: list[dict[str, object]] = []
        for row in klines:
            if not isinstance(row, list) or len(row) < 6:
                continue
            trade_date, open_price, close, high, low, volume = row[:6]
            records.append(self._quote_record(symbol, trade_date, open_price, high, low, close, volume))
        return records

    def _quote_record(
        self,
        symbol: str,
        trade_date: object,
        open_price: object,
        high: object,
        low: object,
        close: object,
        volume: object,
    ) -> dict[str, object]:
        trade_date_value = str(trade_date)
        return {
            "symbol": symbol,
            "trade_date": trade_date_value,
            "open": float(open_price),
            "high": float(high),
            "low": float(low),
            "close": float(close),
            "volume": int(float(volume)),
            "source_timestamp": trade_date_value,
            "source_id": self.source.source_id,
        }

    def _provider_metadata(self, payload: dict[str, object]) -> dict[str, object]:
        data = payload.get("data")
        if not isinstance(data, dict):
            return {}
        if "code" in data or "name" in data:
            return {"provider_code": data.get("code"), "provider_name": data.get("name")}
        for market_code, market_payload in data.items():
            if isinstance(market_payload, dict) and (market_payload.get("qfqday") or market_payload.get("day")):
                return {"provider_code": market_code, "provider_name": market_payload.get("name")}
        return {}


class StaticDataSourceAdapter:
    def __init__(self, data: NormalizedDataSet) -> None:
        self.data = data

    def fetch(self, request: DataRequest) -> NormalizedDataSet:
        return self.data


class DataSourceRegistry:
    _PRIORITY_ORDER = {"T0": 0, "T1": 1, "T2": 2, "T3": 3, "T4": 4}

    def __init__(self) -> None:
        self._sources: dict[str, tuple[DataSourceDefinition, DataSourceAdapter]] = {}

    def register(self, source: DataSourceDefinition, adapter: DataSourceAdapter) -> None:
        self._sources[source.source_id] = (source, adapter)

    def eligible_sources(
        self,
        data_domain: str,
        required_usage: str,
        *,
        require_real: bool = False,
    ) -> list[tuple[DataSourceDefinition, DataSourceAdapter]]:
        eligible = [
            (source, adapter)
            for source, adapter in self._sources.values()
            if source.can_serve(data_domain, required_usage) and (source.is_real_source() or not require_real)
        ]
        return sorted(eligible, key=lambda item: self._PRIORITY_ORDER.get(item[0].priority, 99))


class DataCollectionService:
    _SOURCE_TRUST = {"T0": 1.0, "T1": 0.95, "T2": 0.85, "T3": 0.60, "T4": 0.70}

    def __init__(self, registry: DataSourceRegistry, quality_service: DataQualityService | None = None) -> None:
        self.registry = registry
        self.quality_service = quality_service or DataQualityService()
        self._cache: dict[tuple[str, str, str], NormalizedDataSet] = {}

    def cache_result(self, request: DataRequest, data: NormalizedDataSet) -> None:
        self._cache[self._cache_key(request)] = data

    def collect(
        self,
        request: DataRequest,
        *,
        require_real: bool = False,
        allow_cache: bool = False,
    ) -> DataCollectionResult:
        attempts: list[str] = []
        for source, adapter in self.registry.eligible_sources(
            request.data_domain,
            request.required_usage,
            require_real=require_real,
        ):
            attempts.append(source.source_id)
            try:
                data = adapter.fetch(request)
            except SourceFetchError:
                continue
            report = self._build_report(
                request,
                data,
                source=source,
                attempts=attempts,
                cache_hit=False,
            )
            return DataCollectionResult(source.source_id, data, report)

        cache_key = self._cache_key(request)
        if allow_cache and cache_key in self._cache:
            data = self._cache[cache_key]
            report = self._build_report(
                request,
                data,
                source=None,
                attempts=attempts,
                cache_hit=True,
            )
            return DataCollectionResult(data.source_id, data, report, from_cache=True)

        report = self._build_report(
            request,
            NormalizedDataSet("none", []),
            source=None,
            attempts=attempts,
            cache_hit=False,
        )
        return DataCollectionResult(None, None, report)

    def _build_report(
        self,
        request: DataRequest,
        data: NormalizedDataSet,
        *,
        source: DataSourceDefinition | None,
        attempts: list[str],
        cache_hit: bool,
    ) -> DataQualityReport:
        effective_request = DataRequest(
            request_id=request.request_id,
            trace_id=request.trace_id,
            data_domain=request.data_domain,
            symbol_or_scope=request.symbol_or_scope,
            required_usage=request.required_usage,
            freshness_requirement=request.freshness_requirement,
            required_fields=self._effective_required_fields(request.required_fields, data),
            requesting_stage=request.requesting_stage,
            requesting_agent_or_service=request.requesting_agent_or_service,
            time_range=request.time_range,
        )
        accuracy = 0.7 if cache_hit else self._SOURCE_TRUST.get(source.priority, 0.6) if source else 0.0
        timeliness = 0.7 if cache_hit else 1.0 if data.records else 0.0
        return self.quality_service.evaluate(
            effective_request,
            accuracy=accuracy,
            timeliness=timeliness,
            fallback_attempts=attempts,
            cache_hit=cache_hit,
        )

    def _effective_required_fields(
        self,
        required_fields: list[RequiredField],
        data: NormalizedDataSet,
    ) -> list[RequiredField]:
        record = data.records[0] if data.records else {}
        return [
            RequiredField(
                name=field.name,
                present=field.name in record,
                valid=record.get(field.name) not in (None, ""),
                critical=field.critical,
                weight=field.weight,
            )
            for field in required_fields
        ]

    def _cache_key(self, request: DataRequest) -> tuple[str, str, str]:
        return (request.data_domain, request.symbol_or_scope, request.required_usage)
