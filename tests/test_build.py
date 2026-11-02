import importlib.util
import json
from pathlib import Path
import tempfile
import unittest

ROOT = Path(__file__).resolve().parents[1]
spec = importlib.util.spec_from_file_location("simpsons_build", ROOT / "scripts" / "build.py")
module = importlib.util.module_from_spec(spec)
spec.loader.exec_module(module)


class BuildTests(unittest.TestCase):
    def test_episode_guide_escapes_metadata_and_links_only_known_ids(self):
        guide = module.render_episode_guide({
            "seasons": {"s01": {"id": "s01"}},
            "episodes": {"s01e01": {
                "id": "s01e01", "titles": {"en": "<script>alert(1)</script>"},
                "links": {"wikipedia": None},
                "streaming": {"disney_plus": {"content_id": "id?part"}},
            }},
        })
        self.assertIn("&lt;script&gt;alert(1)&lt;/script&gt;", guide)
        self.assertNotIn("<script>alert(1)</script>", guide)
        self.assertIn("No standalone English Wikipedia article", guide)
        self.assertIn("https://www.disneyplus.com/play/id%3Fpart", guide)

    def test_build_outputs_expected_maps(self):
        with tempfile.TemporaryDirectory() as temp:
            out = Path(temp) / "dist" / "v1"
            count = module.build(ROOT / "data", out)
            self.assertGreaterEqual(count, 2)
            self.assertTrue((out.parent / "index.html").is_file())
            self.assertTrue((out.parent / "docs" / "index.html").is_file())
            self.assertIn('href="/docs/"', (out.parent / "index.html").read_text())
            guide = (out.parent / "episodes" / "index.html").read_text(encoding="utf-8")
            self.assertIn('href="/episodes/"', (out.parent / "index.html").read_text())
            self.assertEqual(guide.count('<tr class="episode-row"'),
                             len(json.loads((out / "episodes.json").read_text())))
            self.assertIn('id="classic"', guide)
            self.assertIn('id="modern"', guide)
            self.assertIn('id="season-38"', guide)
            self.assertIn('French article', guide)
            self.assertIn('id="s01e01-details" hidden', guide)
            self.assertIn('https://www.disneyplus.com/play/ffb14e5a-38db-4522-a559-3cfa52bcf4df', guide)
            self.assertNotIn('href="https://www.disneyplus.com/play/not-ported-over"', guide)
            self.assertIn('Wikipedia (French)', guide)
            episodes = json.loads((out / "episodes.json").read_text(encoding="utf-8"))
            self.assertEqual(sum("wikipedia_fr" in record.get("links", {}) for record in episodes.values()),
                             len(episodes))
            self.assertTrue(all(record["links"]["wikipedia_fr"].startswith("https://fr.wikipedia.org/wiki/")
                                for record in episodes.values()))
            self.assertTrue(all("\ufffd" not in title for record in episodes.values()
                                for title in record["titles"].values()))
            self.assertEqual(episodes["s37e07"]["titles"]["fr-FR"], "L'Empire Quimby")
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
            self.assertEqual(production["Movie1"], {"dataset": "movies", "id": "movie-2007"})
            ullman = json.loads((out / "shorts" / "tracey-ullman.json").read_text(encoding="utf-8"))
            self.assertEqual(set(ullman), {f"MG{number:02}" for number in range(1, 49)})
            self.assertEqual(ullman["MG09"]["original_air_date"], "1987-09-20")
            self.assertEqual(ullman["MG40"]["titles"]["en"], "Simpson Xmas")
            self.assertTrue(all(record["links"]["simpsonswiki"].startswith("https://simpsonswiki.com/wiki/")
                                for record in ullman.values()))
            disney_shorts = json.loads((out / "shorts" / "disney-plus.json").read_text(encoding="utf-8"))
            self.assertEqual(len(disney_shorts), 13)
            self.assertEqual(disney_shorts["the-force-awakens-from-its-nap"]["original_air_date"],
                             "2021-05-04")
            self.assertEqual(disney_shorts["apocalypse-doh"]["original_air_date"], "2025-11-01")
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
            self.assertEqual(json.loads((out / "specials.json").read_text()), {})
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

    def test_disney_short_allows_slug_without_production_code(self):
        with tempfile.TemporaryDirectory() as temp:
            path = Path(temp) / "sample-short.json"
            path.write_text(json.dumps({"id": "sample-short", "titles": {"en": "Sample Short"},
                                        "original_air_date": "2025-11-01"}), encoding="utf-8")
            self.assertNotIn("production_code", module.parse_record(path, "shorts/disney-plus"))
            bad = Path(temp) / "SampleShort.json"
            bad.write_text(json.dumps({"id": "SampleShort", "titles": {"en": "Sample"}}),
                           encoding="utf-8")
            with self.assertRaisesRegex(module.ValidationError, "lowercase title slug"):
                module.parse_record(bad, "shorts/disney-plus")

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
