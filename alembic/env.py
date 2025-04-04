from logging.config import fileConfig

from sqlalchemy import engine_from_config, pool

from accounts.models import *
from alembic import context
from auth.models import *
from categories.models import *
from chats.models import *
from core.database import BaseModel
from core.environment import env
from listings.models import *
from localization.models import *
from locations.models import *
from notifications.models import *
from promotions.models import *
from ratings.models import *
from recommendations.models import *
from stats.models import *
from users.models import *

config = context.config
DATABASE_URL = f"{env.DATABASE_DIALECT}+psycopg2://{env.POSTGRES_USER}:{env.POSTGRES_PASSWORD}@{env.POSTGRES_HOSTNAME}:{env.POSTGRES_PORT}/{env.POSTGRES_DB}"
config.set_main_option("sqlalchemy.url", DATABASE_URL)
target_metadata = BaseModel.metadata


def run_migrations_offline():
    """Run migrations in 'offline' mode.

    This configures the context with just a URL
    and not an Engine, though an Engine is acceptable
    here as well.  By skipping the Engine creation
    we don't even need a DBAPI to be available.

    Calls to context.execute() here emit the given string to the
    script output.

    """
    url = config.get_main_option("sqlalchemy.url")
    context.configure(
        url=url,
        target_metadata=target_metadata,
        literal_binds=True,
        dialect_opts={"paramstyle": "named"},
    )

    with context.begin_transaction():
        context.run_migrations()


def run_migrations_online():
    """Run migrations in 'online' mode.

    In this scenario we need to create an Engine
    and associate a connection with the context.

    """
    connectable = engine_from_config(
        config.get_section(config.config_ini_section),
        prefix="sqlalchemy.",
        poolclass=pool.NullPool,
    )

    with connectable.connect() as connection:
        context.configure(connection=connection, target_metadata=target_metadata)

        with context.begin_transaction():
            context.run_migrations()


if context.is_offline_mode():
    run_migrations_offline()
else:
    run_migrations_online()
