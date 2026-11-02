# Simpsons Metadata API

Free, read-only JSON metadata for *The Simpsons*. Start at **[api.simpsonseh.com](https://api.simpsonseh.com/)**, browse the [episode guide](https://api.simpsonseh.com/episodes/), or use the [interactive API reference](https://api.simpsonseh.com/docs/). No account or API key is required.

## Get started

Each dataset endpoint returns one JSON object keyed by record ID. Download a dataset, then look up the record you need:

```js
const episodes = await fetch('https://api.simpsonseh.com/v1/episodes.json')
  .then(response => response.json());

console.log(episodes['s01e01'].titles.en);
// Simpsons Roasting on an Open Fire
```

The API is static and read-only. It does not offer server-side search, filtering, pagination, or individual record URLs. Browser requests are allowed by CORS. Unknown fields are omitted; a `null` link means its absence was checked.

## Datasets

| Endpoint | Contents |
| --- | --- |
| [`/v1/episodes.json`](https://api.simpsonseh.com/v1/episodes.json) | Regular episodes, keyed by aired-order IDs such as `s01e01` |
| [`/v1/seasons.json`](https://api.simpsonseh.com/v1/seasons.json) | Television seasons, keyed by IDs such as `s01` |
| [`/v1/movies.json`](https://api.simpsonseh.com/v1/movies.json) | Released and announced films, keyed by IDs such as `movie-2007` |
| [`/v1/shorts/tracey-ullman.json`](https://api.simpsonseh.com/v1/shorts/tracey-ullman.json) | Tracey Ullman shorts, keyed by `MG01`–`MG48` production codes |
| [`/v1/shorts/disney-plus.json`](https://api.simpsonseh.com/v1/shorts/disney-plus.json) | Shorts available on Disney+, including earlier theatrical releases, keyed by stable title slugs |
| [`/v1/commercials.json`](https://api.simpsonseh.com/v1/commercials.json) | Commercials |
| [`/v1/specials.json`](https://api.simpsonseh.com/v1/specials.json) | Unnumbered specials other than feature films, keyed by stable title slugs |

Some categories are currently empty and return `{}`. A record may have a `links` object for verified external pages and a `streaming` object for known provider identifiers. Omitted data is unknown, not an assertion that it does not exist.

The [episode guide](https://api.simpsonseh.com/episodes/) groups numbered episodes into season tables and also lists movies, Tracey Ullman shorts, and Disney+ shorts. Select a row for regional titles, references, archived source fields, and a Disney+ link when a content ID is stored. Those playback links are built from imported IDs and are not a guarantee of current or regional availability.

## Lookups and API description

[`production.json`](https://api.simpsonseh.com/v1/production.json), [`tvdb.json`](https://api.simpsonseh.com/v1/tvdb.json), [`tmdb.json`](https://api.simpsonseh.com/v1/tmdb.json), and [`imdb.json`](https://api.simpsonseh.com/v1/imdb.json) map external identifiers to `{ "dataset": "...", "id": "..." }`. [`manifest.json`](https://api.simpsonseh.com/v1/manifest.json) lists the published files and their SHA-256 hashes. The machine-readable API description is [`openapi.json`](https://api.simpsonseh.com/openapi.json).

## License and contributions

Original metadata contributions are licensed [CC BY 4.0](LICENSE-DATA.md); code is [MIT licensed](LICENSE). Credit **Simpsons Metadata contributors** and link to [this repository](https://github.com/thewade/simpsons-metadata) when using the metadata. This project is unaffiliated with the rights holders of *The Simpsons*.

The JSON records in [`data/`](data/) are the source of truth. Corrections and additions are welcome through pull requests; see [CONTRIBUTING.md](CONTRIBUTING.md). Maintainer details are in [DESIGN.md](DESIGN.md), [DEPLOYMENT.md](DEPLOYMENT.md), and the [episode source notes](SOURCES.md).
