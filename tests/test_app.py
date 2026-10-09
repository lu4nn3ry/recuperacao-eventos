"""Testes de segurança e funcionais da API de eventos."""

import pytest

from app import app


@pytest.fixture
def client():
    app.config["TESTING"] = True
    with app.test_client() as c:
        yield c


@pytest.fixture
def evento_com_inscricao(client):
    resp = client.post(
        "/eventos",
        json={"nome": "Workshop", "data": "2026-06-20", "capacidade_maxima": 5},
    )
    assert resp.status_code == 201
    evento_id = resp.get_json()["id"]
    resp = client.post(
        f"/eventos/{evento_id}/inscricoes",
        json={"nome": "Luann", "email": "luann@email.com"},
    )
    assert resp.status_code == 201
    return evento_id


class TestAcessoInscricoes:
    """GET /eventos/<id>/inscricoes exige X-Admin-Key (fail-closed)."""

    def test_sem_chave_configurada_negado(self, client, evento_com_inscricao,
                                          monkeypatch):
        monkeypatch.delenv("ADMIN_API_KEY", raising=False)
        resp = client.get(f"/eventos/{evento_com_inscricao}/inscricoes")
        assert resp.status_code == 403

    def test_sem_header_negado(self, client, evento_com_inscricao,
                               monkeypatch):
        monkeypatch.setenv("ADMIN_API_KEY", "secreta")
        resp = client.get(f"/eventos/{evento_com_inscricao}/inscricoes")
        assert resp.status_code == 403

    def test_chave_errada_negada(self, client, evento_com_inscricao,
                                 monkeypatch):
        monkeypatch.setenv("ADMIN_API_KEY", "secreta")
        resp = client.get(f"/eventos/{evento_com_inscricao}/inscricoes",
                          headers={"X-Admin-Key": "errada"})
        assert resp.status_code == 403

    def test_chave_correta_autorizada(self, client, evento_com_inscricao,
                                      monkeypatch):
        monkeypatch.setenv("ADMIN_API_KEY", "secreta")
        resp = client.get(f"/eventos/{evento_com_inscricao}/inscricoes",
                          headers={"X-Admin-Key": "secreta"})
        assert resp.status_code == 200
        data = resp.get_json()
        assert data[0]["email"] == "luann@email.com"


class TestEndpointsPublicos:
    """Endpoints públicos continuam funcionando normalmente."""

    def test_listar_eventos(self, client, evento_com_inscricao):
        resp = client.get("/eventos")
        assert resp.status_code == 200
        assert resp.get_json()[0]["nome"] == "Workshop"

    def test_lotacao_publica(self, client, evento_com_inscricao):
        resp = client.get(f"/eventos/{evento_com_inscricao}/lotacao")
        assert resp.status_code == 200
        assert resp.get_json()["vagas_ocupadas"] == 1

    def test_evento_inexistente(self, client):
        resp = client.get("/eventos/999")
        assert resp.status_code == 404
