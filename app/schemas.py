from datetime import datetime

from pydantic import BaseModel, HttpUrl


class LinkCriar(BaseModel):
    url: HttpUrl


class LinkResposta(BaseModel):
    code: str
    url_original: str
    url_curta: str
    criado_em: datetime
    cliques: int
