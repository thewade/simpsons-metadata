# Simpsons Metadata

A community-editable, static JSON metadata API for *The Simpsons*. Each source record is a single JSON file. A Python build validates the complete source tree and emits a handful of consolidated JSON datasets and lookup indexes suitable for Cloudflare Pages or GitHub Pages.

## Quick start

Requires Python 3.10+; **no external packages**.

```sh
python3 scripts/build.py
python3 -m unittest discover -s tests -v
```

Generated files live in `dist/v1/`. Preview locally with `python3 -m http.server 8000 --directory dist` and visit `http://localhost:8000/v1/movies.json`.

## Public endpoints

| File | Purpose |
| --- | --- |
| `v1/episodes.json` | Regular episodes keyed by `sxxeyy` |
| `v1/shorts/tracey-ullman.json` | Original Tracey Ullman shorts |
| `v1/shorts/disney-plus.json` | Disney+ shorts |
| `v1/commercials.json` | Commercials |
| `v1/specials.json` | Specials other than feature films |
| `v1/seasons.json` | Season catalogue, seasons 1–38 |
| `v1/movies.json` | Released and announced feature films |
| `v1/production.json` | Production codes to `{dataset,id}` |
| `v1/tvdb.json`, `v1/tmdb.json`, `v1/imdb.json` | External identifiers to `{dataset,id}` |
| `v1/manifest.json` | File paths and SHA-256 checksums |

The movie records appear only in `movies.json`. The production-code lookup points the first film's legacy code `Movie1` to its movie record.

No runtime queries or per-episode HTTP endpoints. Download a dataset and (optionally) an identifier map, then query locally. The individual record JSON is source material, **not** a public endpoint.

Episode records use `links.wikipedia` for an individual English Wikipedia article. A `null` value means the absence of such an article was checked; an unknown link is omitted. The `links` object can hold other verified external URLs as they are added.

The source currently contains 801 regular episodes (548 legacy imports and 253 later additions), one released movie, one announced movie, 38 season records, and one sample Tracey Ullman short. Several categories are empty. The legacy data has not been independently fact-checked. See [DESIGN.md](DESIGN.md) and [CONTRIBUTING.md](CONTRIBUTING.md).

## Licensing

Source code: MIT ([LICENSE](LICENSE)). Original metadata contributions: Creative Commons Attribution 4.0 International ([LICENSE-DATA.md](LICENSE-DATA.md)). Contribute only data you can legally share under those terms. *The Simpsons* and related marks belong to their respective owners; this project is unaffiliated.

## Deploy to Cloudflare Pages

Use the Cloudflare Pages GitHub integration: build command `python3 scripts/build.py`, build output `dist`, production branch `main`. Connect `api.simpsonseh.com` as a custom domain in Pages and create the requested `api` CNAME at the authoritative DNS provider (DreamHost if unchanged). **Do not deploy GitHub Pages and Cloudflare Pages independently.** Detailed instructions: [DEPLOYMENT.md](DEPLOYMENT.md).

The GitHub Actions workflow runs tests and validation only. The generated `dist/_headers` allows browser CORS requests and a five-minute cache on `/v1/*`.

## Optional Disney+ episode links

Episode and movie records can include a `streaming.disney_plus.content_id`. The current IDs were imported from an external dataset and have not been checked against current playback. No direct `/play/` URLs were generated. URL parameters to force 4:3, audio/subtitles or seeking are not part of the public contract. See [DISNEY_PLUS_IDS.md](DISNEY_PLUS_IDS.md) for source and matching details and [STREAMING.md](STREAMING.md) for the field format.

## Legacy website database import

This starter has been populated from a historical SQL excerpt: 548 regular episodes, one film and 23 season/catalogue rows. The source data now includes seasons 1–38, and the historical film row is merged into its movie record. Historical Amazon listings retain their ASINs and DVD/Blu-ray formats with affiliate-free HTTPS URLs; `v1/episodes.json` preserves the old website-specific fields under `legacy`. See [legacy/MIGRATION.md](legacy/MIGRATION.md) for limitations and missing database tables. The included `scripts/import_legacy.py` can reproduce the base import from the original dump.

## French episode titles

The 548 existing regular episode records include `titles.fr-FR` and `titles.fr-CA` from the workspace's `data/titles/simpsons_quebec_titles.json` (also available as CSV). Its [source note](../../data/titles/notes.txt) points to the [French Wikipedia episode list](https://fr.wikipedia.org/wiki/Liste_des_%C3%A9pisodes_des_Simpson). Rows were matched by aired overall number and season episode number, with production codes checked as a second identity signal. Nonbreaking spaces in the working list are represented as regular spaces in API titles. English title differences were mostly punctuation and capitalization. The title list reverses the API's production codes for `s24e19` and `s24e20`; their aired numbers and English titles agree, so only the French titles were added. These are sourced regional title listings, not independently verified dub transcripts.

## Interactive API documentation

Cloudflare Pages serves Swagger UI at the domain root (`https://api.simpsonseh.com/`).
The OpenAPI 3.0 definition is generated at `/openapi.json`; it documents all static dataset/index endpoints.
Both files are generated by `python3 scripts/build.py` into `dist/`, so no changes to the Cloudflare build command are needed.
Swagger UI's pinned CSS/JavaScript files are loaded from jsDelivr CDN; the API itself remains self-hosted on Cloudflare Pages.
