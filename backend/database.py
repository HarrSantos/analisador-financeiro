import os

import mysql.connector
from dotenv import load_dotenv


load_dotenv()


def conectar_banco():
    conexao = mysql.connector.connect(
        host=os.getenv("DB_HOST"),
        port=os.getenv("DB_PORT"),
        user=os.getenv("DB_USER"),
        password=os.getenv("DB_PASSWORD"),
        database=os.getenv("DB_NAME")
    )

    return conexao

conexao = conectar_banco()

cursor = conexao.cursor()

cursor.execute("SELECT * FROM usuario")

resultado = cursor.fetchall()

print(resultado)

cursor.close()
conexao.close()