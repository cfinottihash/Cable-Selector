import sys, os
from pathlib import Path

# Adiciona a raiz do projeto ao Python path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

import streamlit as st
import pandas as pd
from tools.bitola_matcher import estimate_od, suggest_by_bitola

# Carrega e normaliza tabelas
df_bitola = pd.read_csv("mapping_tables/bitola_to_od.csv")
df_bitola.columns = df_bitola.columns.str.strip()

df_csto = pd.read_csv("mapping_tables/csto_selection_table.csv")
df_csto.columns = df_csto.columns.str.strip()

# Ordena as classes de tensão numericamente (15 kV, 25 kV, 35 kV)
tensoes = sorted(
    df_csto["Voltage Class"].unique(),
    key=lambda s: float(s.split()[0])
)

# Configuração da página
st.set_page_config(page_title="CSTO Selector", layout="centered")

# Exibe o logo se ele existir
logo_path = Path(__file__).parent / "assets" / "logo-chardon.png"
if logo_path.exists():
    st.image(str(logo_path), width=200)
else:
    st.warning("Logo não encontrado em assets/logo-chardon.png")

st.title("Protótipo: Seletor de Cold Shrink Termination (CSTO)")

# Entradas do usuário
voltage = st.selectbox("Selecione a classe de tensão:", options=tensoes)

modo = st.radio("Modo de seleção:", ["Por Ø de Isolamento", "Por Bitola + Marca"])

if modo == "Por Ø de Isolamento":
    od = st.number_input(
        "Diâmetro de Isolamento (mm):",
        min_value=float(df_csto["OD Min (mm)"].min()),
        max_value=float(df_csto["OD Max (mm)"].max()),
        value=float(df_csto["OD Min (mm)"].min()),
        step=0.1
    )
else:
    bitola = st.selectbox("Bitola (mm²):", options=sorted(df_bitola["Bitola (mm²)"].unique()))
    fabricante = st.selectbox("Fabricante:", options=sorted(df_bitola["Fabricante"].unique()))
    od = estimate_od(voltage, bitola, fabricante)
    st.info(f"Ø estimado: {od:.1f} mm — bitola {bitola} mm², fabricante {fabricante}")

# Botão de busca dispara todo o bloco abaixo
if st.button("Buscar Terminação"):
    matched = df_csto[
        (df_csto["Voltage Class"] == voltage) &
        (df_csto["OD Min (mm)"] <= od) &
        (df_csto["OD Max (mm)"] >= od)
    ]
    if not matched.empty:
        # Exibe a tabela de CSTO
        st.success("Terminação(s) compatível(is):")
        st.table(matched[["Part Number", "OD Min (mm)", "OD Max (mm)"]])

        # === Seletor de conector só dentro desse bloco ===
        st.subheader("Selecione o conector")
        conn_type = st.selectbox("Tipo de conector:", ["shear-bolt", "compression"])

        # Se for compression, perguntar material
        material = None
        if conn_type == "compression":
            df_conn = pd.read_csv("mapping_tables/connector_selection_table.csv")
            materials = sorted(df_conn["Material"].dropna().unique())
            material = st.selectbox("Material do lug:", options=materials)

        # Reutiliza a mesma bitola do usuário (quando em modo bitola+marca)
        conductor_size = bitola if modo == "Por Bitola + Marca" else st.number_input(
            "Bitola do condutor (mm²):",
            min_value=int(df_bitola["Bitola (mm²)"].min()),
            max_value=int(df_bitola["Bitola (mm²)"].max()),
            value=int(df_bitola["Bitola (mm²)"].min())
        )

        from tools.connector_matcher import suggest_connector
        conn_df = suggest_connector(conductor_size, conn_type, material)

        if not conn_df.empty:
            st.success("Conector(s) compatível(is):")
            st.table(conn_df)
        else:
            st.error("Nenhum conector encontrado para esses parâmetros.")
    else:
        st.error("Nenhuma terminação encontrada para esses parâmetros.")
