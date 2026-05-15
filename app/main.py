import os
from contextlib import asynccontextmanager

from fastapi import Depends, FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import RedirectResponse
from sqlmodel import Session, select

from app.codigo import gerar_codigo
from app.database import criar_banco, get_session
from app.models import Link
from app.schemas import LinkCriar, LinkResposta

BASE_URL = os.environ.get("BASE_URL", "http://localhost:8000")


@asynccontextmanager
async def lifespan(app: FastAPI):
    criar_banco()
    yield


app = FastAPI(
    title="Encurtador de URLs",
    description="API simples para encurtar links, redirecionar e acompanhar cliques.",
    version="1.0.0",
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)


def _para_resposta(link: Link) -> LinkResposta:
    return LinkResposta(
        code=link.code,
        url_original=link.url_original,
        url_curta=f"{BASE_URL}/{link.code}",
        criado_em=link.criado_em,
        cliques=link.cliques,
    )


@app.post("/links", response_model=LinkResposta, status_code=201)
def criar_link(dados: LinkCriar, session: Session = Depends(get_session)) -> LinkResposta:
    codigo = gerar_codigo()
    while session.exec(select(Link).where(Link.code == codigo)).first():
        codigo = gerar_codigo()

    link = Link(code=codigo, url_original=str(dados.url))
    session.add(link)
    session.commit()
    session.refresh(link)
    return _para_resposta(link)


@app.get("/links", response_model=list[LinkResposta])
def listar_links(session: Session = Depends(get_session)) -> list[LinkResposta]:
    links = session.exec(select(Link).order_by(Link.criado_em.desc())).all()
    return [_para_resposta(link) for link in links]


@app.get("/links/{code}", response_model=LinkResposta)
def obter_estatisticas(code: str, session: Session = Depends(get_session)) -> LinkResposta:
    link = session.exec(select(Link).where(Link.code == code)).first()
    if not link:
        raise HTTPException(status_code=404, detail="Link não encontrado")
    return _para_resposta(link)


@app.get("/{code}")
def redirecionar(code: str, session: Session = Depends(get_session)) -> RedirectResponse:
    link = session.exec(select(Link).where(Link.code == code)).first()
    if not link:
        raise HTTPException(status_code=404, detail="Link não encontrado")

    link.cliques += 1
    session.add(link)
    session.commit()

    return RedirectResponse(url=link.url_original, status_code=307)
