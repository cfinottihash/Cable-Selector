import pandas as pd

CSV_PATH = "mapping_tables/csto_selection_table.csv"

# 1. Carrega a tabela e limpa cabeçalhos
df = pd.read_csv(CSV_PATH)
df.columns = df.columns.str.strip()     # remove espaços extras

# 2. (Opcional) converte colunas numéricas p/ float, caso venham como texto
num_cols = ["OD Min (mm)", "OD Max (mm)"]
df[num_cols] = df[num_cols].apply(pd.to_numeric, errors="coerce")

def suggest_csto(voltage_class: str, insulation_od: float) -> pd.DataFrame:
    """
    Retorna as terminações CSTO compatíveis com tensão e O.D. informados.
    """
    return df[
        (df["Voltage Class"] == voltage_class) &
        (df["OD Min (mm)"] <= insulation_od) &
        (df["OD Max (mm)"] >= insulation_od)
    ]

# Smoke-test
if __name__ == "__main__":
    result = suggest_csto("25 kV", 26.5)
    print(result[["Part Number", "OD Min (mm)", "OD Max (mm)"]])
