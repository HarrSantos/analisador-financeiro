import json

from backend.database import conectar_banco

def salvar_importacao(
        usuario_id: int,
        nome_arquivo: str,
        registros: list[dict]
) -> int:
    if not registros:
        raise ValueError("A lista de registros está vazia.")

    conexao = None
    cursor = None

    try:
        conexao = conectar_banco()
        cursor = conexao.cursor()

        consulta = """
            INSERT INTO importacao (usuario_id, nome_arquivo)
            VALUES (%s, %s)
        """

        cursor.execute(
            consulta,
            (usuario_id, nome_arquivo)
        )

        importacao_id = cursor.lastrowid
        valores_registros = []
        for numero_linha, registro in enumerate(registros, start=1):
            valores_registros.append(
                (importacao_id, numero_linha, json.dumps(registro))
            )

        consulta_registros = """
            INSERT INTO registro (importacao_id, numero_linha, dados)
            VALUES (%s, %s, %s)
        """

        cursor.executemany(consulta_registros, valores_registros)

        conexao.commit()
        return importacao_id
    
    except Exception as erro:
        if conexao is not None:
            conexao.rollback()
        raise RuntimeError(
            "Não foi possível salvar a importação no banco de dados."
        ) from erro
    
    finally:
        if cursor is not None:
            cursor.close()
        if conexao is not None:
            conexao.close()

def listar_importacoes(usuario_id: int) -> list[dict]:
    conexao = None
    cursor = None

    try:
        conexao = conectar_banco()
        cursor = conexao.cursor()

        consulta = """
            SELECT id, nome_arquivo, data_importacao
            FROM importacao
            WHERE usuario_id = %s
            ORDER BY data_importacao DESC
        """

        cursor.execute(consulta, (usuario_id,))
        resultados = cursor.fetchall()

        importacoes = []
        for resultado in resultados:
            importacoes.append({ 
                "id": resultado[0],
                "nome_arquivo": resultado[1],
                "data_importacao": resultado[2].isoformat()
            })

        return importacoes
    
    except Exception as erro:
        raise RuntimeError(
            "Não foi possível listar as importações do usuário."
    ) from erro
    
    finally:
        if cursor is not None:
            cursor.close()
        if conexao is not None:
            conexao.close()