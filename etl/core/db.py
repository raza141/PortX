from __future__ import annotations

import os
from contextlib import contextmanager
from dataclasses import dataclass
from typing import Any, Iterable, Sequence

from dotenv import load_dotenv
import psycopg  # Python Postgres client library (psycopg3)
from psycopg import Connection  # Type hint for psycopg Connection
from psycopg_pool import ConnectionPool

# Load .env if present (env vars still win if both exist)
load_dotenv(override=False)


@dataclass(frozen=True)
class DBConfig:
    host: str = os.getenv("POSTGRES_HOST", "localhost")
    port: int = int(os.getenv("POSTGRES_PORT", "5432"))
    db: str = os.getenv("POSTGRES_DB", "PortX")
    user: str = os.getenv("POSTGRES_USER", "postgres")
    password: str = os.getenv("POSTGRES_PASSWORD", "5090")
    sslmode: str = os.getenv(
        "POSTGRES_SSLMODE", "disable"
    )  # disable/require/verify-full
    schema: str = os.getenv("POSTGRES_SCHEMA", "public")
    pool_min: int = int(os.getenv("POSTGRES_POOL_MIN", "1"))
    pool_max: int = int(os.getenv("POSTGRES_POOL_MAX", "5"))

    def dsn(self) -> str:
        return (
            f"postgresql://{self.user}:{self.password}"
            f"@{self.host}:{self.port}/{self.db}"
            f"?sslmode={self.sslmode}"
        )


@contextmanager
def connection(cfg: DBConfig) -> Connection:
    conn: Connection | None = None
    try:
        conn = psycopg.connect(
            host=cfg.host,
            port=cfg.port,
            dbname=cfg.db,
            user=cfg.user,
            password=cfg.password,
            sslmode=cfg.sslmode,
        )
        with conn.cursor() as cur:
            cur.execute(f"set search_path to {cfg.schema}, public;")
        yield conn
    finally:
        if conn is not None:
            conn.close()


@contextmanager
def pool(cfg: DBConfig) -> ConnectionPool:
    pool_obj = ConnectionPool(
        cfg.dsn(),
        min_size=cfg.pool_min,
        max_size=cfg.pool_max,
        kwargs={"autocommit": False},
        open=True,
    )
    try:
        yield pool_obj
    finally:
        pool_obj.close()
        pool_obj.wait_closed()


class PortXDB:
    """Simple Postgres client with a connection pool and helper methods."""

    def __init__(self, cfg: DBConfig | None = None) -> None:
        self.cfg = cfg or DBConfig()
        self.pool = ConnectionPool(
            self.cfg.dsn(),
            min_size=self.cfg.pool_min,
            max_size=self.cfg.pool_max,
            kwargs={"autocommit": False},
            open=True,
        )

    @contextmanager
    def connect(self) -> Connection:
        with self.pool.connection() as conn:
            with conn.cursor() as cur:
                cur.execute(f"set search_path to {self.cfg.schema}, public;")
            yield conn

    def execute(self, sql: str, params: Sequence[Any] | None = None) -> int:
        with self.connect() as conn, conn.cursor() as cur:
            cur.execute(sql, params or ())
            conn.commit()
            return cur.rowcount

    def executemany(self, sql: str, seq_of_params: Iterable[Sequence[Any]]) -> int:
        with self.connect() as conn, conn.cursor() as cur:
            cur.executemany(sql, seq_of_params)
            conn.commit()
            return cur.rowcount

    def fetch_one(self, sql: str, params: Sequence[Any] | None = None) -> Any:
        with self.connect() as conn, conn.cursor() as cur:
            cur.execute(sql, params or ())
            return cur.fetchone()

    def fetch_all(self, sql: str, params: Sequence[Any] | None = None) -> list[tuple]:
        with self.connect() as conn, conn.cursor() as cur:
            cur.execute(sql, params or ())
            return cur.fetchall()

    def ping(self) -> tuple[Any, ...]:
        return self.fetch_one(
            "select current_database(), current_user, inet_server_addr(), inet_server_port();"
        )

    def close(self) -> None:
        self.pool.close()
        self.pool.wait_closed()


if __name__ == "__main__":
    db = PortXDB()
    print("Ping:", db.ping())
