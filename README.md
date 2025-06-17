## Versão atual: v0.3

## Run locally / Codespaces
```bash
pip install -r requirements.txt
streamlit run streamlit_ui/app.py

# Medium Voltage Cable Accessory Selector

# A smart, data-driven tool to help technical and commercial teams select the correct medium-voltage cable accessories based on cable characteristics.

##  Project Overview

#The selector matches a cable to the right accessory using only:
#"1. Voltage class
#2. Either the measured insulation O.D (Øiso) or the conductor cross-section (mm²). The app then estimates Øiso automatically.

#It currently outputs:
 - Cold-shrink termiations (CSTO)
 - Connectors (terminal lugs): Shear-bolt lugs, compression lugs (filtered by material and conductor size)

#Future releases will expand to loadbreak and deadbreak elbows.

## How the app estimates insulation diameter
#The "rule of thumb" is guaranteed by the standards themselves, so no brand tables are needed.

| Step | Formula / value | Standard reference |
|------|-----------------|--------------------|
| **Conductor diameter** | `D_cond = sqrt(4 S / (π · 0.90))`  (class-2 compact conductor, ρ ≈ 0.90) | IEC 60228 |
| **Insulation thickness** | 8.7/15 kV → **3.0 mm**  •  12/20 kV → **4.0 mm**  •  15/25 kV → **5.5 mm**  •  20/35 kV → **7.5 mm** | IEC 60502-2 §6.2 (Tables 6–7) |
| **Nominal Ø_iso** | `Ø_iso = D_cond + 2 × t_iso` | Geometry |
| **Tolerance shown in app** | ± 0.8 mm (≤ 25 kV)  •  ± 1.6 mm (35 kV) | IEC 60502-2 §17.5.2 (−10 % / +15 % on t_iso) |

#Example – 70 mm², 15/25 kV:
#D<sub>cond</sub> ≈ 11.2 mm → Ø<sub>iso</sub> ≈ 11.2 + 2·5.5 = 22.2 mm
#Displayed in the app: 22.2 mm ± 1.2 mm
#Any IEC-compliant cable of that size will fall inside that band, ensuring the correct termination window.
##  Why this project matters
#Choosing accessories by eye is risky: overlapping specs, assorted part numbers, missing O.D. data. The selector can:
# - Turn static catalogs into searcheable tables
# - Apply IEC logic to fill data gaps
# - Narrow choices to only what actually fits (fast, repeatable, mistake-proof)
# Pull requests and issue reports are welcome.