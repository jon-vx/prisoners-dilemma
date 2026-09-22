import os

from alembic import context

from app.db.connection import create_database_engine
from app.db.models import metadata

config = context.config


def run_migrations(connection):
    context.configure(
        connection=connection, target_metadata=metadata, compare_type=True
    )
    with context.begin_transaction():
        context.run_migrations()


if context.is_offline_mode():
    url = os.environ["DATABASE_URL"]
    context.configure(
        url=url,
        target_metadata=metadata,
        literal_binds=True,
        dialect_opts={"paramstyle": "named"},
    )
    with context.begin_transaction():
        context.run_migrations()
else:
    supplied_connection = config.attributes.get("connection")
    if supplied_connection is not None:
        run_migrations(supplied_connection)
    else:
        engine = create_database_engine(os.environ["DATABASE_URL"])
        try:
            with engine.connect() as connection:
                run_migrations(connection)
        finally:
            engine.dispose()
