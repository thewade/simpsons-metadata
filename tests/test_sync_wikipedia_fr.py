import importlib.util
import json
from pathlib import Path
import tempfile
import unittest


ROOT = Path(__file__).resolve().parents[1]
spec = importlib.util.spec_from_file_location("wikipedia_fr_sync", ROOT / "scripts" / "sync_wikipedia_fr.py")
module = importlib.util.module_from_spec(spec)
spec.loader.exec_module(module)


class FrenchWikipediaSyncTests(unittest.TestCase):
    def test_season_links_come_from_article_anchors(self):
        html = '''<a href="https://fr.wikipedia.org/wiki/Saison_5_des_Simpson">Season 5</a>
        <a class="new" href="https://fr.wikipedia.org/wiki/Saison_6_des_Simpson">Season 6</a>'''
        links = module.parse_season_links(html)
        self.assertEqual(links, {5: "https://fr.wikipedia.org/wiki/Saison_5_des_Simpson"})
        with tempfile.TemporaryDirectory() as temp:
            path = Path(temp) / "s05.json"
            path.write_text(json.dumps({"id": "s05", "titles": {"en": "Season Five"},
                                        "links": {"wikipedia": "https://en.wikipedia.org/wiki/The_Simpsons_season_5"}}),
                            encoding="utf-8")
            plans = module.plan_season_updates(links, Path(temp))
        self.assertEqual(plans[0][1]["links"]["wikipedia_fr"], links[5])

    def test_parses_regional_titles_and_ignores_reference_markers(self):
        html = '''<table><tr><td id="ep26">26</td><td>13</td>
        <td><a href="https://fr.wikipedia.org/wiki/Tu_ne_déroberas_point">Tu ne déroberas point</a><sup class="reference">[1]</sup></td>
        <td>Homer vs. Lisa and the 8th Commandment</td>
        <td>Le <abbr>8<sup>e</sup></abbr> commandement</td><td>7F13</td></tr></table>'''
        rows = module.parse_episode_rows(html)
        self.assertEqual(rows[26]["cells"][2], "Tu ne déroberas point")
        self.assertEqual(rows[26]["cells"][4], "Le 8e commandement")
        with tempfile.TemporaryDirectory() as temp:
            path = Path(temp) / "s02e13.json"
            path.write_text(json.dumps({"id": "s02e13", "overall_number": 26,
                                        "titles": {"en": "Example"},
                                        "links": {"wikipedia": None}}), encoding="utf-8")
            plans, counts = module.plan_updates(rows, Path(temp))
        self.assertEqual(counts["matched_episodes"], 1)
        self.assertEqual(plans[0][1]["titles"]["fr-CA"], "Le 8e commandement")
        self.assertEqual(plans[0][1]["links"]["wikipedia_fr"],
                         "https://fr.wikipedia.org/wiki/Tu_ne_d%C3%A9roberas_point")

    def test_unknown_titles_remain_omitted(self):
        html = '''<tr><td id="ep900">900</td><td>1</td><td>Titre français inconnu</td>
        <td>Example</td><td>Titre québécois inconnu</td><td></td></tr>'''
        rows = module.parse_episode_rows(html)
        with tempfile.TemporaryDirectory() as temp:
            path = Path(temp) / "s40e01.json"
            path.write_text(json.dumps({"id": "s40e01", "overall_number": 900,
                                        "titles": {"en": "Example"}}), encoding="utf-8")
            plans, counts = module.plan_updates(rows, Path(temp))
        self.assertEqual(plans, [])
        self.assertEqual(counts["matched_episodes"], 1)


if __name__ == "__main__":
    unittest.main()
