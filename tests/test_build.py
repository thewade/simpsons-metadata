import importlib.util
import json
from pathlib import Path
import tempfile
import unittest

ROOT = Path(__file__).resolve().parents[1]
spec = importlib.util.spec_from_file_location("simpsons_build", ROOT / "scripts" / "build.py")
module = importlib.util.module_from_spec(spec)
spec.loader.exec_module(module)
import_spec = importlib.util.spec_from_file_location("simpsons_import", ROOT / "scripts" / "import_legacy.py")
import_module = importlib.util.module_from_spec(import_spec)
import_spec.loader.exec_module(import_module)


class BuildTests(unittest.TestCase):
    def test_build_outputs_expected_maps(self):
        with tempfile.TemporaryDirectory() as temp:
            out = Path(temp) / "dist" / "v1"
            count = module.build(ROOT / "data", out)
            self.assertGreaterEqual(count, 2)
            self.assertTrue((out.parent / "index.html").is_file())
            api_spec = json.loads((out.parent / "openapi.json").read_text())
            self.assertEqual(api_spec["openapi"], "3.0.3")
            self.assertIn("/v1/episodes.json", api_spec["paths"])
            self.assertIn("/v1/shorts/disney-plus.json", api_spec["paths"])
            self.assertIn("/v1/movies.json", api_spec["paths"])
            production = json.loads((out / "production.json").read_text())
            self.assertEqual(production["7G08"], {"dataset": "episodes", "id": "s01e01"})
            self.assertEqual(production["MG01"], {"dataset": "shorts/tracey-ullman", "id": "MG01"})
            self.assertEqual(production["Movie1"], {"dataset": "movies", "id": "movie-2007"})
            self.assertEqual(json.loads((out / "commercials.json").read_text()), {})
            seasons = json.loads((out / "seasons.json").read_text())
            self.assertEqual(len(seasons), 38)
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
            self.assertEqual(movies["movie-2027"]["planned_release_date"], "2027-09-03")
            self.assertNotIn("production_code", movies["movie-2027"])
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

    def test_legacy_amazon_url_normalization(self):
        self.assertEqual(
            import_module.clean_amazon_url("http://www.amazon.ca/dp/B005SOH7QS?tag=simpeh-20", "B005SOH7QS"),
            "https://www.amazon.ca/dp/B005SOH7QS",
        )
        with self.assertRaisesRegex(ValueError, "disagree"):
            import_module.clean_amazon_url("http://www.amazon.ca/dp/B005SOH7QS?tag=simpeh-20", "B005SOH7MW")


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
