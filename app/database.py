import os
from collections.abc import Generator

from sqlalchemy import text
from sqlmodel import Session, SQLModel, create_engine

DATABASE_URL = os.environ.get("DATABASE_URL", "sqlite:///./encurtador.db")

# Provedores costumam entregar "postgres://..."; o SQLAlchemy precisa do driver explícito.
for prefixo in ("postgres://", "postgresql://"):
    if DATABASE_URL.startswith(prefixo):
        DATABASE_URL = "postgresql+psycopg://" + DATABASE_URL[len(prefixo):]
        break

# Schema próprio num Postgres compartilhado com outros projetos (opcional).
DB_SCHEMA = os.environ.get("DB_SCHEMA")

if DATABASE_URL.startswith("sqlite"):
    connect_args = {"check_same_thread": False}
elif DB_SCHEMA:
    connect_args = {"options": f"-csearch_path={DB_SCHEMA}"}
else:
    connect_args = {}

engine = create_engine(DATABASE_URL, connect_args=connect_args, pool_pre_ping=True)


def criar_banco() -> None:
    if DB_SCHEMA and not DATABASE_URL.startswith("sqlite"):
        with engine.begin() as conn:
            conn.execute(text(f'CREATE SCHEMA IF NOT EXISTS "{DB_SCHEMA}"'))
    SQLModel.metadata.create_all(engine)


def get_session() -> Generator[Session, None, None]:
    with Session(engine) as session:
        yield session
