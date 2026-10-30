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
        SELECT
                importacao.id,
                importacao.nome_arquivo,
                importacao.data_importacao,
            COUNT(registro.id) AS total_registros
            FROM importacao
            LEFT JOIN registro
                ON importacao.id = registro.importacao_id
            WHERE importacao.usuario_id = %s
            GROUP BY
                importacao.id,
                importacao.nome_arquivo,
                importacao.data_importacao
            ORDER BY importacao.data_importacao DESC
            """

        cursor.execute(consulta, (usuario_id,))
        resultados = cursor.fetchall()

        importacoes = []

        for resultado in resultados:
            importacoes.append({
                "id": resultado[0],
                "nome_arquivo": resultado[1],
                "data_importacao": resultado[2].isoformat(),
                "total_registros": resultado[3]
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
            

def buscar_importacao(usuario_id: int, importacao_id: int) -> dict:
    conexao = None
    cursor = None

    try:
        conexao = conectar_banco()
        cursor = conexao.cursor()

        consulta = """
            SELECT
                importacao.id,
                importacao.nome_arquivo,
                importacao.data_importacao,
                registro.numero_linha,
                registro.dados
            FROM importacao
            LEFT JOIN registro
                ON importacao.id = registro.importacao_id
            WHERE importacao.id = %s
                AND importacao.usuario_id = %s
            ORDER BY registro.numero_linha
        """

        cursor.execute(consulta, (importacao_id, usuario_id))
        resultado = cursor.fetchall()

        if not resultado:
            raise ValueError("Importação não encontrada.")

        if resultado[0][3] is None:
            return {
                "id": resultado[0][0],
                "nome_arquivo": resultado[0][1],
                "data_importacao": resultado[0][2].isoformat(),
                "registros": []
            }

        return {
            "id": resultado[0][0],
            "nome_arquivo": resultado[0][1],
            "data_importacao": resultado[0][2].isoformat(),
            "registros": [
                {
                    "numero_linha": registro[3],
                    "dados": json.loads(registro[4])
                }
                for registro in resultado
            ]
        }

    except ValueError:
        raise

    except Exception as erro:
        raise RuntimeError(
            "Não foi possível buscar a importação."
        ) from erro

    finally:
        if cursor is not None:
            cursor.close()
        if conexao is not None:
            conexao.close()


def deletar_importacao(usuario_id: int, importacao_id: int) -> None:
    conexao = None
    cursor = None

    try:
        conexao = conectar_banco()
        cursor = conexao.cursor()

        consulta = """
            DELETE FROM importacao
            WHERE id = %s AND usuario_id = %s
        """

        cursor.execute(consulta, (importacao_id, usuario_id))
        if cursor.rowcount == 0:
            raise ValueError("Importação não encontrada.")

        conexao.commit()

    except ValueError:
        raise

    except Exception as erro:
        if conexao is not None:
            conexao.rollback()
        raise RuntimeError(
            "Não foi possível deletar a importação."
        ) from erro

    finally:
        if cursor is not None:
            cursor.close()
        if conexao is not None:
            conexao.close()