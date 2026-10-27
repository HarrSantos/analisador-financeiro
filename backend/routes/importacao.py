from flask import Blueprint, jsonify, request, session

from backend.security import login_required
from backend.services.importacao_service import (
    ler_csv,
    converter_registros
)
from backend.services.armazenamento_service import (
    salvar_importacao,
    listar_importacoes
)


importacao = Blueprint(
    "importacao",
    __name__,
    url_prefix="/api/importacao"
)


@importacao.route("/csv", methods=["POST"])
@login_required
def importar_csv():
    if "arquivo" not in request.files:
        return jsonify({
            "erro": "Nenhum arquivo foi enviado."
        }), 400

    arquivo = request.files["arquivo"]

    if not arquivo.filename:
        return jsonify({
            "erro": "Selecione um arquivo CSV."
        }), 400

    if not arquivo.filename.lower().endswith(".csv"):
        return jsonify({
            "erro": "Envie um arquivo com extensão .csv."
        }), 400

    try:
        df = ler_csv(arquivo.read())
        registros = converter_registros(df)

    except ValueError as erro:
        return jsonify({
            "erro": str(erro)
        }), 400

    try:
        importacao_id = salvar_importacao(
            usuario_id=session["usuario_id"],
            nome_arquivo=arquivo.filename,
            registros=registros
        )

    except Exception:
        return jsonify({
            "erro": "Não foi possível salvar a importação no banco de dados."
        }), 500

    return jsonify({
        "mensagem": "Arquivo CSV importado e salvo com sucesso.",
        "importacao_id": importacao_id,
        "colunas": df.columns.tolist(),
        "total_registros": len(registros)
    }), 201
    
    
@importacao.route("/", methods=["GET"])
@login_required
def listar_importacoes_usuario():
    try:
        importacoes = listar_importacoes(usuario_id=session["usuario_id"])
    except Exception:
        return jsonify({
            "erro": "Não foi possível listar as importações do usuário."
        }), 500

    return jsonify(importacoes), 200