from sqlalchemy import create_engine
from sqlalchemy.engine import Engine, make_url


def create_database_engine(database_url: str) -> Engine:
    url = make_url(database_url)
    if url.drivername in {"postgres", "postgresql"}:
        url = url.set(drivername="postgresql+psycopg")
    if url.drivername != "postgresql+psycopg":
        raise ValueError("DATABASE_URL must use PostgreSQL (postgresql+psycopg://)")
    return create_engine(url, pool_pre_ping=True, connect_args={"connect_timeout": 5})
