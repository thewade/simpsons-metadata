# Legacy MySQL import — October 31, 2026

This migration used the user-supplied SQL excerpt from the website database. This is **not** a complete database backup.

## Imported

- 548 `episodes` rows → `data/episodes/sXXeYY.json`, aired-order ID from source `season` + `sepisode`.
- 1 `episodes` row with type `movie` → `data/specials/Movie1.json` (kept original production-code ID).
- 23 `seasons` insert rows → `data/seasons/sXX.json` and `data/seasons/movie.json`.
- Two Amazon listing slots per source season row, retaining ASINs and complete URLs (including affiliate tag parameters).
- Original `seasons` row values stored as the eight-element `legacy.original_columns` array because the supplied excerpt has **no CREATE TABLE for seasons** and field names other than the obvious labels are unverified.
- Original `episodes` columns `type`, `epnum`, `tcode`, `season`, `sepisode`, `SHOWCODE`, `SNPP`, and `Wikipedia` are retained verbatim under `legacy`; `prodcode`, `title`, and `airdate` are represented by normalized fields.

## Preserved, but not published as content data

- The `jokes` table definition and three legacy views are preserved in `legacy/database-structures.sql` for reference.
- The excerpt contains no `INSERT INTO jokes` entries and no table definitions or rows for `actors` and `artwork`. No actual joke, actor, or artwork records can be recovered from this file.
- `seasons` has 23 insert rows but lacks its table definition. Do not guess what the first and second Amazon product positions represent.
- The views `actorsjoin`, `artworkjoin`, `jokesjoin` are not published in the static API and are **not** run during conversion.

## Intentional handling

- No corrections, title updates, or external enrichment were performed.
- Legacy blank strings and numeric zeroes are retained in the `legacy` payload. Optional normalized fields are omitted where appropriate.
- Listings are **historical source data**, not a statement of current Amazon availability or accuracy.
- The original starter `s01e01.json` was replaced by the imported source record; the starter `MG01` short is retained separately.

## Repeat the conversion

```bash
python3 scripts/import_legacy.py /path/to/source-dump.sql
python3 scripts/build.py
python3 -m unittest discover -s tests -v
```

The importer refuses to overwrite records with different values. For a fresh conversion, run it against a new checkout or an empty data directory. Review imported changes before committing them to a public repo.
