import pandas as pd

# Carrega e normaliza cabeçalhos
df_csto = pd.read_csv("mapping_tables/csto_selection_table.csv")
df_csto.columns = df_csto.columns.str.strip()

df_bitola = pd.read_csv("mapping_tables/bitola_to_od.csv")
df_bitola.columns = df_bitola.columns.str.strip()

def estimate_od(classe, bitola, fabricante=None):
    sel = df_bitola[
        (df_bitola["Classe de Tensão"] == classe) &
        (df_bitola["Bitola (mm²)"]     == bitola)
    ]
    if fabricante:
        sel = sel[sel["Fabricante"] == fabricante]
    return sel["OD Nominal (mm)"].mean()

def suggest_by_bitola(classe, bitola, fabricante=None):
   # 1) Estima o Ø a partir de bitola+marca
    od = estimate_od(classe, bitola, fabricante)

    # 2) Define uma tolerância (ex.: 0.5 mm)
    tol = 0.5
    
    # 3) Aplica o filtro com tolerância nas faixas de OD Min/Max
    return df_csto[
        (df_csto["Voltage Class"]   == classe) &
        (df_csto["OD Min (mm)"]    <= od) &
        (df_csto["OD Max (mm)"]    >= od)
    ]


