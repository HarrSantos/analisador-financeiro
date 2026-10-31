from flask import Blueprint, jsonify, session
from backend.security import login_required
from backend.services.analise_service import (
    criar_analise,
    listar_analises,
    buscar_analise
)

analise_bp = Blueprint("analise", __name__, url_prefix="/api/analise")


@analise_bp.route("/criar/<int:importacao_id>", methods=["POST"])
@login_required
def criar_analise_endpoint(importacao_id: int):
    usuario_id = session["usuario_id"]

    try:
        analise_id = criar_analise(usuario_id, importacao_id)
        return jsonify({"analise_id": analise_id}), 201

    except ValueError:
        return jsonify({"erro": "Importação não encontrada."}), 404

    except Exception:
        return jsonify({
            "erro": "Erro interno ao processar a solicitação."
        }), 500


@analise_bp.route("/listar", methods=["GET"])
@login_required
def listar_analises_endpoint():
    usuario_id = session["usuario_id"]

    try:
        analises = listar_analises(usuario_id)
        return jsonify(analises), 200

    except Exception:
        return jsonify({
            "erro": "Erro interno ao processar a solicitação."
        }), 500


@analise_bp.route("/buscar/<int:analise_id>", methods=["GET"])
@login_required
def buscar_analise_endpoint(analise_id: int):
    usuario_id = session["usuario_id"]

    try:
        analise = buscar_analise(usuario_id, analise_id)
        return jsonify(analise), 200

    except ValueError:
        return jsonify({
            "erro": "Análise não encontrada."
        }), 404

    except Exception:
        return jsonify({
            "erro": "Erro interno ao processar a solicitação."
        }), 500
