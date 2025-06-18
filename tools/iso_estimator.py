import math
import pandas as pd

# ── IEC-nominal insulation thickness by user label (mm) ──────────────
INS_T = {
    "15 kV": 3.0,
    "25 kV": 4.0,
    "35 kV": 5.5
}

# reinforced override for “35 kV” wind-cables
INS_T_REINF = {
    "35 kV": 8.8
}

# ── IEC tolerance for display (± mm) ───────────────────────────────────
TOL = {
    "15 kV": 0.8,
    "25 kV": 1.0,
    "35 kV": 1.2
}

# ── load pre-trained quadratic coefficients (by raw label) ─────────────
_CURVE_CSV = "mapping_tables/iso_curves_poly.csv"
try:
    _CURVES = (
        pd.read_csv(_CURVE_CSV)
          .set_index("Voltage")[["a2","a1","a0"]]
    )
except Exception as e:
    raise RuntimeError(f"Could not load curve CSV {_CURVE_CSV}: {e}")

def by_bitola(voltage: str, s_mm2: float, *, reinforced: bool=False) -> float:
    # 1) pega coeficientes da curva
    a2, a1, a0 = _CURVES.loc[voltage, ["a2","a1","a0"]]

    # 2) previsão quadrática em √S
    rootS = math.sqrt(s_mm2)
    pred = a2 * rootS**2 + a1 * rootS + a0

    # 3) ajuste “reinforced” se aplicável
    if reinforced and voltage in INS_T_REINF:
        extra = (INS_T_REINF[voltage] - INS_T[voltage]) * 2
        pred += extra

    return round(pred, 1)

def tol(voltage: str) -> float:
    """Return the ± tolerance (mm) to display alongside the estimate."""
    return TOL[voltage]

# ── legacy: estimate from outer diameter if needed ────────────────────────
def by_outer(voltage: str, d_ext: float) -> float:
    from tools.iso_estimator import OFFSET
    v = _norm(voltage)
    return round(d_ext - OFFSET[v], 1)
