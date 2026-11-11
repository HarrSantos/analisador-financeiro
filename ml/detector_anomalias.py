import pandas as pd
from sklearn.ensemble import IsolationForest

def analisar_transacoes(registros: list[dict], colunas: dict) -> list[dict]:
    if not registros or len(registros) < 3:
        return []

    df = pd.DataFrame(registros)

    colunas_para_analisar = []

    for nome_coluna, informacoes in colunas.items():
        if informacoes["tipo"] == "numerico" and informacoes["papel"] == "nao_identificador":
            colunas_para_analisar.append(nome_coluna)

    if not colunas_para_analisar:
        return []

    X = df[colunas_para_analisar].copy()

    for coluna in colunas_para_analisar:
        X[coluna] = pd.to_numeric(X[coluna], errors="coerce")

    X = X.dropna()

    if len(X) < 3:
        return []

    modelo = IsolationForest(contamination=0.1, random_state=42) #contamination=0.1 significa que estima-se cerca de 10% de anomalias na amostra
    modelo.fit(X)

    previsoes = modelo.predict(X)
    pontuacoes = modelo.decision_function(X)

    X["anomalia"] = previsoes
    X["pontuacao"] = pontuacoes

    anomalias_detectadas = []

    for index, linha in X.iterrows():

        if linha["anomalia"] == -1:
            numero_linha = index + 1

            valores_encontrados = ", ".join(
                f"{coluna}: {linha[coluna]}"
                for coluna in colunas_para_analisar
            )

            anomalias_detectadas.append({
                "numero_linha": int(numero_linha),
                "nivel": "ALTO",
                "pontuacao": float(linha["pontuacao"]),
                "descricao": f"Combinação atípica detectada: {valores_encontrados}."
            })

    quantidade_anomalias = len(anomalias_detectadas)

    if quantidade_anomalias == 1:
        return anomalias_detectadas

    if quantidade_anomalias > 1:

        maior_score = max(
            anomalia["pontuacao"]
            for anomalia in anomalias_detectadas
        )

        menor_score = min(
            anomalia["pontuacao"]
            for anomalia in anomalias_detectadas
        )

        diferenca = maior_score - menor_score

        for anomalia in anomalias_detectadas:

            if diferenca == 0:
                nivel_atipicidade = 1
            else:
                nivel_atipicidade = (
                    maior_score - anomalia["pontuacao"]
                ) / diferenca

            if nivel_atipicidade <= 0.33:
                anomalia["nivel"] = "BAIXO"

            elif nivel_atipicidade <= 0.66:
                anomalia["nivel"] = "MÉDIO"

            else:
                anomalia["nivel"] = "ALTO"

    return anomalias_detectadas