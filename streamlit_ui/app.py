# streamlit_ui/app.py
import sys, os, re
from pathlib import Path
import pandas as pd
import streamlit as st

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))
from tools.iso_estimator     import by_bitola, tol
from tools.connector_matcher import suggest_connector

# ───────────────────── data ──────────────────────
df_cable = (
    pd.read_csv(
        "mapping_tables/bitola_to_od.csv",
        names=["Cable Voltage", "S_mm2", "Brand", "Cable",
               "OD_iso_mm", "D_cond_mm", "T_iso_mm"],
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

def _order_kv(txt: str) -> float:
    m = re.match(r"([\d.]+)", txt)
    return float(m.group(1)) if m else float("inf")

CABLE_VOLTAGES = sorted(df_cable["Cable Voltage"].unique(), key=_order_kv)
BRANDS         = sorted(df_cable["Brand"].dropna().unique())
BITOLAS_ALL    = sorted(df_cable["S_mm2"].astype(float).unique())   # lista única

# ───────────────────── layout ─────────────────────
st.set_page_config(page_title="CSTO Selector", layout="centered")
logo = Path(__file__).parent / "assets" / "logo-chardon.png"
if logo.exists():
    st.image(str(logo), width=200)
st.title("Protótipo — Seletor de Cold-Shrink Termination")

# ───────────────────── inputs ─────────────────────
st.header("Passo 1: Seleção do cabo")

know_iso = st.radio(
    "Você já sabe o Ø sobre isolação do cabo?",
    ("Não, preciso estimar pela bitola", "Sim, digitar valor real")
)

# classe de tensão do cabo (sempre)
cabo_tensao = st.selectbox("Classe de tensão do cabo:", CABLE_VOLTAGES)
tensao_term = TENS_MAP[cabo_tensao]
tolerance   = tol(tensao_term)

# --------------------------------------------------
if know_iso.startswith("Sim"):
    # caminho A – usuário sabe Ø
    d_iso = st.number_input("Ø sobre isolação (mm)", min_value=0.0, step=0.1, key="iso_real")
    s_mm2 = st.selectbox(
        "Seção nominal (mm²) para escolher lug:",
        BITOLAS_ALL,
        key="bitola_lug_manual"
    )
    st.info(f"Ø sobre isolação informado: **{d_iso:.1f} mm**")
    used_real = True
else:
    # caminho B – estimar Ø a partir da bitola e marca
    cabo_marca = st.selectbox("Marca do cabo (opcional):", ["Todas"] + BRANDS, key="marca")
    filtro = df_cable[df_cable["Cable Voltage"] == cabo_tensao]
    if cabo_marca != "Todas":
        filtro = filtro[filtro["Brand"] == cabo_marca]

    bitolas = sorted(filtro["S_mm2"].astype(float).unique())
    s_mm2   = st.selectbox("Seção nominal (mm²):", bitolas, key="bitola_estim")

    row = filtro[filtro["S_mm2"].astype(float) == float(s_mm2)]
    if not row.empty:                               # valor exato do catálogo
        d_iso   = float(row.iloc[0]["OD_iso_mm"])
        d_cond  = float(row.iloc[0]["D_cond_mm"])
        t_iso_r = float(row.iloc[0]["T_iso_mm"])
        st.info(f"Ø sobre isolação ESTIMADA: **{d_iso:.1f} mm ± {tolerance} mm**")
        st.caption(f"Ø condutor: {d_cond} mm | Espessura isolação: {t_iso_r} mm")
        used_real = True
    else:                                           # predição estatística
        d_iso = by_bitola(tensao_term, float(s_mm2))
        st.warning(f"Ø sobre isolação ESTIMADA: **{d_iso:.1f} mm ± {tolerance} mm**")
        st.caption("Sem dado exato: estimado pela curva estatística.")
        used_real = False

st.markdown(
    "<small style='color:#bbb'>⚠️⚠️⚠️ Sempre confirme com o cliente os dados reais do cabo!⚠️⚠️⚠️</small>",
    unsafe_allow_html=True
)

# ───────────────────── lógica de busca ─────────────────────
if "search_done" not in st.session_state:
    st.session_state.search_done = False

if st.button("Passo 2: Clique aqui para Buscar Terminações Compatíveis"):
    st.session_state.search_done = True

if st.session_state.search_done:
    match = df_csto[
        (df_csto["Voltage Class"] == tensao_term) &
        (df_csto["OD Min (mm)"] <= d_iso + tolerance) &
        (df_csto["OD Max (mm)"] >= d_iso - tolerance)
    ]

    if match.empty:
        st.error("Nenhuma terminação encontrada.")
    else:
        st.success("Terminação(s) compatível(is):")
        st.table(match[["Part Number", "OD Min (mm)", "OD Max (mm)"]])

        for _, row in match.iterrows():
            if not (row["OD Min (mm)"] <= d_iso <= row["OD Max (mm)"]):
                st.warning(
                    f"Ø {d_iso:.1f} mm fora do range nominal "
                    f"({row['OD Min (mm)']}–{row['OD Max (mm)']} mm), "
                    f"mas aceito pela tolerância (±{tolerance} mm)."
                )

        # ───── sugestão de lug SEM reiniciar processo ─────
        st.header("Passo 3: Seleção de terminal (lug)")
        conn_ui = st.selectbox("Selecione o Tipo de Terminal:", ["Compressão", "Torquimétrico"], key="tipo_lug")
        kind    = "compression" if conn_ui == "Compressão" else "shear-bolt"

        mat = None
        if kind == "compression":
            mat = st.selectbox(
                "Selecione o Material do terminal:",
                sorted(df_conn["Material"].dropna().unique()),
                key="material_lug"
            )

        conn_df = suggest_connector(int(float(s_mm2)), kind, mat)
        if conn_df.empty:
            st.error("Nenhum terminal/lug encontrado para esses parâmetros.")
        else:
            st.subheader("Lugs compatíveis")
            st.table(conn_df)
