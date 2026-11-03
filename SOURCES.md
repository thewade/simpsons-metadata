# Metadata source pages

The JSON files in `data/` are the source of truth for this API. These Wikipedia
lists are reference pages used to check episode facts and links during periodic
manual syncs:

| Reference | Used for |
| --- | --- |
| [English episodes, seasons 1–20](https://en.wikipedia.org/wiki/List_of_The_Simpsons_episodes_%28seasons_1%E2%80%9320%29) | Aired order, original air dates, production codes, English episode articles |
| [English episodes, season 21 onward](https://en.wikipedia.org/wiki/List_of_The_Simpsons_episodes_%28season_21%E2%80%93present%29) | The same fields for later seasons |
| [French episode list](https://fr.wikipedia.org/wiki/Liste_des_%C3%A9pisodes_des_Simpson) | `titles.fr-FR`, `titles.fr-CA`, French episode articles, and French season articles |
| [French article for the 2007 film](https://fr.wikipedia.org/wiki/Les_Simpson%2C_le_film) | The film's shared French and Québec title and French article link |

The existing episode air dates and short first-release dates were migrated into
dated `en` release entries. This migration did not infer country or network from
the source lists. The published `original_air_date` remains derived from the
earliest dated release. Additional regional release details need their own
verification before being added.
The GB/Sky1 and US/FOX details for `s20e14` were supplied by the maintainer.

`links.wikipedia` points to a standalone English episode, season, or movie article.
`links.wikipedia_fr` points to a standalone French episode, season, or movie article. List-page
links belong in this document, not in those per-episode fields. An omitted title
or link means it was not established; a list placeholder such as “Titre
québécois inconnu” is not an episode title. Do not infer a French article URL
from a translated title. Check the link on the list or article page.

## Simpsons Archive episode pages

Checked on 2026-11-02. The [Simpsons Archive episode guides](https://www.simpsonsarchive.com/episodeguide/season1.html)
provide direct episode links for seasons 1–12 and the first ten entries in
[season 13](https://www.simpsonsarchive.com/episodeguide/season13.html). The
guide links were matched to 279 existing episode records by production code and
stored as `links.simpsons_archive`. Some guide `.html` links redirect to `.txt`
capsules; the guide's URL is retained. The separately verified
[`DABF06.txt` capsule](https://www.simpsonsarchive.com/episodes/DABF06.txt)
adds `s13e11`, for 280 links total. The old `legacy.SNPP` values remain as
historical source data, including the mistyped `episodea/3F19.html` path in
`s07e22`; its new link follows the [season 7 guide](https://www.simpsonsarchive.com/episodeguide/season7.html).
The later [season guides](https://www.simpsonsarchive.com/episodeguide/season14.html)
list episodes without individual links, so those records have no archive link.

## Refresh the French titles and links

The current French sync used [revision 240864494](https://fr.wikipedia.org/w/index.php?title=Liste_des_%C3%A9pisodes_des_Simpson&oldid=240864494),
downloaded on 2026-11-01. The sync matched all 801 existing numbered episode
records and added 801 French episode article links and 38 French season article
links. It filled 14 `fr-FR` and seven
`fr-CA` titles and corrected four existing `fr-FR` titles. The three production
code disagreements in `s24e19`, `s24e20`, and `s37e15` were left unchanged for
separate review.

For a later sync, save the **rendered HTML** of the French list, review the dry
run, then apply and validate:

```sh
mkdir -p dist
curl -L 'https://fr.wikipedia.org/wiki/Liste_des_%C3%A9pisodes_des_Simpson' -o dist/wiki-fr.html
python scripts/sync_wikipedia_fr.py --html dist/wiki-fr.html
python scripts/sync_wikipedia_fr.py --html dist/wiki-fr.html --apply
python -m unittest discover -s tests -v
python scripts/build.py
```

In PowerShell, replace the first two lines with
`New-Item -ItemType Directory -Force dist | Out-Null` and
`Invoke-WebRequest -Uri 'https://fr.wikipedia.org/wiki/Liste_des_%C3%A9pisodes_des_Simpson' -OutFile 'dist/wiki-fr.html'`.

The script matches existing episode records by overall episode number, verifies
their season episode number, and matches season records by season number. It
updates only known French titles and article links.
It reports production code disagreements without changing those fields. Review
the resulting diff and update the revision and date above when syncing again.

## Refresh regional episode release dates

`scripts/sync_wikipedia_fr_releases.py` reads each episode's known
`links.wikipedia_fr` article through the [MediaWiki Action API](https://www.mediawiki.org/wiki/API:Revisions)
and extracts `USA`, `France`, and `Québec` dates from its episode infobox. It
records the article revision ID, proposed changes, and any identity or date
disagreement in `dist/wiki-fr-release-report.json`. API responses are cached in
`dist/wiki-fr-release-cache/`. Both paths are ignored by Git.

```sh
python scripts/sync_wikipedia_fr_releases.py --refresh --as-of 2026-11-02
# Review dist/wiki-fr-release-report.json before merging:
python scripts/sync_wikipedia_fr_releases.py --offline --as-of 2026-11-02 --apply
python -m unittest discover -s tests -v
python scripts/build.py
```

Replace `--as-of` with the date of a later sync, or omit it to use the local
current date. The cutoff keeps announced future broadcasts out of actual
`releases`. A cached run (`--offline`) reproduces the reviewed proposal without
another network request; `--refresh` downloads new revisions. The tool verifies
season, episode number, production code, and existing English date where
available. If the article's USA date disagrees but its identity fields match,
the tool uses its regional dates while preserving the existing English entry.
If identity is uncertain, or a regional date precedes the recorded original
release, it leaves that date for manual review in the report. A France entry
with separate Disney+ and W9 dates keeps both releases and their networks.

On 2026-11-02, the report covered 803 distinct articles for 809 episodes. It
merged dates into 802 records, including 810 France and 346 Québec release
entries, and identified the US country for 786 existing English releases. Seven
records had unresolved article identity/date disagreements. Two France dates
were earlier than the existing original release, and one Québec broadcast was
still in the future; those dates were not merged. Review the report again when
refreshing the sources.

### Simpsons Park cross-check

The [Simpsons Park episode guide](https://www.simpsonspark.com/guide-des-episodes)
and its individual episode pages provide a secondary source for dates. On
2026-11-02, their season/episode numbers, production codes, and flag-marked
broadcast dates were checked for the seven records that the MediaWiki importer
could not identify confidently, and for the two France dates that preceded the
original release. The nine records have a direct `links.simpsonspark` URL.
The site distinguishes US, France, Québec, Belgium, and Disney+ dates; a
Belgium date was not treated as a France release. Its Disney+ dates are recorded
as France releases with `network: "Disney+"` when the linked French episode page
shows that platform. No Québec date was inferred from a French-language title.

| Episode | Added regional dates from its Simpsons Park page |
| --- | --- |
| [s07e01](https://www.simpsonspark.com/episodes/qui_a_tire_sur_mr_burns_partie_2) | France 1996-01-27 |
| [s12e15](https://www.simpsonspark.com/episodes/homer-fait-la-grve-de-la-faim) | France 2001-10-11 |
| [s12e16](https://www.simpsonspark.com/episodes/la-brute-et-les-surdous) | France 2001-10-15 |
| [s14e15](https://www.simpsonspark.com/episodes/homer-patron-de-la-centrale) | France 2003-12-27 |
| [s28e13](https://www.simpsonspark.com/episodes/phatsby-le-magnifique-2-2) | France 2019-01-12; Québec 2018-01-18 |
| [s31e20](https://www.simpsonspark.com/episodes/prtres-en-guerre-deuxime-partie) | France Disney+ 2020-10-02; Québec 2021-03-11 |
| [s33e07](https://www.simpsonspark.com/episodes/a-serious-flanders%C2%A0-parts-2) | France Disney+ 2022-10-05; Québec 2022-11-17 |
| [s36e06](https://www.simpsonspark.com/episodes/courts-mtrages-au-fminin) | France Disney+ 2025-01-24 |
| [s36e11](https://www.simpsonspark.com/episodes/un-nol-sous-hypnose-partie-2) | France Disney+ 2024-12-17 |

The French Wikipedia infoboxes for the multi-part episodes sometimes describe
only the first part. Simpsons Park has separate pages for both parts, allowing
the second parts to be matched by production code and episode number. Where the
two sources disagree, the source-specific dates and links above document the
choice. The MediaWiki importer will continue to report those discrepancies.

### Québec premiere networks

The maintainer supplied a season-based network mapping on 2026-11-02. Existing
dated `fr-CA` releases were checked against the corresponding broadcast period
before adding `network`:

| Seasons | Network | Applied to current releases |
| --- | --- | --- |
| 1 | Super Écran from 1991-02-15 | 13 undated releases |
| 2–12 | TQS | 256 undated releases |
| 13–35 | Télétoon, September 2004–September 2025 | 341 dated and 158 undated releases |
| 36 onward | Noovo from 2026-09-09 | Eight dated releases in season 36 |

The season 36 change is supported by [Bell Media's 2026 announcement](https://www.bellmedia.ca/fr/salle-de-presse/presse/bell-media-et-disney-annoncent-un-nouvel-accord-pour-la-diffusion-et-le-doublage-des-simpson-au-quebec-2/).
[Corus's autumn 2024 programming announcement](https://assets.corusent.com/wp-content/uploads/2024/08/Communique_Lancement_CorusFr_A24.pdf)
lists season 35 among Télétoon's new programming. The older [French Wikipedia
series history](https://fr.wikipedia.org/wiki/Les_Simpson) describes the
Super Écran, TQS, and Télétoon transitions. A [2004 Télétoon press release](https://www.simpsonspark.com/images/news/teletoon_simpson.pdf)
explicitly announces its season 13 Québec premiere, and [Simpsons Park's
broadcast history](https://www.simpsonspark.com/dossiers/pays) says TQS funded
the dub through season 12. These network values are inferred
from the season and date, rather than from an individual episode listing; an
episode-specific source takes precedence if a later check finds an exception.
Three existing `Télétoon (Canada)` labels were normalized to `Télétoon`.

The maintainer also confirmed on 2026-11-02 that every main-series episode
before season 36 had a Québec French dub. For 427 episodes in seasons 1–35
without a dated Québec release, an undated `{"language": "fr-CA", "country":
"CA"}` entry records that fact. Its `network` now follows the season mapping
above, while its premiere date remains unknown. Existing dated Québec entries
and their networks were preserved. The undated entries can be completed when
episode-level premiere evidence is found.

### US premiere networks

The maintainer confirmed that numbered episodes premiered on FOX in the US,
except the Disney+ exclusive episodes. The [FOX series page](https://www.fox.com/the-simpsons/)
identifies the broadcaster, while the [Disney+ exclusive episode
list](https://simpsonswiki.com/wiki/Disney%2B_exclusive_episodes) identifies the
eight exclusive numbered records by production code: `35ABF19`–`35ABF22` and
`36ABF19`–`36ABF22`. These are `s36e10`, `s36e11`, `s36e14`, `s36e18`, and
`s37e16`–`s37e19`. Their `en` US release entries have `network: "Disney+"`;
the other 801 numbered episodes' US entries have `network: "FOX"`. The 22
English entries whose country was still omitted were identified as US
premieres from this episode classification. The separate GB/Sky1 release in
`s20e14` remains alongside its later US/FOX release.
The [Wikisimpsons broadcast-order list](https://simpsonswiki.com/wiki/List_of_episodes)
was cross-checked on 2026-11-02: its Disney+ sections correspond to those same
eight records. It also lists four later season 38 broadcasts that are not yet
in this dataset; none is marked as a Disney+ premiere.

The [season 32 episode list](https://fr.wikipedia.org/wiki/Saison_32_des_Simpson)
also records a Canadian broadcast of `s32e04` on 2020-10-18 before its US
broadcast on 2020-11-01. The maintainer identified Citytv as the Canadian
network; a [contemporaneous episode reminder](https://tstoaddicts.com/2020/10/31/episode-reminder-treehouse-of-horror-xxxi-season-32-episode-4-2/)
independently notes the earlier Citytv airing. Its existing French releases
remain in the dataset, and the API's derived `original_air_date` is now
2020-10-18.

## Film articles

The 2007 film's [French article](https://fr.wikipedia.org/wiki/Les_Simpson%2C_le_film)
lists “Les Simpson, le film” as both the French and Québec title. As checked on
2026-11-01, the [2027 film's English article](https://en.wikipedia.org/wiki/The_New_Simpsons_Movie)
has no French Wikipedia language link, and no established French or Québec title
was found. Its `links.wikipedia_fr` is `null`; its regional titles remain omitted.
Recheck both when the film receives a localized title or French article.

## Short film sources

Checked on 2026-11-01. The Tracey Ullman dataset contains 48 shorts. [The Simpsons shorts, revision
1377993342](https://en.wikipedia.org/w/index.php?title=The_Simpsons_shorts&oldid=1377993342)
supplies the aired titles and dates; [Wikisimpsons production order, revision
1487273](https://simpsonswiki.com/w/index.php?title=List_of_episodes_by_production_order&oldid=1487273)
supplies the `MG01`–`MG48` production codes and individual Wikisimpsons links.
Wikipedia and Wikisimpsons disagree on the dates of `MG09`, `MG16`, `MG17`,
`MG28`, and `MG29`; these records use the dates on the Wikipedia shorts list.
The parenthesized `4W`/`5W` codes on Wikisimpsons belong to *The Tracey Ullman
Show* episodes and are not used as the shorts' production codes.
The two lists also use different English names for `MG10`, `MG15`, `MG19`, and
`MG40`; the records use the titles on the Wikipedia shorts list.

The Disney+ dataset contains the [nine shorts listed on Wikipedia, revision
1374017134](https://en.wikipedia.org/w/index.php?title=The_Simpsons_Disney%2B_shorts&oldid=1374017134),
plus four *Simpsons × Fortnite* shorts released on Disney+ in 2025:
[Apocalypse D'oh!](https://simpsonswiki.com/wiki/Apocalypse_D%27oh%21),
[Sugar High](https://simpsonswiki.com/wiki/Sugar_High),
[Multiplidiocy](https://simpsonswiki.com/wiki/Multiplidiocy), and
[The Incredible Bulk](https://simpsonswiki.com/wiki/The_Incredible_Bulk).
The dataset also includes three earlier shorts now available on Disney+:
[The Longest Daycare](https://en.wikipedia.org/wiki/The_Longest_Daycare),
[Playdate with Destiny](https://en.wikipedia.org/wiki/Playdate_with_Destiny), and
[Te Deseo Lo Mejor](https://en.wikipedia.org/wiki/Te_Deseo_Lo_Mejor).
Their dated release entries record their first public release, including theatrical
premieres for the two Maggie shorts. The Disney+ list does not provide production
codes for its nine films, and no verified codes were found for the other seven
shorts. All 16 use stable lowercase title slugs; `production_code` is omitted.
Full-length Disney+ exclusive episodes remain in `data/episodes/`.

[The Simpsons Yule Log](https://simpsonswiki.com/wiki/The_Simpsons_Yule_Log)
is an hour-long Disney+ special, so it is in `data/specials/`, keyed by a title
slug without a production code. Its December 22, 2025 release date comes from
that article. The repository owner supplied its French-language display title
and Disney+ content ID along with those of 12 shorts on November 1, 2026; see
[DISNEY_PLUS_IDS.md](DISNEY_PLUS_IDS.md).
