#!/usr/bin/env python3
"""Gather regional episode dates from linked French Wikipedia articles.

Uses the MediaWiki Action API and a local cache of article wikitext/revision IDs.
The default is a dry run with a JSON report; --apply merges only verified dates.
"""

import argparse
from collections import Counter, defaultdict
from datetime import date, datetime, timezone
from hashlib import sha256
from html import unescape
import json
import os
from pathlib import Path
import re
import shutil
import subprocess
import time
import unicodedata
from urllib.parse import unquote, urlencode, urlsplit
from urllib.request import Request, urlopen


ROOT = Path(__file__).resolve().parents[1]
API = "https://fr.wikipedia.org/w/api.php"
USER_AGENT = "SimpsonsMetadataSync/0.1 (https://github.com/thewade/simpsons-metadata; metadata maintenance)"
REGIONS = {"usa": ("en", "US"), "france": ("fr-FR", "FR"), "quebec": ("fr-CA", "CA")}
NETWORK_ALIASES = {"Télétoon (Canada)": "Télétoon"}
MONTHS = {name: number for number, name in enumerate(
    ("janvier", "fevrier", "mars", "avril", "mai", "juin", "juillet", "aout",
     "septembre", "octobre", "novembre", "decembre"), 1)}
DATE_RE = re.compile(r"(?<!\d)(\d{1,2})(?:er|e|re)?\s+(" + "|".join(MONTHS) + r")\s+(\d{4})(?!\d)")
NUMERIC_DATE_RE = re.compile(r"(?<!\d)(\d{1,2})\s+(\d{1,2})\s+(\d{4})(?!\d)")
INFOBOX_RE = re.compile(r"\{\{\s*Infobox\s+[ÉE]pisode\s+des\s+Simpson\b", re.I)


def normalize(value):
    return "".join(char for char in unicodedata.normalize("NFD", value.casefold())
                   if unicodedata.category(char) != "Mn")


def known_articles(episode_dir):
    records = {}
    by_title = defaultdict(list)
    for path in sorted(episode_dir.glob("s*e*.json")):
        record = json.loads(path.read_text(encoding="utf-8"))
        link = record.get("links", {}).get("wikipedia_fr")
        if not link:
            continue
        parsed = urlsplit(link)
        if parsed.scheme != "https" or parsed.netloc != "fr.wikipedia.org" or not parsed.path.startswith("/wiki/") or parsed.query or parsed.fragment:
            raise ValueError(f"Unexpected French article link in {path}: {link}")
        title = unquote(parsed.path.removeprefix("/wiki/")).replace("_", " ")
        records[record["id"]] = (path, record, title)
        by_title[title].append(record["id"])
    return records, by_title


def cache_path(cache_dir, title):
    return cache_dir / (sha256(title.encode("utf-8")).hexdigest() + ".json")


def get_json(url):
    curl = shutil.which("curl.exe" if os.name == "nt" else "curl")
    if curl:
        result = subprocess.run([curl, "--fail", "--silent", "--show-error", "--location",
                                 "--max-time", "90", "--user-agent", USER_AGENT, url],
                                capture_output=True, check=False)
        if result.returncode:
            raise RuntimeError(result.stderr.decode("utf-8", errors="replace").strip())
        return json.loads(result.stdout)
    request = Request(url, headers={"User-Agent": USER_AGENT})
    with urlopen(request, timeout=90) as response:
        return json.load(response)


def fetch_batch(titles):
    params = {"action": "query", "prop": "revisions", "rvprop": "ids|content",
              "rvslots": "main", "titles": "|".join(titles), "redirects": "1",
              "format": "json", "formatversion": "2", "maxlag": "5"}
    url = API + "?" + urlencode(params)
    for attempt in range(4):
        try:
            payload = get_json(url)
            if "error" in payload:
                raise RuntimeError(str(payload["error"]))
            return payload["query"]
        except (OSError, RuntimeError, ValueError) as exc:
            if attempt == 3:
                raise RuntimeError(f"MediaWiki request failed: {exc}") from exc
            time.sleep(2 ** attempt)
    raise AssertionError("unreachable")


def fetch_articles(titles, cache_dir, refresh=False, offline=False):
    cache_dir.mkdir(parents=True, exist_ok=True)
    result = {}
    missing = []
    for title in titles:
        path = cache_path(cache_dir, title)
        if path.exists() and not refresh:
            result[title] = json.loads(path.read_text(encoding="utf-8"))
        else:
            missing.append(title)
    if missing and offline:
        raise RuntimeError(f"{len(missing)} articles are absent from the cache")
    for start in range(0, len(missing), 30):
        batch = missing[start:start + 30]
        query = fetch_batch(batch)
        aliases = {item["from"]: item["to"] for kind in ("normalized", "redirects")
                   for item in query.get(kind, [])}
        pages = {page["title"]: page for page in query["pages"]}
        for title in batch:
            resolved = title
            for _ in range(4):
                if resolved not in aliases:
                    break
                resolved = aliases[resolved]
            page = pages.get(resolved)
            revision = (page or {}).get("revisions", [{}])[0]
            entry = {"requested_title": title, "title": resolved,
                     "revid": revision.get("revid"),
                     "wikitext": revision.get("slots", {}).get("main", {}).get("content")}
            result[title] = entry
            cache_path(cache_dir, title).write_text(
                json.dumps(entry, ensure_ascii=False) + "\n", encoding="utf-8", newline="\n")
        print(f"Fetched {min(start + len(batch), len(missing))}/{len(missing)} uncached articles", flush=True)
        time.sleep(0.5)
    return result


def infobox_fields(wikitext):
    match = INFOBOX_RE.search(wikitext)
    if not match:
        return None
    start = match.start()
    depth = 0
    end = None
    for index in range(start, len(wikitext) - 1):
        pair = wikitext[index:index + 2]
        if pair == "{{":
            depth += 1
        elif pair == "}}":
            depth -= 1
            if depth == 0:
                end = index
                break
    if end is None:
        return None
    fields = {}
    current = None
    for line in wikitext[start:end].splitlines()[1:]:
        field = re.match(r"^\s*\|\s*([^=|]+?)\s*=\s*(.*)$", line)
        if field:
            current = normalize(field.group(1).strip())
            fields[current] = field.group(2).strip()
        elif current:
            fields[current] += " " + line.strip()
    return fields


def french_date(value):
    if not value or normalize(value).strip().startswith("inedit") or normalize(value).strip() in {"non diffuse", "non diffusee", "n/a", "?", "-"}:
        return None, None
    cleaned = re.split(r"<ref\b", value, maxsplit=1, flags=re.I)[0]
    cleaned = re.sub(r"\[\[(?:[^]|]*\|)?([^]]+)\]\]", r"\1", cleaned)
    cleaned = re.sub(r"<[^>]+>|[{}|\[\]]", " ", unescape(cleaned))
    cleaned = normalize(" ".join(cleaned.split()))
    found = set()
    for day, month, year in DATE_RE.findall(cleaned):
        try:
            found.add(date(int(year), MONTHS[month], int(day)).isoformat())
        except ValueError:
            return None, "invalid_date"
    for day, month, year in NUMERIC_DATE_RE.findall(cleaned):
        try:
            found.add(date(int(year), int(month), int(day)).isoformat())
        except ValueError:
            return None, "invalid_date"
    found.update(re.findall(r"\b\d{4}-\d{2}-\d{2}\b", cleaned))
    if len(found) == 1:
        return next(iter(found)), None
    return None, "ambiguous_date" if len(found) > 1 else "unparsed_date"


def regional_dates(value):
    if not value:
        return [], []
    segments = re.split(r"<br\s*/?>", value, flags=re.I)
    results = []
    issues = []
    for segment in segments:
        air_date, issue = french_date(segment)
        if issue:
            issues.append(issue)
        if air_date:
            network_match = re.search(r"<small>\s*\(?\s*\[\[([^]|]+)", segment, re.I)
            network = network_match.group(1).strip() if network_match else None
            network = NETWORK_ALIASES.get(network, network)
            results.append((air_date, network))
    if len(results) > 1 and any(network is None for _, network in results):
        return [], ["ambiguous_date"]
    return results, issues


def matches_record(fields, record, usa_dates):
    code = record.get("production_code")
    code_matches = bool(code and re.search(r"(?<![A-Za-z0-9])" + re.escape(code) + r"(?![A-Za-z0-9])",
                                           fields.get("code", ""), re.I))
    season, number = map(int, re.fullmatch(r"s(\d+)e(\d+)", record["id"]).groups())
    season_values = {int(value) for value in re.findall(r"\b\d+\b", fields.get("saison", ""))}
    episode_values = {int(value) for value in re.findall(r"\b\d+\b", fields.get("numero", ""))}
    if season_values and season not in season_values:
        return False, "season_mismatch"
    number_matches = not episode_values or number in episode_values
    known_english_dates = {item["date"] for item in record.get("releases", [])
                           if item["language"] == "en" and "date" in item}
    usa_agrees = any(air_date in known_english_dates for air_date, _ in usa_dates)
    known_non_us = any(item["language"] == "en" and item.get("country") not in (None, "US")
                       for item in record.get("releases", []))
    if usa_dates and not usa_agrees and not known_non_us:
        # The article is still identifiable when both its code and episode number
        # agree. Never use its conflicting USA date to alter an English release.
        return (True, "usa_date_disagreement") if code_matches and number_matches else (False, "usa_date_disagreement")
    if code_matches and number_matches:
        return True, None
    if code_matches and usa_agrees:
        return True, "episode_number_disagreement"
    if number_matches and usa_agrees:
        return True, "production_code_disagreement"
    return False, "production_code_mismatch" if not code_matches else "episode_number_mismatch"


def merge_release(releases, language, country, air_date, network=None):
    network = NETWORK_ALIASES.get(network, network)
    matching = [item for item in releases if item["language"] == language and item.get("country") == country
                and NETWORK_ALIASES.get(item.get("network"), item.get("network")) == network]
    if matching:
        if any(item.get("date") == air_date for item in matching):
            return None
        undated = [item for item in matching if "date" not in item]
        if len(undated) == 1 and len(matching) == 1:
            undated[0]["date"] = air_date
            return "dated_existing"
        return "conflict"
    if network is None and any(item["language"] == language and item.get("country") == country
                               and item.get("date") == air_date for item in releases):
        return None
    undated_market = [item for item in releases if item["language"] == language
                      and item.get("country") == country and "date" not in item]
    if len(undated_market) == 1:
        previous_network = NETWORK_ALIASES.get(undated_market[0].get("network"),
                                                undated_market[0].get("network"))
        if network and previous_network and network != previous_network:
            return "conflict"
        undated_market[0]["date"] = air_date
        if network and not previous_network:
            undated_market[0]["network"] = network
        return "dated_existing"
    same_date_market = [item for item in releases if item["language"] == language and item.get("date") == air_date
                        and item.get("country") == country and "network" not in item]
    if network and len(same_date_market) == 1:
        same_date_market[0]["network"] = network
        return "added_network"
    same_date = [item for item in releases if item["language"] == language and item.get("date") == air_date
                 and "country" not in item]
    if len(same_date) == 1:
        same_date[0]["country"] = country
        if network:
            same_date[0]["network"] = network
        return "added_country"
    entry = {"language": language, "date": air_date, "country": country}
    if network:
        entry["network"] = network
    releases.append(entry)
    return "added_release"


def plan_updates(records, pages, as_of=None):
    if as_of is None:
        as_of = date.today()
    plans = []
    report = []
    counts = Counter()
    for ident, (path, record, title) in sorted(records.items()):
        page = pages[title]
        row = {"id": ident, "article": record["links"]["wikipedia_fr"],
               "revid": page.get("revid"), "changes": [], "issues": []}
        if not page.get("wikitext"):
            row["issues"].append("missing_article")
        else:
            fields = infobox_fields(page["wikitext"])
            if fields is None:
                row["issues"].append("missing_infobox")
            else:
                usa_dates, usa_issues = regional_dates(fields.get("usa", ""))
                matched, reason = matches_record(fields, record, usa_dates)
                if not matched:
                    row["issues"].append(reason)
                else:
                    counts["matched_records"] += 1
                    if reason:
                        row["issues"].append(reason)
                    releases = record.setdefault("releases", [])
                    first_english = min((item["date"] for item in releases
                                         if item["language"] == "en" and "date" in item), default=None)
                    for field, (language, country) in REGIONS.items():
                        if field == "usa" and reason == "usa_date_disagreement":
                            continue
                        dates, issues = (usa_dates, usa_issues) if field == "usa" else regional_dates(fields.get(field, ""))
                        for issue in issues:
                            row["issues"].append(f"{field}:{issue}")
                        for air_date, network in dates:
                            if air_date > as_of.isoformat():
                                row["issues"].append(f"{field}:future_date")
                                continue
                            if field != "usa" and first_english and air_date < first_english:
                                row["issues"].append(f"{field}:before_original_release")
                                continue
                            outcome = merge_release(releases, language, country, air_date, network)
                            if outcome == "conflict":
                                row["issues"].append(f"{field}:conflicting_existing_release")
                            elif outcome:
                                row["changes"].append({"language": language, "country": country,
                                                       "date": air_date, "network": network, "action": outcome})
                                counts[f"{language}_{outcome}"] += 1
        if row["changes"]:
            plans.append((path, record))
        for issue in row["issues"]:
            counts[issue] += 1
        report.append(row)
    counts["articles"] = len(pages)
    counts["records"] = len(records)
    counts["changed_records"] = len(plans)
    return plans, report, counts


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--apply", action="store_true", help="merge reviewed, unambiguous dates into episode JSON")
    parser.add_argument("--refresh", action="store_true", help="refetch articles even if cached")
    parser.add_argument("--offline", action="store_true", help="use cached API responses only")
    parser.add_argument("--cache-dir", type=Path, default=ROOT / "dist" / "wiki-fr-release-cache")
    parser.add_argument("--report", type=Path, default=ROOT / "dist" / "wiki-fr-release-report.json")
    parser.add_argument("--as-of", type=date.fromisoformat, default=date.today(),
                        help="latest date considered an actual release (YYYY-MM-DD; default today)")
    args = parser.parse_args()
    if args.offline and args.refresh:
        parser.error("--offline and --refresh cannot be combined")
    records, by_title = known_articles(ROOT / "data" / "episodes")
    pages = fetch_articles(sorted(by_title), args.cache_dir, args.refresh, args.offline)
    plans, rows, counts = plan_updates(records, pages, args.as_of)
    args.report.parent.mkdir(parents=True, exist_ok=True)
    args.report.write_text(json.dumps({"generated_at": datetime.now(timezone.utc).isoformat(),
                                       "as_of": args.as_of.isoformat(),
                                       "summary": dict(sorted(counts.items())), "records": rows},
                                      ensure_ascii=False, indent=2) + "\n", encoding="utf-8", newline="\n")
    for name, count in sorted(counts.items()):
        print(f"{name}: {count}")
    print(f"Report: {args.report}")
    if args.apply:
        for path, record in plans:
            path.write_text(json.dumps(record, ensure_ascii=False, indent=2) + "\n",
                            encoding="utf-8", newline="\n")
        print(f"Applied {len(plans)} episode updates")
    else:
        print("Dry run; review the report and pass --apply to merge")


if __name__ == "__main__":
    main()
