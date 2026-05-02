from __future__ import annotations

import contextlib
import socket
import subprocess
import time
from pathlib import Path

import psycopg
from alembic import command
from alembic.config import Config
from sqlalchemy import create_engine, text

from velentrade.db.seed import apply_wi001_seed


def _find_free_port() -> int:
    with socket.socket() as sock:
        sock.bind(("127.0.0.1", 0))
        return int(sock.getsockname()[1])


@contextlib.contextmanager
def _postgres_container():
    port = _find_free_port()
    name = f"velentrade-wi001-{port}"
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


def test_postgres_migration_and_seed_smoke():
    with _postgres_container() as database_url:
        config = Config(str(Path("alembic.ini")))
        config.set_main_option("sqlalchemy.url", database_url)
        command.upgrade(config, "head")

        engine = create_engine(database_url, future=True)
        apply_wi001_seed(engine)

        with engine.connect() as connection:
            tables = {
                row[0]
                for row in connection.execute(
                    text(
                        "select table_name from information_schema.tables "
                        "where table_schema = 'public' and table_name in "
                        "('artifact','memory_item','context_snapshot','model_profile','tool_profile','skill_package','skill_package_version')"
                    )
                )
            }
            assert {
                "artifact",
                "memory_item",
                "context_snapshot",
                "model_profile",
                "tool_profile",
                "skill_package",
                "skill_package_version",
            }.issubset(tables)

            context_snapshot_count = connection.execute(text("select count(*) from context_snapshot")).scalar_one()
            model_profile_count = connection.execute(text("select count(*) from model_profile")).scalar_one()
            tool_profile_count = connection.execute(text("select count(*) from tool_profile")).scalar_one()
            skill_package_count = connection.execute(text("select count(*) from skill_package")).scalar_one()

        assert context_snapshot_count == 1
        assert model_profile_count == 1
        assert tool_profile_count == 1
        assert skill_package_count >= 1
