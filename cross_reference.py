#!/usr/bin/env python3
"""Cross-reference people across elite organizations and corporate boards."""
import csv
import re
from pathlib import Path
from collections import defaultdict

try:
    import pandas as pd
except ImportError:
    pd = None


def normalize_name(name: str) -> str:
    """Normalize name for matching: lowercase, strip, collapse spaces."""
    if not name:
        return ""
    # Remove common suffixes for matching
    name = re.sub(r"\s*(Jr\.?|Sr\.?|II|III|IV)\s*$", "", name, flags=re.I)
    name = re.sub(r"\s+", " ", name.strip().lower())
    return name


def load_csv(path: Path, name_col: str = "name") -> dict[str, list[dict]]:
    """Load CSV and index by normalized name."""
    if not path.exists():
        return {}
    by_name = defaultdict(list)
    with open(path, "r", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        for row in reader:
            name = row.get(name_col, "").strip()
            if name:
                by_name[normalize_name(name)].append(row)
    return dict(by_name)


def fuzzy_match(name: str, candidates: set[str]) -> list[str]:
    """Find potential matches (exact or last name + first initial)."""
    norm = normalize_name(name)
    if norm in candidates:
        return [norm]

    matches = []
    parts = norm.split()
    if len(parts) >= 2:
        last = parts[-1]
        first_init = parts[0][0] if parts[0] else ""
        for c in candidates:
            c_parts = c.split()
            if len(c_parts) >= 2 and c_parts[-1] == last and c_parts[0][0] == first_init:
                matches.append(c)
    return matches


def main():
    data_dir = Path(__file__).parent / "data"

    # Load all datasets
    directors = load_csv(data_dir / "directors_3plus_boards.csv")
    skull_bones = load_csv(data_dir / "skull_bones_members.csv")
    bilderberg = load_csv(data_dir / "bilderberg_attendees.csv")

    # Build cross-reference
    all_names = set(directors.keys()) | set(skull_bones.keys()) | set(bilderberg.keys())
    overlaps = []

    for norm_name in all_names:
        sources = []
        if norm_name in directors:
            sources.append("senate_3plus_boards")
        if norm_name in skull_bones:
            sources.append("skull_and_bones")
        if norm_name in bilderberg:
            sources.append("bilderberg")

        if len(sources) >= 2:
            # Get display name from first available source
            display = norm_name.title()
            for d in [directors, skull_bones, bilderberg]:
                if norm_name in d and d[norm_name]:
                    display = d[norm_name][0].get("name", display)
                    break

            overlaps.append({
                "name": display,
                "sources": ", ".join(sources),
                "source_count": len(sources),
            })

    # Sort by number of overlaps
    overlaps.sort(key=lambda x: (-x["source_count"], x["name"]))

    # Write results
    output_path = data_dir / "cross_reference.csv"
    output_path.parent.mkdir(parents=True, exist_ok=True)

    with open(output_path, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=["name", "sources", "source_count"])
        writer.writeheader()
        writer.writerows(overlaps)

    print(f"Found {len(overlaps)} people in 2+ sources")
    print(f"Saved to {output_path}")

    # Summary
    for o in overlaps[:20]:
        print(f"  {o['name']}: {o['sources']}")


if __name__ == "__main__":
    main()
