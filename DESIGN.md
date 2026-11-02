# Design: static Simpsons metadata API (MVP)

## Goals and non-goals

- The `data/` JSON records in Git are the single source of truth for multiple projects; public, read-only JSON output.
- Free hosting; no database, functions, authentication, API keys or server-side query language.
- Contributions via pull request; Git commits are the provenance trail. No separate source-tracking database.
- The build publishes a minimal OpenAPI document for the static endpoints.
- No aliases or numeric surrogate IDs.

## Record identity and datasets

- Regular TV episodes use the established common **aired** order: `s01e01`, `s07e23` (lowercase and two or more digits for each component). The numbering is treated as stable and never automatically reordered to match an external service.
- Tracey Ullman shorts and commercials are identified by **production code**; preserve its meaningful spelling (e.g. `MG01`). Disney+ shorts and unnumbered specials use stable lowercase title slugs and omit `production_code` until one is verified. Films use `movie-YYYY`, based on the release year or announced release year when the record is created, as their ID. Keep these IDs stable if a title or planned release changes; store a verified production code separately when known.
- Record identity is the pair (`dataset`, `id`), e.g. (`episodes`, `s01e01`) or (`shorts/tracey-ullman`, `MG01`). This avoids cross-dataset collisions.
- Source files are `data/<dataset>/<id>.json` (non-episode directories mirror published datasets). Git filenames must be portable and are validated against the record ID.
- Supported datasets: `episodes`, `seasons`, `movies`, `shorts/tracey-ullman`, `shorts/disney-plus`, `commercials`, `specials`. No combined `shorts.json`.
- The public JSON has object keys equal to internal IDs; each value contains the record's own fields, including `id` for convenient use.

## Record fields (informal, extensible)

- `id` is required and matches the filename.
- `titles` is required, nonempty, and keyed by BCP 47 tags (`en`, `fr-CA`, `fr-FR`, etc.). The build checks a pragmatic syntax subset, not the complete IANA language registry.
- A Tracey Ullman short or commercial requires `production_code`, equal to `id`. A Disney+ short, unnumbered special or movie may omit it until verified; when present it need not equal the record ID.
- An episode may include `production_code` if known.
- `tvdb`, `tmdb`, `imdb` are optional external identifier strings. They are **not** used as internal IDs.
- `links` is an optional, nonempty object of named HTTPS URLs or `null`, such as `"links": {"wikipedia": "https://en.wikipedia.org/wiki/..."}`. `wikipedia` is the English article and `wikipedia_fr` is the French article; the reference lists and sync process are documented in [SOURCES.md](SOURCES.md). Link names use lowercase letters, digits and underscores. Verify the target against the record's identity; do not construct URLs from titles. Omit a link key when its status is unknown; use `null` only after confirming that the named destination does not exist.
- `releases` records known releases of an episode or short. Each entry needs a BCP 47 `language`; `date` (YYYY-MM-DD), `country` (two-letter uppercase code), and `network` are optional when known. Omit an unknown date rather than setting it to `null`. A release entry means a release is known, not merely that a dub exists. The existing episode and short air dates were migrated to dated `en` entries without inferring a country or network. The build publishes `original_air_date` as the earliest dated release for existing API consumers and guide ordering. Movies still use `release_date` for an actual theatrical date or `planned_release_date` for an announced date.
- `original_aspect_ratio` is recorded for numbered episodes: `4:3` through `s20e09` and `16:9` from `s20e10` onward. It describes the episode's original format, independent of a streaming service's remastering preference.
- Missing information is **omitted**, not guessed. The explicit `null` value for a link means its absence was checked and confirmed.
- If multiple identifiers genuinely refer to the same item, put them in that item's record. If an identifier appears on two different records, publishing fails rather than silently choosing one.

Example: `data/episodes/s01e01.json`.

## Static publication format

`python3 scripts/build.py` reads every record, validates **the entire source tree**, and publishes consolidated, sorted JSON under `dist/v1/`.

- `episodes.json`, `seasons.json`, `movies.json`, `shorts/tracey-ullman.json`, `shorts/disney-plus.json`, `commercials.json`, `specials.json`: full metadata by internal ID.
- `production.json`, `tvdb.json`, `tmdb.json`, `imdb.json`: identifier -> `{ "dataset": "...", "id": "..." }`.
- `manifest.json`: checksums and paths for the files in the same build, allowing client-side cache invalidation.

Build output is generated; **never edit it manually**. It is not committed to Git. GitHub Actions validates pull requests; Cloudflare Pages publishes pushes to `main`.

## Constraints and decisions

- The indexes enforce **global uniqueness** of each identifier within its scheme, even across datasets. Duplicate `production_code`, `tvdb`, etc. fail the build. Existing repeated data is allowed if consistent within *one* record (e.g. `MG01` as both `id` and `production_code`).
- A data set can be empty; it still produces `{}`.
- JSON formatting is pretty-printed, sorted and UTF-8 to make diffs and local use easy. Clients can HTTP-cache or pin a downloaded copy.
- `/v1/` is the consumer-facing data contract. Films live in `movies.json`; `seasons.json` and `specials.json` contain only their respective record types. Future incompatible changes require a new path.
- Cloudflare Pages is the deployment target for `api.simpsonseh.com`, using GitHub integration. DreamHost remains the existing website/database host and can retain authoritative DNS. GitHub Actions validates the data; the Cloudflare build serves static files.
- If project needs grow: consider immutable release snapshots, variants for differing regional/platform titles, a full BCP 47 validator, or search tooling **when actually needed**.

## Trade-off: some non-episode items need production codes

The production-code rule for Tracey Ullman shorts and commercials intentionally cannot represent an item with no known production code. Disney+ shorts and unnumbered specials use title slugs when their production codes have not been verified; movies use year-based IDs. If two films share a release year, the movie ID policy will need an extension. If a later short or special repeats a title, add a disambiguating suffix while keeping existing IDs stable. To support other categories without a production code, revise their ID policy deliberately rather than putting fabricated codes into the database.

## Rights

The MIT license covers code, not metadata. CC BY 4.0 applies to contributors' original metadata and permits commercial reuse with attribution; it does **not** authorize copying protected third-party databases, episode descriptions or artwork. Contributors are responsible for sharing only material licensed appropriately or independently compiled facts.


## Seasons and movies

A `seasons` dataset contains seasons 1–38. The old movie catalogue row and film record are merged into `data/movies/movie-2007.json`; the announced sequel is `data/movies/movie-2027.json`. Both are published in `v1/movies.json`. The 23 imported catalogue rows retain their legacy values, with the film row under `legacy.catalogue_row` and its episode-table row under `legacy.episode_row`. Amazon URLs in `legacy.original_columns` have affiliate parameters removed. The first Amazon slot is treated as DVD and the second as Blu-ray, consistent with the historical release pattern; individual product pages have not been reverified. The 2007 release date is inherited from the legacy film air-date field, whose region was not recorded.

When present on a season or movie, `amazon_listings` contains one entry per known format: `asin`, `format` (`dvd` or `blu_ray`), and a clean `https://www.amazon.ca/dp/<ASIN>` URL. A missing listing means no product URL was imported; it does not assert that no release exists. The sequel's September 3, 2027 date is a plan, not an actual release date.

## Optional provider URLs and website integration

Verified Disney+ content IDs and URLs may be stored under `streaming.disney_plus` (see `STREAMING.md`). There is no assumption that URL arguments can force 4:3/16:9, captions, audio, timestamp seeks, or clipping. This is optional per record; unknown values are omitted. If the old PHP/MySQL site needs metadata, it should consume the published API as a downstream copy. That integration must never write changes back into the canonical JSON from the old SQL data. The historical SQL migration tool is archived under `legacy/` and is outside the build and validation workflow.
