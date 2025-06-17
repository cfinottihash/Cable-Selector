import sys, os
from pathlib import Path

# ── path do projeto ─────────────────────────────────────────────────────
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from tools.iso_estimator import by_bitola
import tools.iso_estimator as iso

import streamlit as st
import pandas as pd

# ── dados ---------------------------------------------------------------
df_bitola = (
    pd.read_csv("mapping_tables/bitola_to_od.csv")
      .rename(columns=str.strip)
)
df_csto = (
    pd.read_csv("mapping_tables/csto_selection_table.csv")
      .rename(columns=str.strip)
)

tensoes = sorted(df_csto["Voltage Class"].unique(),
                 key=lambda s: float(s.split()[0]))
bitolas_padrao = sorted(df_bitola["Bitola (mm²)"].unique())

# ── layout --------------------------------------------------------------
st.set_page_config(page_title="CSTO Selector", layout="centered")
logo = Path(__file__).parent / "assets" / "logo-chardon.png"
if logo.exists():
    st.image(str(logo), width=200)

st.title("Protótipo: Seletor de Cold-Shrink Termination")

# ── estado --------------------------------------------------------------
searched = st.session_state.setdefault("searched", False)

# ── entrada -------------------------------------------------------------
voltage = st.selectbox("Classe de tensão:", tensoes)

mode = st.radio("Informar cabo por…",
                ("Ø sobre isolação", "Bitola (estimativa Ø)"))

if mode == "Ø sobre isolação":
    d_iso = st.number_input("Ø sobre isolação (mm)", 0.0, step=0.1)
    s_mm2 = None
else:
    s_mm2 = st.selectbox("Seção nominal (mm²)", bitolas_padrao)
    d_iso = by_bitola(voltage, s_mm2)
    st.info(f"Ø sobre isolação estimado: **{d_iso} mm ± {iso.tol(voltage)} mm**")

if st.button("Buscar Terminação"):
    st.session_state.searched = True

# ── resultado -----------------------------------------------------------
if st.session_state.searched:
    match = df_csto[
        (df_csto["Voltage Class"] == voltage) &
        (df_csto["OD Min (mm)"] <= d_iso) &
        (df_csto["OD Max (mm)"] >= d_iso)
    ]

    if match.empty:
        st.error("Nenhuma terminação encontrada.")
        st.stop()

    st.success("Terminação(s) compatível(is):")
    st.table(match[["Part Number", "OD Min (mm)", "OD Max (mm)"]])

    # bitola para conector
    conductor_size = int(s_mm2) if s_mm2 else st.selectbox(
        "Bitola do condutor (mm²)", bitolas_padrao)

    conn_type = st.selectbox("Tipo de conector:", ["shear-bolt", "compression"])
    material = None
    if conn_type == "compression":
        df_conn = pd.read_csv("mapping_tables/connector_selection_table.csv")
        material = st.selectbox("Material do lug:",
                                sorted(df_conn["Material"].dropna().unique()))

    from tools.connector_matcher import suggest_connector
    conn_df = suggest_connector(conductor_size, conn_type, material)

    if conn_df.empty:
        st.error("Nenhum conector encontrado.")
    else:
        st.table(conn_df)
