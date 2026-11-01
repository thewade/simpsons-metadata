# Legacy MySQL import — October 31, 2026

This migration used the user-supplied SQL excerpt from the website database. This is **not** a complete database backup.

## Imported

- 548 `episodes` rows → `data/episodes/sXXeYY.json`, aired-order ID from source `season` + `sepisode`.
- 1 `episodes` row with type `movie`, merged with its catalogue row → `data/movies/movie-2007.json` (production code `Movie1` retained separately).
- 23 `seasons` insert rows → 22 `data/seasons/sXX.json` files and the `legacy.catalogue_row` on the movie record.
- Two Amazon listing slots per source season row, treated as DVD first and Blu-ray second based on the historical release pattern. ASINs are retained and URLs are normalized to clean HTTPS product links without affiliate parameters. Individual product pages have not been reverified.
- Source `seasons` row values are stored as the eight-element `legacy.original_columns` array, except Amazon URLs are sanitized as above. The supplied excerpt has **no CREATE TABLE for seasons**.
- Original `episodes` columns `type`, `epnum`, `tcode`, `season`, `sepisode`, `SHOWCODE`, `SNPP`, and `Wikipedia` are retained verbatim under `legacy` (under `legacy.episode_row` for the film); `prodcode`, `title`, and `airdate` are represented by normalized fields.

## Preserved, but not published as content data

- The `jokes` table definition and three legacy views are preserved in `legacy/database-structures.sql` for reference.
- The excerpt contains no `INSERT INTO jokes` entries and no table definitions or rows for `actors` and `artwork`. No actual joke, actor, or artwork records can be recovered from this file.
- `seasons` has 23 insert rows but lacks its table definition. The dataset owner clarified that the product slots represent DVD and Blu-ray; their ordering is inferred from the historical release pattern.
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
