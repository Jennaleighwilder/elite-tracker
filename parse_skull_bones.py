#!/usr/bin/env python3
"""Parse Skull and Bones member list from Wikipedia HTML."""
import csv
from pathlib import Path

try:
    from bs4 import BeautifulSoup
except ImportError:
    print("Install beautifulsoup4: pip install beautifulsoup4")
    raise


def parse_skull_bones(html_file: str) -> list[dict]:
    """Parse the Wikipedia member list (bullet format: - [Name](link)(year), position)."""
    import re

    with open(html_file, "r", encoding="utf-8") as f:
        soup = BeautifulSoup(f.read(), "html.parser")

    members = []
    seen = set()

    # Restrict to main content (exclude nav, toc, etc.)
    content = soup.find("div", {"id": "mw-content-text"}) or soup.find("div", {"id": "bodyContent"}) or soup

    # Format: <li><a href="/wiki/Name">Name</a> (YYYY), position</li>
    for li in content.find_all("li"):
        # Skip nav items
        if li.find_parent("nav") or "mw-list-item" in (li.get("class") or []):
            continue
        link = li.find("a", href=lambda h: h and h.startswith("/wiki/") and ":" not in h)
        if not link:
            continue
        name = link.get_text(strip=True)
        if not name or len(name) < 4:
            continue
        text = li.get_text()
        # Must have (4-digit year) pattern for member entries
        cohort_match = re.search(r"\((\d{4})\)", text)
        if not cohort_match:
            continue
        cohort = cohort_match.group(1)
        position = re.sub(r"^.*?\(\d{4}\)\s*,?\s*", "", text).strip()
        position = re.sub(r"\[\d+\]$", "", position).strip()[:200]  # Remove ref numbers
        key = (name, cohort)
        if key not in seen:
            seen.add(key)
            members.append({"name": name, "cohort": cohort, "position": position})

    return members


def main():
    html_path = Path(__file__).parent / "data" / "skull_bones.html"
    output_path = Path(__file__).parent / "data" / "skull_bones_members.csv"

    if not html_path.exists():
        print(f"Place skull_bones.html in {html_path}")
        return

    members = parse_skull_bones(str(html_path))
    print(f"Parsed {len(members)} members")

    with open(output_path, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=["name", "cohort", "position"])
        writer.writeheader()
        writer.writerows(members)

    print(f"Saved to {output_path}")


if __name__ == "__main__":
    main()
