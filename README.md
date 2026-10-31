# Simpsons Metadata

A community-editable, static JSON metadata API for *The Simpsons*. Each source record is a single JSON file. A Python build validates the complete source tree and emits a handful of consolidated JSON datasets and lookup indexes suitable for GitHub Pages.

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

The example records are a tiny starter set, not a complete database. Other categories begin empty. See [DESIGN.md](DESIGN.md) and [CONTRIBUTING.md](CONTRIBUTING.md).

## Licensing

Source code: MIT ([LICENSE](LICENSE)). Original metadata contributions: Creative Commons Attribution 4.0 International ([LICENSE-DATA.md](LICENSE-DATA.md)). Contribute only data you can legally share under those terms. *The Simpsons* and related marks belong to their respective owners; this project is unaffiliated.

## Deploy to GitHub Pages

1. Create a **public** GitHub repository and commit the project contents (not the ignored `dist/` folder).
2. Push to the `main` branch.
3. In the repository settings, open **Pages** and choose **GitHub Actions** as the build/deployment source.
4. The included workflow validates changes and deploys on pushes to `main`. Pull requests run validation without deploying.
5. The public URL will be `https://<owner>.github.io/<repo>/v1/episodes.json` unless using a custom domain.

To point an application at the API, configure its base URL once and cache the consolidated datasets. No server-side lookup endpoint is provided.
