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
- Other fields such as `original_air_date` may be added as needed; YYYY-MM-DD date values are checked when that field is present.
- Missing information is **omitted**, not filled with `null` or guessed values.
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
- GitHub Pages is the MVP host. A separate CDN can be added later without changing the data format. Public Pages sites should not be treated as a guaranteed unlimited-bandwidth hosting service.
- If project needs grow: consider immutable release snapshots, variants for differing regional/platform titles, a full BCP 47 validator, or search tooling **when actually needed**.

## Trade-off: all non-episode items need production codes

This policy intentionally cannot represent an item with no known production code. It is strict, not an accidental validator limitation. To support commercial assets or Disney+ shorts without one, you would need to relax the ID rule to allow curated slugs. Make that a conscious policy change rather than putting fabricated codes into the database.

## Rights

The MIT license covers code, not metadata. CC BY 4.0 applies to contributors' original metadata and permits commercial reuse with attribution; it does **not** authorize copying protected third-party databases, episode descriptions or artwork. Contributors are responsible for sharing only material licensed appropriately or independently compiled facts.
