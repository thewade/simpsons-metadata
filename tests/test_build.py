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
    def test_build_outputs_expected_maps(self):
        with tempfile.TemporaryDirectory() as temp:
            out = Path(temp) / "dist" / "v1"
            count = module.build(ROOT / "data", out)
            self.assertGreaterEqual(count, 2)
            production = json.loads((out / "production.json").read_text())
            self.assertEqual(production["7G08"], {"dataset": "episodes", "id": "s01e01"})
            self.assertEqual(production["MG01"], {"dataset": "shorts/tracey-ullman", "id": "MG01"})
            self.assertEqual(json.loads((out / "commercials.json").read_text()), {})

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
