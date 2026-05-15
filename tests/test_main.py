import pytest
from fastapi.testclient import TestClient
from sqlmodel import Session, SQLModel, create_engine
from sqlmodel.pool import StaticPool

from app.database import get_session
from app.main import app


@pytest.fixture(name="session")
def session_fixture():
    engine = create_engine(
        "sqlite://", connect_args={"check_same_thread": False}, poolclass=StaticPool
    )
    SQLModel.metadata.create_all(engine)
    with Session(engine) as session:
        yield session


@pytest.fixture(name="client")
def client_fixture(session: Session):
    def get_session_override():
        return session

    app.dependency_overrides[get_session] = get_session_override
    with TestClient(app) as client:
        yield client
    app.dependency_overrides.clear()


def test_criar_link_retorna_codigo_e_url_curta(client: TestClient):
    resposta = client.post("/links", json={"url": "https://www.exemplo.com/pagina"})

    assert resposta.status_code == 201
    dados = resposta.json()
    assert len(dados["code"]) == 6
    assert dados["url_curta"].endswith(dados["code"])
    assert dados["cliques"] == 0


def test_criar_link_com_url_invalida_retorna_422(client: TestClient):
    resposta = client.post("/links", json={"url": "isso-nao-e-uma-url"})
    assert resposta.status_code == 422


def test_redirecionar_incrementa_cliques(client: TestClient):
    criado = client.post("/links", json={"url": "https://www.exemplo.com"}).json()
    codigo = criado["code"]

    resposta = client.get(f"/{codigo}", follow_redirects=False)

    assert resposta.status_code == 307
    assert resposta.headers["location"] == "https://www.exemplo.com/"

    stats = client.get(f"/links/{codigo}").json()
    assert stats["cliques"] == 1


def test_redirecionar_codigo_inexistente_retorna_404(client: TestClient):
    resposta = client.get("/codigo-que-nao-existe", follow_redirects=False)
    assert resposta.status_code == 404


def test_listar_links_retorna_todos_criados(client: TestClient):
    client.post("/links", json={"url": "https://a.com"})
    client.post("/links", json={"url": "https://b.com"})

    resposta = client.get("/links")

    assert resposta.status_code == 200
    assert len(resposta.json()) == 2


def test_obter_estatisticas_de_link_inexistente_retorna_404(client: TestClient):
    resposta = client.get("/links/nao-existe")
    assert resposta.status_code == 404
