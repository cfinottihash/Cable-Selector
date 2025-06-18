import sys, os
from pathlib import Path

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))
from tools.iso_estimator import by_bitola, tol

import streamlit as st
import pandas as pd
import math

# ── data ───────────────────────────────────────────────────────────────
df_cable = pd.read_csv("mapping_tables/bitola_to_od.csv").rename(columns=str.strip)
df_csto  = pd.read_csv("mapping_tables/csto_selection_table.csv").rename(columns=str.strip)

tensoes        = sorted(df_csto["Voltage Class"].unique(), key=lambda s: float(s.split()[0]))
bitolas_padrao = sorted(df_cable["S_mm2"].dropna().unique())

# ── layout ─────────────────────────────────────────────────────────────
st.set_page_config(page_title="CSTO Selector", layout="centered")
logo = Path(__file__).parent / "assets" / "logo-chardon.png"
if logo.exists():
    st.image(str(logo), width=200)

st.title("Protótipo — Seletor de Cold-Shrink Termination")

st.session_state.setdefault("searched", False)

# ── input ──────────────────────────────────────────────────────────────
voltage = st.selectbox("Classe de tensão:", tensoes)
reinforced = False
if voltage == "35 kV":
    reinforced = st.checkbox("Isolação reforçada (8,8 mm) — cabos eólicos")

mode = st.radio("Informar cabo por …", ("Ø sobre isolação", "Bitola (estimativa Ø)"))

if mode == "Ø sobre isolação":
    d_iso = st.number_input("Ø sobre isolação (mm)", min_value=0.0, step=0.1)
    s_mm2 = None
    st.info(f"Você digitou Ø sobre isolação: **{d_iso} mm ± {tol(voltage)} mm**")
else:
    s_mm2 = st.selectbox("Seção nominal (mm²):", bitolas_padrao)
    d_iso = by_bitola(voltage, s_mm2, reinforced=reinforced)
    st.info(f"Ø sobre isolação estimado: **{d_iso} mm ± {tol(voltage)} mm**")

if st.button("Buscar Terminação"):
    st.session_state.searched = True

# ── results ─────────────────────────────────────────────────────────────
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

    if mode == "Bitola (estimativa Ø)":
        st.markdown(
            "<div style='color:#900; background:#fee; padding:8px; "
            "border-radius:4px; margin-top:16px;'>"
            "⚠️ <strong>Atenção:</strong> esta é apenas uma estimativa de Ø sobre "
            "isolação. Recomendamos confirmar o diâmetro real com o cliente antes "
            "da compra para garantir o encaixe correto."
            "</div>",
            unsafe_allow_html=True
        )

    # ── terminal suggestion ───────────────────────────────────────────────
    conductor_size = int(s_mm2) if s_mm2 else st.selectbox("Seção nominal (mm²):", bitolas_padrao)

    conn_type_ui = st.selectbox(
        "Tipo de Lug (Compressão ou Torquimétrico):",
        ["Compressão", "Torquimétrico"]
    )
    type_map = {"Compressão": "compression", "Torquimétrico": "shear-bolt"}
    type_arg = type_map[conn_type_ui]

    material = None
    if type_arg == "compression":
        df_conn = pd.read_csv("mapping_tables/connector_selection_table.csv")
        material = st.selectbox("Material do terminal:", sorted(df_conn["Material"].dropna().unique()))

    from tools.connector_matcher import suggest_connector
    conn_df = suggest_connector(conductor_size, type_arg, material)

    if conn_df.empty:
        st.error("Nenhum conector/lug encontrado para esses parâmetros.")
    else:
        st.subheader("Lug compatíveis")
        st.table(conn_df)
