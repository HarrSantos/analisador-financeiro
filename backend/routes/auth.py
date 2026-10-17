from email_validator import validate_email, EmailNotValidError
from werkzeug.security import generate_password_hash
from werkzeug.security import check_password_hash
import mysql.connector
from flask import Blueprint, request, jsonify, session
from backend.database import conectar_banco

auth = Blueprint("auth", __name__)

# Rota de cadastro
@auth.route("/api/auth/cadastro", methods=["POST"])
def cadastrar():
    dados = request.get_json()

    if not isinstance(dados, dict):
        return jsonify({"erro": "Dados inválidos."}), 400

    nome = dados.get("nome")
    email = dados.get("email")
    senha = dados.get("senha")

    # Verifica se os campos foram enviados
    if not nome or not email or not senha:
        return jsonify({"erro": "Preencha todos os campos."}), 400

    # Verifica se todos os campos são textos
    if not isinstance(nome, str) or not isinstance(email, str) or not isinstance(senha, str):
        return jsonify({"erro": "Dados inválidos."}), 400

    # Remove espaços das pontas do nome e do e-mail
    nome = nome.strip()
    email = email.strip()

    # Verifica se os campos contêm conteúdo válido
    if not nome or not email or not senha.strip():
        return jsonify({"erro": "Preencha os campos corretamente."}), 400

    # Verifica se os campos não excedem o limite de caracteres
    if len(email) > 255 or len(nome) > 120 or len(senha) > 128:
        return jsonify({"erro": "Tamanho máximo excedido."}), 400

    # Valida o formato do e-mail
    try:
        email_validado = validate_email(email, check_deliverability=False)
        email = email_validado.normalized
    except EmailNotValidError:
        return jsonify({"erro": "E-mail inválido."}), 400

    conexao = None
    cursor = None

    try:
        # Verifica se o e-mail já está cadastrado no banco de dados
        conexao = conectar_banco()
        cursor = conexao.cursor()
        
        consulta = "SELECT id FROM usuario WHERE email = %s"
        cursor.execute(consulta, (email,))
        usuario_existente = cursor.fetchone()
        
        # O e-mail já está cadastrado
        if usuario_existente:
            return jsonify({"erro": "E-mail já cadastrado."}), 409

        # transforma a senha em hash antes de armazená-la no banco de dados
        senha_hash = generate_password_hash(senha)

        # Insere o novo usuário no banco de dados
        consulta = "INSERT INTO usuario (nome, email, senha) VALUES (%s, %s, %s)"
        cursor.execute(consulta, (nome, email, senha_hash))

        conexao.commit()

        return jsonify({"mensagem": "Usuário cadastrado com sucesso!"}), 201
    
    except mysql.connector.Error:
        if conexao is not None:
            conexao.rollback()

        return jsonify({"erro": "Não foi possível concluir o cadastro."}), 500

    finally:
        if cursor is not None:
            cursor.close()
        if conexao is not None:
            conexao.close()

# Rota de login
@auth.route("/api/auth/login", methods=["POST"])
def login():
    dados = request.get_json()

    if not isinstance(dados, dict):
        return jsonify({"erro": "Dados inválidos."}), 400

    email = dados.get("email")
    senha = dados.get("senha")

    if not email or not senha:
        return jsonify({"erro": "Preencha todos os campos."}), 400

    if not isinstance(email, str) or not isinstance(senha, str):
        return jsonify({"erro": "Dados inválidos."}), 400

    email = email.strip()

    if not email or not senha.strip():
        return jsonify({"erro": "Preencha todos os campos."}), 400

    cursor = None
    conexao = None

    try:
        conexao = conectar_banco()
        cursor = conexao.cursor()

        consulta = "SELECT id, senha FROM usuario WHERE email = %s"
        cursor.execute(consulta, (email,))
        usuario = cursor.fetchone()

        if not usuario:
            return jsonify({"erro": "E-mail ou senha inválidos."}), 401

        check_senha = check_password_hash(usuario[1], senha)

        if not check_senha:
            return jsonify({"erro": "E-mail ou senha inválidos."}), 401

        session.clear()
        session["usuario_id"] = usuario[0]

        return jsonify({
            "mensagem": "Login bem-sucedido!",
            "usuario_id": usuario[0]
        }), 200
    
    except mysql.connector.Error:
        return jsonify({"erro": "Não foi possível realizar o login."}), 500

    finally:
        if cursor is not None:
            cursor.close()
        if conexao is not None:
            conexao.close()

# Verifica se o usuário está logado
@auth.route("/api/auth/verificar-sessao", methods=["GET"])
def verificar_sessao():
    if "usuario_id" in session:
        return jsonify({
            "logado": True,
            "usuario_id": session["usuario_id"]
        }), 200
    
    else:
        return jsonify({"logado": False}), 401

# Logout route
@auth.route("/api/auth/logout", methods=["POST"])
def logout():
    session.clear()
    return jsonify({"mensagem": "Logout realizado com sucesso."}), 200