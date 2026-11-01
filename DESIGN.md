# Design: static Simpsons metadata API (MVP)

## Goals and non-goals

- Single source of truth in Git for multiple projects; public, read-only JSON output.
- Free hosting; no database, functions, authentication, API keys or server-side query language.
- Contributions via pull request; Git commits are the provenance trail. No separate source-tracking database.
- No JSON Schema or formal OpenAPI document until there is a concrete need.
- No aliases or numeric surrogate IDs.

## Record identity and datasets

- Regular TV episodes use the established common **aired** order: `s01e01`, `s07e23` (lowercase and two or more digits for each component). The numbering is treated as stable and never automatically reordered to match an external service.
- All other records are identified by **production code**; preserve its meaningful spelling (e.g. `MG01`). Where no verified production code exists, **do not invent one**. Leave the record unadded until the code is established or the policy is deliberately revised. This is particularly relevant to newer shorts and commercials. The repository includes empty datasets for those categories.
- Record identity is the pair (`dataset`, `id`), e.g. (`episodes`, `s01e01`) or (`shorts/tracey-ullman`, `MG01`). This avoids cross-dataset collisions.
- Source files are `data/<dataset>/<id>.json` (non-episode directories mirror published datasets). Git filenames must be portable and are validated against the record ID.
- Supported datasets: `episodes`, `shorts/tracey-ullman`, `shorts/disney-plus`, `commercials`, `specials`. No combined `shorts.json`.
- The public JSON has object keys equal to internal IDs; each value contains the record's own fields, including `id` for convenient use.

## Record fields (informal, extensible)

- `id` is required and matches the filename.
- `titles` is required, nonempty, and keyed by BCP 47 tags (`en`, `fr-CA`, `fr-FR`, etc.). The build checks a pragmatic syntax subset, not the complete IANA language registry.
- A non-episode record requires `production_code`, equal to `id`.
- An episode may include `production_code` if known.
- `tvdb`, `tmdb`, `imdb` are optional external identifier strings. They are **not** used as internal IDs.
- `links` is an optional, nonempty object of named HTTPS URLs or `null`, such as `"links": {"wikipedia": "https://en.wikipedia.org/wiki/..."}`. Link names use lowercase letters, digits and underscores. Verify the target against the record's identity; do not construct URLs from titles. Omit a link key when its status is unknown; use `null` only after confirming that the named destination does not exist.
- Other fields such as `original_air_date` may be added as needed; YYYY-MM-DD date values are checked when that field is present.
- Missing information is **omitted**, not guessed. The explicit `null` value for a link means its absence was checked and confirmed.
- If multiple identifiers genuinely refer to the same item, put them in that item's record. If an identifier appears on two different records, publishing fails rather than silently choosing one.

Example: `data/episodes/s01e01.json`.

## Static publication format

`python3 scripts/build.py` reads every record, validates **the entire source tree**, and publishes consolidated, sorted JSON under `dist/v1/`.

- `episodes.json`, `shorts/tracey-ullman.json`, `shorts/disney-plus.json`, `commercials.json`, `specials.json`: full metadata by internal ID.
- `production.json`, `tvdb.json`, `tmdb.json`, `imdb.json`: identifier -> `{ "dataset": "...", "id": "..." }`.
- `manifest.json`: checksums and paths for the files in the same build, allowing client-side cache invalidation.

Build output is generated; **never edit it manually**. It is not committed to Git. GitHub Actions validates pull requests and publishes only pushes to `main`. Publishing uploads one complete build as a GitHub Pages artifact.

## Constraints and decisions

- The indexes enforce **global uniqueness** of each identifier within its scheme, even across datasets. Duplicate `production_code`, `tvdb`, etc. fail the build. Existing repeated data is allowed if consistent within *one* record (e.g. `MG01` as both `id` and `production_code`).
- A data set can be empty; it still produces `{}`.
- JSON formatting is pretty-printed, sorted and UTF-8 to make diffs and local use easy. Clients can HTTP-cache or pin a downloaded copy.
- `/v1/` means consumer-facing data contract version 1. Incompatible changes require a new path. No version bump needed for ordinary additions or corrections.
- Cloudflare Pages is the deployment target for `api.simpsonseh.com`, using GitHub integration. DreamHost remains the existing website/database host and can retain authoritative DNS. GitHub Actions validates the data; the Cloudflare build serves static files.
- If project needs grow: consider immutable release snapshots, variants for differing regional/platform titles, a full BCP 47 validator, or search tooling **when actually needed**.

## Trade-off: all non-episode items need production codes

This policy intentionally cannot represent an item with no known production code. It is strict, not an accidental validator limitation. To support commercial assets or Disney+ shorts without one, you would need to relax the ID rule to allow curated slugs. Make that a conscious policy change rather than putting fabricated codes into the database.

## Rights

The MIT license covers code, not metadata. CC BY 4.0 applies to contributors' original metadata and permits commercial reuse with attribution; it does **not** authorize copying protected third-party databases, episode descriptions or artwork. Contributors are responsible for sharing only material licensed appropriately or independently compiled facts.


## Legacy season/catalogue records

A `seasons` dataset (`data/seasons/*.json` → `dist/v1/seasons.json`) supports historical website season entries and associated Amazon listings. Values of uncertain meaning remain in `legacy.original_columns`, pending a full database schema.

## Optional provider URLs and website integration

Verified Disney+ episode URLs may be stored under `streaming.disney_plus` (see `STREAMING.md`). There is no assumption that URL arguments can force 4:3/16:9, captions, audio, timestamp seeks, or clipping. This is optional per record; unknown values are omitted. The old PHP/MySQL site may periodically synchronize `episodes.json` and `seasons.json` using a separate importer, but the Git-hosted JSON is canonical. That sync should use a privileged *separate* DB account and keep the site's runtime account read-only. The legacy SQL table uses MyISAM and production codes as its primary key; perform an explicit mapping and staging/transaction strategy before implementing destructive synchronization.
