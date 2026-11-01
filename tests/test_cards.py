"""Offline tests. No network, no token."""
import datetime
import pathlib
import sys
import unittest
import xml.etree.ElementTree as ET

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent.parent / "src"))

from readme_cards.cards import RENDERERS                      # noqa: E402
from readme_cards.github import Stats                         # noqa: E402
from readme_cards.render import THEMES, bytes_human, human, lang_color  # noqa: E402


def sample(days=371, restricted=0) -> Stats:
    s = Stats(login="octocat", name="The Octocat", total_contributions=1234,
              commits=1000, pull_requests=200, reviews=30, issues=4,
              repositories=12, stars=7, followers=3, restricted=restricted)
    base = datetime.date(2026, 1, 1)
    s.calendar = [
        ((base + datetime.timedelta(days=i)).isoformat(), i % 5)
        for i in range(days)
    ]
    s.languages = {"TypeScript": 5_000_000, "Python": 2_000_000, "Go": 900_000}
    return s


class TestStreaks(unittest.TestCase):
    def test_trailing_empty_day_does_not_break_streak(self):
        s = sample(0)
        s.calendar = [("a", 1), ("b", 1), ("c", 0)]
        self.assertEqual(s.streaks(), (2, 2))

    def test_gap_ends_current_streak(self):
        s = sample(0)
        s.calendar = [("a", 5), ("b", 0), ("c", 1), ("d", 1)]
        self.assertEqual(s.streaks(), (2, 2))

    def test_empty_calendar(self):
        s = sample(0)
        s.calendar = []
        self.assertEqual(s.streaks(), (0, 0))

    def test_active_days(self):
        s = sample(0)
        s.calendar = [("a", 0), ("b", 3), ("c", 1)]
        self.assertEqual(s.active_days, 2)


class TestFormatting(unittest.TestCase):
    def test_human(self):
        self.assertEqual(human(999), "999")
        self.assertEqual(human(1500), "1.5k")
        self.assertEqual(human(9367), "9.4k")
        self.assertEqual(human(12000), "12k")
        self.assertEqual(human(2_000_000), "2M")

    def test_bytes_human(self):
        self.assertTrue(bytes_human(5_000_000).endswith("MB"))
        self.assertEqual(bytes_human(12), "12 B")

    def test_lang_color_is_stable_and_known(self):
        self.assertEqual(lang_color("TypeScript", 0), "#3178c6")
        self.assertEqual(lang_color("Nonesuch", 3), lang_color("Nonesuch", 3))


class TestRendering(unittest.TestCase):
    def test_every_card_in_every_theme_is_well_formed_svg(self):
        s = sample()
        for theme_name, theme in THEMES.items():
            for card_name, fn in RENDERERS.items():
                svg = fn(s, theme)
                with self.subTest(theme=theme_name, card=card_name):
                    root = ET.fromstring(svg)
                    self.assertTrue(root.tag.endswith("svg"))
                    self.assertGreater(int(float(root.get("width"))), 0)

    def test_language_card_handles_no_languages(self):
        s = sample()
        s.languages = {}
        ET.fromstring(RENDERERS["languages"](s, THEMES["dark"]))

    def test_activity_card_handles_one_week(self):
        s = sample()
        s.calendar = [("2026-01-01", 1)]
        ET.fromstring(RENDERERS["activity"](s, THEMES["dark"]))

    def test_names_are_xml_escaped(self):
        s = sample()
        s.name = 'Ampersand & "quotes" <tag>'
        ET.fromstring(RENDERERS["stats"](s, THEMES["dark"]))

    def test_hidden_private_contributions_are_surfaced(self):
        s = sample(restricted=4321)
        self.assertIn("private hidden", RENDERERS["stats"](s, THEMES["dark"]))


if __name__ == "__main__":
    unittest.main()
