# Simpsons Metadata

A community-editable, static JSON metadata API for *The Simpsons*. Each source record is a single JSON file. A Python build validates the complete source tree and emits a handful of consolidated JSON datasets and lookup indexes suitable for Cloudflare Pages or GitHub Pages.

## Quick start

Requires Python 3.10+; **no external packages**.

```sh
python3 scripts/build.py
python3 -m unittest discover -s tests -v
```

Generated files live in `dist/v1/`. Preview locally with `python3 -m http.server 8000 --directory dist` and visit `http://localhost:8000/v1/episodes.json`.

## Public endpoints

| File | Purpose |
| --- | --- |
| `v1/episodes.json` | Regular episodes keyed by `sxxeyy` |
| `v1/shorts/tracey-ullman.json` | Original Tracey Ullman shorts |
| `v1/shorts/disney-plus.json` | Disney+ shorts |
| `v1/commercials.json` | Commercials |
| `v1/specials.json` | Specials |
| `v1/production.json` | Production codes to `{dataset,id}` |
| `v1/tvdb.json`, `v1/tmdb.json`, `v1/imdb.json` | External identifiers to `{dataset,id}` |
| `v1/manifest.json` | File paths and SHA-256 checksums |

No runtime queries or per-episode HTTP endpoints. Download a dataset and (optionally) an identifier map, then query locally. The individual record JSON is source material, **not** a public endpoint.

The source currently contains 548 legacy episodes, one movie, 23 season/catalogue records (with Amazon listings), and one sample Tracey Ullman short. Several categories are empty. The legacy data has not been independently fact-checked. See [DESIGN.md](DESIGN.md) and [CONTRIBUTING.md](CONTRIBUTING.md).

## Licensing

Source code: MIT ([LICENSE](LICENSE)). Original metadata contributions: Creative Commons Attribution 4.0 International ([LICENSE-DATA.md](LICENSE-DATA.md)). Contribute only data you can legally share under those terms. *The Simpsons* and related marks belong to their respective owners; this project is unaffiliated.

## Deploy to Cloudflare Pages

Use the Cloudflare Pages GitHub integration: build command `python3 scripts/build.py`, build output `dist`, production branch `main`. Connect `api.simpsonseh.com` as a custom domain in Pages and create the requested `api` CNAME at the authoritative DNS provider (DreamHost if unchanged). **Do not deploy GitHub Pages and Cloudflare Pages independently.** Detailed instructions: [DEPLOYMENT.md](DEPLOYMENT.md).

The GitHub Actions workflow runs tests and validation only. The generated `dist/_headers` allows browser CORS requests and a five-minute cache on `/v1/*`.

## Optional Disney+ episode links

Verified direct `/play/<content-id>` links can be added as `streaming.disney_plus` metadata. No links are invented for existing data. URL parameters to force 4:3, audio/subtitles or seeking are not part of the public contract. See [STREAMING.md](STREAMING.md).

## Legacy website database import

This starter has been populated from a historical SQL excerpt: 548 regular episodes, one film and 23 season/catalogue rows. The new `v1/seasons.json` preserves Amazon listing URLs and ASINs; `v1/episodes.json` preserves the old website-specific fields under `legacy`. See [legacy/MIGRATION.md](legacy/MIGRATION.md) for limitations and missing database tables. The included `scripts/import_legacy.py` can reproduce the import from the original dump.
