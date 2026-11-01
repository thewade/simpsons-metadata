# Contributing

1. Create or edit exactly one source record in the matching `data/` directory, such as `data/episodes/s01e01.json`.
   The JSON records are authoritative; the historical SQL importer is retired.
2. Use the canonical `sxxeyy` aired order for TV episodes, `movie-YYYY` for films, and genuine production codes for other non-episode material. A film's production code, when known, goes in its own field. **Do not use TVDB's episode IDs or special order as canonical IDs.**
3. Put translated titles under BCP 47 language tags (`fr-CA`, not `fr_ca`). Omit unknown fields entirely.
4. Run `python3 scripts/build.py` and `python3 -m unittest discover -s tests -v` before opening a pull request.
5. In the PR description, explain the correction or addition. Git discussion and commit history are the audit trail; no `source` field is necessary.
6. By contributing, you agree that original metadata you submit is licensed under CC BY 4.0 and code you submit under MIT. Do not bulk copy metadata from providers whose terms forbid redistribution.

Validation rejects duplicate internal IDs in a dataset, duplicate external IDs or production codes across items, invalid file names/IDs, and malformed JSON. Additions to previously empty categories are welcome when the production code is verified.
