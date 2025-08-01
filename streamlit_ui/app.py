# streamlit_ui/app.py
import sys, os, re
from pathlib import Path
import pandas as pd
import streamlit as st

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))
from tools.iso_estimator     import by_bitola, tol
from tools.connector_matcher import suggest_connector

# ── DATA ────────────────────────────────────────────
df_cable = (
    pd.read_csv("mapping_tables/bitola_to_od.csv",
                names=["Cable Voltage","S_mm2","Brand","Cable",
                       "OD_iso_mm","D_cond_mm","T_iso_mm"],
                header=0)
      .rename(columns=str.strip)
)
df_csto = pd.read_csv("mapping_tables/csto_selection_table.csv").rename(columns=str.strip)
df_csti = pd.read_csv("mapping_tables/csti_selection_table.csv").rename(columns=str.strip)  # <- NOVO
df_conn = pd.read_csv("mapping_tables/connector_selection_table.csv").rename(columns=str.strip)

TENS_MAP = {"8.7/15 kV":"15 kV", "12/20 kV":"25 kV", "15/25 kV":"25 kV", "20/35 kV":"35 kV"}

def _order_kv(t:str) -> float:
    m = re.match(r"([\d.]+)", t); return float(m.group(1)) if m else 1e9

CABLE_VOLTAGES = sorted(df_cable["Cable Voltage"].unique(), key=_order_kv)
BRANDS         = sorted(df_cable["Brand"].dropna().unique())
LUG_MATERIALS  = sorted(df_conn["Material"].dropna().unique())

# ── LAYOUT ──────────────────────────────────────────
st.set_page_config("CST Selector", layout="centered")
logo = Path(__file__).parent / "assets" / "logo-chardon.png"
if logo.exists(): st.image(str(logo), width=200)
st.title("Protótipo — Seletor de Cold-Shrink Termination")
st.session_state.setdefault("searched", False)
# ── 1. ENTRADAS CABO ───────────────────────────────
st.header("Seleção do cabo")

env_choice = st.radio("Aplicação da terminação:",
                      ("Externa (Outdoor)", "Interna (Indoor)"),
                      horizontal=True)

know_iso = st.radio("Você já sabe o Ø sobre isolação do cabo?",
                    ("Não, preciso estimar pela bitola",
                     "Sim, digitar valor real"))

cabo_tensao = st.selectbox("Classe de tensão do cabo:", CABLE_VOLTAGES)
tensao_term = TENS_MAP[cabo_tensao]
tolerance   = tol(tensao_term)

# Branch A – usuário digita Ø manualmente
if know_iso.startswith("Sim"):
    d_iso = st.number_input("Ø sobre isolação (mm)", min_value=0.0, step=0.1)
    # ainda precisamos da seção para o lug
    s_mm2 = st.selectbox("Seção nominal (mm²) para escolher lug:",
                         sorted(df_cable["S_mm2"].astype(float).unique()))
    st.info(f"Ø sobre isolação informado: **{d_iso:.1f} mm**")
    used_real = True

# Branch B – estimamos pela bitola + (marca opcional)
else:
    cabo_marca = st.selectbox("Marca do cabo (opcional):", ["Todas"] + BRANDS)

    filtro = df_cable[df_cable["Cable Voltage"] == cabo_tensao]
    if cabo_marca != "Todas":
        filtro = filtro[filtro["Brand"] == cabo_marca]

    bitolas = sorted(filtro["S_mm2"].astype(float).unique())
    s_mm2   = st.selectbox("Seção nominal (mm²):", bitolas)

    linha = filtro[filtro["S_mm2"].astype(float) == float(s_mm2)]
    if not linha.empty:
        d_iso      = linha.iloc[0]["OD_iso_mm"]
        d_cond     = linha.iloc[0]["D_cond_mm"]
        t_iso_real = linha.iloc[0]["T_iso_mm"]
        st.info(f"Ø sobre isolação ESTIMADA: **{d_iso:.1f} mm ± {tolerance} mm**")
        st.caption(f"Ø condutor: {d_cond} mm | Espessura isolação: {t_iso_real} mm")
        used_real = True
    else:
        d_iso = by_bitola(tensao_term, float(s_mm2))
        st.warning(f"Ø sobre isolação ESTIMADA: **{d_iso:.1f} mm ± {tolerance} mm**")
        st.caption("Valor gerado pela curva estatística – confirme no campo.")
        used_real = False

st.markdown("<small style='color:#bbb'>⚠️ Sempre confirme com o cliente os dados reais do cabo!</small>",
            unsafe_allow_html=True)

# ── 2. BUSCA DE TERMINAÇÃO ─────────────────────────
if st.button("Buscar Terminação"):
    st.session_state.searched = True

# só entra aqui depois de clicar em "Buscar Terminação"
if st.session_state.searched:
    df_term = df_csto if env_choice.startswith("Externa") else df_csti
    family  = "CSTO"  if env_choice.startswith("Externa") else "CSTI"

    matches = df_term[
        (df_term["Voltage Class"] == tensao_term) &
        (df_term["OD Min (mm)"] <= d_iso + tolerance) &
        (df_term["OD Max (mm)"] >= d_iso - tolerance)
    ]

    if matches.empty:
        st.error(f"Nenhuma terminação {family} encontrada.")
        st.stop()

    # Resultado dentro de um expander para não inungdar a tela
    with st.expander(f"Ver terminações {family} compatíveis"):
        st.success(f"Terminação(s) {family} compatível(is):")
        st.table(
            matches.assign(**{
                "OD Min (mm)": matches["OD Min (mm)"].round(1),
                "OD Max (mm)": matches["OD Max (mm)"].round(1)
            })[
                ["Part Number","OD Min (mm)","OD Max (mm)"]
            ]
        )

        # alertas de tolerância
        for _, r in matches.iterrows():
            if not (r["OD Min (mm)"] <= d_iso <= r["OD Max (mm)"]):
                st.warning(
                    f"Ø {d_iso:.1f} mm fora do nominal "
                    f"({r['OD Min (mm)']}–{r['OD Max (mm)']} mm), "
                    f"aceito pela tolerância ±{tolerance} mm."
                )

    # ── 3. LUG SUGGESTION ─────────────────────────────
    with st.expander("Sugestão de terminais (lugs)"):
        st.header("Seleção de terminal (lug)")
        conn_ui = st.selectbox("Tipo de Terminal:", ["Compressão","Torquimétrico"])
        kind    = "compression" if conn_ui == "Compressão" else "shear-bolt"

        mat = st.selectbox("Material do terminal:", LUG_MATERIALS) if kind=="compression" else None

        conn_df = suggest_connector(int(float(s_mm2)), kind, mat)
        if conn_df.empty:
            st.error("Nenhum terminal/lug encontrado.")
        else:
            st.table(conn_df)