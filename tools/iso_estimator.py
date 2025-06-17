# tools/iso_estimator.py
import math

# espessura nominal da isolação (mm)
INS_T = {"8.7/15": 3.0, "12/20": 4.0, "15/25": 5.5, "20/35": 7.5}

# variação ≥ isolação ≤ capa (para o caso Ø externo — não usamos mais)
OFFSET = {"8.7/15": 9.0, "12/20": 9.5, "15/25": 11.0, "20/35": 12.0}

# tolerância total do Ø de isolação (± mm)
TOL = {"8.7/15": 0.8, "12/20": 1.0, "15/25": 1.2, "20/35": 1.6}

# alias do selectbox (“15 kV”, “25 kV”… → código IEC)
ALIASES = {"15 kV": "8.7/15", "25 kV": "15/25", "35 kV": "20/35"}
_norm = lambda v: ALIASES.get(v, v)

# ── funções públicas ──────────────────────────────────────────────────────
def by_bitola(voltage: str, s_mm2: float) -> float:
    """Estimativa de Ø sobre isolação a partir da bitola."""
    v = _norm(voltage)
    d_cond = math.sqrt(4 * s_mm2 / (math.pi * 0.90))      # condutor compacto
    return round(d_cond + 2 * INS_T[v], 1)

def tol(voltage: str) -> float:
    """Devolve a tolerância ± em mm para a tensão escolhida."""
    return TOL[_norm(voltage)]

# ── opcional: vou manter se um mdia precisar usar─────────────────────
def by_outer(voltage: str, d_ext: float) -> float:
    v = _norm(voltage)
    return round(d_ext - OFFSET[v], 1)
