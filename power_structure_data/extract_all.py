#!/usr/bin/env python3
"""
Power Structure Data Extraction - Complete Pipeline
Downloads and extracts all data from public sources.
"""
import re
import time
import csv
import logging
from pathlib import Path
from datetime import datetime

import requests
from bs4 import BeautifulSoup

try:
    from PyPDF2 import PdfReader
except ImportError:
    try:
        from pypdf import PdfReader
    except ImportError:
        PdfReader = None

try:
    import pandas as pd
except ImportError:
    pd = None

DATA_DIR = Path(__file__).parent
LOG_FILE = DATA_DIR / "extraction.log"
FAILED_URLS = DATA_DIR / "failed_urls.log"

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s",
    handlers=[
        logging.FileHandler(LOG_FILE),
        logging.StreamHandler(),
    ],
)
logger = logging.getLogger(__name__)


def log_failed(url: str, reason: str):
    with open(FAILED_URLS, "a") as f:
        f.write(f"{datetime.now().isoformat()}\t{url}\t{reason}\n")


def fetch(url: str, dest: Path, timeout: int = 30) -> bool:
    """Download URL to file. Returns True on success."""
    try:
        time.sleep(1)
        r = requests.get(url, timeout=timeout, headers={"User-Agent": "Mozilla/5.0"})
        r.raise_for_status()
        dest.parent.mkdir(parents=True, exist_ok=True)
        dest.write_bytes(r.content)
        logger.info(f"Downloaded: {dest.name}")
        return True
    except Exception as e:
        logger.warning(f"Failed {url}: {e}")
        log_failed(url, str(e))
        return False


# ========== DATASET 1: 1978 SENATE REPORT ==========
def dataset1_senate_report():
    """HathiTrust - Senate Report PDF. Note: HathiTrust viewer may not allow direct PDF download."""
    url = "http://babel.hathitrust.org/cgi/pt?id=mdp.39015077914680"
    pdf_path = DATA_DIR / "senate_report_1978.pdf"

    # Try to get PDF - HathiTrust often requires session/cookies for download
    pdf_url = f"{url};view=1up;seq=1;format=pdf"
    if not fetch(pdf_url, pdf_path):
        # Try alternative URL format
        fetch(f"https://babel.hathitrust.org/cgi/pt?id=mdp.39015077914680&view=1up&seq=1&format=pdf", pdf_path)

    if pdf_path.exists() and PdfReader and pdf_path.stat().st_size > 1000:
        try:
            reader = PdfReader(str(pdf_path))
            directors = []
            for page_num in range(235, min(278, len(reader.pages))):
                text = reader.pages[page_num].extract_text() or ""
                for line in text.split("\n"):
                    if re.match(r"^[A-Z][A-Z\s\.]+(?:,|$)", line) and len(line) > 3:
                        directors.append({"name": line.strip()[:100], "page": page_num + 1})
            df = pd.DataFrame(directors) if pd else None
            if df is not None and len(df) > 0:
                df.to_csv(DATA_DIR / "directors_3plus_boards.csv", index=False)
                logger.info(f"Extracted {len(directors)} directors from Senate Report")
        except Exception as e:
            logger.warning(f"Senate PDF extraction failed: {e}")
    else:
        logger.info("Senate Report PDF not available - add manually from HathiTrust")


# ========== DATASET 2: CFR FINDING AID ==========
def dataset2_cfr():
    """Princeton - CFR finding aid."""
    url = "http://arks.princeton.edu/ark:/88435/dsp011c18dj67m"
    pdf_path = DATA_DIR / "cfr_finding_aid.pdf"
    fetch(url, pdf_path)

    if pdf_path.exists() and PdfReader:
        try:
            reader = PdfReader(str(pdf_path))
            members = []
            for page in reader.pages:
                text = page.extract_text() or ""
                for match in re.findall(r"([A-Z][a-z]+ [A-Z][a-z]+(?: [A-Z][a-z]+)?)", text):
                    if 5 < len(match) < 50 and "University" not in match and "Press" not in match and "Council" not in match:
                        members.append({"name": match, "source": "CFR finding aid"})
            if members:
                df = pd.DataFrame(members)
                df.drop_duplicates(subset=["name"], inplace=True)
                df.to_csv(DATA_DIR / "cfr_members_1921_1951.csv", index=False)
                logger.info(f"Extracted {len(df)} names from CFR finding aid")
        except Exception as e:
            logger.warning(f"CFR extraction failed: {e}")


# ========== DATASET 3: SKULL AND BONES ==========
def dataset3_skull_bones():
    """Wikipedia - Skull and Bones roster."""
    urls = [
        "https://en.wikipedia.org/wiki/List_of_Skull_and_Bones_members",
        "https://en.wikipedia.org/w/index.php?title=List_of_Skull_and_Bones_members&diff=1242971543&oldid=1114727412",
    ]
    members = []
    seen = set()

    for url in urls:
        time.sleep(1)
        try:
            r = requests.get(url, timeout=30, headers={"User-Agent": "Mozilla/5.0"})
            r.raise_for_status()
            soup = BeautifulSoup(r.text, "html.parser")
            content = soup.find("div", {"id": "mw-content-text"}) or soup.find("div", {"id": "bodyContent"}) or soup

            # Tables
            for table in soup.find_all("table", {"class": "wikitable"}):
                for row in table.find_all("tr")[1:]:
                    cells = row.find_all(["td", "th"])
                    if len(cells) >= 2:
                        name = (cells[1] if len(cells) > 1 else cells[0]).get_text(strip=True)
                        cohort = cells[0].get_text(strip=True) if cells[0].get_text().replace(" ", "").isdigit() else ""
                        position = cells[2].get_text(strip=True) if len(cells) > 2 else ""
                        if name and len(name) > 3 and name not in seen:
                            seen.add(name)
                            members.append({"name": name, "cohort_year": cohort, "position": position, "century": "unknown"})

            # List items
            for li in content.find_all("li"):
                if li.find_parent("nav"):
                    continue
                link = li.find("a", href=lambda h: h and h.startswith("/wiki/") and ":" not in h)
                if not link:
                    continue
                name = link.get_text(strip=True)
                if not name or len(name) < 4:
                    continue
                text = li.get_text()
                cohort_match = re.search(r"\((\d{4})\)", text)
                if not cohort_match:
                    continue
                cohort = cohort_match.group(1)
                position = re.sub(r"^.*?\(\d{4}\)\s*,?\s*", "", text).strip()[:200]
                # Filter out non-person names (events, places, etc.)
                if any(x in name.lower() for x in ["olympics", "summer", "winter", "war", "conference"]):
                    continue
                key = (name, cohort)
                if key not in seen:
                    seen.add(key)
                    century = "19th" if cohort < "1900" else "20th" if cohort.isdigit() else "unknown"
                    members.append({"name": name, "cohort_year": cohort, "position": position, "century": century})
        except Exception as e:
            logger.warning(f"Skull and Bones {url}: {e}")
            log_failed(url, str(e))

    if members:
        df = pd.DataFrame(members)
        df.to_csv(DATA_DIR / "skull_bones_complete.csv", index=False)
        logger.info(f"Extracted {len(members)} Skull and Bones members")


# ========== DATASET 4: BILDERBERG ==========
def dataset4_bilderberg():
    """German and English Wikipedia - Bilderberg attendees."""
    attendees = []
    seen = set()

    # German
    url_de = "https://de.wikipedia.org/wiki/Liste_von_Teilnehmern_an_Bilderberg-Konferenzen"
    try:
        time.sleep(1)
        r = requests.get(url_de, timeout=30, headers={"User-Agent": "Mozilla/5.0"})
        r.raise_for_status()
        soup = BeautifulSoup(r.text, "html.parser")
        for table in soup.find_all("table", {"class": "wikitable"}):
            for row in table.find_all("tr")[1:]:
                cells = row.find_all(["td", "th"])
                if len(cells) >= 4:
                    name = cells[0].get_text(strip=True)
                    country = cells[2].get_text(strip=True) if len(cells) > 2 else ""
                    if name and (name, country) not in seen:
                        seen.add((name, country))
                        attendees.append({
                            "name": name,
                            "years": cells[1].get_text(strip=True) if len(cells) > 1 else "",
                            "country": country,
                            "sector": cells[3].get_text(strip=True) if len(cells) > 3 else "",
                            "position": cells[4].get_text(strip=True) if len(cells) > 4 else "",
                        })
    except Exception as e:
        logger.warning(f"German Bilderberg: {e}")
        log_failed(url_de, str(e))

    # English
    url_en = "https://en.wikipedia.org/wiki/List_of_Bilderberg_participants"
    try:
        time.sleep(1)
        r = requests.get(url_en, timeout=30, headers={"User-Agent": "Mozilla/5.0"})
        r.raise_for_status()
        soup = BeautifulSoup(r.text, "html.parser")
        for table in soup.find_all("table", {"class": "wikitable"}):
            for row in table.find_all("tr")[1:]:
                cells = row.find_all(["td", "th"])
                if len(cells) >= 2:
                    name = cells[0].get_text(strip=True)
                    if not name or name.lower() in ("participants", "name", "---"):
                        continue
                    country = cells[1].get_text(strip=True) if len(cells) > 1 else ""
                    position = cells[2].get_text(strip=True) if len(cells) > 2 else ""
                    if (name, country) not in seen:
                        seen.add((name, country))
                        attendees.append({
                            "name": name,
                            "years": "",
                            "country": country,
                            "sector": "Unknown",
                            "position": position,
                        })
    except Exception as e:
        logger.warning(f"English Bilderberg: {e}")
        log_failed(url_en, str(e))

    if attendees:
        df = pd.DataFrame(attendees)
        df.to_csv(DATA_DIR / "bilderberg_attendees.csv", index=False)
        logger.info(f"Extracted {len(attendees)} Bilderberg attendees")


# ========== DATASET 5: TRILATERAL ==========
def dataset5_trilateral():
    """Rockefeller Archive - Trilateral finding aid + known founding members."""
    url = "https://dimes.rockarch.org/collections/FVYj2u2ReLkppp2DZLYVs7"
    fetch(url, DATA_DIR / "trilateral_finding_aid.html")

    # Known founding members from primary sources
    founders = [
        {"name": "David Rockefeller", "source": "founder", "role": "Founder, North American Chairman"},
        {"name": "Zbigniew Brzezinski", "source": "founder", "role": "Founder, Director"},
        {"name": "Gerard C. Smith", "source": "founder", "role": "Founder"},
        {"name": "Henry D. Owen", "source": "founder", "role": "Founder"},
        {"name": "George S. Franklin", "source": "founder", "role": "Founder"},
        {"name": "Charles B. Heck", "source": "founder", "role": "Founder"},
        {"name": "Alan Greenspan", "source": "founder", "role": "Founding member"},
        {"name": "Paul Volcker", "source": "founder", "role": "Founding member"},
    ]
    members = list(founders)

    html_path = DATA_DIR / "trilateral_finding_aid.html"
    if html_path.exists():
        soup = BeautifulSoup(html_path.read_text(), "html.parser")
        text = soup.get_text()
        for name in re.findall(r"([A-Z][a-z]+ [A-Z][a-z]+(?: [A-Z][a-z]+)?)", text):
            if 5 < len(name) < 50 and "University" not in name and "Commission" not in name:
                if any(f in name for f in ["Rockefeller", "Brzezinski", "Volcker", "Greenspan", "Kissinger"]):
                    if not any(m["name"] == name for m in members):
                        members.append({"name": name, "source": "finding aid", "role": ""})

    if members:
        df = pd.DataFrame(members)
        df.to_csv(DATA_DIR / "trilateral_members.csv", index=False)
        logger.info(f"Extracted {len(members)} Trilateral members")
    else:
        # Ensure at least founders are saved
        df = pd.DataFrame(founders)
        df.to_csv(DATA_DIR / "trilateral_members.csv", index=False)
        logger.info(f"Saved {len(founders)} Trilateral founding members")


# ========== DATASET 6: DUNL / S&P ==========
def dataset6_dunl():
    """DUNL.org - verify and capture."""
    urls = [
        ("https://DUNL.org", "dunl_portal.html"),
        ("https://DUNL.org/api/docs", "dunl_api_docs.html"),
        ("https://DUNL.org/downloads/", "dunl_downloads.html"),
        ("https://DUNL.org/sample/companies.csv", "sp_sample_companies.csv"),
    ]
    for url, fname in urls:
        path = DATA_DIR / fname
        if path.suffix == ".csv":
            path = DATA_DIR / "sp_sample_companies.csv"
        fetch(url, path)


# ========== DATASET 7: BOHEMIAN GROVE ==========
def dataset7_bohemian_grove():
    """USC Archive - Bohemian Grove finding aid."""
    url = "https://archives.usc.edu/repositories/3/archival_objects/118929"
    fetch(url, DATA_DIR / "bohemian_grove_finding_aid.html")

    access_path = DATA_DIR / "bohemian_grove_access.txt"
    access_path.write_text("""To access the actual 1980 Bohemian Grove guest list:

Repository: USC Libraries Special Collections
Location: Doheny Memorial Library 206, 3550 Trousdale Parkway, Los Angeles, CA 90089-0189
Email: specol@usc.edu
Reference: Box 124, Folder 40, Herbert G. Klein papers

Request: "Please provide digital copies of Box 124, Folder 40 from the Herbert G. Klein papers, containing the 1980 Bohemian Grove guest list, Klein's membership application, and correspondence with Dick Cheney, George H.W. Bush, Karl Rove, and Richard Nixon."

The collection is open for research but stored off site. Advance notice required.
""")


# ========== DATASET 9: SEC EDGAR (Board Interlock - Evidence Layer 1) ==========
def dataset9_sec_edgar():
    """SEC DEF 14A - Board directors from proxy statements."""
    try:
        import sys
        sys.path.insert(0, str(DATA_DIR))
        from extractors.sec_edgar import extract_board_interlocks
        directors = extract_board_interlocks(["JPM", "C", "BAC", "GS", "MS", "WFC", "BLK"])
        if directors and pd is not None:
            df = pd.DataFrame(directors)
            df.to_csv(DATA_DIR / "board_interlocks_sec.csv", index=False)
            logger.info(f"SEC EDGAR: {len(directors)} board interlocks")
    except Exception as e:
        logger.warning(f"SEC EDGAR extraction failed: {e}")


# ========== DATASET 10: FORM 990 (Institutional Affiliation - Evidence Layer 2) ==========
def dataset10_form_990():
    """ProPublica/IRS Form 990 - Nonprofit org network."""
    try:
        import sys
        sys.path.insert(0, str(DATA_DIR))
        from extractors.form_990 import extract_institutional_affiliations
        affils = extract_institutional_affiliations()
        if affils and pd is not None:
            df = pd.DataFrame(affils)
            df.to_csv(DATA_DIR / "institutional_affiliations_990.csv", index=False)
            logger.info(f"Form 990: {len(affils)} institutional affiliations")
    except Exception as e:
        logger.warning(f"Form 990 extraction failed: {e}")


# ========== DATASET 8: PENN LIBRARIES ==========
def dataset8_penn():
    """Penn Libraries alternative."""
    url = "https://onlinebooks.library.upenn.edu/webbin/book/lookupid?key=ha006604514"
    fetch(url, DATA_DIR / "senate_report_penn.html")


# ========== CROSS-REFERENCE & NETWORK ==========
def create_cross_reference():
    """Build master network from all datasets."""
    dfs = {}
    for name, path in [
        ("skull_bones", DATA_DIR / "skull_bones_complete.csv"),
        ("bilderberg", DATA_DIR / "bilderberg_attendees.csv"),
        ("cfr", DATA_DIR / "cfr_members_1921_1951.csv"),
        ("directors", DATA_DIR / "directors_3plus_boards.csv"),
        ("board_interlocks", DATA_DIR / "board_interlocks_sec.csv"),
    ]:
        if path.exists():
            try:
                dfs[name] = pd.read_csv(path)
            except Exception:
                pass

    if not dfs:
        logger.warning("No CSV files to cross-reference")
        return

    def normalize(n):
        return re.sub(r"\s*(Jr\.?|Sr\.?|II|III)\s*$", "", str(n).strip().lower(), flags=re.I)
    def get_names(df, col="name"):
        if col not in df.columns:
            return set()
        return {normalize(n) for n in df[col].dropna() if not pd.isna(n)}

    all_sets = {k: get_names(v) for k, v in dfs.items()}
    overlaps = []

    for norm_name in set().union(*all_sets.values()):
        sources = [k for k, s in all_sets.items() if norm_name in s]
        if len(sources) >= 2:
            display = norm_name.title()
            for df in dfs.values():
                if "name" in df.columns:
                    match = df[df["name"].apply(normalize) == norm_name]
                    if not match.empty:
                        display = match.iloc[0]["name"]
                        break
            overlaps.append({"name": display, "sources": ", ".join(sources), "source_count": len(sources)})

    overlaps.sort(key=lambda x: (-x["source_count"], x["name"]))
    if overlaps:
        pd.DataFrame(overlaps).to_csv(DATA_DIR / "cross_reference.csv", index=False)
        logger.info(f"Cross-reference: {len(overlaps)} people in 2+ sources")

    # Network edges
    edges = []

    # Board interlocks: people who share a board (same company)
    if "board_interlocks" in dfs:
        bi = dfs["board_interlocks"]
        if "name" in bi.columns and "company" in bi.columns:
            by_company = bi.groupby("company")["name"].apply(list)
            for company, members in by_company.items():
                for i, n1 in enumerate(members):
                    for n2 in members[i + 1 :]:
                        edges.append({"source": n1, "target": n2, "relationship": "shared_board", "organization": company, "year": ""})

    # Skull and Bones cohorts
    if "skull_bones" in dfs and "cohort_year" in dfs["skull_bones"].columns:
        sb = dfs["skull_bones"]
        for cohort in sb["cohort_year"].dropna().unique():
            if str(cohort).isdigit():
                members = sb[sb["cohort_year"] == cohort]["name"].tolist()
                for i, n1 in enumerate(members):
                    for n2 in members[i + 1 :]:
                        edges.append({"source": n1, "target": n2, "relationship": "Skull and Bones cohort", "organization": "Skull and Bones", "year": cohort})
    if edges:
        pd.DataFrame(edges).to_csv(DATA_DIR / "network_edges.csv", index=False)
        logger.info(f"Created {len(edges)} network edges")


# ========== NETWORK VISUALIZATION ==========
def create_network_viz():
    """Generate network visualization."""
    try:
        import networkx as nx
        import matplotlib
        matplotlib.use("Agg")
        import matplotlib.pyplot as plt
    except ImportError:
        logger.warning("NetworkX/matplotlib not installed - skip visualization")
        return

    edges_path = DATA_DIR / "network_edges.csv"
    if not edges_path.exists():
        logger.info("No network_edges.csv for visualization")
        return

    edges_df = pd.read_csv(edges_path)
    if edges_df.empty or "source" not in edges_df.columns or "target" not in edges_df.columns:
        return

    G = nx.Graph()
    for _, row in edges_df.iterrows():
        G.add_edge(row["source"], row["target"])

    if G.number_of_nodes() == 0:
        return

    plt.figure(figsize=(20, 20))
    pos = nx.spring_layout(G, k=0.5, iterations=50)
    nx.draw_networkx(G, pos, node_size=20, font_size=6, with_labels=False)
    plt.savefig(DATA_DIR / "network_visualization.png", dpi=150, bbox_inches="tight")
    plt.close()
    logger.info(f"Network viz saved: {G.number_of_nodes()} nodes, {G.number_of_edges()} edges")


# ========== SUMMARY ==========
def create_summary():
    """Generate download summary."""
    summary = []
    for name, path in [
        ("Skull and Bones", "skull_bones_complete.csv"),
        ("Bilderberg", "bilderberg_attendees.csv"),
        ("1978 Directors", "directors_3plus_boards.csv"),
        ("CFR Members", "cfr_members_1921_1951.csv"),
        ("Trilateral", "trilateral_members.csv"),
        ("Board Interlocks (SEC)", "board_interlocks_sec.csv"),
        ("Institutional (990)", "institutional_affiliations_990.csv"),
        ("Cross-reference", "cross_reference.csv"),
    ]:
        p = DATA_DIR / path
        if p.exists():
            try:
                n = len(pd.read_csv(p))
                summary.append({"dataset": name, "records": n, "file": path})
            except Exception:
                pass
    if summary:
        pd.DataFrame(summary).to_csv(DATA_DIR / "download_summary.csv", index=False)
        logger.info("\nDOWNLOAD SUMMARY:")
        for s in summary:
            logger.info(f"  {s['dataset']}: {s['records']} records -> {s['file']}")


# ========== MAIN ==========
def main():
    DATA_DIR.mkdir(parents=True, exist_ok=True)
    if FAILED_URLS.exists():
        FAILED_URLS.unlink()
    logger.info("=== POWER STRUCTURE DATA EXTRACTION ===")

    dataset1_senate_report()
    dataset2_cfr()
    dataset3_skull_bones()
    dataset4_bilderberg()
    dataset5_trilateral()
    dataset6_dunl()
    dataset7_bohemian_grove()
    dataset8_penn()
    dataset9_sec_edgar()
    dataset10_form_990()

    create_cross_reference()
    create_network_viz()
    create_summary()

    logger.info("=== EXTRACTION COMPLETE ===")


if __name__ == "__main__":
    main()
