#!/usr/bin/env python3
"""Validate record JSON and compile consolidated, static API datasets."""

import argparse
from collections import defaultdict
from datetime import date
from hashlib import sha256
from html import escape
import json
from pathlib import Path
from urllib.parse import quote, urlparse
import re
import shutil
import sys

ROOT = Path(__file__).resolve().parents[1]
DATASETS = {
    "episodes": "episodes.json",
    "seasons": "seasons.json",
    "movies": "movies.json",
    "shorts/tracey-ullman": "shorts/tracey-ullman.json",
    "shorts/disney-plus": "shorts/disney-plus.json",
    "commercials": "commercials.json",
    "specials": "specials.json",
}
SCHEMES = ("production", "tvdb", "tmdb", "imdb")
# Pragmatic subset of BCP 47: common language, script, region and variant tags.
LANG_TAG = re.compile(r"^[a-z]{2,3}(?:-[A-Z][a-z]{3})?(?:-(?:[A-Z]{2}|[0-9]{3}))?(?:-[a-zA-Z0-9]{4,8})*$")
EPISODE_ID = re.compile(r"^s[0-9]{2,}e[0-9]{2,}$")
OTHER_ID = re.compile(r"^[A-Za-z0-9][A-Za-z0-9._-]*$")
SHORT_SLUG = re.compile(r"^[a-z0-9]+(?:-[a-z0-9]+)*$")


class ValidationError(Exception):
    pass


def reject_duplicate_keys(pairs):
    result = {}
    for key, value in pairs:
        if key in result:
            raise ValidationError(f"Duplicate JSON key: {key!r}")
        result[key] = value
    return result


def parse_record(path, dataset):
    try:
        record = json.loads(path.read_text(encoding="utf-8"), object_pairs_hook=reject_duplicate_keys)
    except (ValueError, UnicodeError) as exc:
        raise ValidationError(f"{path}: invalid JSON: {exc}") from exc
    if not isinstance(record, dict):
        raise ValidationError(f"{path}: record must be a JSON object")
    ident = record.get("id")
    if not isinstance(ident, str) or ident != path.stem:
        raise ValidationError(f"{path}: id must be a string equal to filename stem")
    if dataset == "episodes":
        if not EPISODE_ID.fullmatch(ident) or ident.startswith("s00") or re.search(r"e0+$", ident):
            raise ValidationError(f"{path}: expected aired ID such as s01e01")
    elif not OTHER_ID.fullmatch(ident):
        raise ValidationError(f"{path}: invalid ID")
    if dataset == "seasons" and not re.fullmatch(r"s[0-9]{2,}", ident):
        raise ValidationError(f"{path}: season id must be sXX")
    if dataset == "movies" and not re.fullmatch(r"movie-[0-9]{4}", ident):
        raise ValidationError(f"{path}: movie id must be movie-YYYY")
    if dataset == "shorts/disney-plus" and not SHORT_SLUG.fullmatch(ident):
        raise ValidationError(f"{path}: Disney+ short id must be a lowercase title slug")
    if dataset not in ("episodes", "seasons", "movies", "shorts/disney-plus") and record.get("production_code") != ident:
        raise ValidationError(f"{path}: non-episode id must equal production_code")
    if "original_aspect_ratio" in record:
        if dataset != "episodes":
            raise ValidationError(f"{path}: original_aspect_ratio is only for episodes")
        season, episode = map(int, re.fullmatch(r"s(\d+)e(\d+)", ident).groups())
        expected = "4:3" if (season, episode) <= (20, 9) else "16:9"
        if record["original_aspect_ratio"] != expected:
            raise ValidationError(f"{path}: invalid original_aspect_ratio")
    titles = record.get("titles")
    if not isinstance(titles, dict) or not titles:
        raise ValidationError(f"{path}: titles must be a nonempty object")
    for lang, title in titles.items():
        if not LANG_TAG.fullmatch(lang) or not isinstance(title, str) or not title.strip():
            raise ValidationError(f"{path}: invalid language tag/title {lang!r}")
    for field in ("production_code", "tvdb", "tmdb", "imdb"):
        if field in record and (not isinstance(record[field], str) or not record[field].strip()):
            raise ValidationError(f"{path}: {field} must be a nonempty string when present")
    if "links" in record:
        links = record["links"]
        if not isinstance(links, dict) or not links:
            raise ValidationError(f"{path}: links must be a nonempty object")
        for site, url in links.items():
            if not isinstance(site, str) or not re.fullmatch(r"[a-z][a-z0-9_]*", site):
                raise ValidationError(f"{path}: invalid link name {site!r}")
            if url is None:
                continue
            if not isinstance(url, str) or not url or url != url.strip() or re.search(r"\s", url):
                raise ValidationError(f"{path}: links.{site} must be an HTTPS URL or null")
            try:
                parsed = urlparse(url)
                valid = parsed.scheme == "https" and parsed.hostname and parsed.username is None and parsed.password is None
            except ValueError:
                valid = False
            if not valid:
                raise ValidationError(f"{path}: links.{site} must be an HTTPS URL or null")
    if "amazon_listings" in record:
        listings = record["amazon_listings"]
        if dataset not in ("seasons", "movies") or not isinstance(listings, list) or not listings:
            raise ValidationError(f"{path}: amazon_listings must be a nonempty season or movie listing array")
        formats = set()
        for listing in listings:
            if not isinstance(listing, dict) or set(listing) != {"url", "asin", "format"}:
                raise ValidationError(f"{path}: each Amazon listing needs url, asin and format")
            asin, media_format = listing["asin"], listing["format"]
            if not isinstance(asin, str) or not re.fullmatch(r"[A-Z0-9]{10}", asin):
                raise ValidationError(f"{path}: invalid Amazon ASIN")
            if media_format not in ("dvd", "blu_ray") or media_format in formats:
                raise ValidationError(f"{path}: invalid or duplicate Amazon format")
            formats.add(media_format)
            if listing["url"] != f"https://www.amazon.ca/dp/{asin}":
                raise ValidationError(f"{path}: Amazon URL must be the clean HTTPS ASIN link")
    if dataset == "movies" and "original_air_date" in record:
        raise ValidationError(f"{path}: movies use release_date or planned_release_date")
    if dataset == "movies" and "release_date" in record and "planned_release_date" in record:
        raise ValidationError(f"{path}: a movie cannot have both release dates")
    for date_field in ("original_air_date", "release_date", "planned_release_date"):
        if date_field in record:
            value = record[date_field]
            try:
                if not isinstance(value, str) or not re.fullmatch(r"[0-9]{4}-[0-9]{2}-[0-9]{2}", value):
                    raise ValueError("format")
                date.fromisoformat(value)
            except ValueError as exc:
                raise ValidationError(f"{path}: {date_field} must be YYYY-MM-DD") from exc
    streaming = record.get("streaming", {})
    if not isinstance(streaming, dict):
        raise ValidationError(f"{path}: streaming must be an object")
    disney = streaming.get("disney_plus")
    if disney is not None:
        if not isinstance(disney, dict) or not disney:
            raise ValidationError(f"{path}: streaming.disney_plus must be a nonempty object")
        allowed = {"content_id", "url"}
        if set(disney) - allowed:
            raise ValidationError(f"{path}: unsupported Disney+ playback field(s): {sorted(set(disney) - allowed)}")
        content_id = disney.get("content_id")
        url = disney.get("url")
        if content_id is not None and (not isinstance(content_id, str) or not re.fullmatch(r"[A-Za-z0-9-]+", content_id)):
            raise ValidationError(f"{path}: invalid Disney+ content_id")
        if url is not None:
            if not isinstance(url, str):
                raise ValidationError(f"{path}: Disney+ url must be a string")
            parsed = urlparse(url)
            if parsed.scheme != "https" or parsed.hostname not in {"disneyplus.com", "www.disneyplus.com"} or not re.fullmatch(r"/play/[A-Za-z0-9-]+/?", parsed.path) or parsed.query or parsed.fragment:
                raise ValidationError(f"{path}: Disney+ url must be a direct https://www.disneyplus.com/play/<id> link (no query/fragment)")
            url_id = parsed.path.strip("/").split("/")[-1]
            if content_id is not None and content_id != url_id:
                raise ValidationError(f"{path}: Disney+ URL and content_id disagree")
    return record


def collect(source):
    catalog = {dataset: {} for dataset in DATASETS}
    index = {scheme: {} for scheme in SCHEMES}
    for dataset in DATASETS:
        folder = source / dataset
        if not folder.is_dir():
            raise ValidationError(f"Missing dataset directory: {folder}")
        for path in sorted(folder.iterdir()):
            if path.name == ".gitkeep":
                continue
            if path.suffix != ".json" or not path.is_file():
                raise ValidationError(f"Unexpected file in {folder}: {path.name}")
            record = parse_record(path, dataset)
            ident = record["id"]
            if ident in catalog[dataset]:
                raise ValidationError(f"Duplicate internal ID in {dataset}: {ident}")
            catalog[dataset][ident] = record
            target = {"dataset": dataset, "id": ident}
            for scheme in SCHEMES:
                field = "production_code" if scheme == "production" else scheme
                if field not in record:
                    continue
                value = record[field]
                if value in index[scheme] and index[scheme][value] != target:
                    raise ValidationError(f"Duplicate {field} {value!r}: {index[scheme][value]} and {target}")
                index[scheme][value] = target
    return catalog, index


def json_bytes(obj):
    return (json.dumps(obj, indent=2, ensure_ascii=False, sort_keys=True) + "\n").encode("utf-8")


def openapi_document():
    """Minimal OpenAPI contract for the published, read-only static JSON datasets."""
    descriptions = {
        "episodes": "Regular television episodes, keyed by sXXeYY.",
        "seasons": "Season catalogue entries, including legacy Amazon listings.",
        "movies": "Feature films, including announced releases.",
        "shorts/tracey-ullman": "Tracey Ullman shorts, keyed by production code.",
        "shorts/disney-plus": "Disney+ shorts, keyed by stable title slug; production code optional.",
        "commercials": "Commercials, keyed by production code.",
        "specials": "Specials and other non-regular items.",
        "production": "Production code to dataset and internal ID.",
        "tvdb": "TVDB identifier to dataset and internal ID.",
        "tmdb": "TMDB identifier to dataset and internal ID.",
        "imdb": "IMDb identifier to dataset and internal ID.",
        "manifest": "Published filenames and their SHA-256 hashes.",
    }
    paths = {}
    for name, description in descriptions.items():
        path = f"/v1/{DATASETS[name]}" if name in DATASETS else f"/v1/{name}.json"
        paths[path] = {"get": {
            "tags": ["Datasets" if name in DATASETS else "Lookups" if name != "manifest" else "Metadata"],
            "summary": description,
            "operationId": "get_" + name.replace("/", "_").replace("-", "_"),
            "responses": {"200": {
                "description": "JSON object (static, no server-side filtering).",
                "content": {"application/json": {"schema": {"type": "object", "additionalProperties": True}}}
            }}
        }}
    return {
        "openapi": "3.0.3",
        "info": {"title": "Simpsons Metadata API", "version": "1.0.0",
                 "description": "Free, static, read-only JSON datasets. Each endpoint returns a complete dataset or mapping. No authentication, pagination or server-side queries. Metadata is licensed CC BY 4.0."},
        "servers": [{"url": "https://api.simpsonseh.com", "description": "Production"}],
        "tags": [{"name": "Datasets"}, {"name": "Lookups"}, {"name": "Metadata"}],
        "paths": paths,
    }


def render_episode_guide(catalog):
    """Render the numbered episodes as accessible, expandable season tables."""
    template = (ROOT / "deployment" / "episodes" / "index.html").read_text(encoding="utf-8")
    by_season = defaultdict(list)
    for record in catalog["episodes"].values():
        season_number = int(record["id"].split("e", 1)[0][1:])
        by_season[season_number].append(record)
    numbers = sorted({int(key[1:]) for key in catalog["seasons"]} | set(by_season))
    h = lambda value: escape(str(value), quote=True)
    jumps = "".join(f'<a href="#season-{number:02}">{number}</a>' for number in numbers)
    groups = []
    for first, last, label, anchor in ((1, 20, "Seasons 1–20", "classic"),
                                        (21, float("inf"), "Season 21 onward", "modern")):
        members = [number for number in numbers if first <= number <= last]
        if not members:
            continue
        sections = []
        for number in members:
            records = sorted(by_season[number], key=lambda record: int(record["id"].split("e", 1)[1]))
            season = catalog["seasons"].get(f"s{number:02}", {})
            dates = [record["original_air_date"] for record in records if "original_air_date" in record]
            years = sorted({value[:4] for value in dates})
            year_label = years[0] if len(years) == 1 else f"{years[0]}–{years[-1]}" if years else ""
            season_links = []
            for site, label in (("wikipedia", "English article"), ("wikipedia_fr", "French article")):
                url = season.get("links", {}).get(site)
                if url:
                    season_links.append(f'<a href="{h(url)}" target="_blank" rel="noopener noreferrer">{label} ↗</a>')
            season_link_html = "".join(season_links)
            heading = (f'<header class="season-heading"><div><p class="season-kicker">{h(year_label)}</p>'
                       f'<h3 id="season-{number:02}">Season {number}</h3></div>'
                       f'<div class="season-meta"><span>{len(records)} numbered episodes</span>{season_link_html}</div></header>')
            if not records:
                sections.append(f'<section class="season">{heading}<p class="empty">No numbered episode records in this season yet.</p></section>')
                continue
            rows = []
            for record in records:
                ident = record["id"]
                episode_number = int(ident.split("e", 1)[1])
                title = record["titles"].get("en", next(iter(record["titles"].values())))
                aired = record.get("original_air_date")
                displayed_date = (f'{date.fromisoformat(aired).strftime("%B")} {date.fromisoformat(aired).day}, '
                                  f'{date.fromisoformat(aired).year}') if aired else "—"
                date_html = f'<time datetime="{h(aired)}">{h(displayed_date)}</time>' if aired else "—"
                production = record.get("production_code", "—")
                overall = record.get("overall_number", "—")
                details_id = f"{ident}-details"
                rows.append(
                    f'<tr class="episode-row" id="{h(ident)}"><td>{h(overall)}</td><td>{episode_number}</td>'
                    f'<th scope="row"><button type="button" class="episode-toggle" aria-expanded="false" '
                    f'aria-controls="{h(details_id)}">{h(title)}</button></th><td>{date_html}</td>'
                    f'<td><code>{h(production)}</code></td><td class="row-arrow" aria-hidden="true">⌄</td></tr>'
                )
                facts = []
                for language, translated in record["titles"].items():
                    if language != "en":
                        facts.append(f'<div><dt>Title ({h(language)})</dt><dd>{h(translated)}</dd></div>')
                if "original_aspect_ratio" in record:
                    facts.append(f'<div><dt>Original aspect ratio</dt><dd>{h(record["original_aspect_ratio"])}</dd></div>')
                for key, field_label in (("tvdb", "TVDB"), ("tmdb", "TMDB"), ("imdb", "IMDb")):
                    if key in record:
                        facts.append(f'<div><dt>{field_label}</dt><dd><code>{h(record[key])}</code></dd></div>')
                fact_html = f'<dl class="detail-facts">{"".join(facts)}</dl>' if facts else ""
                links = []
                for site, url in record.get("links", {}).items():
                    if url is None:
                        if site == "wikipedia":
                            links.append('<span class="no-link">No standalone English Wikipedia article</span>')
                    else:
                        name = {"wikipedia": "Wikipedia (English)",
                                "wikipedia_fr": "Wikipedia (French)"}.get(site, site.replace("_", " ").title())
                        links.append(f'<a href="{h(url)}" target="_blank" rel="noopener noreferrer">{h(name)} ↗</a>')
                disney = record.get("streaming", {}).get("disney_plus", {})
                content_id = disney.get("content_id")
                disney_url = (f'https://www.disneyplus.com/play/{quote(content_id, safe="")}'
                              if content_id else disney.get("url"))
                if disney_url:
                    links.append(f'<a href="{h(disney_url)}" target="_blank" rel="noopener noreferrer">Open on Disney+ ↗</a>')
                links_html = f'<div class="detail-links">{"".join(links)}</div>' if links else '<p class="no-link">No external links recorded.</p>'
                legacy = record.get("legacy")
                legacy_html = (f'<details class="legacy"><summary>Archived source fields</summary>'
                               f'<pre>{h(json.dumps(legacy, ensure_ascii=False, indent=2))}</pre></details>') if legacy else ""
                rows.append(
                    f'<tr class="detail-row" id="{h(details_id)}" hidden><td colspan="6"><div class="detail-panel">'
                    f'<div class="detail-top"><div><p class="detail-label">{h(ident)} · Episode details</p>'
                    f'<h4>{h(title)}</h4></div><a class="permalink" href="#{h(ident)}">Link to episode</a></div>'
                    f'{fact_html}{links_html}{legacy_html}</div></td></tr>'
                )
            table = ('<div class="table-scroll"><table><thead><tr><th scope="col">Overall</th><th scope="col">No.</th>'
                     '<th scope="col">Episode</th><th scope="col">Original air date</th>'
                     '<th scope="col">Production code</th><th scope="col"><span class="sr-only">Details</span></th>'
                     f'</tr></thead><tbody>{"".join(rows)}</tbody></table></div>')
            sections.append(f'<section class="season">{heading}{table}</section>')
        groups.append(f'<section class="group" id="{anchor}"><div class="group-heading"><p class="eyebrow">Episode catalogue</p>'
                      f'<h2>{label}</h2></div>{"".join(sections)}</section>')
    replacements = {
        "{{EPISODE_COUNT}}": str(len(catalog["episodes"])),
        "{{SEASON_COUNT}}": str(len(numbers)),
        "<!-- SEASON_JUMPS -->": jumps,
        "<!-- EPISODE_TABLES -->": "".join(groups),
    }
    for marker, content in replacements.items():
        if template.count(marker) != 1:
            raise ValidationError(f"Episode guide template must contain exactly one {marker}")
        template = template.replace(marker, content)
    return template


def build(source, destination):
    catalog, index = collect(source)  # validate everything before touching output
    episode_html = render_episode_guide(catalog)
    files = {DATASETS[d]: records for d, records in catalog.items()}
    files.update({f"{scheme}.json": records for scheme, records in index.items()})
    if destination.exists():
        shutil.rmtree(destination)
    destination.mkdir(parents=True)
    checksums = {}
    for relative, content in sorted(files.items()):
        path = destination / relative
        path.parent.mkdir(parents=True, exist_ok=True)
        payload = json_bytes(content)
        path.write_bytes(payload)
        checksums[relative] = sha256(payload).hexdigest()
    (destination / "manifest.json").write_bytes(json_bytes({"api_version": 1, "files": checksums}))
    # Cloudflare Pages custom headers.
    headers_source = ROOT / "deployment" / "_headers"
    if headers_source.exists():
        shutil.copyfile(headers_source, destination.parent / "_headers")
    # Publish the consumer pages, API explorer, and OpenAPI description.
    for name in ("index.html", "docs/index.html"):
        page = ROOT / "deployment" / name
        if page.exists():
            target = destination.parent / name
            target.parent.mkdir(parents=True, exist_ok=True)
            shutil.copyfile(page, target)
    episode_page = destination.parent / "episodes" / "index.html"
    episode_page.parent.mkdir(parents=True, exist_ok=True)
    episode_page.write_text(episode_html, encoding="utf-8")
    spec = openapi_document()
    (destination.parent / "openapi.json").write_bytes(json_bytes(spec))
    (destination.parent / ".nojekyll").touch()
    return sum(map(len, catalog.values()))


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--source", type=Path, default=ROOT / "data")
    parser.add_argument("--out", type=Path, default=ROOT / "dist" / "v1")
    args = parser.parse_args()
    try:
        count = build(args.source, args.out)
    except ValidationError as exc:
        print(f"ERROR: {exc}", file=sys.stderr)
        return 1
    print(f"Validated {count} records; generated API in {args.out}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
