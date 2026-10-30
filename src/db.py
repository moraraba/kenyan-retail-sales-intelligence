"""
Tiny PostgreSQL helper that shells out to `psql`, so the project needs no extra Python driver.

Connection comes from the standard libpq environment variables:
    PGHOST (default /tmp socket or localhost), PGPORT, PGUSER (default postgres),
    PGDATABASE (default mavuno), PGPASSWORD
If you prefer SQLAlchemy/psycopg2, `query()` is the only function you need to swap.
"""
import io
import os
import subprocess

import pandas as pd

DB = os.environ.get("PGDATABASE", "mavuno")


def _env():
    env = os.environ.copy()
    env.setdefault("PGUSER", "postgres")
    env.setdefault("PGOPTIONS", "-c client_min_messages=warning")
    env.setdefault("PGHOST", "/tmp" if os.path.exists("/tmp/.s.PGSQL.5432") else "localhost")
    return env


def run_file(path, db=DB, extra=None):
    cmd = ["psql", "-v", "ON_ERROR_STOP=1", "-q", "-d", db, "-f", str(path)] + (extra or [])
    subprocess.run(cmd, check=True, env=_env())


def execute(sql, db=DB):
    subprocess.run(["psql", "-v", "ON_ERROR_STOP=1", "-q", "-d", db, "-c", sql], check=True, env=_env())


def query(sql, db=DB):
    """Run a SELECT and return a DataFrame."""
    out = subprocess.run(["psql", "-v", "ON_ERROR_STOP=1", "-d", db, "--csv", "-c", sql],
                         check=True, env=_env(), capture_output=True, text=True)
    return pd.read_csv(io.StringIO(out.stdout)) if out.stdout.strip() else pd.DataFrame()


def ensure_database(db=DB):
    exists = subprocess.run(["psql", "-d", "postgres", "-tAc", f"SELECT 1 FROM pg_database WHERE datname='{db}'"],
                            env=_env(), capture_output=True, text=True).stdout.strip()
    if exists != "1":
        subprocess.run(["createdb", db], check=True, env=_env())


def load_named_queries(path):
    """Split a .sql file into {name: sql} using '-- name: <id>' markers."""
    blocks, name, buf = {}, None, []
    for line in open(path, encoding="utf-8"):
        if line.startswith("-- name:"):
            if name:
                blocks[name] = "".join(buf).strip()
            name, buf = line.split(":", 1)[1].strip(), []
        elif name:
            buf.append(line)
    if name:
        blocks[name] = "".join(buf).strip()
    return blocks
