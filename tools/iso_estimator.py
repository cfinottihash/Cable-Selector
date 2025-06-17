# tools/iso_estimator.py
import math

INS_T = {"8.7/15": 3.0, "12/20": 4.0, "15/25": 5.5, "20/35": 7.5}
# valor reforçado para cabos eólicos / especiais
INS_T_REINF = {"20/35": 8.8}          # só muda esta classe

TOL = {"8.7/15": 0.8, "12/20": 1.0, "15/25": 1.2, "20/35": 1.6}

ALIASES = {"15 kV": "8.7/15", "25 kV": "15/25", "35 kV": "20/35"}
_norm = lambda v: ALIASES.get(v, v)

def by_bitola(voltage: str, s_mm2: float, *, reinforced=False) -> float:
    """Estima Ø_iso; se reinforced=True usa isolação reforçada (ex.: cabos Wind)."""
    v = _norm(voltage)
    t_iso = INS_T_REINF.get(v, INS_T[v]) if reinforced else INS_T[v]
    d_cond = math.sqrt(4 * s_mm2 / (math.pi * 0.90))
    return round(d_cond + 2 * t_iso, 1)

def tol(voltage: str) -> float:
    return TOL[_norm(voltage)]


# ── opcional: vou manter se um mdia precisar usar─────────────────────
def by_outer(voltage: str, d_ext: float) -> float:
    v = _norm(voltage)
    return round(d_ext - OFFSET[v], 1)
