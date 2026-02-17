#!/usr/bin/env python3
"""
IRS Form 990 / ProPublica - Institutional Affiliation Extractor (Evidence Layer 2)
Maps nonprofit boards, officers, and grant networks.
"""
import json
import time
from pathlib import Path

import requests

DATA_DIR = Path(__file__).parent.parent
API_BASE = "https://projects.propublica.org/nonprofits/api/v2"


def search_organizations(query: str, state: str | None = None) -> list[dict]:
    """Search nonprofits by name."""
    url = f"{API_BASE}/search.json"
    params = {"q": query}
    if state:
        params["state[id]"] = state
    try:
        time.sleep(0.5)
        r = requests.get(url, params=params, timeout=30)
        r.raise_for_status()
        data = r.json()
        return data.get("organizations", [])
    except Exception as e:
        print(f"ProPublica search failed: {e}")
        return []


def get_organization(ein: int) -> dict | None:
    """Get full org details including filings."""
    url = f"{API_BASE}/organizations/{ein}.json"
    try:
        time.sleep(0.5)
        r = requests.get(url, timeout=30)
        r.raise_for_status()
        return r.json()
    except Exception as e:
        print(f"Org fetch failed for EIN {ein}: {e}")
        return None


def extract_institutional_affiliations(queries: list[str] | None = None) -> list[dict]:
    """Build institutional affiliation nodes from key policy/foundation orgs."""
    if queries is None:
        queries = [
            "Council on Foreign Relations",
            "Rockefeller Foundation",
            "Rockefeller Brothers Fund",
            "Ford Foundation",
            "Carnegie Corporation",
            "Brookings",
            "Heritage Foundation",
            "American Enterprise Institute",
            "Trilateral Commission",
            "Bilderberg",
        ]

    affiliations = []
    seen = set()

    for q in queries:
        orgs = search_organizations(q)
        for org in orgs[:5]:  # Top 5 per query
            ein = org.get("ein")
            name = org.get("name", "")
            city = org.get("city", "")
            state = org.get("state", "")
            if (ein, name) in seen:
                continue
            seen.add((ein, name))

            details = get_organization(ein)
            if details:
                o = details.get("organization", {})
                filings = details.get("filings_with_data", [])
                latest = filings[0] if filings else {}
                affiliations.append({
                    "org_name": name,
                    "ein": ein,
                    "city": city,
                    "state": state,
                    "assets": o.get("asset_amount"),
                    "tax_year": latest.get("tax_prd_yr"),
                    "source": "IRS Form 990",
                    "evidence_layer": "institutional_affiliation",
                })
            print(f"  {name}: EIN {ein}")

    return affiliations


def extract_org_network() -> list[dict]:
    """Get org-to-org structure for cross-reference (grants, related orgs)."""
    # ProPublica org data has filings - grant data would need Form 990 XML parsing
    # For now return org list for node creation
    return extract_institutional_affiliations()


if __name__ == "__main__":
    print("Form 990 / ProPublica - Institutional Affiliation extraction")
    affils = extract_institutional_affiliations()
    out = DATA_DIR / "institutional_affiliations_990.csv"
    if affils:
        import csv
        with open(out, "w", newline="", encoding="utf-8") as f:
            w = csv.DictWriter(f, fieldnames=["org_name", "ein", "city", "state", "assets", "tax_year", "source", "evidence_layer"])
            w.writeheader()
            w.writerows(affils)
        print(f"Saved {len(affils)} orgs to {out}")
