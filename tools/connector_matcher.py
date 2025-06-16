import pandas as pd

# Carrega e normaliza
df_conn = pd.read_csv("mapping_tables/connector_selection_table.csv")
df_conn.columns = df_conn.columns.str.strip()

def suggest_connector(conductor_size: int, kind: str = "shear-bolt", material: str | None = None) -> pd.DataFrame:
    """
    Retorna DataFrame com Connector Code, Min, Max e Material para o conductor_size e kind.
    """
    sel = df_conn[
        (df_conn["Type"] == kind) &
        (df_conn["Min Conductor (mm²)"] <= conductor_size) &
        (df_conn["Max Conductor (mm²)"] >= conductor_size)
    ]
    if kind == "compression" and material:
        sel = sel[sel["Material"].str.lower() == material.lower()]
    return sel[["Connector Code", "Min Conductor (mm²)", "Max Conductor (mm²)", "Material"]]
