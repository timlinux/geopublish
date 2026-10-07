# SPDX-FileCopyrightText: 2026 Kartoza
# SPDX-License-Identifier: MIT
import os
from dataclasses import dataclass
from pathlib import Path

from dotenv import load_dotenv


@dataclass(frozen=True)
class PgConfig:
    host: str
    port: str
    dbname: str
    user: str
    password: str
    sslmode: str

    def conninfo(self) -> str:
        parts = [
            f"host={self.host}",
            f"port={self.port}",
            f"dbname={self.dbname}",
            f"user={self.user}",
            f"sslmode={self.sslmode}",
        ]
        if self.password:
            parts.append(f"password={self.password}")
        return " ".join(parts)


REQUIRED_VARS = ("PGHOST", "PGPORT", "PGDATABASE", "PGUSER")


def load_config(env_file: Path | None = None) -> PgConfig:
    load_dotenv(env_file)
    missing = [name for name in REQUIRED_VARS if not os.environ.get(name)]
    if missing:
        raise RuntimeError(
            f"Missing required environment variable(s): {', '.join(missing)}. "
            "Copy .env.example to .env and fill in your PostgreSQL connection details."
        )
    return PgConfig(
        host=os.environ["PGHOST"],
        port=os.environ["PGPORT"],
        dbname=os.environ["PGDATABASE"],
        user=os.environ["PGUSER"],
        password=os.environ.get("PGPASSWORD", ""),
        sslmode=os.environ.get("PGSSLMODE", "prefer"),
    )
