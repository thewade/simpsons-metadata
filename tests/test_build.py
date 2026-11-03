import importlib.util
import json
from pathlib import Path
import re
import tempfile
import unittest

ROOT = Path(__file__).resolve().parents[1]
spec = importlib.util.spec_from_file_location("simpsons_build", ROOT / "scripts" / "build.py")
module = importlib.util.module_from_spec(spec)
spec.loader.exec_module(module)


class BuildTests(unittest.TestCase):
    def test_guide_title_fallbacks(self):
        titles = {"en": "English", "fr": "French", "fr-FR": "France", "fr-CA": "Québec"}
        self.assertEqual(module.guide_title(titles, "en"), "English")
        self.assertEqual(module.guide_title(titles, "fr-FR"), "France")
        self.assertEqual(module.guide_title(titles, "fr-CA"), "Québec")
        self.assertEqual(module.guide_title({"en": "English", "fr-FR": "France"}, "fr-CA"), "France")
        self.assertEqual(module.guide_title({"en": "English", "fr": "French"}, "fr-CA"), "French")
        self.assertEqual(module.guide_title({"en": "English"}, "fr-CA"), "English")

    def test_episode_guide_escapes_metadata_and_links_only_known_ids(self):
        guide = module.render_episode_guide({
            "seasons": {"s01": {"id": "s01"}},
            "episodes": {"s01e01": {
                "id": "s01e01", "titles": {"en": "<script>alert(1)</script>"},
                "links": {"wikipedia": None},
                "streaming": {"disney_plus": {"content_id": "id?part"}},
            }},
            "movies": {"movie-2027": {
                "id": "movie-2027", "titles": {"en": "Film & <script>"},
                "planned_release_date": "2027-09-03",
            }},
        })
        self.assertIn("&lt;script&gt;alert(1)&lt;/script&gt;", guide)
        self.assertNotIn("<script>alert(1)</script>", guide)
        self.assertIn("No standalone English Wikipedia article", guide)
        self.assertIn("https://www.disneyplus.com/play/id%3Fpart", guide)
        self.assertIn("Film &amp; &lt;script&gt;", guide)
        self.assertNotIn("Film & <script>", guide)
        self.assertIn('<div data-english-title hidden><dt data-i18n="englishTitle">English title</dt>'
                      '<dd>&lt;script&gt;alert(1)&lt;/script&gt;</dd></div>', guide)
        self.assertIn('id="movie-2027-details" hidden', guide)
        self.assertIn('September 3, 2027</time> <span class="date-note" data-i18n="planned">(planned)</span>', guide)

    def test_build_outputs_expected_maps(self):
        with tempfile.TemporaryDirectory() as temp:
            out = Path(temp) / "dist" / "v1"
            count = module.build(ROOT / "data", out)
            self.assertGreaterEqual(count, 2)
            self.assertTrue((out.parent / "index.html").is_file())
            self.assertTrue((out.parent / "docs" / "index.html").is_file())
            self.assertTrue((out.parent / "site-i18n.js").is_file())
            self.assertIn('href="/docs/"', (out.parent / "index.html").read_text())
            landing = (out.parent / "index.html").read_text(encoding="utf-8")
            self.assertIn('id="language-select"', landing)
            self.assertIn('src="site-i18n.js"', landing)
            self.assertIn('id="sample-title" data-title-en="Simpsons Roasting on an Open Fire" '
                          'data-title-fr-fr="Noël mortel" data-title-fr-ca="Homer au nez rouge"', landing)
            guide = (out.parent / "episodes" / "index.html").read_text(encoding="utf-8")
            self.assertIn('id="language-select"', guide)
            self.assertIn('src="../site-i18n.js"', guide)
            self.assertIn('data-title-fr-fr="Noël mortel" data-title-fr-ca="Homer au nez rouge"', guide)
            self.assertRegex(guide, r'id="s13e14"[^\n]*data-title-fr-fr="To Bart or not to Bart"'
                                    r' data-title-fr-ca="Contes du domaine public"')
            i18n = (out.parent / "site-i18n.js").read_text(encoding="utf-8")
            french_keys = set(re.findall(r'^\s+([A-Za-z][A-Za-z0-9]*):',
                                         i18n.split("const french = {", 1)[1].split("\n  };", 1)[0], re.M))
            used_keys = set(re.findall(r'data-i18n(?:-html|-aria)?="([A-Za-z][A-Za-z0-9]*)"',
                                       landing + guide))
            self.assertFalse(used_keys - french_keys)
            self.assertIn('href="/episodes/"', (out.parent / "index.html").read_text())
            self.assertEqual(guide.count('<tr class="episode-row"'),
                             len(json.loads((out / "episodes.json").read_text())))
            self.assertEqual(guide.count('<tr class="episode-row media-row"'), 66)
            ids = re.findall(r'\bid="([^"]+)"', guide)
            controls = re.findall(r'\baria-controls="([^"]+)"', guide)
            self.assertEqual(len(ids), len(set(ids)))
            self.assertEqual(len(controls), guide.count('<tr class="episode-row'))
            self.assertTrue(set(controls).issubset(ids))
            self.assertIn('id="classic"', guide)
            self.assertIn('id="modern"', guide)
            self.assertIn('id="movies"', guide)
            self.assertIn('id="tracey-ullman-shorts"', guide)
            self.assertIn('id="disney-plus-shorts"', guide)
            self.assertIn('id="movie-2007-details" hidden', guide)
            self.assertIn('id="MG01-details" hidden', guide)
            self.assertIn('id="the-longest-daycare-details" hidden', guide)
            self.assertIn('DVD on Amazon', guide)
            self.assertIn('https://www.disneyplus.com/play/066a121a-a89a-44a8-9f2d-56b21f0c7241', guide)
            self.assertIn('id="season-38"', guide)
            self.assertIn('French article', guide)
            self.assertIn('id="s01e01-details" hidden', guide)
            self.assertIn('<dt data-i18n="aspectRatio">Original aspect ratio</dt><dd>4:3</dd>', guide)
            self.assertIn('<dt data-i18n="aspectRatio">Original aspect ratio</dt><dd>16:9</dd>', guide)
            self.assertIn('https://www.disneyplus.com/play/ffb14e5a-38db-4522-a559-3cfa52bcf4df', guide)
            self.assertNotIn('href="https://www.disneyplus.com/play/not-ported-over"', guide)
            self.assertIn('Wikipedia (French)', guide)
            self.assertIn('Simpsons Archive', guide)
            episodes = json.loads((out / "episodes.json").read_text(encoding="utf-8"))
            self.assertTrue(all(record["original_air_date"] ==
                                min(release["date"] for release in record["releases"] if "date" in release)
                                for record in episodes.values()))
            self.assertTrue(all(any(release["language"] == "fr-CA" and release.get("country") == "CA"
                                    for release in record["releases"])
                                for record in episodes.values() if int(record["id"][1:3]) < 36))
            self.assertIn({"language": "fr-CA", "country": "CA", "network": "Super Écran"},
                          episodes["s01e01"]["releases"])
            self.assertIn({"language": "fr-CA", "country": "CA", "network": "TQS"},
                          episodes["s09e01"]["releases"])
            self.assertIn({"language": "fr-CA", "country": "CA", "network": "Télétoon"},
                          episodes["s13e01"]["releases"])
            disney_exclusive = {"s36e10", "s36e11", "s36e14", "s36e18",
                                "s37e16", "s37e17", "s37e18", "s37e19"}
            for episode in episodes.values():
                us_releases = [item for item in episode["releases"]
                               if item["language"] == "en" and item.get("country") == "US"]
                self.assertEqual(len(us_releases), 1, episode["id"])
                self.assertEqual(us_releases[0]["network"],
                                 "Disney+" if episode["id"] in disney_exclusive else "FOX")
            self.assertEqual(episodes["s20e14"]["releases"][:2], [
                {"language": "en", "date": "2009-03-17", "country": "GB", "network": "Sky1"},
                {"language": "en", "date": "2009-03-22", "country": "US", "network": "FOX"},
            ])
            self.assertEqual(episodes["s32e04"]["original_air_date"], "2020-10-18")
            self.assertIn({"language": "en", "date": "2020-10-18", "country": "CA",
                           "network": "Citytv"}, episodes["s32e04"]["releases"])
            self.assertTrue(any(item["language"] == "fr-FR" and item["country"] == "FR"
                                for item in episodes["s20e14"]["releases"]))
            self.assertIn({"language": "fr-CA", "date": "2015-11-26", "country": "CA",
                           "network": "Télétoon"}, episodes["s26e13"]["releases"])
            self.assertIn({"language": "fr-CA", "date": "2026-10-21", "country": "CA",
                           "network": "Noovo"}, episodes["s36e07"]["releases"])
            self.assertEqual(episodes["s20e09"]["original_aspect_ratio"], "4:3")
            self.assertEqual(episodes["s20e10"]["original_aspect_ratio"], "16:9")
            self.assertEqual(sum("original_aspect_ratio" in record for record in episodes.values()), len(episodes))
            self.assertTrue(all(record["original_aspect_ratio"] ==
                                ("4:3" if tuple(map(int, record["id"][1:].split("e"))) <= (20, 9) else "16:9")
                                for record in episodes.values()))
            self.assertEqual(sum("wikipedia_fr" in record.get("links", {}) for record in episodes.values()),
                             len(episodes))
            self.assertTrue(all(record["links"]["wikipedia_fr"].startswith("https://fr.wikipedia.org/wiki/")
                                for record in episodes.values()))
            self.assertTrue(all("\ufffd" not in title for record in episodes.values()
                                for title in record["titles"].values()))
            self.assertEqual(episodes["s37e07"]["titles"]["fr-FR"], "L'Empire Quimby")
            archive_links = {key: record["links"]["simpsons_archive"] for key, record in episodes.items()
                             if "simpsons_archive" in record.get("links", {})}
            self.assertEqual(len(archive_links), 280)
            self.assertEqual(archive_links["s01e01"],
                             "https://www.simpsonsarchive.com/episodes/7G08.html")
            self.assertEqual(archive_links["s07e22"],
                             "https://www.simpsonsarchive.com/episodes/3F19.html")
            self.assertEqual(archive_links["s13e11"],
                             "https://www.simpsonsarchive.com/episodes/DABF06.txt")
            self.assertNotIn("s13e12", archive_links)
            self.assertNotIn("s14e01", archive_links)
            exclusive_ids = {
                "s36e10": "ed114092-e308-46da-8a7c-04272cce1e45",
                "s36e11": "ed114092-e308-46da-8a7c-04272cce1e45",
                "s36e14": "c27f4ec6-3cf9-485c-9b40-9f0d0fba639d",
                "s36e18": "7624fc2b-178e-460c-ab85-9af4ced2e510",
                "s37e16": "1173a9d5-2521-4f37-b6a1-cddbd20fb393",
                "s37e17": "1173a9d5-2521-4f37-b6a1-cddbd20fb393",
                "s37e18": "bc7b17f1-bf0b-46f8-8654-d67354c6c268",
                "s37e19": "5acb669f-c090-4b00-8dfd-36710909ee1d",
            }
            for episode_id, content_id in exclusive_ids.items():
                self.assertEqual(episodes[episode_id]["streaming"]["disney_plus"]["content_id"], content_id)
            self.assertEqual(episodes["s36e10"]["titles"]["fr-CA"], "Un Noël sous hypnose")
            self.assertEqual(episodes["s37e16"]["titles"]["fr-CA"],
                             "Les Simpson : Extreme Makeover : Homer Edition")
            self.assertEqual(episodes["s37e19"]["overall_number"], 809)
            self.assertIn("https://www.disneyplus.com/play/1173a9d5-2521-4f37-b6a1-cddbd20fb393", guide)
            self.assertEqual(episodes["s36e01"]["titles"]["fr-CA"], "La fête de Bart")
            api_spec = json.loads((out.parent / "openapi.json").read_text())
            self.assertEqual(api_spec["openapi"], "3.0.3")
            self.assertIn("/v1/episodes.json", api_spec["paths"])
            self.assertIn("/v1/shorts/disney-plus.json", api_spec["paths"])
            self.assertIn("/v1/movies.json", api_spec["paths"])
            production = json.loads((out / "production.json").read_text())
            self.assertEqual(production["7G08"], {"dataset": "episodes", "id": "s01e01"})
            self.assertEqual(production["MG01"], {"dataset": "shorts/tracey-ullman", "id": "MG01"})
            self.assertEqual(production["MG48"], {"dataset": "shorts/tracey-ullman", "id": "MG48"})
            self.assertEqual(production["36ABF21"], {"dataset": "episodes", "id": "s37e17"})
            self.assertEqual(production["RABF13"], {"dataset": "episodes", "id": "s24e19"})
            self.assertEqual(production["RABF12"], {"dataset": "episodes", "id": "s24e20"})
            self.assertEqual(production["Movie1"], {"dataset": "movies", "id": "movie-2007"})
            ullman = json.loads((out / "shorts" / "tracey-ullman.json").read_text(encoding="utf-8"))
            self.assertEqual(set(ullman), {f"MG{number:02}" for number in range(1, 49)})
            self.assertEqual(ullman["MG09"]["original_air_date"], "1987-09-20")
            self.assertTrue(all(record["releases"] ==
                                [{"language": "en", "date": record["original_air_date"]}]
                                for record in ullman.values()))
            self.assertEqual(ullman["MG40"]["titles"]["en"], "Simpson Xmas")
            self.assertTrue(all(record["links"]["simpsonswiki"].startswith("https://simpsonswiki.com/wiki/")
                                for record in ullman.values()))
            disney_shorts = json.loads((out / "shorts" / "disney-plus.json").read_text(encoding="utf-8"))
            self.assertEqual(len(disney_shorts), 16)
            self.assertTrue(all(record["releases"] ==
                                [{"language": "en", "date": record["original_air_date"]}]
                                for record in disney_shorts.values()))
            self.assertEqual(disney_shorts["the-force-awakens-from-its-nap"]["original_air_date"],
                             "2021-05-04")
            self.assertEqual(disney_shorts["apocalypse-doh"]["original_air_date"], "2025-11-01")
            supplied_short_ids = {
                "the-most-wonderful-time-of-the-year": "3839790c-c962-4d61-a5f8-ba2350a83f47",
                "may-the-12th-be-with-you": "28a4c172-5dda-460f-a7e0-98d29c5b3d7f",
                "rogue-not-quite-one": "13c6353b-7794-420c-9a84-831b4943d271",
                "the-simpsons-meet-the-bocellis-in-feliz-navidad": "1dcf7fc2-0989-44eb-992c-938c07a1c26f",
                "welcome-to-the-club": "1d60097d-e7a1-4fe2-8fe1-038f5f46d709",
                "when-billie-met-lisa": "ea439976-b9b0-4ac6-b79f-77c7b1a709da",
                "the-good-the-bart-and-the-loki": "3ffb8049-a23a-4251-b0f6-8a70386919e2",
                "the-force-awakens-from-its-nap": "8ca133cb-d680-45f7-ba51-fc7c92c61db0",
                "the-longest-daycare": "066a121a-a89a-44a8-9f2d-56b21f0c7241",
                "playdate-with-destiny": "6ea838b5-b5ac-45e0-8980-881d906a91a0",
                "plusaversary": "3c791468-6f02-4c33-bbff-ee4b54ef8feb",
                "te-deseo-lo-mejor": "4d935ff3-aa17-4e11-975a-30009a09b359",
            }
            for short_id, content_id in supplied_short_ids.items():
                self.assertEqual(disney_shorts[short_id]["streaming"]["disney_plus"]["content_id"], content_id)
                self.assertIn("fr", disney_shorts[short_id]["titles"])
                self.assertNotIn("fr-CA", disney_shorts[short_id]["titles"])
            self.assertEqual(disney_shorts["playdate-with-destiny"]["titles"]["fr"],
                             "Maggie Simpson dans « Le Jeu du Destin »")
            self.assertTrue(all("production_code" not in record for record in disney_shorts.values()))
            self.assertNotIn("apocalypse-doh", production)
            self.assertEqual(json.loads((out / "commercials.json").read_text()), {})
            seasons = json.loads((out / "seasons.json").read_text())
            self.assertEqual(len(seasons), 38)
            self.assertEqual(sum("wikipedia_fr" in record.get("links", {}) for record in seasons.values()), 38)
            self.assertEqual(seasons["s05"]["links"]["wikipedia_fr"],
                             "https://fr.wikipedia.org/wiki/Saison_5_des_Simpson")
            self.assertNotIn("movie", seasons)
            self.assertEqual(seasons["s38"]["links"]["wikipedia"],
                             "https://en.wikipedia.org/wiki/The_Simpsons_season_38")
            self.assertEqual([item["format"] for item in seasons["s14"]["amazon_listings"]],
                             ["dvd", "blu_ray"])
            self.assertEqual(seasons["s01"]["amazon_listings"][0]["format"], "dvd")
            self.assertEqual(seasons["s20"]["amazon_listings"][0]["format"], "blu_ray")
            self.assertEqual(seasons["s14"]["amazon_listings"][0]["url"],
                             "https://www.amazon.ca/dp/B005SOH7QS")
            movies = json.loads((out / "movies.json").read_text())
            self.assertEqual(set(movies), {"movie-2007", "movie-2027"})
            self.assertEqual(movies["movie-2007"]["release_date"], "2007-07-26")
            self.assertEqual(movies["movie-2007"]["production_code"], "Movie1")
            self.assertEqual(movies["movie-2007"]["titles"]["fr-FR"], "Les Simpson, le film")
            self.assertEqual(movies["movie-2007"]["titles"]["fr-CA"], "Les Simpson, le film")
            self.assertEqual(movies["movie-2007"]["links"]["wikipedia_fr"],
                             "https://fr.wikipedia.org/wiki/Les_Simpson,_le_film")
            self.assertEqual(movies["movie-2027"]["planned_release_date"], "2027-09-03")
            self.assertNotIn("production_code", movies["movie-2027"])
            self.assertIsNone(movies["movie-2027"]["links"]["wikipedia_fr"])
            self.assertNotIn("fr-FR", movies["movie-2027"]["titles"])
            specials = json.loads((out / "specials.json").read_text(encoding="utf-8"))
            self.assertEqual(set(specials), {"the-simpsons-yule-log"})
            self.assertEqual(specials["the-simpsons-yule-log"]["streaming"]["disney_plus"]["content_id"],
                             "e04cc982-370f-4b16-96c4-73218b8bb168")
            self.assertEqual(specials["the-simpsons-yule-log"]["titles"]["fr"],
                             "The Simpsons Yule Log")
            self.assertNotIn("the-simpsons-yule-log", production)
            self.assertEqual(json.loads((out / "manifest.json").read_text())["api_version"], 1)

    def test_rejects_duplicate_external_ids(self):
        with tempfile.TemporaryDirectory() as temp:
            source = Path(temp) / "data"
            for dataset in module.DATASETS:
                (source / dataset).mkdir(parents=True)
            for key in ("s01e01", "s01e02"):
                (source / "episodes" / f"{key}.json").write_text(json.dumps({
                    "id": key, "titles": {"en": key}, "tvdb": "SAME"
                }))
            with self.assertRaisesRegex(module.ValidationError, "Duplicate tvdb"):
                module.collect(source)

    def test_rejects_missing_non_episode_production(self):
        with tempfile.TemporaryDirectory() as temp:
            path = Path(temp) / "MG01.json"
            path.write_text(json.dumps({"id": "MG01", "titles": {"en": "Good Night"}}))
            with self.assertRaisesRegex(module.ValidationError, "production_code"):
                module.parse_record(path, "shorts/tracey-ullman")

    def test_rejects_wrong_original_aspect_ratio(self):
        with tempfile.TemporaryDirectory() as temp:
            path = Path(temp) / "s20e10.json"
            record = {"id": "s20e10", "titles": {"en": "Example"},
                      "original_aspect_ratio": "4:3"}
            path.write_text(json.dumps(record), encoding="utf-8")
            with self.assertRaisesRegex(module.ValidationError, "original_aspect_ratio"):
                module.parse_record(path, "episodes")

    def test_disney_short_allows_slug_without_production_code(self):
        with tempfile.TemporaryDirectory() as temp:
            path = Path(temp) / "sample-short.json"
            path.write_text(json.dumps({"id": "sample-short", "titles": {"en": "Sample Short"},
                                        "releases": [{"language": "en", "date": "2025-11-01"}]}),
                            encoding="utf-8")
            self.assertNotIn("production_code", module.parse_record(path, "shorts/disney-plus"))
            bad = Path(temp) / "SampleShort.json"
            bad.write_text(json.dumps({"id": "SampleShort", "titles": {"en": "Sample"}}),
                           encoding="utf-8")
            with self.assertRaisesRegex(module.ValidationError, "lowercase title slug"):
                module.parse_record(bad, "shorts/disney-plus")

    def test_special_allows_slug_without_production_code(self):
        with tempfile.TemporaryDirectory() as temp:
            path = Path(temp) / "sample-special.json"
            path.write_text(json.dumps({"id": "sample-special", "titles": {"en": "Sample Special"}}),
                            encoding="utf-8")
            self.assertNotIn("production_code", module.parse_record(path, "specials"))
            bad = Path(temp) / "SampleSpecial.json"
            bad.write_text(json.dumps({"id": "SampleSpecial", "titles": {"en": "Sample"}}),
                           encoding="utf-8")
            with self.assertRaisesRegex(module.ValidationError, "lowercase title slug"):
                module.parse_record(bad, "specials")

    def test_rejects_duplicate_json_keys(self):
        with tempfile.TemporaryDirectory() as temp:
            path = Path(temp) / "s01e01.json"
            path.write_text('{"id":"s01e01","id":"s01e01","titles":{"en":"Hello"}}')
            with self.assertRaisesRegex(module.ValidationError, "Duplicate JSON key"):
                module.parse_record(path, "episodes")

    def test_rejects_bad_language_tag(self):
        with tempfile.TemporaryDirectory() as temp:
            path = Path(temp) / "s01e01.json"
            path.write_text(json.dumps({"id": "s01e01", "titles": {"fr_CA": "Titre"}}))
            with self.assertRaisesRegex(module.ValidationError, "language tag"):
                module.parse_record(path, "episodes")

    def test_releases_allow_unknown_dates_and_derive_first_air_date(self):
        with tempfile.TemporaryDirectory() as temp:
            path = Path(temp) / "s01e01.json"
            record = {"id": "s01e01", "titles": {"en": "Example"}, "releases": [
                {"language": "en", "date": "2009-03-22", "country": "US", "network": "FOX"},
                {"language": "en", "date": "2009-03-17", "country": "GB", "network": "Sky1"},
                {"language": "fr-CA", "country": "CA"},
            ]}
            path.write_text(json.dumps(record), encoding="utf-8")
            parsed = module.parse_record(path, "episodes")
            self.assertEqual(parsed["original_air_date"], "2009-03-17")
            self.assertNotIn("date", parsed["releases"][2])
            for invalid in (
                {"language": "fr-CA", "date": None},
                {"language": "fr_CA"},
                {"language": "en", "date": "2009-02-30"},
                {"language": "en", "country": "UK1"},
                {"language": "en", "network": " "},
            ):
                with self.subTest(invalid=invalid):
                    record["releases"] = [invalid]
                    path.write_text(json.dumps(record), encoding="utf-8")
                    with self.assertRaises(module.ValidationError):
                        module.parse_record(path, "episodes")
            record["releases"] = [{"language": "en", "date": "2009-03-17"}]
            record["original_air_date"] = "2009-03-22"
            path.write_text(json.dumps(record), encoding="utf-8")
            with self.assertRaisesRegex(module.ValidationError, "derived from releases"):
                module.parse_record(path, "episodes")

    def test_validates_reference_links(self):
        with tempfile.TemporaryDirectory() as temp:
            path = Path(temp) / "s01e01.json"
            record = {"id": "s01e01", "titles": {"en": "Example"},
                      "links": {"wikipedia": "https://en.wikipedia.org/wiki/List_of_The_Simpsons_episodes#ep1"}}
            path.write_text(json.dumps(record))
            self.assertEqual(module.parse_record(path, "episodes")["links"], record["links"])
            record["links"] = {"wikipedia": None}
            path.write_text(json.dumps(record))
            self.assertIsNone(module.parse_record(path, "episodes")["links"]["wikipedia"])
            for invalid in (None, {}, {"wikipedia": "http://en.wikipedia.org/wiki/Example"},
                            {"bad name": "https://example.org"},
                            {"wikipedia": "https://user@example.org/page"},
                            {"wikipedia": False}):
                with self.subTest(links=invalid):
                    record["links"] = invalid
                    path.write_text(json.dumps(record))
                    with self.assertRaisesRegex(module.ValidationError, "links|link name"):
                        module.parse_record(path, "episodes")

    def test_rejects_affiliate_amazon_listing(self):
        with tempfile.TemporaryDirectory() as temp:
            path = Path(temp) / "s14.json"
            path.write_text(json.dumps({
                "id": "s14", "titles": {"en": "Season Fourteen"},
                "amazon_listings": [{"url": "https://www.amazon.ca/dp/B005SOH7QS?tag=affiliate",
                                     "asin": "B005SOH7QS", "format": "dvd"}]
            }))
            with self.assertRaisesRegex(module.ValidationError, "clean HTTPS ASIN link"):
                module.parse_record(path, "seasons")

    def test_movie_without_production_code_and_release_date_validation(self):
        with tempfile.TemporaryDirectory() as temp:
            path = Path(temp) / "movie-2027.json"
            record = {"id": "movie-2027", "titles": {"en": "New Movie"},
                      "planned_release_date": "2027-09-03"}
            path.write_text(json.dumps(record))
            self.assertEqual(module.parse_record(path, "movies"), record)
            record["planned_release_date"] = "2027-02-30"
            path.write_text(json.dumps(record))
            with self.assertRaisesRegex(module.ValidationError, "planned_release_date"):
                module.parse_record(path, "movies")
            path = Path(temp) / "new-movie.json"
            record["id"] = "new-movie"
            record["planned_release_date"] = "2027-09-03"
            path.write_text(json.dumps(record))
            with self.assertRaisesRegex(module.ValidationError, "movie-YYYY"):
                module.parse_record(path, "movies")

if __name__ == "__main__":
    unittest.main()

class StreamingTests(unittest.TestCase):
    def _parse(self, disney):
        with tempfile.TemporaryDirectory() as temp:
            path = Path(temp) / 's01e01.json'
            path.write_text(json.dumps({'id':'s01e01', 'titles':{'en':'Example'},'streaming':{'disney_plus': disney}}))
            return module.parse_record(path,'episodes')

    def test_accepts_verified_shape(self):
        record = self._parse({'content_id':'abc-123','url':'https://www.disneyplus.com/play/abc-123'})
        self.assertEqual(record['streaming']['disney_plus']['content_id'], 'abc-123')

    def test_rejects_mismatched_content_id(self):
        with self.assertRaisesRegex(module.ValidationError, 'disagree'):
            self._parse({'content_id':'abc','url':'https://www.disneyplus.com/play/xyz'})

    def test_rejects_unsupported_playback_parameters(self):
        with self.assertRaisesRegex(module.ValidationError, 'no query/fragment'):
            self._parse({'url':'https://www.disneyplus.com/play/abc?t=30'})

    def test_rejects_unsupported_language_overrides(self):
        with self.assertRaisesRegex(module.ValidationError, 'unsupported Disney'):
            self._parse({'content_id':'abc','audio_language':'fr-CA'})
