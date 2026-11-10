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

def identificar_colunas(registros: list[dict]) -> dict:
    tipos_colunas = {}

    for coluna in registros[0]:
        valores = []

        for registro in registros:
            valor = registro[coluna]
            valores.append(valor)

        tipo = identificar_tipo_coluna(valores)
        resultado = classificar_coluna(coluna, valores)

        tipos_colunas[coluna] = {
            "tipo": tipo,
            "papel": resultado
        }

    return tipos_colunas

def identificar_tipo_coluna(valores):
    if not valores:
        return "outro"

    todos_numericos = True
    todos_texto = True

    for valor in valores:
        if  not isinstance(valor, str):
            todos_texto = False

        if  not isinstance(valor, (int, float)):
            todos_numericos = False

    if todos_numericos:
        return "numerico"

    elif todos_texto:
        return "texto"

    else:
        return "outro"

def gerar_estatisticas(registros: list[dict], anomalias: list[dict], colunas: dict) -> dict:

    estatisticas = {
        "total_registros": len(registros),
        "total_anomalias": len(anomalias)
    }

    colunas_para_analisar = []

    for nome_coluna, informacoes in colunas.items():

        eh_numerica = informacoes["tipo"] == "numerico"
        eh_identificador = informacoes["papel"] == "identificador"
        eh_temporal = informacoes["papel"] == "temporal"
        eh_categorico = informacoes["papel"] == "categorico"

        if eh_numerica and not eh_identificador and not eh_temporal and not eh_categorico:
            colunas_para_analisar.append(nome_coluna)

            estatisticas[nome_coluna] = {
                "soma": 0,
                "quantidade_valores": 0,
                "media": 0
            }

    for registro in registros:
        for coluna in colunas_para_analisar:

            valor = registro.get(coluna)

            if isinstance(valor, (int, float)):
                estatisticas[coluna]["soma"] += valor
                estatisticas[coluna]["quantidade_valores"] += 1

    for coluna in colunas_para_analisar:

        dados_coluna = estatisticas[coluna]

        if dados_coluna["quantidade_valores"] > 0:
            dados_coluna["media"] = (
                dados_coluna["soma"] / dados_coluna["quantidade_valores"]
            )

    return estatisticas

def buscar_resultado_analise(usuario_id: int, analise_id: int) -> dict:
    analise = buscar_analise(usuario_id, analise_id)
    anomalias = buscar_anomalias(usuario_id, analise_id)

    importacao_id = analise["importacao_id"]

    registros = buscar_registros_para_analise(importacao_id, usuario_id)

    colunas = identificar_colunas(registros)
    estatisticas = gerar_estatisticas(registros, anomalias, colunas)

    return {
        "analise": analise,
        "registros": registros,
        "anomalias": anomalias,
        "estatisticas": estatisticas,
        "colunas": colunas
    }

def classificar_coluna(nome_coluna, valores):
    pontuacao = pontuar_identificador(nome_coluna, valores)

    if pontuacao >= 60:
        return "identificador"

    temporal = identificar_coluna_temporal(nome_coluna)

    if temporal:
        return "temporal"

    categorico = identificar_coluna_categorica(nome_coluna)

    if categorico:
        return "categorico"

    return "nao_identificador"


def pontuar_identificador(nome_coluna, valores):
    identificadores_fortes = [
        "id",
        "identificador",
        "uuid",
        "guid",
        "cpf",
        "cnpj",
        "rg",
        "matricula",
        "matrícula",
        "passaporte",
        "numero_documento",
        "número_documento",
        "documento",
        "codigo",
        "código",
        "cod",
        "numero_pedido",
        "número_pedido",
        "pedido_id",
        "cliente_id",
        "usuario_id",
        "user_id",
        "produto_id",
        "funcionario_id",
        "funcionário_id",
        "transacao_id",
        "transação_id",
        "registro_id",
        "importacao_id",
        "importação_id",
        "chave",
        "chave_id",
        "codigo_produto",
        "código_produto",
        "codigo_cliente",
        "código_cliente",
        "codigo_barras",
        "código_barras",
        "barcode"
    ]

    identificadores_contextuais = [
        "produto",
        "cliente",
        "funcionario",
        "fornecedor",
        "pedido"
    ]

    pontuacao = 0

    palavras_coluna = nome_coluna.lower().split("_")

    for palavra in palavras_coluna:
        if palavra in identificadores_fortes:
            pontuacao += 50
            break
        elif palavra in identificadores_contextuais:
            pontuacao += 20
            break

    if valores:
        valores_unicos = set(valores)
        proporcao_unicos = len(valores_unicos) / len(valores)
        if proporcao_unicos == 1.0:
            pontuacao += 30
        elif proporcao_unicos >= 0.8:
            pontuacao += 20
        elif proporcao_unicos >= 0.6:
            pontuacao += 10

    if identificar_sequencial(valores):
        pontuacao += 10

    if identificar_mesmo_tamanho(valores):
        pontuacao += 5

    if identificar_alfanumerico(valores):
        pontuacao += 15

    return pontuacao

def identificar_sequencial(valores):
    if not valores:
        return False

    if len(valores) < 2:
        return False

    valores_numericos = []

    for valor in valores:
        try:
            valor = int(valor)
            valores_numericos.append(valor)
        except ValueError:
            return False

    ordenados = sorted(valores_numericos)

    diferenca = ordenados[1] - ordenados[0]

    for i in range(len(ordenados) - 1):
        diferenca_atual = ordenados[i + 1] - ordenados[i]

        if diferenca_atual != diferenca:
            return False

    return True

def identificar_mesmo_tamanho(valores):
    if not valores:
        return False

    tamanho_inicial = len(str(valores[0]))

    for valor in valores:
        if len(str(valor)) != tamanho_inicial:
            return False

    return True

def identificar_alfanumerico(valores):
    if not valores:
        return False

    valores_alphanumericos = 0

    for valor in valores:
        tem_numero = False
        tem_letra = False

        for caracter in str(valor):
            if caracter.isdigit():
                tem_numero = True
            if caracter.isalpha():
                tem_letra = True

        if tem_numero and tem_letra:
            valores_alphanumericos += 1

    if valores_alphanumericos == len(valores):
        return True

    return False

def identificar_coluna_temporal(nome_coluna):

    identificadores_temporais = [
        "ano",
        "anos",
        "data",
        "datas",
        "dia",
        "dias",
        "mes",
        "mês",
        "meses",
        "semana",
        "semanas",
        "quinzena",
        "quinzenal",
        "bimestre",
        "bimestral",
        "trimestre",
        "trimestral",
        "quadrimestre",
        "semestre",
        "semestral",
        "periodo",
        "período",
        "periodos",
        "períodos",
        "exercicio",
        "exercício",
        "competencia",
        "competência",
        "hora",
        "horas",
        "horario",
        "horário",
        "minuto",
        "minutos",
        "segundo",
        "segundos",
        "vencimento",
        "validade",
        "emissao",
        "emissão",
        "lancamento",
        "lançamento",
        "nascimento",
        "criacao",
        "criação",
        "atualizacao",
        "atualização",
        "inicio",
        "início",
        "fim",
        "expiracao",
        "expiração",
        "year",
        "years",
        "date",
        "dates",
        "day",
        "days",
        "month",
        "months",
        "week",
        "weeks",
        "fortnight",
        "quarter",
        "quarterly",
        "semester",
        "period",
        "periods",
        "time",
        "times",
        "hour",
        "hours",
        "minute",
        "minutes",
        "second",
        "seconds",
        "timestamp",
        "datetime",
        "deadline",
        "due",
        "expiry",
        "expiration",
        "validity",
        "birth",
        "created",
        "updated"
    ]

    palavras_coluna = nome_coluna.lower().split("_")

    for palavra in palavras_coluna:
        if palavra in identificadores_temporais:
            return True

    return False

def identificar_coluna_categorica(nome_coluna):
    nomes_categoricos = [
    "status",
    "situacao",
    "situação",
    "tipo",
    "categoria",
    "departamento",
    "regiao",
    "região",
    "cidade",
    "estado",
    "pais",
    "país",
    "genero",
    "gênero",
    "classification",
    "category",
    "department",
    "region",
    "country"
    ]

    palavras_coluna = nome_coluna.lower().split("_")

    for palavra in palavras_coluna:
        if palavra in nomes_categoricos:
            return True

    return False