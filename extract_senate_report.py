#!/usr/bin/env python3
"""Extract director names from 1978 Senate Report PDF (pages 236-278)."""
import re
import csv
from pathlib import Path

try:
    from PyPDF2 import PdfReader
except ImportError:
    print("Install PyPDF2: pip install PyPDF2")
    raise


def extract_directors_from_pdf(pdf_path: str, start_page: int = 236, end_page: int = 279) -> list[dict]:
    """Extract director names from specific pages of the Senate report."""
    pdf_path = Path(pdf_path)
    if not pdf_path.exists():
        raise FileNotFoundError(f"PDF not found: {pdf_path}")

    reader = PdfReader(str(pdf_path))
    directors = []

    for page_num in range(start_page - 1, min(end_page, len(reader.pages))):
        page = reader.pages[page_num]
        text = page.extract_text() or ""

        # Pattern for names (capitalized, may include JR/SR/II/III)
        name_pattern = r"^([A-Z][A-Za-z\s\.\-]+(?:,\s*JR\.?|,\s*SR\.?|,\s*II|,\s*III)?)\s*[,|]"
        lines = text.split("\n")

        for line in lines:
            match = re.match(name_pattern, line.strip())
            if match:
                name = match.group(1).strip().rstrip(",")
                if len(name) > 3 and name not in ("THE", "AND", "FOR"):
                    directors.append({
                        "name": name,
                        "page": page_num + 1,
                        "full_line": line.strip()[:200],
                    })

    return directors


def main():
    pdf_path = Path(__file__).parent / "data" / "senate_report_1978.pdf"
    output_path = Path(__file__).parent / "data" / "directors_3plus_boards.csv"

    pdf_path.parent.mkdir(parents=True, exist_ok=True)

    if not pdf_path.exists():
        print(f"Place senate_report_1978.pdf in {pdf_path}")
        return

    directors = extract_directors_from_pdf(pdf_path)
    print(f"Extracted {len(directors)} directors")

    with open(output_path, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=["name", "page", "full_line"])
        writer.writeheader()
        writer.writerows(directors)

    print(f"Saved to {output_path}")


if __name__ == "__main__":
    main()
