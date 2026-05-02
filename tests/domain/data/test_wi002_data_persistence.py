from __future__ import annotations

import contextlib
import socket
import subprocess
import time
from pathlib import Path

import psycopg
from alembic import command
from alembic.config import Config
from sqlalchemy import create_engine, select

from velentrade.db.base import Base
from velentrade.db.seed import apply_wi001_seed
from velentrade.domain.data.persistence import SqlAlchemyDataCollectionStore, build_source_registry_from_db
from velentrade.domain.data.quality import DataRequest, RequiredField
from velentrade.domain.data.sources import DataCollectionService


def _find_free_port() -> int:
    with socket.socket() as sock:
        sock.bind(("127.0.0.1", 0))
        return int(sock.getsockname()[1])


@contextlib.contextmanager
def _postgres_container():
    port = _find_free_port()
    name = f"velentrade-data-pg-{port}"
    subprocess.run(
        [
            "docker",
            "run",
            "--rm",
            "-d",
            "--name",
            name,
            "-e",
            "POSTGRES_USER=velentrade",
            "-e",
            "POSTGRES_PASSWORD=velentrade",
            "-e",
            "POSTGRES_DB=velentrade",
            "-p",
            f"127.0.0.1:{port}:5432",
            "postgres:16-alpine",
        ],
        check=True,
        capture_output=True,
        text=True,
    )
    try:
        url = f"postgresql+psycopg://velentrade:velentrade@127.0.0.1:{port}/velentrade"
        deadline = time.time() + 40
        while time.time() < deadline:
            try:
                with psycopg.connect(
                    f"host=127.0.0.1 port={port} dbname=velentrade user=velentrade password=velentrade"
                ) as connection:
                    with connection.cursor() as cursor:
                        cursor.execute("select 1")
                        cursor.fetchone()
                    break
            except psycopg.Error:
                time.sleep(1)
        else:
            raise RuntimeError("PostgreSQL container did not become ready in time.")
        yield url
    finally:
        subprocess.run(["docker", "rm", "-f", name], check=False, capture_output=True, text=True)


def _decision_request() -> DataRequest:
    return DataRequest(
        request_id="quote-persist-1",
        trace_id="trace-quote-persist-1",
        data_domain="a_share_market",
        symbol_or_scope="600000.SH",
        required_usage="decision_core",
        freshness_requirement="same_trading_day",
        required_fields=[
            RequiredField("symbol", present=True, valid=True, critical=True),
            RequiredField("trade_date", present=True, valid=True, critical=True),
            RequiredField("close", present=True, valid=True, critical=True),
            RequiredField("volume", present=True, valid=True),
            RequiredField("source_timestamp", present=True, valid=True),
        ],
        requesting_stage="S1",
        requesting_agent_or_service="data_service",
    )


def test_public_data_collection_persists_request_lineage_and_quality_report_to_postgres():
    with _postgres_container() as database_url:
        config = Config(str(Path("alembic.ini")))
        config.set_main_option("sqlalchemy.url", database_url)
        command.upgrade(config, "head")

        engine = create_engine(database_url, future=True)
        apply_wi001_seed(engine)
        registry = build_source_registry_from_db(
            engine,
            fetch_text=lambda _url: (
                '{"code":0,"msg":"","data":{"sh600000":{"qfqday":['
                '["2026-04-17","9.970","9.860","10.000","9.850","579330.000"]'
                ']}}}'
            ),
        )
        request = _decision_request()
        result = DataCollectionService(registry).collect(request, require_real=True)

        persisted = SqlAlchemyDataCollectionStore(engine).persist_result(request, result)

        tables = Base.metadata.tables
        with engine.connect() as connection:
            source_row = connection.execute(
                select(tables["data_source_registry"]).where(tables["data_source_registry"].c.source_id == "tencent-public-kline")
            ).mappings().one()
            request_row = connection.execute(
                select(tables["data_request"]).where(tables["data_request"].c.request_id == request.request_id)
            ).mappings().one()
            report_row = connection.execute(
                select(tables["data_quality_report"]).where(tables["data_quality_report"].c.request_id == request.request_id)
            ).mappings().one()
            lineage_row = connection.execute(
                select(tables["data_lineage"]).where(tables["data_lineage"].c.request_id == request.request_id)
            ).mappings().one()

        assert source_row["adapter_kind"] == "public_http_json_kline_daily_quote"
        assert source_row["payload"]["symbol_mapper"] == "tencent_market_symbol"
        assert request_row["data_domain"] == "a_share_market"
        assert report_row["quality_band"] == "normal"
        assert report_row["decision_core_status"] == "pass"
        assert lineage_row["source_id"] == "tencent-public-kline"
        assert lineage_row["payload"]["records"][0]["symbol"] == "600000.SH"
        assert persisted["completion_level"] == "db_persistent"
