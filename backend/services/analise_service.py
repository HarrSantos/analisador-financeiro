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
                importacao.id AS importacao_id,
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
            "importacao_id": resultado[1],
            "nome_arquivo": resultado[2],
            "data_analise": resultado[3].isoformat(),
            "status": resultado[4]
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
            ORDER BY registro.numero_linha ASC
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

        colunas = identificar_colunas(registros)

        anomalias = detectar_anomalias(registros, colunas)

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

def buscar_anomalias(usuario_id: int, analise_id: int) -> list[dict]:
    buscar_analise(usuario_id, analise_id)

    cursor = None
    conexao = None

    try:
        conexao = conectar_banco()
        cursor = conexao.cursor()

        consulta_anomalias = """
            SELECT
                anomalia.id,
                importacao.id AS importacao_id,
                anomalia.nivel,
                anomalia.descricao,
                registro.numero_linha,
                registro.dados
            FROM anomalia
            INNER JOIN registro ON anomalia.registro_id = registro.id
            INNER JOIN importacao ON registro.importacao_id = importacao.id
            WHERE anomalia.analise_id = %s

        """
        cursor.execute(consulta_anomalias, (analise_id,))
        resultados = cursor.fetchall()

        anomalias = []
        for row in resultados:
            anomalia = {
                "id": row[0],
                "importacao_id": row[1],
                "nivel": row[2],
                "descricao": row[3],
                "numero_linha": row[4],
                "dados": json.loads(row[5])
            }
            anomalias.append(anomalia)

        return anomalias

    except AnaliseNaoEncontradaError:
        raise

    except Exception as erro:
        raise RuntimeError("Não foi possível buscar as anomalias.") from erro

    finally:
        if cursor is not None:
            cursor.close()
        if conexao is not None:
            conexao.close()

IDENTIFICADORES_FORTES = {
    "id", "identificador", "uuid", "guid",
    "cpf", "cnpj", "rg",
    "matricula", "matrícula",
    "passaporte", "documento",
    "numero_documento", "número_documento",
    "codigo", "código", "cod",
    "numero_pedido", "número_pedido",
    "pedido_id", "cliente_id", "usuario_id", "user_id",
    "produto_id", "funcionario_id", "funcionário_id",
    "transacao_id", "transação_id",
    "registro_id", "importacao_id", "importação_id",
    "chave", "chave_id",
    "codigo_produto", "código_produto",
    "codigo_cliente", "código_cliente",
    "codigo_barras", "código_barras", "barcode"
}

IDENTIFICADORES_CONTEXTUAIS = {
    "produto", "cliente", "funcionario",
    "funcionário", "fornecedor", "pedido"
}

NOMES_TEMPORAIS = {
    "ano", "anos", "data", "datas",
    "dia", "dias", "mes", "mês", "meses",
    "semana", "semanas", "quinzena", "quinzenal",
    "bimestre", "bimestral", "trimestre", "trimestral",
    "quadrimestre", "semestre", "semestral",
    "periodo", "período", "periodos", "períodos",
    "exercicio", "exercício", "competencia", "competência",
    "hora", "horas", "horario", "horário",
    "minuto", "minutos", "segundo", "segundos",
    "vencimento", "validade", "emissao", "emissão",
    "lancamento", "lançamento", "nascimento",
    "criacao", "criação", "atualizacao", "atualização",
    "inicio", "início", "fim", "expiracao", "expiração",
    "year", "years", "date", "dates", "day", "days",
    "month", "months", "week", "weeks", "fortnight",
    "quarter", "quarterly", "semester", "period", "periods",
    "time", "times", "hour", "hours", "minute", "minutes",
    "second", "seconds", "timestamp", "datetime",
    "deadline", "due", "expiry", "expiration",
    "validity", "birth", "created", "updated"
}

NOMES_CATEGORICOS = {
    "status", "situacao", "situação",
    "tipo", "categoria", "departamento",
    "regiao", "região", "cidade",
    "estado", "pais", "país",
    "genero", "gênero",
    "classification", "category",
    "department", "region", "country"
}

PAPEIS_EXCLUIDOS_DAS_ESTATISTICAS = {
    "identificador",
    "temporal",
    "categorico"
}


def identificar_tipo_coluna(valores: list) -> str:
    if not valores:
        return "outro"

    valores_validos = [
        valor for valor in valores
        if valor is not None and valor != ""
    ]

    if not valores_validos:
        return "outro"

    todos_numericos = True
    todos_texto = True

    for valor in valores_validos:
        if not isinstance(valor, (int, float)) or isinstance(valor, bool):
            todos_numericos = False

        if not isinstance(valor, str):
            todos_texto = False

    if todos_numericos:
        return "numerico"

    elif todos_texto:
        return "texto"

    return "outro"


def pontuar_identificador(nome_coluna: str, valores: list) -> int:
    pontuacao = 0

    nome = nome_coluna.lower()
    palavras = nome.split("_")

    identificador_forte = (
        any(palavra in IDENTIFICADORES_FORTES for palavra in palavras)
        or any(
            "_" in termo and termo in nome
            for termo in IDENTIFICADORES_FORTES
        )
    )

    identificador_contextual = any(
        palavra in IDENTIFICADORES_CONTEXTUAIS
        for palavra in palavras
    )

    if identificador_forte:
        pontuacao += 50

    elif identificador_contextual:
        pontuacao += 20

    valores_validos = [
        valor for valor in valores
        if valor is not None and valor != ""
    ]

    if not valores_validos:
        return pontuacao

    valores_unicos = {str(valor) for valor in valores_validos}
    proporcao_unicos = len(valores_unicos) / len(valores_validos)

    if proporcao_unicos == 1.0:
        pontuacao += 30

    elif proporcao_unicos >= 0.8:
        pontuacao += 20

    elif proporcao_unicos >= 0.6:
        pontuacao += 10

    if len(valores_validos) >= 2:
        valores_numericos = []

        for valor in valores_validos:
            try:
                if isinstance(valor, bool):
                    raise ValueError

                if isinstance(valor, float) and not valor.is_integer():
                    raise ValueError

                if (
                    isinstance(valor, str)
                    and not valor.strip().lstrip("+-").isdigit()
                ):
                    raise ValueError

                valores_numericos.append(int(valor))

            except (ValueError, TypeError, OverflowError):
                valores_numericos = []
                break

        if len(valores_numericos) == len(valores_validos):
            ordenados = sorted(valores_numericos)
            diferenca = ordenados[1] - ordenados[0]

            sequencial = (
                diferenca != 0
                and all(
                    ordenados[i + 1] - ordenados[i] == diferenca
                    for i in range(len(ordenados) - 1)
                )
            )

            if sequencial:
                pontuacao += 10

    representacoes = [str(valor) for valor in valores_validos]
    tamanhos = {len(valor) for valor in representacoes}

    if len(tamanhos) == 1:
        pontuacao += 5

    todos_alfanumericos = all(
        any(caracter.isdigit() for caracter in str(valor))
        and any(caracter.isalpha() for caracter in str(valor))
        for valor in valores_validos
    )

    if todos_alfanumericos:
        pontuacao += 15

    return pontuacao


def classificar_coluna(nome_coluna: str, valores: list) -> str:
    pontuacao = pontuar_identificador(nome_coluna, valores)

    palavras = set(nome_coluna.lower().split("_"))

    if pontuacao >= 60:
        return "identificador"

    if palavras & NOMES_TEMPORAIS:
        return "temporal"

    if palavras & NOMES_CATEGORICOS:
        return "categorico"

    return "nao_identificador"


def identificar_colunas(registros: list[dict]) -> dict:
    tipos_colunas = {}

    if not registros:
        return tipos_colunas

    for coluna in registros[0]:
        valores = [
            registro.get(coluna)
            for registro in registros
        ]

        tipo = identificar_tipo_coluna(valores)
        papel = classificar_coluna(coluna, valores)

        tipos_colunas[coluna] = {
            "tipo": tipo,
            "papel": papel
        }

    return tipos_colunas


def gerar_estatisticas(
    registros: list[dict],
    anomalias: list[dict],
    colunas: dict
) -> dict:

    estatisticas = {
        "total_registros": len(registros),
        "total_anomalias": len(anomalias)
    }

    colunas_para_analisar = []

    for nome_coluna, informacoes in colunas.items():
        eh_numerica = informacoes["tipo"] == "numerico"
        papel_excluido = (
            informacoes["papel"] in PAPEIS_EXCLUIDOS_DAS_ESTATISTICAS
        )

        if eh_numerica and not papel_excluido:
            colunas_para_analisar.append(nome_coluna)

            estatisticas[nome_coluna] = {
                "soma": 0,
                "quantidade_valores": 0,
                "media": 0
            }

    for registro in registros:
        for coluna in colunas_para_analisar:
            valor = registro.get(coluna)

            if isinstance(valor, (int, float)) and not isinstance(valor, bool):
                estatisticas[coluna]["soma"] += valor
                estatisticas[coluna]["quantidade_valores"] += 1

    for coluna in colunas_para_analisar:
        dados_coluna = estatisticas[coluna]
        quantidade = dados_coluna["quantidade_valores"]

        if quantidade > 0:
            dados_coluna["media"] = dados_coluna["soma"] / quantidade

    return estatisticas


def buscar_resultado_analise(usuario_id: int, analise_id: int) -> dict:
    analise = buscar_analise(usuario_id, analise_id)
    anomalias = buscar_anomalias(usuario_id, analise_id)

    importacao_id = analise["importacao_id"]

    registros = buscar_registros_para_analise(
        importacao_id,
        usuario_id
    )

    colunas = identificar_colunas(registros)

    estatisticas = gerar_estatisticas(
        registros,
        anomalias,
        colunas
    )

    return {
        "analise": analise,
        "registros": registros,
        "anomalias": anomalias,
        "estatisticas": estatisticas,
        "colunas": colunas
    }