
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
            engine="python",
            encoding="utf-8-sig"
        )

    except (pd.errors.ParserError, UnicodeDecodeError) as erro:
        raise ValueError(
            "Não foi possível interpretar o arquivo CSV."
        ) from erro

    df.columns = (
        df.columns
        .astype(str)
        .str.replace("\ufeff", "", regex=False)
        .str.strip()
    )

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

def converter_registros(df: pd.DataFrame) -> list[dict]:
    df = df.astype(object).where(pd.notna(df), None)

    return df.to_dict(orient="records")
