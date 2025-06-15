import streamlit as st
import pandas as pd

# carrega a tabela CSTO
CSV_PATH = "mapping_tables/csto_selection_table.csv"
df = pd.read_csv(CSV_PATH) # Corrected variable name from CST_PATH to CSV_PATH

st.set_page_config(page_title="CSTO Selector", layout="centered")
st.title("Prototipo: Seletor de Cold Shrink Termination (CSTO)")

# Entradas do usuario
voltage = st.selectbox(
    "Selecione a classe de tensão:",
    options=df["Voltage Class"].unique()
)

# Corrected placement of od variable and parentheses for max() function
od = st.number_input(
    "Diâmetro de Isolamento (mm):",
    min_value=float(df["OD Min (mm)"].min()),
    max_value=float(df["OD Max (mm)"].max()), # Corrected parentheses
    value=float(df["OD Min (mm)"].min()),
    step=0.1
)

# Ao Clicar, faz o match
if st.button("Buscar Terminação"): # Corrected colon to a closing quote
    matched = df[
        (df["Voltage Class"] == voltage) &
        (df["OD Min (mm)"] <= od) &
        (df["OD Max (mm)"] >= od)
    ]
    if not matched.empty:
        st.success("Terminação(s) compatível(is):")
        # Corrected column name: "OD min(mm)" should be "OD Min (mm)"
        # And "OD Max(mm)" should be "OD Max (mm)" for consistency with the CSV.
        st.table(matched[["Part Number", "OD Min (mm)", "OD Max (mm)"]])
    else:
        st.error("Nenhuma terminação encontrada para esses parâmetros.")