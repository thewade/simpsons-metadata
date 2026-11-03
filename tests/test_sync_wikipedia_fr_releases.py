import importlib.util
from datetime import date
from pathlib import Path
import unittest


ROOT = Path(__file__).resolve().parents[1]
spec = importlib.util.spec_from_file_location("release_sync", ROOT / "scripts" / "sync_wikipedia_fr_releases.py")
sync = importlib.util.module_from_spec(spec)
spec.loader.exec_module(sync)


class FrenchReleaseSyncTests(unittest.TestCase):
    def test_infobox_dates_and_networks(self):
        page = """{{Infobox Épisode des Simpson
| saison = 25
| numéro = 7
| code = SABF04
| USA = {{date|8|décembre|2013|à la télévision}}<ref>{{date|2 juillet 2009}}</ref>
| France = {{date|7 avril 2020}} <small>([[Disney+]])</small><br />11 avril 2020 <small>([[W9]])</small>
| Québec = [[16 octobre]] [[2014]]
}}"""
        fields = sync.infobox_fields(page)
        self.assertEqual(sync.regional_dates(fields["usa"]), ([("2013-12-08", None)], []))
        self.assertEqual(sync.regional_dates(fields["france"]),
                         ([("2020-04-07", "Disney+"), ("2020-04-11", "W9")], []))
        self.assertEqual(sync.regional_dates(fields["quebec"]), ([("2014-10-16", None)], []))
        self.assertEqual(sync.french_date("{{date|5|11|1995|à la télévision}}"), ("1995-11-05", None))
        self.assertEqual(sync.regional_dates("inédit <small>(TV : censuré)</small>"), ([], []))

    def test_verified_match_and_merge(self):
        record = {"id": "s25e07", "production_code": "SABF04", "releases": [
            {"language": "en", "date": "2013-12-08"}, {"language": "fr-CA", "country": "CA"}]}
        fields = {"code": "SABF04", "saison": "25", "numero": "7"}
        self.assertEqual(sync.matches_record(fields, record, [("2013-12-08", None)]), (True, None))
        self.assertEqual(sync.merge_release(record["releases"], "en", "US", "2013-12-08"), "added_country")
        self.assertEqual(sync.merge_release(record["releases"], "fr-CA", "CA", "2014-10-16"), "dated_existing")
        self.assertIsNone(sync.merge_release(record["releases"], "en", "US", "2013-12-08"))
        self.assertEqual(record["releases"][1]["date"], "2014-10-16")
        record["releases"][1]["network"] = "Télétoon"
        self.assertIsNone(sync.merge_release(record["releases"], "fr-CA", "CA", "2014-10-16",
                                              "Télétoon (Canada)"))
        unknown = [{"language": "fr-CA", "country": "CA"}]
        self.assertEqual(sync.merge_release(unknown, "fr-CA", "CA", "2014-10-16", "Télétoon"),
                         "dated_existing")
        self.assertEqual(unknown, [{"language": "fr-CA", "country": "CA",
                                    "date": "2014-10-16", "network": "Télétoon"}])
        known_network = [{"language": "fr-CA", "country": "CA", "network": "TQS"}]
        self.assertEqual(sync.merge_release(known_network, "fr-CA", "CA", "2001-10-16",
                                            "Télétoon"), "conflict")
        self.assertEqual(sync.merge_release(known_network, "fr-CA", "CA", "2001-10-16"),
                         "dated_existing")
        self.assertEqual(known_network[0]["network"], "TQS")
        self.assertEqual(sync.matches_record(fields, record, [("2013-12-09", None)]),
                         (True, "usa_date_disagreement"))

    def test_two_part_article_and_wrong_link(self):
        fields = {"code": "36ABF20<br />36ABF21", "saison": "37", "numero": "16 et 17"}
        second = {"id": "s37e17", "production_code": "36ABF21",
                  "releases": [{"language": "en", "date": "2026-06-17"}]}
        self.assertEqual(sync.matches_record(fields, second, [("2026-06-17", None)]), (True, None))
        wrong = {"code": "WABF04", "saison": "28", "numero": "12"}
        episode = {"id": "s28e13", "production_code": "WABF05",
                   "releases": [{"language": "en", "date": "2017-01-15"}]}
        self.assertEqual(sync.matches_record(wrong, episode, [("2017-01-15", None)]),
                         (False, "production_code_mismatch"))

    def test_future_broadcast_is_not_a_release(self):
        record = {"id": "s36e09", "production_code": "35ABF20", "links": {
            "wikipedia_fr": "https://fr.wikipedia.org/wiki/Example"},
            "releases": [{"language": "en", "date": "2024-12-08"}]}
        article = """{{Infobox Épisode des Simpson
| saison = 36
| numéro = 9
| code = 35ABF20
| USA = 8 décembre 2024
| Québec = 4 novembre 2026
}}"""
        records = {"s36e09": (Path("s36e09.json"), record, "Example")}
        pages = {"Example": {"revid": 1, "wikitext": article}}
        plans, rows, counts = sync.plan_updates(records, pages, date(2026, 11, 2))
        self.assertEqual(counts["quebec:future_date"], 1)
        self.assertNotIn("fr-CA", [item["language"] for item in record["releases"]])
        self.assertNotIn("2026-11-04", [change["date"] for row in rows for change in row["changes"]])

    def test_conflicting_us_date_does_not_replace_existing_date(self):
        record = {"id": "s03e04", "production_code": "8F03", "links": {
            "wikipedia_fr": "https://fr.wikipedia.org/wiki/Example"},
            "releases": [{"language": "en", "date": "1991-10-10"}]}
        article = """{{Infobox Épisode des Simpson
| saison = 3
| numéro = 4
| code = 8F03
| USA = 31 octobre 1991
| France = 21 mars 1992
}}"""
        records = {"s03e04": (Path("s03e04.json"), record, "Example")}
        pages = {"Example": {"revid": 1, "wikitext": article}}
        _, rows, _ = sync.plan_updates(records, pages, date(2026, 11, 2))
        self.assertIn("usa_date_disagreement", rows[0]["issues"])
        self.assertEqual(record["releases"], [
            {"language": "en", "date": "1991-10-10"},
            {"language": "fr-FR", "date": "1992-03-21", "country": "FR"}])


if __name__ == "__main__":
    unittest.main()
