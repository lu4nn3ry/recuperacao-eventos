import hmac
import os

from flask import Flask, jsonify, request


app = Flask(__name__)


def _chave_admin_configurada():
    return os.environ.get("ADMIN_API_KEY", "")


def _admin_autorizado():
    """Valida o header X-Admin-Key contra ADMIN_API_KEY (fail-closed).

    Sem a variável de ambiente configurada, nenhuma requisição é autorizada.
    A comparação usa hmac.compare_digest para evitar timing attacks.
    """
    chave_esperada = _chave_admin_configurada()
    if not chave_esperada:
        return False
    chave_recebida = request.headers.get("X-Admin-Key", "")
    return hmac.compare_digest(chave_recebida, chave_esperada)


class Evento:
    def __init__(self, id, nome, data, capacidade_maxima, descricao=""):
        self.id = id
        self.nome = nome
        self.data = data
        self.capacidade_maxima = capacidade_maxima
        self.descricao = descricao
        self.inscricoes = []

    def to_dict(self):
        return {
            "id": self.id,
            "nome": self.nome,
            "data": self.data,
            "capacidade_maxima": self.capacidade_maxima,
            "descricao": self.descricao,
            "vagas_disponiveis": self.capacidade_maxima - len(self.inscricoes),
        }

    def inscrever(self, participante):
        if len(self.inscricoes) >= self.capacidade_maxima:
            return False, "Evento lotado"

        self.inscricoes.append(participante)
        return True, "Inscricao realizada com sucesso"

    def verificar_lotacao(self):
        vagas_ocupadas = len(self.inscricoes)
        return {
            "evento": self.nome,
            "capacidade_maxima": self.capacidade_maxima,
            "vagas_ocupadas": vagas_ocupadas,
            "vagas_disponiveis": self.capacidade_maxima - vagas_ocupadas,
            "status": "lotado" if vagas_ocupadas >= self.capacidade_maxima else "disponivel",
        }


class Participante:
    def __init__(self, id, nome, email):
        self.id = id
        self.nome = nome
        self.email = email

    def to_dict(self):
        return {
            "id": self.id,
            "nome": self.nome,
            "email": self.email,
        }


db_eventos = []
id_evento_seq = 1
id_participante_seq = 1


@app.post("/eventos")
def criar_evento():
    global id_evento_seq
    dados = request.get_json()
    evento = Evento(id_evento_seq, dados["nome"], dados["data"], dados["capacidade_maxima"], dados.get("descricao", ""))
    db_eventos.append(evento)
    id_evento_seq += 1
    return jsonify(evento.to_dict()), 201


@app.get("/eventos")
def listar_eventos():
    return jsonify([e.to_dict() for e in db_eventos])


@app.get("/eventos/<int:id>")
def obter_evento(id):
    evento = next((e for e in db_eventos if e.id == id), None)
    if not evento:
        return jsonify({"erro": "Evento nao encontrado"}), 404
    return jsonify(evento.to_dict())


@app.post("/eventos/<int:id>/inscricoes")
def inscrever_participante(id):
    global id_participante_seq
    evento = next((e for e in db_eventos if e.id == id), None)
    if not evento:
        return jsonify({"erro": "Evento nao encontrado"}), 404
    dados = request.get_json()
    participante = Participante(id_participante_seq, dados["nome"], dados["email"])
    sucesso, mensagem = evento.inscrever(participante)
    if not sucesso:
        return jsonify({"erro": mensagem}), 400
    id_participante_seq += 1
    return jsonify({"mensagem": mensagem, "participante": participante.to_dict()}), 201


@app.get("/eventos/<int:id>/inscricoes")
def listar_inscricoes(id):
    if not _admin_autorizado():
        return jsonify({"erro": "Acesso restrito a administradores"}), 403
    evento = next((e for e in db_eventos if e.id == id), None)
    if not evento:
        return jsonify({"erro": "Evento nao encontrado"}), 404
    return jsonify([p.to_dict() for p in evento.inscricoes])


@app.get("/eventos/<int:id>/lotacao")
def verificar_lotacao(id):
    evento = next((e for e in db_eventos if e.id == id), None)
    if not evento:
        return jsonify({"erro": "Evento nao encontrado"}), 404
    return jsonify(evento.verificar_lotacao())


if __name__ == "__main__":
    app.run(debug=True)
