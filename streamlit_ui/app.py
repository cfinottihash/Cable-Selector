# streamlit_ui/app.py
import sys, os, re
from pathlib import Path

import pandas as pd
import streamlit as st

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))
from tools.iso_estimator import by_bitola, tol
from tools.connector_matcher import suggest_connector

# ───────────────────── data ──────────────────────
df_cable = (
    pd.read_csv(
        "mapping_tables/bitola_to_od.csv",
        names=[
            "Cable Voltage", "S_mm2", "Brand", "Cable",
            "OD_iso_mm", "D_cond_mm", "T_iso_mm"
        ],
        header=0
    ).rename(columns=str.strip)
)
df_csto  = pd.read_csv("mapping_tables/csto_selection_table.csv").rename(columns=str.strip)
df_conn  = pd.read_csv("mapping_tables/connector_selection_table.csv").rename(columns=str.strip)

TENS_MAP = {
    "8.7/15 kV": "15 kV",
    "12/20 kV": "25 kV",
    "15/25 kV": "25 kV",
    "20/35 kV": "35 kV",
}

def _order_kv(txt:str) -> float:
    m = re.match(r"([\d.]+)", txt)
    return float(m.group(1)) if m else float("inf")

CABLE_VOLTAGES = sorted(df_cable["Cable Voltage"].unique(), key=_order_kv)
BRANDS         = sorted(df_cable["Brand"].dropna().unique())

# ───────────────────── layout ─────────────────────
st.set_page_config(page_title="CSTO Selector", layout="centered")
logo = Path(__file__).parent / "assets" / "logo-chardon.png"
if logo.exists():
    st.image(str(logo), width=200)
st.title("Protótipo — Seletor de Cold-Shrink Termination")

# ───────────────────── inputs ─────────────────────
st.header("Seleção do cabo")

know_iso = st.radio(
    "Você já sabe o Ø sobre isolação do cabo?",
    ("Não, preciso estimar pela bitola", "Sim, digitar valor real")
)

# ➊ escolha da classe de tensão do cabo (sempre necessária)
cabo_tensao = st.selectbox("Classe de tensão do cabo:", CABLE_VOLTAGES)
tensao_term = TENS_MAP[cabo_tensao]           # tensão que define a CSTO
tolerance   = tol(tensao_term)

if know_iso.startswith("Sim"):
    # caminho A ─ usuário digita Ø
    d_iso  = st.number_input("Ø sobre isolação (mm)", min_value=0.0, step=0.1)
    s_mm2  = st.number_input("Seção nominal (mm²) para escolher lug:", min_value=1.0, step=1.0)
    st.info(f"Ø sobre isolação informado: **{d_iso:.1f} mm**")
    used_real = True
else:
    # caminho B ─ estimar a partir da bitola
    cabo_marca = st.selectbox("Marca do cabo (opcional):", ["Todas"] + BRANDS)
    filtro = df_cable[df_cable["Cable Voltage"] == cabo_tensao]
    if cabo_marca != "Todas":
        filtro = filtro[filtro["Brand"] == cabo_marca]

    bitolas = sorted(filtro["S_mm2"].astype(float).unique())
    s_mm2   = st.selectbox("Seção nominal (mm²):", bitolas)

    row = filtro[filtro["S_mm2"].astype(float) == float(s_mm2)]
    if not row.empty:                        # dado real de catálogo
        d_iso      = float(row.iloc[0]["OD_iso_mm"])
        d_cond     = float(row.iloc[0]["D_cond_mm"])
        t_iso_real = float(row.iloc[0]["T_iso_mm"])
        st.info(f"Ø sobre isolação REAL: **{d_iso:.1f} mm ± {tolerance} mm**")
        st.caption(f"Ø condutor: {d_cond} mm | Espessura isolação: {t_iso_real} mm")
        used_real  = True
    else:                                   # fallback estatístico
        d_iso     = by_bitola(tensao_term, float(s_mm2))
        st.warning(
            f"Ø sobre isolação ESTIMADA: **{d_iso:.1f} mm ± {tolerance} mm**"
        )
        st.caption(
            "Não há dado exato para essa bitola/marca — valor gerado pela curva estatística."
        )
        used_real = False

# alerta permanente
st.markdown(
    "<small style='color:#bbb'>⚠️ Sempre confirme com o cliente os dados reais do cabo antes de concluir a compra.</small>",
    unsafe_allow_html=True
)

# ───────────────────── busca CSTO ─────────────────────
if st.button("Buscar Terminação"):
    match = df_csto[
        (df_csto["Voltage Class"] == tensao_term) &
        (df_csto["OD Min (mm)"] <= d_iso + tolerance) &
        (df_csto["OD Max (mm)"] >= d_iso - tolerance)
    ]

    if match.empty:
        st.error("Nenhuma terminação encontrada.")
        st.stop()

    st.success("Terminação(s) compatível(is):")
    st.table(match[["Part Number", "OD Min (mm)", "OD Max (mm)"]])

    # avisa se entrou só por tolerância
    for _, row in match.iterrows():
        if not (row["OD Min (mm)"] <= d_iso <= row["OD Max (mm)"]):
            st.warning(
                f"Ø {d_iso:.1f} mm fora do range nominal "
                f"({row['OD Min (mm)']}–{row['OD Max (mm)']} mm), "
                f"mas aceito pela tolerância (±{tolerance} mm). Confirme encaixe real!"
            )

    # ───────────── LUG / CONNECTOR SUGGESTION ─────────────
    st.header("Seleção de terminal (lug)")
    conn_ui = st.selectbox("Tipo de Terminal:", ["Compressão", "Torquimétrico"])
    kind    = "compression" if conn_ui == "Compressão" else "shear-bolt"

    mat = None
    if kind == "compression":
        mat = st.selectbox("Material do terminal:", sorted(df_conn["Material"].dropna().unique()))

    conn_df = suggest_connector(int(s_mm2), kind, mat)
    if conn_df.empty:
        st.error("Nenhum terminal/lug encontrado para esses parâmetros.")
    else:
        st.subheader("Lugs compatíveis")
        st.table(conn_df)

# ───────────────────── end ─────────────────────
