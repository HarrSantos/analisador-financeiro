
from flask import Flask
from backend.routes.auth import auth

app = Flask(__name__)

app.register_blueprint(auth)

@app.route("/")
def inicio():
    return "Analisador Financeiro funcionando!"

if __name__ == "__main__":
    app.run(debug=True)
