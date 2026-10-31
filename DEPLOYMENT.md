# Deploy to api.simpsonseh.com (Cloudflare Pages)

The repository is the source of truth. Cloudflare Pages serves **static generated files**, with no runtime database, Worker, or server-side search.

## Create and connect the Pages project

1. In the Cloudflare dashboard, open **Compute → Workers & Pages**, and create a **Pages** project connected to `thewade/simpsons-metadata` on GitHub.
2. Select `main` as the production branch.
3. Framework preset **None**; repository root `/`; build command `python3 scripts/build.py`; output directory `dist`.
4. Use a supported Python builder version (the project needs Python >=3.10; dependencies are standard library only).
5. Deploy. Verify `https://<your-project>.pages.dev/v1/episodes.json` and `/v1/manifest.json` before changing DNS.

The included GitHub Actions workflow **validates only**; Cloudflare's Git integration performs deployment. Branch protection requiring the validation workflow is recommended.

## Custom domain with DreamHost DNS

1. In the Pages project, open **Custom domains**, add `api.simpsonseh.com`, and follow verification steps.
2. At the DNS provider controlling `simpsonseh.com` (DreamHost, if authoritative), create a CNAME for `api` pointing at your **actual** `<your-project>.pages.dev` hostname. Remove any conflicting `api` A/AAAA/CNAME records.
3. Do not change the apex domain or the primary website's DNS. Do not create a DreamHost-hosted website for `api`.
4. Wait for the domain and HTTPS certificate status to become active; verify `https://api.simpsonseh.com/v1/episodes.json`.

A custom domain must be registered in the Pages project; a DNS CNAME on its own is insufficient.

## Headers, caching and releases

`deployment/_headers` is copied to `dist/_headers` by `scripts/build.py` and applied to Pages static assets. `/v1/*` allows cross-origin browser requests and uses a five-minute client cache. `manifest.json` contains SHA-256 checksums of generated datasets. Clients should cache datasets locally and only re-fetch changed files.

This MVP publishes the current `/v1/` snapshot, not immutable commit-pinned snapshots. Add versioned release assets if consumers later need transactional consistency across multiple files.

## Test

```bash
python3 -m unittest discover -s tests -v
python3 scripts/build.py
python3 -m http.server 8000 --directory dist
# another terminal:
curl -fsSL http://localhost:8000/v1/manifest.json | python3 -m json.tool
```

No secrets, access keys, or database credentials should be committed to this repository.
