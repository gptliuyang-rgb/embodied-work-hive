from datetime import datetime, timezone
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch
import hive

class RadarTests(unittest.TestCase):
    def test_official_links_only_and_navigation_excluded(self):
        source = {"url": "https://example.com/blog", "name": "Lab", "path_pattern": "^/blog/[^/]+$", "exclude_paths": ["/blog/research"]}
        html = '<a href="/blog/new">A new robot policy</a><a href="https://evil.test/blog/x">Fake breakthrough</a><a href="/blog/research">All Research</a>'
        rows = hive.parse_html(html, source)
        self.assertEqual([r["url"] for r in rows], ["https://example.com/blog/new"])
        self.assertIsNone(rows[0]["published"])

    def test_atom_publication_date_is_not_update_date(self):
        xml = '<feed xmlns="http://www.w3.org/2005/Atom"><entry><id>https://arxiv.org/abs/2601.00001v1</id><title>Robot agents</title><published>2026-01-01T00:00:00Z</published><updated>2026-11-18T00:00:00Z</updated></entry></feed>'
        rows = hive.parse_xml(xml, {"kind": "atom", "name": "arXiv"})
        self.assertTrue(rows[0]["published"].startswith("2026-01-01"))

    def test_old_and_future_papers_filtered(self):
        xml = '<rss><channel>' + ''.join(f'<item><title>Robot {i}</title><link>https://example.com/{i}</link><pubDate>{date}</pubDate></item>' for i, date in enumerate(['Mon, 01 Jan 2024 00:00:00 GMT', 'Wed, 18 Nov 2026 00:00:00 GMT', 'Fri, 20 Nov 2026 00:00:00 GMT'])) + '</channel></rss>'
        with patch('hive.download', return_value=xml):
            rows, health = hive.collect({"url": "https://example.com/feed", "name": "Lab", "kind": "xml"}, datetime(2026, 11, 18, 12, tzinfo=timezone.utc), 14)
        self.assertEqual(len(rows), 1)
        self.assertEqual(health['status'], 'ok')

    def test_same_day_rerun_keeps_discoveries_next_day_deduplicates(self):
        state = {}
        item = {"url": "https://example.com/robot", "source": "Lab", "title": "Robot"}
        first, _ = hive.select_items([item], state, '2026-11-18', 12)
        again, _ = hive.select_items([], state, '2026-11-18', 12)
        tomorrow, _ = hive.select_items([item], state, '2026-11-19', 12)
        self.assertEqual(first, again)
        self.assertEqual(tomorrow, [])

    def test_reviewer_cannot_invent_source_ids_or_links(self):
        for card in [{"id": 99, "note": "claim", "question": "why"}, {"id": 1, "note": "https://fake.test", "question": "why"}]:
            with self.assertRaises(ValueError):
                hive.validate_cards({"cards": [card]}, 1)

    def test_all_sources_failed_does_not_change_state(self):
        with tempfile.TemporaryDirectory() as folder:
            root = Path(folder)
            (root / 'state').mkdir()
            path = root / 'state' / 'seen.json'
            original = '{"seen": {}}'
            path.write_text(original)
            with patch('hive.collect', return_value=([], {"source": "Lab", "status": "failed", "matched": 0})):
                with self.assertRaises(RuntimeError):
                    hive.run({"timezone": "UTC", "paper_lookback_days": 14, "sources": [{}]}, root)
            self.assertEqual(path.read_text(), original)

    def test_partial_failure_is_recorded(self):
        config = {"timezone": "UTC", "paper_lookback_days": 14, "max_daily_items": 12, "model": "unused", "sources": [{}, {}]}
        item = {"url": "https://example.com/new", "source": "Lab", "title": "New robot", "published": None, "evidence": "official_index"}
        results = [([item], {"source": "Lab", "status": "ok", "matched": 1}), ([], {"source": "Other", "status": "failed", "matched": 0})]
        with tempfile.TemporaryDirectory() as folder, patch('hive.collect', side_effect=results), patch('hive.analyze', return_value=([], 'no model')):
            hive.run(config, Path(folder), datetime(2026, 11, 18, tzinfo=timezone.utc))
            report = (Path(folder) / 'reports' / 'latest.md').read_text(encoding='utf-8')
            self.assertIn('Other：failed', report)
            self.assertIn('建立历史基线', report)

    def test_html_is_escaped(self):
        self.assertNotIn('<script>', hive.md('<script>alert(1)</script>'))

if __name__ == '__main__':
    unittest.main()
