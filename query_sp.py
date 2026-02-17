#!/usr/bin/env python3
"""Query S&P Capital IQ / DUNL.org API for company relationships."""
import csv
import requests
from pathlib import Path

# DUNL.org - verify actual API base URL from their docs
BASE_URL = "https://api.dunl.org/v1"  # May need adjustment


def search_companies(name: str) -> list[dict]:
    """Search for companies by name."""
    url = f"{BASE_URL}/companies/search"
    try:
        response = requests.get(url, params={"name": name}, timeout=10)
        response.raise_for_status()
        data = response.json()
        return data if isinstance(data, list) else data.get("results", [])
    except Exception as e:
        print(f"Search error for '{name}': {e}")
        return []


def get_company_relationships(company_id: str) -> list[dict]:
    """Get parent/subsidiary relationships."""
    url = f"{BASE_URL}/companies/{company_id}/relationships"
    try:
        response = requests.get(url, timeout=10)
        response.raise_for_status()
        return response.json()
    except Exception as e:
        print(f"Relationships error for {company_id}: {e}")
        return []


def main():
    # Example: Chase Manhattan relationships
    data_dir = Path(__file__).parent / "data"
    data_dir.mkdir(parents=True, exist_ok=True)

    companies = search_companies("Chase Manhattan")
    if not companies:
        print("No results. Check DUNL.org API docs for correct endpoint.")
        return

    chase_id = companies[0].get("identifier", companies[0].get("id", ""))
    relationships = get_company_relationships(chase_id)

    output_path = data_dir / "chase_relationships.csv"
    with open(output_path, "w", newline="", encoding="utf-8") as f:
        writer = csv.writer(f)
        writer.writerow(["type", "company", "lei"])
        for rel in relationships:
            writer.writerow([
                rel.get("type", ""),
                rel.get("name", ""),
                rel.get("lei", ""),
            ])

    print(f"Saved {len(relationships)} relationships to {output_path}")


if __name__ == "__main__":
    main()
