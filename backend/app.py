
import os
from pathlib import Path
from datetime import timedelta

from dotenv import load_dotenv
from flask import Flask
from backend.routes.auth import auth

BASE_DIR = Path(__file__).resolve().parent.parent
load_dotenv(BASE_DIR / ".env")

app = Flask(__name__)

app.config["SECRET_KEY"] = os.getenv("FLASK_SECRET_KEY")

if not app.config["SECRET_KEY"]:
    raise RuntimeError("FLASK_SECRET_KEY não foi configurada.")

# Segurança dos cookies da sessão
app.config.update(
    SESSION_COOKIE_HTTPONLY=True,
    SESSION_COOKIE_SAMESITE="Lax",
    SESSION_COOKIE_SECURE=(
        os.getenv("SESSION_COOKIE_SECURE", "false").lower() == "true"
    ),
    PERMANENT_SESSION_LIFETIME=timedelta(hours=2)
)

app.register_blueprint(auth)

@app.route("/")
def inicio():
    return "Analisador Financeiro funcionando!"

if __name__ == "__main__":
    app.run(debug=True)
