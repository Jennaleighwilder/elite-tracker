# Power Structure Data

Automated extraction from public sources for the Secret Societies Network Tracker.

## Quick Start

```bash
# From project root
pip install -r ../requirements.txt
python extract_all.py
python create_network_viz.py   # Exports network_d3.json for D3.js
```

## Output Files

| File | Source | Records |
|------|--------|---------|
| `skull_bones_complete.csv` | Wikipedia | 340+ |
| `bilderberg_attendees.csv` | Wikipedia (EN + DE) | 1,700+ |
| `trilateral_members.csv` | Rockefeller Archive + known founders | 8 |
| `cfr_members_1921_1951.csv` | Princeton finding aid | (if PDF parses) |
| `directors_3plus_boards.csv` | 1978 Senate Report | (manual PDF required) |
| `cross_reference.csv` | Overlaps across sources | 5+ |
| `network_edges.csv` | Skull and Bones cohort links | 370+ |
| `network_d3.json` | D3.js-ready graph | nodes + links |

## Manual Downloads Required

1. **1978 Senate Report** – HathiTrust blocks automated download.  
   [Download manually](http://babel.hathitrust.org/cgi/pt?id=mdp.39015077914680) → Save as `senate_report_1978.pdf`

2. **Bohemian Grove** – USC archive requires email request.  
   See `bohemian_grove_access.txt` for contact info.

## Failed URLs (Logged)

- HathiTrust PDF (403)
- USC Archives (403)

## DUNL.org (S&P Data Unlocked)

Portal and API docs downloaded. Sample data may be HTML redirect. Check `dunl_portal.html` and `dunl_api_docs.html` for current endpoints.
