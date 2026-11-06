#🠗 importando as bibliotecas panda e sklearn
import pandas as pd
from sklearn.ensemble import IsolationForest

#🠗 VERIFICANDO SE TEM DADOS O SUFICIENTES (MÍNIMO 3), RETORNANDO VAZIO (sim, foi o Rone que escreveu tudo isso e não o chat GPT)
def analisar_transacoes(registros: list[dict]) -> list[dict]:
    if not registros or len(registros) < 3:
        return []

    df = pd.DataFrame(registros) # Transforma a lista de dicionários em um DataFrame("planilha") do Pandas

    #🠗 2. Identificar a coluna de valor (procura por nomes comuns em planilhas)
    coluna_valor = None
    for col in df.columns:
        if col.lower() in ['valor', 'preco', 'preço', 'quantia']:
            coluna_valor = col
            break

    if not coluna_valor: #se não der certo ele transmite a mensagem de erro
        raise ValueError("Nenhuma coluna de valor compatível foi encontrada nos registros.")

    #🠗 3. Limpeza e preparação: garante que os valores são numéricos e remove vazios
    df[coluna_valor] = pd.to_numeric(df[coluna_valor], errors='coerce')
    df = df.dropna(subset=[coluna_valor]) # Remove linhas que falharam na conversão ou estão vazias

    if len(df) < 3:
        return []

    #🠗 4. Configurar e treinar o Isolation Forest
    X = df[[coluna_valor]]
    modelo = IsolationForest(contamination=0.1, random_state=42) #contamination=0.1 significa que estima-se cerca de 10% de anomalias na amostra
    modelo.fit(X)

    #🠗 5. Executar a predição (-1 para anomalias, 1 para normais)
    previsoes = modelo.predict(X)
    df['anomalia'] = previsoes

    #🠗 6. Percorrer os resultados para montar o formato de saída exigido pelo backend
    anomalias_detectadas = []

    for index, linha in df.iterrows():
        if linha['anomalia'] == -1:
            # O index começa em 0 no Pandas, mas as linhas da folha de cálculo começam em 1
            numero_linha = index + 2
            valor_encontrado = linha[coluna_valor]

            anomalias_detectadas.append({
                "numero_linha": int(numero_linha),
                "nivel": "ALTO",
                "descricao": f"O valor R$ {valor_encontrado:.2f} foge do comportamento padrão dos restantes lançamentos."
            })

    return anomalias_detectadas