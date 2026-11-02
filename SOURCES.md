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
