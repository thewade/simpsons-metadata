#!/usr/bin/env python3
"""Validate record JSON and compile consolidated, static API datasets."""

import argparse
from datetime import date
from hashlib import sha256
import json
from pathlib import Path
from urllib.parse import urlparse
import re
import shutil
import sys

ROOT = Path(__file__).resolve().parents[1]
DATASETS = {
    "episodes": "episodes.json",
    "seasons": "seasons.json",
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
        raise ValidationError(f"{path}: invalid production-code ID")
    if dataset not in ("episodes", "seasons") and record.get("production_code") != ident:
        raise ValidationError(f"{path}: non-episode id must equal production_code")
    titles = record.get("titles")
    if not isinstance(titles, dict) or not titles:
        raise ValidationError(f"{path}: titles must be a nonempty object")
    for lang, title in titles.items():
        if not LANG_TAG.fullmatch(lang) or not isinstance(title, str) or not title.strip():
            raise ValidationError(f"{path}: invalid language tag/title {lang!r}")
    for field in ("production_code", "tvdb", "tmdb", "imdb"):
        if field in record and (not isinstance(record[field], str) or not record[field].strip()):
            raise ValidationError(f"{path}: {field} must be a nonempty string when present")
    if "original_air_date" in record:
        value = record["original_air_date"]
        try:
            if not isinstance(value, str) or not re.fullmatch(r"[0-9]{4}-[0-9]{2}-[0-9]{2}", value):
                raise ValueError("format")
            date.fromisoformat(value)
        except ValueError as exc:
            raise ValidationError(f"{path}: original_air_date must be YYYY-MM-DD") from exc
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
        "shorts/tracey-ullman": "Tracey Ullman shorts, keyed by production code.",
        "shorts/disney-plus": "Disney+ shorts, keyed by production code.",
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


def build(source, destination):
    catalog, index = collect(source)  # validate everything before touching output
    files = {DATASETS[d]: records for d, records in catalog.items()}
    files.update({f"{scheme}.json": records for scheme, records in index.items()})
    # A version root is rewritten only after successful validation.
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
    # GitHub Pages should not run Jekyll on the published tree.
    # Cloudflare Pages custom headers; GitHub Pages ignores _headers safely.
    headers_source = ROOT / "deployment" / "_headers"
    if headers_source.exists():
        shutil.copyfile(headers_source, destination.parent / "_headers")
    # Publish a static Swagger UI landing page and an OpenAPI description.
    swagger_page = ROOT / "deployment" / "index.html"
    if swagger_page.exists():
        shutil.copyfile(swagger_page, destination.parent / "index.html")
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
