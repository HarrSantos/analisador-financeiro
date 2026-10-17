import os
from pathlib import Path
from dotenv import load_dotenv
from flask import Flask
from backend.routes.auth import auth

BASE_DIR = Path(__file__).resolve().parent.parent
load_dotenv(BASE_DIR / ".env")

app = Flask(__name__)

app.config["SECRET_KEY"] = os.getenv("FLASK_SECRET_KEY")

if not app.config["SECRET_KEY"]:
    raise RuntimeError("FLASK_SECRET_KEY não foi configurada.")

app.register_blueprint(auth)

@app.route("/")
def inicio():
    return "Analisador Financeiro funcionando!"

if __name__ == "__main__":
    app.run(debug=True)