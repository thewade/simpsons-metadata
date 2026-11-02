#!/usr/bin/env python3
"""Review or apply French episode titles and article links from a saved Wikipedia page.

Download the rendered French episode list, then run this script with --html PATH.
The default is a dry run; --apply updates existing numbered episode records only.
"""

import argparse
from collections import Counter
from html.parser import HTMLParser
import json
from pathlib import Path
import re
from urllib.parse import quote, urlsplit, urlunsplit


ROOT = Path(__file__).resolve().parents[1]
UNKNOWN_TITLES = {"fr-FR": "titre français inconnu", "fr-CA": "titre québécois inconnu"}


class EpisodeTableParser(HTMLParser):
    def __init__(self):
        super().__init__(convert_charrefs=True)
        self.rows = []
        self.row = None
        self.cell = None
        self.skip_reference = 0

    def handle_starttag(self, tag, attrs):
        attrs = dict(attrs)
        if tag == "tr":
            self.row = {"cells": [], "overall": None, "fr_link": None}
        elif tag == "td" and self.row is not None:
            self.cell = []
            match = re.fullmatch(r"ep(\d+)", attrs.get("id", ""))
            if match and not self.row["cells"]:
                self.row["overall"] = int(match.group(1))
        elif tag == "a" and self.cell is not None and len(self.row["cells"]) == 2:
            href = attrs.get("href", "")
            if href.startswith("https://fr.wikipedia.org/wiki/") and "new" not in attrs.get("class", "").split():
                self.row["fr_link"] = href
        elif tag == "sup" and self.cell is not None:
            if "reference" in attrs.get("class", "").split() or attrs.get("id", "").startswith("cite_ref"):
                self.skip_reference += 1
        elif tag == "br" and self.cell is not None:
            self.cell.append(" ")

    def handle_endtag(self, tag):
        if tag == "sup" and self.skip_reference:
            self.skip_reference -= 1
        elif tag == "td" and self.cell is not None:
            self.row["cells"].append(" ".join("".join(self.cell).split()))
            self.cell = None
        elif tag == "tr" and self.row is not None:
            if self.row["overall"] is not None:
                self.rows.append(self.row)
            self.row = None

    def handle_data(self, data):
        if self.cell is not None and not self.skip_reference:
            self.cell.append(data)


def parse_episode_rows(html):
    parser = EpisodeTableParser()
    parser.feed(html)
    rows = {}
    for row in parser.rows:
        overall = row["overall"]
        cells = row["cells"]
        if overall in rows or len(cells) != 6 or not cells[1].isdigit() or int(cells[0]) != overall:
            raise ValueError(f"Unexpected or duplicate episode row {overall}")
        rows[overall] = row
    if not rows:
        raise ValueError("No episode rows found; check the downloaded Wikipedia page")
    return rows


def article_url(href):
    parsed = urlsplit(href)
    if parsed.scheme != "https" or parsed.netloc != "fr.wikipedia.org" or not parsed.path.startswith("/wiki/"):
        raise ValueError(f"Unexpected French article URL: {href}")
    return urlunsplit((parsed.scheme, parsed.netloc,
                       quote(parsed.path, safe="/:@!$&'()*+,;=-._~%"), parsed.query, parsed.fragment))


def plan_updates(rows, episode_dir):
    plans = []
    counts = Counter()
    seen_overall = set()
    for path in sorted(episode_dir.glob("s*e*.json")):
        record = json.loads(path.read_text(encoding="utf-8"))
        overall = record.get("overall_number")
        if overall in seen_overall or overall not in rows:
            raise ValueError(f"Missing or duplicate Wikipedia row for {path.name}: {overall}")
        seen_overall.add(overall)
        row = rows[overall]
        cells = row["cells"]
        if int(path.stem.split("e", 1)[1]) != int(cells[1]):
            raise ValueError(f"Season episode number differs for {path.name}: {cells[1]}")
        if cells[5] and cells[5] != record.get("production_code"):
            counts["production_code_disagreements"] += 1
        changed = False
        for language, column in (("fr-FR", 2), ("fr-CA", 4)):
            title = cells[column]
            if title and title.casefold() != UNKNOWN_TITLES[language] and record["titles"].get(language) != title:
                counts[f"{language}_titles"] += 1
                record["titles"][language] = title
                changed = True
        if row["fr_link"]:
            link = article_url(row["fr_link"])
            if record.get("links", {}).get("wikipedia_fr") != link:
                record.setdefault("links", {})["wikipedia_fr"] = link
                counts["french_article_links"] += 1
                changed = True
        if changed:
            plans.append((path, record))
    counts["matched_episodes"] = len(seen_overall)
    counts["changed_files"] = len(plans)
    return plans, counts


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--html", type=Path, required=True, help="saved rendered French Wikipedia episode list")
    parser.add_argument("--apply", action="store_true", help="write changes to data/episodes")
    args = parser.parse_args()
    rows = parse_episode_rows(args.html.read_text(encoding="utf-8"))
    plans, counts = plan_updates(rows, ROOT / "data" / "episodes")
    for name in ("matched_episodes", "changed_files", "fr-FR_titles", "fr-CA_titles",
                 "french_article_links", "production_code_disagreements"):
        print(f"{name}: {counts[name]}")
    if args.apply:
        for path, record in plans:
            path.write_text(json.dumps(record, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
        print("Applied changes")
    else:
        print("Dry run; pass --apply to write changes")


if __name__ == "__main__":
    main()
