import sys, os
from pathlib import Path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))
from tools.iso_estimator import by_bitola, tol

import streamlit as st
import pandas as pd
import re

# ── data ───────────────────────────────────────────────────────────────
df_cable = (
    pd.read_csv("mapping_tables/bitola_to_od.csv",
        names=["Cable Voltage", "S_mm2", "Brand", "Cable", "OD_iso_mm", "D_cond_mm", "T_iso_mm"],
        header=0)
    .rename(columns=str.strip)
)
df_csto = pd.read_csv("mapping_tables/csto_selection_table.csv").rename(columns=str.strip)

# Mapeamento de tensão do cabo para tensão da terminação
TENS_MAP = {
    "8.7/15 kV": "15 kV",
    "12/20 kV": "25 kV",
    "15/25 kV": "25 kV",
    "20/35 kV": "35 kV"
}
def ordenar_tensoes(val):
    match = re.match(r"([\d\.]+)", val)
    return float(match.group(1)) if match else float('inf')
cabos_tensoes = sorted(df_cable["Cable Voltage"].unique(), key=ordenar_tensoes)
marcas = sorted(df_cable["Brand"].dropna().unique())

# ── layout ─────────────────────────────────────────────────────────────
st.set_page_config(page_title="CSTO Selector", layout="centered")
logo = Path(__file__).parent / "assets" / "logo-chardon.png"
if logo.exists():
    st.image(str(logo), width=200)
st.title("Protótipo — Seletor de Cold-Shrink Termination")

st.session_state.setdefault("searched", False)

# ── input ──────────────────────────────────────────────────────────────
st.header("Seleção do cabo")

# 1) Ask up front if they know the real insulation diameter
know_iso = st.radio(
    "Você já sabe o Ø sobre isolação do cabo?",
    ("Não, preciso estimar pela bitola", "Sim, digitar valor real")
)

if know_iso.startswith("Sim"):
    # direct input of the real diameter
    d_iso = st.number_input(
        "Ø sobre isolação (mm)", min_value=0.0, step=0.1
    )
    tolerance = 0.0
    st.info(f"Ø sobre isolação informado: **{d_iso:.1f} mm**")
    st.caption("Você forneceu o valor real que tem do cabo em campo.")
    used_real = True

else:
    # brand + section → estimate path
    used_real = False

    cabo_tensao = st.selectbox("Classe de tensão do cabo:", cabos_tensoes)
    cabo_marca = st.selectbox("Marca do cabo (opcional):", ["Todas"] + marcas)

    df_filtrado = df_cable[df_cable["Cable Voltage"] == cabo_tensao]
    if cabo_marca != "Todas":
        df_filtrado = df_filtrado[df_filtrado["Brand"] == cabo_marca]

    bitolas_disp = sorted(df_filtrado["S_mm2"].astype(float).unique())
    s_mm2 = st.selectbox("Seção nominal (mm²):", bitolas_disp)

    # lookup real if exists else estimate
    linha = df_filtrado[df_filtrado["S_mm2"].astype(float) == float(s_mm2)]
    tensao_term = TENS_MAP[cabo_tensao]
    tolerance = tol(tensao_term)

    if not linha.empty:
        # use catalog value
        d_iso = float(linha.iloc[0]["OD_iso_mm"])
        d_cond = float(linha.iloc[0]["D_cond_mm"])
        t_iso  = float(linha.iloc[0]["T_iso_mm"])
        st.info(f"Ø sobre isolação REAL: **{d_iso:.1f} mm**")
        st.caption(f"Ø condutor: {d_cond} mm | Espessura isolação: {t_iso} mm")
        used_real = True
    else:
        # statistical estimate
        d_iso = by_bitola(tensao_term, float(s_mm2))
        st.warning(
            f"Ø sobre isolação ESTIMADA: **{d_iso:.1f} mm ± {tolerance} mm**"
        )
        st.caption(
            "Não há dado exato para essa bitola/marca. "
            "Estimado pela curva estatística."
        )
        # 🔴 new “always confirm” reminder:
        st.markdown(
            "<div style='color:#900; background:#fee; padding:8px; "
            "border-radius:4px; margin-top:8px;'>"
            "⚠️ <strong>Atenção:</strong> Sempre confirme com o cliente "
            "os dados reais do cabo antes de finalizar a compra."
            "</div>",
            unsafe_allow_html=True
        )

    # Aviso se o resultado só entrou por conta da tolerância
    for idx, row in match.iterrows():
        if not (row["OD Min (mm)"] <= d_iso <= row["OD Max (mm)"]):
            st.warning(
                f"Atenção: Ø sobre isolação ({d_iso} mm) está fora do range nominal "
                f"({row['OD Min (mm)']}–{row['OD Max (mm)']} mm), mas entra considerando a tolerância (±{tolerance} mm). "
                "Confirme o encaixe real com o cliente."
            )

    # ── terminal suggestion ───────────────────────────────────────────────
    st.header("Seleção de terminal (lug)")
    conn_type_ui = st.selectbox(
        "Tipo de Terminal (Compressão ou Torquimétrico):",
        ["Compressão", "Torquimétrico"]
    )
    type_map = {"Compressão": "compression", "Torquimétrico": "shear-bolt"}
    type_arg = type_map[conn_type_ui]

    df_conn = pd.read_csv("mapping_tables/connector_selection_table.csv")
    material = None
    if type_arg == "compression":
        material = st.selectbox("Material do terminal:", sorted(df_conn["Material"].dropna().unique()))

    from tools.connector_matcher import suggest_connector
    conn_df = suggest_connector(float(s_mm2), type_arg, material)

    if conn_df.empty:
        st.error("Nenhum terminal/lug encontrado para esses parâmetros.")
    else:
        st.subheader("Lugs compatíveis")
        st.table(conn_df)

# Fim do app
