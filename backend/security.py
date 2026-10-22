
from functools import wraps
from flask import jsonify, session


def login_required(func):
    @wraps(func)
    def wrapper(*args, **kwargs):
        if "usuario_id" not in session:
            return jsonify({
                "erro": "Autenticação necessária."
            }), 401

        return func(*args, **kwargs)

    return wrapper
