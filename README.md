# Elite Network Tracker / Power Structure Data

Cross-reference people across elite organizations (Skull and Bones, Bilderberg, CFR, Trilateral Commission) and corporate board positions from the 1978 Senate Report.

## Quick Start (Full Pipeline)

```bash
# 1. Install dependencies
pip install -r requirements.txt

# 2. Run the complete extraction pipeline (downloads + extracts all public sources)
python3 power_structure_data/extract_all.py

# 3. Create network visualization (D3-ready JSON + optional PNG)
python3 power_structure_data/create_network_viz.py
```

## Alternative: Manual Scripts

```bash
# Download data (HTML files)
./download_data.sh

# Run individual parsers
python3 parse_skull_bones.py
python3 parse_bilderberg.py

# (Optional) Add Senate Report PDF to data/senate_report_1978.pdf, then:
python3 extract_senate_report.py

# Cross-reference across all datasets
python3 cross_reference.py
```

## Data Sources

| Dataset | Source | Status |
|---------|--------|--------|
| **Skull and Bones** | Wikipedia | ✅ Auto-downloaded |
| **Bilderberg** | Wikipedia | ✅ Auto-downloaded |
| **1978 Senate Report** | HathiTrust | Manual: [Download PDF](http://babel.hathitrust.org/cgi/pt?id=mdp.39015077914680) → save as `data/senate_report_1978.pdf` |
| **CFR Finding Aid** | Princeton | ✅ Auto-downloaded |
| **Trilateral** | Rockefeller Archive | ✅ Finding aid downloaded |

## Output Files

| File | Content |
|------|---------|
| `power_structure_data/skull_bones_complete.csv` | Skull and Bones roster (340+ members) |
| `power_structure_data/bilderberg_attendees.csv` | Bilderberg participants (1,700+) |
| `power_structure_data/trilateral_members.csv` | Trilateral founding members |
| `power_structure_data/directors_3plus_boards.csv` | Senate Report directors (manual PDF) |
| `power_structure_data/cross_reference.csv` | People in 2+ sources |
| `power_structure_data/network_edges.csv` | Skull and Bones cohort links |
| `power_structure_data/network_d3.json` | D3.js-ready graph for visualization |

## Scripts

- **parse_skull_bones.py** – Parse Wikipedia member list
- **parse_bilderberg.py** – Parse Wikipedia participant tables
- **extract_senate_report.py** – Extract directors from PDF (pages 236–278)
- **cross_reference.py** – Find overlaps across datasets
- **query_sp.py** – Query DUNL.org API for company relationships

## Manual Downloads

1. **Senate Report 1978**: http://babel.hathitrust.org/cgi/pt?id=mdp.39015077914680  
   → Click Download → Full PDF → save as `data/senate_report_1978.pdf`

2. **DUNL.org**: https://DUNL.org/downloads/ for bulk company data
