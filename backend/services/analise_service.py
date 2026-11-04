import json
import logging
from backend.database import conectar_banco
from ml.detector_anomalias import analisar_transacoes as detectar_anomalias
from backend.exceptions import AnaliseNaoEncontradaError


def criar_analise(usuario_id: int, importacao_id: int) -> int:
    conexao = None
    cursor = None

    try:
        conexao = conectar_banco()
        cursor = conexao.cursor()

        consulta = """
            SELECT importacao.id
            FROM importacao
            WHERE importacao.id = %s
                AND importacao.usuario_id = %s
        """

        cursor.execute(consulta, (importacao_id, usuario_id))
        resultado = cursor.fetchone()

        if not resultado:
            raise ValueError("Importação não encontrada.")

        consulta = """
            INSERT INTO analise (importacao_id)
            VALUES (%s)
        """
        cursor.execute(consulta, (importacao_id,))
        analise_id = cursor.lastrowid
        conexao.commit()
        return analise_id

    except ValueError:
        raise

    except Exception as erro:
        if conexao is not None:
            conexao.rollback()
        raise RuntimeError("Não foi possível criar a análise.") from erro

    finally:
        if cursor is not None:
            cursor.close()
        if conexao is not None:
            conexao.close()

def listar_analises(usuario_id: int) -> list[dict]:
    conexao = None
    cursor = None

    try:
        conexao = conectar_banco()
        cursor = conexao.cursor()

        consulta = """
            SELECT
                analise.id,
                importacao.nome_arquivo,
                analise.data_analise,
                analise.status
            FROM analise
            INNER JOIN importacao
                ON analise.importacao_id = importacao.id
            WHERE importacao.usuario_id = %s
            ORDER BY analise.data_analise DESC
        """

        cursor.execute(consulta, (usuario_id,))
        resultados = cursor.fetchall()

        return [
            {
                "id": resultado[0],
                "nome_arquivo": resultado[1],
                "data_analise": resultado[2].isoformat(),
                "status": resultado[3]
            }
            for resultado in resultados
        ]

    except Exception as erro:
        raise RuntimeError("Não foi possível listar as análises.") from erro

    finally:
        if cursor is not None:
            cursor.close()
        if conexao is not None:
            conexao.close()

def buscar_analise(usuario_id: int, analise_id: int) -> dict:
    conexao = None
    cursor = None

    try:
        conexao = conectar_banco()
        cursor = conexao.cursor()

        consulta = """
            SELECT
                analise.id,
                importacao.nome_arquivo,
                analise.data_analise,
                analise.status
            FROM analise
            INNER JOIN importacao
                ON analise.importacao_id = importacao.id
            WHERE analise.id = %s
                AND importacao.usuario_id = %s
        """

        cursor.execute(consulta, (analise_id, usuario_id))
        resultado = cursor.fetchone()

        if not resultado:
            raise AnaliseNaoEncontradaError("Análise não encontrada ou usuário não autorizado.")

        return {
            "id": resultado[0],
            "nome_arquivo": resultado[1],
            "data_analise": resultado[2].isoformat(),
            "status": resultado[3]
        }

    except AnaliseNaoEncontradaError:
        raise

    except Exception as erro:
        raise RuntimeError("Não foi possível buscar a análise.") from erro

    finally:
        if cursor is not None:
            cursor.close()
        if conexao is not None:
            conexao.close()

def buscar_registros_para_analise(importacao_id: int, usuario_id: int) -> list[dict]:
    conexao = None
    cursor = None

    try:
        conexao = conectar_banco()
        cursor = conexao.cursor()

        consulta = """
            SELECT registro.dados
            FROM registro
            INNER JOIN importacao
            ON registro.importacao_id = importacao.id
            WHERE importacao.id = %s
                AND importacao.usuario_id = %s
        """

        cursor.execute(consulta, (importacao_id, usuario_id))
        resultados = cursor.fetchall()

        return [
            json.loads(resultado[0])
            for resultado in resultados
        ]

    except json.JSONDecodeError as erro:
        raise RuntimeError("Os dados de um registro possuem JSON inválido.") from erro

    except Exception as erro:
        raise RuntimeError("Não foi possível buscar os registros para análise.") from erro

    finally:
        if cursor is not None:
            cursor.close()
        if conexao is not None:
            conexao.close()

def atualizar_status_analise(conexao, usuario_id: int, analise_id: int, status: str) -> None:
    cursor = None

    status_permitidos = {"PENDENTE", "PROCESSANDO", "CONCLUIDA", "ERRO"}

    if status not in status_permitidos:
        raise ValueError("Status inválido")

    try:
        cursor = conexao.cursor()

        consulta_verificacao = """
            SELECT analise.id
            FROM analise
            WHERE analise.id = %s
                AND importacao_id IN (
                    SELECT id FROM importacao WHERE usuario_id = %s
                )
        """

        cursor.execute(consulta_verificacao, (analise_id, usuario_id))
        resultado = cursor.fetchone()

        if not resultado:
            raise AnaliseNaoEncontradaError("Análise não encontrada ou usuário não autorizado.")

        consulta = """
            UPDATE analise
            SET status = %s
            WHERE analise.id = %s
                AND importacao_id IN (
                    SELECT id FROM importacao WHERE usuario_id = %s
                )
        """

        cursor.execute(consulta, (status, analise_id, usuario_id))

    except AnaliseNaoEncontradaError:
        raise

    except Exception as erro:
        raise RuntimeError("Não foi possível atualizar o status da análise.") from erro

    finally:
        if cursor is not None:
            cursor.close()

def processar_analise(usuario_id: int, analise_id: int) -> None:
    cursor = None
    conexao = None
    consulta_concluida = False

    try:
        conexao = conectar_banco()
        cursor = conexao.cursor()

        consulta = """
            SELECT importacao.id
            FROM analise
            INNER JOIN importacao ON analise.importacao_id = importacao.id
            WHERE analise.id = %s
            AND importacao.usuario_id = %s
        """
        cursor.execute(consulta, (analise_id, usuario_id))
        resultado = cursor.fetchone()

        if resultado is None:
            raise AnaliseNaoEncontradaError("Análise não encontrada ou usuário não autorizado.")

        importacao_id = resultado[0]
        consulta_concluida = True

    except AnaliseNaoEncontradaError:
        raise

    except Exception as erro:
        raise RuntimeError("Erro ao consultar a análise.") from erro

    finally:
        if cursor is not None:
            cursor.close()
            cursor = None
        if not consulta_concluida and conexao is not None:
            conexao.close()

    try:
        atualizar_status_analise(conexao, usuario_id, analise_id, "PROCESSANDO")

        conexao.commit()

        registros = buscar_registros_para_analise(importacao_id, usuario_id)

        if not registros:
            raise ValueError("Não há registros para análise.")

        anomalias = detectar_anomalias(registros)

        salvar_anomalias(conexao, analise_id, importacao_id, anomalias)

        atualizar_status_analise(conexao, usuario_id, analise_id, "CONCLUIDA")

        conexao.commit()

    except AnaliseNaoEncontradaError:
        if conexao is not None:
            conexao.rollback()
        raise

    except ValueError:
        if conexao is not None:
            conexao.rollback()
        marcar_analise_com_erro(usuario_id, analise_id)
        raise

    except Exception as erro:
        if conexao is not None:
            conexao.rollback()
        marcar_analise_com_erro(usuario_id, analise_id)

        raise RuntimeError("Erro ao processar a análise.") from erro

    finally:
        if cursor is not None:
            cursor.close()
        if conexao is not None:
            conexao.close()

def salvar_anomalias(conexao, analise_id: int, importacao_id: int, anomalias: list[dict]) -> None:
    cursor = None

    try:
        cursor = conexao.cursor()

        consulta = """
            SELECT id
            FROM analise WHERE id = %s
            AND importacao_id = %s
        """

        cursor.execute(consulta, (analise_id, importacao_id))
        resultado = cursor.fetchone()

        if resultado is None:
            raise AnaliseNaoEncontradaError("Análise não encontrada ou importação não correspondente.")

        consulta_registro = """
            SELECT id
            FROM registro
            WHERE numero_linha = %s AND importacao_id = %s
        """

        consulta_excluir = """
            DELETE FROM anomalia
            WHERE analise_id = %s
        """
        cursor.execute(consulta_excluir, (analise_id,))

        consulta_anomalia = """
            INSERT INTO anomalia (analise_id, registro_id, nivel, descricao)
            VALUES (%s, %s, %s, %s)
        """

        dados_anomalias = []

        for anomalia in anomalias:
            numero_linha = anomalia["numero_linha"]

            cursor.execute(consulta_registro, (numero_linha, importacao_id))
            resultado = cursor.fetchone()

            if resultado is None:
                raise ValueError(
                    f"Registro da linha {numero_linha} não encontrado na importação."
                )

            registro_id = resultado[0]

            nivel = anomalia["nivel"]
            descricao = anomalia["descricao"]

            dados_anomalias.append((analise_id, registro_id, nivel, descricao))

        cursor.executemany(consulta_anomalia, dados_anomalias)

    except AnaliseNaoEncontradaError:
        raise

    except ValueError:
        raise

    except Exception as erro:
        raise RuntimeError("Não foi possível salvar as anomalias.") from erro

    finally:
        if cursor is not None:
            cursor.close()

def marcar_analise_com_erro(usuario_id: int, analise_id: int) -> None:
    conexao = None
    try:
        conexao = conectar_banco()
        atualizar_status_analise(conexao, usuario_id, analise_id, "ERRO")
        conexao.commit()

    except Exception:
        logging.exception("Não foi possível marcar a análise como ERRO.")

    finally:
        if conexao is not None:
            conexao.close()