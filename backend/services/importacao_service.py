
import pandas as pd
from io import BytesIO


def ler_csv(conteudo: bytes) -> pd.DataFrame:
    if not conteudo:
        raise ValueError("O arquivo CSV está vazio.")

    arquivo = BytesIO(conteudo)

    try:
        df = pd.read_csv(
            arquivo,
            sep=None,
            engine="python"
        )

    except (pd.errors.ParserError, UnicodeDecodeError) as erro:
        raise ValueError(
            "Não foi possível interpretar o arquivo CSV."
        ) from erro

    if df.empty:
        raise ValueError("O CSV não contém registros.")

    if df.dropna(how="all").empty:
        raise ValueError("O CSV não contém dados válidos.")

    if any(
        str(coluna).startswith("Unnamed:")
        for coluna in df.columns
    ):
        raise ValueError(
            "O CSV contém uma ou mais colunas sem nome."
        )

    return df
