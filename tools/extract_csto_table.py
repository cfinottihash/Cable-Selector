import pdfplumber, pandas as pd, pathlib, re

PDF_PATH = pathlib.Path("data/152535CSTO_05072025_final_compressed-2_compres-1.pdf")
OUT_CSV  = pathlib.Path("mapping_tables/csto_selection_table.csv")

rows = []
with pdfplumber.open(PDF_PATH) as pdf:
    for page in pdf.pages:
        text = page.extract_text(x_tolerance=3, y_tolerance=3)
        if not text or "Cable Insulation" not in text:
            continue                # pula páginas sem a tabela
        for line in text.splitlines():
            # Ex.: "25-CSTO-B ... 20.4-35.4"
            if re.search(r"\d{2}-CSTO-[ABC]", line):
                part   = re.search(r"\d{2}-CSTO-[ABC]", line).group(0)
                volts  = part.split("-")[0] + " kV"
                od_rng = re.search(r"\d+\.\d+\s*-\s*\d+\.\d+", line)
                if od_rng:
                    od_min, od_max = od_rng.group(0).replace(" ", "").split("-")
                    rows.append([volts, part, od_min, od_max])

df = (pd.DataFrame(rows,
      columns=["Voltage Class", "Part Number", "OD Min (mm)", "OD Max (mm)"])
      .drop_duplicates()
      .sort_values(["Voltage Class", "Part Number"]))

OUT_CSV.parent.mkdir(parents=True, exist_ok=True)
df.to_csv(OUT_CSV, index=False)

print(f"✅  Extracted rows: {len(df)}")
print(df)
