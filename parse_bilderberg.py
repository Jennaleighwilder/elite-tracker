#!/usr/bin/env python3
"""Parse Bilderberg attendee lists from Wikipedia HTML."""
import csv
from pathlib import Path

try:
    from bs4 import BeautifulSoup
except ImportError:
    print("Install beautifulsoup4: pip install beautifulsoup4")
    raise


def parse_bilderberg(html_file: str) -> list[dict]:
    """Parse Bilderberg participant tables. Format: Participants | Nationality | Title."""
    with open(html_file, "r", encoding="utf-8") as f:
        soup = BeautifulSoup(f.read(), "html.parser")

    attendees = []
    seen = set()  # Dedupe by normalized name

    for table in soup.find_all("table", {"class": "wikitable"}):
        rows = table.find_all("tr")
        if not rows:
            continue

        headers = [c.get_text(strip=True).lower() for c in rows[0].find_all(["th", "td"])]

        for row in rows[1:]:
            cells = row.find_all(["td", "th"])
            if len(cells) >= 1:
                name = cells[0].get_text(strip=True)
                # Skip header-like rows
                if not name or name.lower() in ("participants", "name", "---"):
                    continue
                country = cells[1].get_text(strip=True) if len(cells) > 1 else ""
                position = cells[2].get_text(strip=True) if len(cells) > 2 else ""
                key = (name.lower(), country.lower())
                if key not in seen:
                    seen.add(key)
                    attendees.append({
                        "name": name,
                        "years": "",  # By-year tables don't have years column
                        "country": country,
                        "sector": "",
                        "position": position,
                    })

    return attendees


def main():
    html_path = Path(__file__).parent / "data" / "bilderberg.html"
    output_path = Path(__file__).parent / "data" / "bilderberg_attendees.csv"

    if not html_path.exists():
        print(f"Place bilderberg.html in {html_path}")
        return

    attendees = parse_bilderberg(str(html_path))
    print(f"Parsed {len(attendees)} attendees")

    with open(output_path, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(
            f, fieldnames=["name", "years", "country", "sector", "position"]
        )
        writer.writeheader()
        writer.writerows(attendees)

    print(f"Saved to {output_path}")


if __name__ == "__main__":
    main()
