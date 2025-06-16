import pandas as pd

# Carrega e normaliza
df_conn = pd.read_csv("mapping_tables/connector_selection_table.csv")
df_conn.columns = df_conn.columns.str.strip()

def suggest_connector(conductor_size: int, kind: str = "shear-bolt") -> list[str]:
    """
    Retorna a lista de códigos de conector compatíveis
    para o tamanho de condutor e tipo escolhido.
    kind: "shear-bolt" ou "compression"
    """
    sel = df_conn[
        (df_conn["Type"] == kind) &
        (df_conn["Min Conductor (mm²)"] <= conductor_size) &
        (df_conn["Max Conductor (mm²)"] >= conductor_size)
    ]
    return sel["Connector Code"].tolist()
