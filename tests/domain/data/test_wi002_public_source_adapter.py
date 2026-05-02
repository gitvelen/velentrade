from __future__ import annotations

import pytest

from velentrade.domain.data.quality import DataRequest, RequiredField
from velentrade.domain.data.sources import (
    DataCollectionService,
    DataSourceDefinition,
    DataSourceRegistry,
    PublicHttpJsonKlineDailyQuoteAdapter,
    NormalizedDataSet,
    PublicHttpCsvDailyQuoteAdapter,
    SourceFetchError,
    StaticDataSourceAdapter,
    eastmoney_secid_mapper,
    tencent_market_symbol_mapper,
)


def _decision_request(required_fields: list[RequiredField] | None = None) -> DataRequest:
    return DataRequest(
        request_id="quote-req-1",
        trace_id="trace-quote-1",
        data_domain="a_share_market",
        symbol_or_scope="600000.SH",
        required_usage="decision_core",
        freshness_requirement="same_trading_day",
        required_fields=required_fields
        or [
            RequiredField("symbol", present=True, valid=True, critical=True),
            RequiredField("trade_date", present=True, valid=True, critical=True),
            RequiredField("close", present=True, valid=True, critical=True),
            RequiredField("volume", present=True, valid=True),
            RequiredField("source_timestamp", present=True, valid=True),
        ],
        requesting_stage="S1",
        requesting_agent_or_service="data_service",
    )


def _public_source(source_id: str = "public-http-daily") -> DataSourceDefinition:
    return DataSourceDefinition(
        source_id=source_id,
        data_domain="a_share_market",
        allowed_usage=("research", "decision_core"),
        priority="T1",
        status="active",
        license_summary="public HTTP CSV; review provider terms before production use",
        rate_limit={"requests_per_minute": 30},
        adapter_kind="public_http_csv_daily_quote",
        endpoint_template="https://quotes.example/{symbol}.csv",
        cache_ttl_seconds=86400,
    )


def _eastmoney_source(source_id: str = "eastmoney-public-kline") -> DataSourceDefinition:
    return DataSourceDefinition(
        source_id=source_id,
        data_domain="a_share_market",
        allowed_usage=("research", "decision_core"),
        priority="T2",
        status="active",
        license_summary="Eastmoney public quote endpoint; no API key; review provider terms and rate limits before production use",
        rate_limit={"requests_per_minute": 20},
        adapter_kind="public_http_json_kline_daily_quote",
        endpoint_template=(
            "https://push2his.eastmoney.com/api/qt/stock/kline/get?"
            "secid={symbol}&fields1=f1,f2,f3&fields2=f51,f52,f53,f54,f55,f56,f57"
            "&klt=101&fqt=1&beg=19900101&end=20500101"
        ),
        cache_ttl_seconds=86400,
    )


def test_public_http_csv_adapter_fetches_and_normalizes_quote_with_metadata():
    fetched_urls: list[str] = []

    def fetch_text(url: str) -> str:
        fetched_urls.append(url)
        return (
            "Date,Open,High,Low,Close,Volume\n"
            "2026-04-30,10.10,10.50,10.00,10.35,123456\n"
        )

    source = _public_source()
    adapter = PublicHttpCsvDailyQuoteAdapter(source, fetch_text=fetch_text)

    data = adapter.fetch(_decision_request())

    assert fetched_urls == ["https://quotes.example/600000.SH.csv"]
    assert source.adapter_kind == "public_http_csv_daily_quote"
    assert source.license_summary.startswith("public HTTP CSV")
    assert source.rate_limit["requests_per_minute"] == 30
    assert data.source_id == "public-http-daily"
    assert data.records == [
        {
            "symbol": "600000.SH",
            "trade_date": "2026-04-30",
            "open": 10.10,
            "high": 10.50,
            "low": 10.00,
            "close": 10.35,
            "volume": 123456,
            "source_timestamp": "2026-04-30",
            "source_id": "public-http-daily",
        }
    ]


def test_public_http_json_kline_adapter_fetches_and_normalizes_eastmoney_quote():
    fetched_urls: list[str] = []

    def fetch_text(url: str) -> str:
        fetched_urls.append(url)
        return (
            '{"rc":0,"data":{"code":"600000","market":1,"name":"浦发银行",'
            '"klines":["2026-04-01,10.20,10.24,10.37,10.18,574165,590411590.00"]}}'
        )

    source = _eastmoney_source()
    adapter = PublicHttpJsonKlineDailyQuoteAdapter(
        source,
        fetch_text=fetch_text,
        symbol_mapper=eastmoney_secid_mapper,
    )

    data = adapter.fetch(_decision_request())

    assert fetched_urls == [source.endpoint_template.format(symbol="1.600000")]
    assert data.source_id == "eastmoney-public-kline"
    assert data.metadata["adapter_kind"] == "public_http_json_kline_daily_quote"
    assert data.metadata["provider_name"] == "浦发银行"
    assert data.records == [
        {
            "symbol": "600000.SH",
            "trade_date": "2026-04-01",
            "open": 10.20,
            "high": 10.37,
            "low": 10.18,
            "close": 10.24,
            "volume": 574165,
            "amount": 590411590.0,
            "source_timestamp": "2026-04-01",
            "source_id": "eastmoney-public-kline",
        }
    ]


def test_public_http_json_kline_adapter_fetches_and_normalizes_tencent_quote():
    fetched_urls: list[str] = []

    def fetch_text(url: str) -> str:
        fetched_urls.append(url)
        return (
            '{"code":0,"msg":"","data":{"sh600000":{"qfqday":['
            '["2026-04-17","9.970","9.860","10.000","9.850","579330.000"]'
            ']}}}'
        )

    source = DataSourceDefinition(
        source_id="tencent-public-kline",
        data_domain="a_share_market",
        allowed_usage=("research", "decision_core"),
        priority="T2",
        status="active",
        license_summary="Tencent public quote endpoint; no API key; review provider terms and rate limits before production use",
        rate_limit={"requests_per_minute": 20},
        adapter_kind="public_http_json_kline_daily_quote",
        endpoint_template="https://web.ifzq.gtimg.cn/appstock/app/fqkline/get?param={symbol},day,,,10,qfq",
        cache_ttl_seconds=86400,
    )
    adapter = PublicHttpJsonKlineDailyQuoteAdapter(
        source,
        fetch_text=fetch_text,
        symbol_mapper=tencent_market_symbol_mapper,
    )

    data = adapter.fetch(_decision_request())

    assert fetched_urls == [source.endpoint_template.format(symbol="sh600000")]
    assert data.source_id == "tencent-public-kline"
    assert data.metadata["adapter_kind"] == "public_http_json_kline_daily_quote"
    assert data.metadata["provider_code"] == "sh600000"
    assert data.records == [
        {
            "symbol": "600000.SH",
            "trade_date": "2026-04-17",
            "open": 9.970,
            "high": 10.000,
            "low": 9.850,
            "close": 9.860,
            "volume": 579330,
            "source_timestamp": "2026-04-17",
            "source_id": "tencent-public-kline",
        }
    ]


def test_eastmoney_symbol_mapper_requires_a_share_exchange_suffix():
    assert eastmoney_secid_mapper("600000.SH") == "1.600000"
    assert eastmoney_secid_mapper("000001.SZ") == "0.000001"
    with pytest.raises(SourceFetchError):
        eastmoney_secid_mapper("AAPL.US")


def test_tencent_symbol_mapper_requires_a_share_exchange_suffix():
    assert tencent_market_symbol_mapper("600000.SH") == "sh600000"
    assert tencent_market_symbol_mapper("000001.SZ") == "sz000001"
    with pytest.raises(SourceFetchError):
        tencent_market_symbol_mapper("AAPL.US")


def test_registry_requires_real_source_and_skips_fixture_only_sources():
    registry = DataSourceRegistry()
    fixture_source = DataSourceDefinition(
        source_id="fixture-only",
        data_domain="a_share_market",
        allowed_usage=("decision_core",),
        priority="T4",
        status="fixture_only",
        license_summary="fixture only",
        rate_limit={"requests_per_minute": 0},
        adapter_kind="fixture_contract",
    )
    registry.register(fixture_source, StaticDataSourceAdapter(NormalizedDataSet("fixture-only", [])))
    registry.register(_public_source(), PublicHttpCsvDailyQuoteAdapter(_public_source(), fetch_text=lambda _: ""))

    eligible = registry.eligible_sources("a_share_market", "decision_core", require_real=True)

    assert [source.source_id for source, _adapter in eligible] == ["public-http-daily"]


def test_collection_uses_fallback_source_and_blocks_execution_core_cache():
    primary = _public_source("primary-public")
    backup = _public_source("backup-public")
    registry = DataSourceRegistry()
    registry.register(
        primary,
        PublicHttpCsvDailyQuoteAdapter(
            primary,
            fetch_text=lambda _url: (_ for _ in ()).throw(SourceFetchError("primary unavailable")),
        ),
    )
    registry.register(
        backup,
        PublicHttpCsvDailyQuoteAdapter(
            backup,
            fetch_text=lambda _url: "Date,Open,High,Low,Close,Volume\n2026-04-30,10,11,9,10.8,200\n",
        ),
    )
    service = DataCollectionService(registry)

    decision_result = service.collect(_decision_request(), require_real=True)

    assert decision_result.selected_source_id == "backup-public"
    assert decision_result.report.fallback_attempts == ["primary-public", "backup-public"]
    assert decision_result.report.quality_band == "normal"
    assert decision_result.report.decision_core_status == "pass"

    execution_request = DataRequest(
        request_id="exec-cache-1",
        trace_id="trace-exec-cache-1",
        data_domain="a_share_market",
        symbol_or_scope="600000.SH",
        required_usage="execution_core",
        freshness_requirement="realtime",
        required_fields=[
            RequiredField("last_price", present=True, valid=True, critical=True),
            RequiredField("source_timestamp", present=True, valid=True, critical=True),
        ],
        requesting_stage="S6",
        requesting_agent_or_service="execution_service",
    )
    service.cache_result(execution_request, NormalizedDataSet("cache-snapshot", [{"last_price": 10.8}]))

    execution_result = service.collect(execution_request, require_real=True, allow_cache=True)

    assert execution_result.from_cache is True
    assert execution_result.report.execution_core_status == "blocked"
    assert execution_result.report.cache_usage["may_create_execution_authorization"] is False


def test_collection_blocks_when_critical_fields_are_missing():
    source = _public_source()
    registry = DataSourceRegistry()
    registry.register(
        source,
        PublicHttpCsvDailyQuoteAdapter(
            source,
            fetch_text=lambda _url: "Date,Open,High,Low,Close\n2026-04-30,10,11,9,10.8\n",
        ),
    )
    service = DataCollectionService(registry)
    request = _decision_request(
        [
            RequiredField("close", present=True, valid=True, critical=True),
            RequiredField("volume", present=True, valid=True, critical=True),
        ]
    )

    result = service.collect(request, require_real=True)

    assert result.report.quality_band == "blocked"
    assert result.report.reason_code == "critical_field_blocked"
    assert result.report.critical_field_results == {"close": True, "volume": False}
