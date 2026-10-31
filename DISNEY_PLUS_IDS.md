# Disney+ content ID import — October 31, 2026

The `streaming.disney_plus.content_id` values came from the workspace copy of
[`simpsons_data.json`](../../external/simpsons_data/simpsons_data.json) at
[`colinxfleming/simpsons_data` commit `721276cad20dcafebd54d4a246187b5ee8d583aa`](https://github.com/colinxfleming/simpsons_data/tree/721276cad20dcafebd54d4a246187b5ee8d583aa).
That repository describes its dataset as scraped from SimpsonsWorld. These IDs
have not been checked against current Disney+ playback; the API stores IDs only,
without constructing `/play/` URLs or asserting regional availability.

The import added IDs to 547 existing regular episodes and the existing movie,
then created 253 regular episode records. Existing titles, dates, production
codes, overall numbers, and legacy fields were not changed. New records contain
only their aired-order ID, required titles, overall number, and Disney+ ID.
English titles came from the external episode entries, except where an entry
combines two episodes or has a malformed title. Available France and Quebec
titles and overall numbers came from the workspace's
[`simpsons_quebec_titles.json`](../../data/titles/simpsons_quebec_titles.json).
Unknown regional titles were omitted. For `s37e12`–`s37e15`, which are beyond
that local title list, aired numbering and the corrected `s37e12` English title
were checked against the [French Wikipedia episode list](https://fr.wikipedia.org/wiki/Liste_des_%C3%A9pisodes_des_Simpson).

## Identity reconciliation

- The external season/episode positions for `s16e20`/`s16e21` and
  `s25e12`/`s25e13` are reversed relative to the API's titles. IDs were matched
  by episode title rather than assigned by position.
- One external season 28 entry covers both `s28e12` and `s28e13`; one season 33
  entry covers `s33e06` and `s33e07`. Each pair shares its source content ID.
  Subsequent season 33 entries were matched to `s33e08`–`s33e22` by title.
- The external season 36 list omits four episodes included in the workspace's
  aired-order list. Its entries numbered 10–18 were matched by title to
  `s36e12`, `s36e13`, `s36e15`–`s36e17`, and `s36e19`–`s36e22`.
  `s36e10`, `s36e11`, `s36e14`, and `s36e18` received no ID or new record.
- `s03e01` has the source value `not-ported-over`, so it received no ID.
  Nineteen other season 99 entries were omitted because this API requires
  verified production-code IDs for non-episode records.

## Existing data check

The external entry for `s20e14` gives March 22, 2009, while the existing API
record says March 17, 2009. The title matches, so its content ID was added; the
air date was left unchanged for separate review. Other source title variations
were not copied over existing API titles. The full API build validates the
resulting source tree.
