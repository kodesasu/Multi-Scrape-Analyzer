"""Offline integration smoke for the documented Python versions."""
import unittest

import main


class AnalysisSmokeTest(unittest.TestCase):
    def test_downloaded_html_flows_through_both_analyzers(self):
        result = main.process_task({
            "url": "https://example.test/",
            "success": True,
            "type": "text/html; charset=utf-8",
            "content": '<p>Hello hello <a href="/next">world</a></p>',
        })
        self.assertEqual(result["url"], "https://example.test/")
        self.assertEqual(result["words"]["total_word_count"], 3)
        self.assertEqual(result["html"]["html_tags_count"], {"p": 1, "a": 1})
        self.assertEqual(result["html"]["all_page_links"], {"/next"})


if __name__ == "__main__":
    unittest.main()
