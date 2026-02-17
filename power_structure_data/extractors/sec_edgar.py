#!/usr/bin/env python3
"""
SEC EDGAR - Board Interlock Extractor (Evidence Layer 1)
Fetches DEF 14A proxy statements for director lists.
SEC requires User-Agent with contact info - use your email.
"""
import json
import re
import time
from pathlib import Path

import requests

# SEC requires a descriptive User-Agent - replace with your email
HEADERS = {
    "User-Agent": "PowerStructureResearch/1.0 (research@example.com)",
    "Accept": "application/json",
    "Accept-Encoding": "gzip, deflate",
    "Host": "www.sec.gov",
}

DATA_DIR = Path(__file__).parent.parent


def get_company_tickers() -> dict:
    """Fetch SEC company ticker -> CIK mapping."""
    url = "https://www.sec.gov/files/company_tickers.json"
    try:
        r = requests.get(url, headers=HEADERS, timeout=30)
        r.raise_for_status()
        return r.json()
    except Exception as e:
        print(f"SEC tickers failed: {e}")
        return {}


def get_submissions(cik: str) -> dict | None:
    """Get company filing history. CIK must be zero-padded to 10 digits."""
    cik_padded = str(cik).zfill(10)
    url = f"https://data.sec.gov/submissions/CIK{cik_padded}.json"
    try:
        time.sleep(0.2)  # SEC rate limit: 10 requests/second
        r = requests.get(url, headers=HEADERS, timeout=30)
        r.raise_for_status()
        return r.json()
    except Exception as e:
        print(f"Submissions failed for CIK {cik}: {e}")
        return None


def find_def14a(submissions: dict) -> str | None:
    """Find most recent DEF 14A filing URL."""
    recent = submissions.get("filings", {}).get("recent", {})
    if not recent:
        recent = submissions  # Some versions put arrays at top level
    forms = recent.get("form", [])
    if not forms:
        return None
    forms = [f.upper() if f else "" for f in forms]
    accessions = recent.get("accessionNumber", [])
    cik = submissions.get("cik", "").lstrip("0") or "0"
    for i, form in enumerate(forms):
        if form == "DEF 14A" and i < len(accessions):
            accession = accessions[i]
            accession_clean = accession.replace("-", "")
            return f"https://www.sec.gov/Archives/edgar/data/{cik}/{accession_clean}/{accession}.htm"
    return None


def extract_directors_from_def14a(html: str, company: str) -> list[dict]:
    """Parse DEF 14A HTML for director names. Heuristic pattern matching."""
    from bs4 import BeautifulSoup

    soup = BeautifulSoup(html, "html.parser")
    directors = []
    seen = set()

    # Common patterns in DEF 14A (director tables, bios)
    patterns = [
        r"(?:Director|Trustee|Member of the Board)[:\s]+([A-Z][a-z]+ [A-Z][a-z]+(?: [A-Z][a-z]+)?(?:,?\s*(?:Jr\.?|Sr\.?|II|III))?)",
        r"([A-Z][a-z]+ [A-Z][a-z]+(?: [A-Z][a-z]+)?),?\s*(?:age|Age)\s*\d+",
    ]

    text = soup.get_text()
    for pattern in patterns:
        for match in re.finditer(pattern, text, re.IGNORECASE):
            name = match.group(1).strip().rstrip(",")
            name = re.sub(r"\s*(Jr\.?|Sr\.?|II|III)\s*$", r" \1", name)
            if re.match(r"^[A-Z][a-z]+ [A-Z][a-z]+", name) and len(name) > 5 and len(name) < 60:
                if name not in seen:
                    seen.add(name)
                    directors.append({"name": name, "company": company, "source": "DEF 14A", "evidence_layer": "board_interlock"})

    # Also look for table rows with "Director" in adjacent cells
    for row in soup.find_all("tr"):
        cells = row.find_all(["td", "th"])
        for i, cell in enumerate(cells):
            if "director" in cell.get_text().lower() and i > 0:
                name = cells[i - 1].get_text(strip=True)
                if re.match(r"^[A-Z][a-z]+ [A-Z][a-z]+", name) and len(name) > 5:
                    if name not in seen:
                        seen.add(name)
                        directors.append({"name": name, "company": company, "source": "DEF 14A", "evidence_layer": "board_interlock"})

    return directors


def get_def14a_html(url: str) -> str | None:
    """Fetch DEF 14A HTML."""
    try:
        time.sleep(0.2)
        r = requests.get(url, headers=HEADERS, timeout=30)
        r.raise_for_status()
        return r.text
    except Exception as e:
        print(f"DEF 14A fetch failed: {e}")
        return None


def extract_board_interlocks(tickers: list[str] | None = None) -> list[dict]:
    """Main extraction pipeline."""
    if tickers is None:
        tickers = ["JPM", "C", "BAC", "GS", "MS", "WFC", "BLK", "V", "MA", "AXP"]  # Major financials

    ticker_map = get_company_tickers()
    if not ticker_map:
        return []

    cik_by_ticker = {v["ticker"]: v["cik_str"] for v in ticker_map.values()}
    all_directors = []

    for ticker in tickers:
        ticker = ticker.upper()
        cik = cik_by_ticker.get(ticker)
        if not cik:
            continue
        subs = get_submissions(cik)
        if not subs:
            continue
        company = subs.get("name", ticker)
        url = find_def14a(subs)
        if not url:
            continue
        html = get_def14a_html(url)
        if html:
            directors = extract_directors_from_def14a(html, company)
            all_directors.extend(directors)
            print(f"  {ticker}: {len(directors)} directors")

    return all_directors


if __name__ == "__main__":
    print("SEC EDGAR - Board Interlock extraction")
    directors = extract_board_interlocks()
    out = DATA_DIR / "board_interlocks_sec.csv"
    if directors:
        import csv
        with open(out, "w", newline="", encoding="utf-8") as f:
            w = csv.DictWriter(f, fieldnames=["name", "company", "source", "evidence_layer"])
            w.writeheader()
            w.writerows(directors)
        print(f"Saved {len(directors)} to {out}")
