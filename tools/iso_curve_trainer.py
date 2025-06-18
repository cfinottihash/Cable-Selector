# tools/iso_curve_trainer.py
import pandas as pd
import numpy as np

CSV_RAW   = "mapping_tables/bitola_to_od.csv"
CSV_CURVE = "mapping_tables/iso_curves_poly.csv"
N_MIN     = 8

def load_data():
    df = pd.read_csv(CSV_RAW).dropna(subset=["S_mm2","OD_iso_mm"])
    df["rootS"] = np.sqrt(df["S_mm2"])
    return df

def fit_group(df):
    x = df["rootS"].values
    y = df["OD_iso_mm"].values
    coeffs = np.polyfit(x, y, 2)
    y_hat  = np.polyval(coeffs, x)
    r2 = 1 - ((y - y_hat)**2).sum() / ((y - y.mean())**2).sum()
    return (*coeffs, r2)

def train():
    df = load_data()
    rows = []
    for v, grp in df.groupby("Voltage"):
        if len(grp) >= N_MIN:
            a2, a1, a0, r2 = fit_group(grp)
        else:
            # fallback to linear if too few points
            a1, a0 = np.polyfit(grp["rootS"], grp["OD_iso_mm"], 1)
            a2, r2 = 0.0, np.nan
        rows.append({"Voltage": v, "a2": a2, "a1": a1, "a0": a0, "R2": r2})
    pd.DataFrame(rows).to_csv(CSV_CURVE, index=False)
    print(f"Wrote {CSV_CURVE}")

if __name__=="__main__":
    train()