# Wikipedia source pages

The JSON files in `data/` are the source of truth for this API. These Wikipedia
lists are reference pages used to check episode facts and links during periodic
manual syncs:

| Reference | Used for |
| --- | --- |
| [English episodes, seasons 1–20](https://en.wikipedia.org/wiki/List_of_The_Simpsons_episodes_%28seasons_1%E2%80%9320%29) | Aired order, original air dates, production codes, English episode articles |
| [English episodes, season 21 onward](https://en.wikipedia.org/wiki/List_of_The_Simpsons_episodes_%28season_21%E2%80%93present%29) | The same fields for later seasons |
| [French episode list](https://fr.wikipedia.org/wiki/Liste_des_%C3%A9pisodes_des_Simpson) | `titles.fr-FR`, `titles.fr-CA`, French episode articles, and French season articles |
| [French article for the 2007 film](https://fr.wikipedia.org/wiki/Les_Simpson%2C_le_film) | The film's shared French and Québec title and French article link |

`links.wikipedia` points to a standalone English episode, season, or movie article.
`links.wikipedia_fr` points to a standalone French episode, season, or movie article. List-page
links belong in this document, not in those per-episode fields. An omitted title
or link means it was not established; a list placeholder such as “Titre
québécois inconnu” is not an episode title. Do not infer a French article URL
from a translated title. Check the link on the list or article page.

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
