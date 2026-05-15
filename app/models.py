from datetime import datetime, timezone

from sqlmodel import Field, SQLModel


class Link(SQLModel, table=True):
    id: int | None = Field(default=None, primary_key=True)
    code: str = Field(index=True, unique=True)
    url_original: str
    criado_em: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    cliques: int = Field(default=0)
