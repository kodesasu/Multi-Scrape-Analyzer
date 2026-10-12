import unittest
import io
from contextlib import redirect_stdout
from unittest.mock import patch

import main


class AnalysisRegressionTests(unittest.TestCase):
    def test_empty_html_has_well_typed_zero_statistics(self):
        words = main.analyze_words('')
        self.assertEqual(words['total_word_count'], 0)
        self.assertEqual(words['word_list'], [])
        self.assertEqual(words['word_frequency'], {})
        self.assertEqual(words['character_distributions'], {})
        self.assertEqual(words['longest_word'], {})
        self.assertEqual(words['avg_word_length'], 0.0)
        self.assertEqual(words['most_common_word'], {})

    def test_punctuation_only_text_is_also_empty(self):
        self.assertEqual(main.analyze_words('<p>!!!</p><p>---</p>')['total_word_count'], 0)

    def test_adjacent_block_text_nodes_do_not_merge_words(self):
        _, words = main.clean_words('<p>alpha</p><p>beta</p>')
        self.assertEqual(words, ['alpha', 'beta'])
        self.assertEqual(main.analyze_words('<p>alpha</p><p>beta</p>')['total_word_count'], 2)

    def test_process_task_parses_html_once_with_real_beautifulsoup(self):
        with patch.object(main, 'BeautifulSoup', wraps=main.BeautifulSoup) as parse:
            result = main.process_task({
                'url': 'https://example.test/',
                'type': 'text/html; charset=utf-8',
                'content': '<p>alpha</p><p>beta</p><a href="/next">next</a>',
            })
        self.assertNotIn('error', result)
        self.assertEqual(parse.call_count, 1)
        self.assertEqual(result['words']['word_list'], ['alpha', 'beta', 'next'])
        self.assertEqual(result['html']['all_page_links'], {'/next'})

    def test_non_string_text_content_is_isolated_as_page_error(self):
        bad = main.process_task({'url': 'bad', 'type': 'text/html', 'content': None})
        good = main.process_task({'url': 'good', 'type': 'text/html', 'content': '<p>ok</p>'})
        self.assertIn('error', bad)
        self.assertEqual(good['words']['word_list'], ['ok'])

    def test_unsupported_content_type_is_described_accurately(self):
        result = main.process_task({
            'url': 'https://api.test/', 'type': 'application/json', 'content': {},
        })
        self.assertIn('Unsupported content type', result['error'])
        self.assertIn('application/json', result['error'])

    def test_url_splits_preserve_duplicates_order_and_balance(self):
        urls = ['a', 'a', 'b', 'c', 'd']
        groups = main.split_urls(urls)
        self.assertEqual(tuple(map(len, groups)), (2, 2, 1))
        self.assertEqual([url for group in groups for url in group], urls)

    def test_small_url_inputs_are_distributed_without_skew(self):
        self.assertEqual(tuple(map(len, main.split_urls(['a', 'b']))), (1, 1, 0))
        self.assertEqual(main.split_urls([]), ([], [], []))

    def test_media_type_matching_is_case_insensitive_and_not_substring_based(self):
        self.assertNotIn('error', main.process_task({
            'url': 'page', 'type': 'Text/HTML; charset=utf-8', 'content': '<p>ok</p>',
        }))
        self.assertIn('error', main.process_task({
            'url': 'binary', 'type': 'application/context', 'content': 'not text',
        }))

    def test_analysis_errors_are_printed_without_download_failures(self):
        output = io.StringIO()
        with redirect_stdout(output):
            main.report_errors([], [{'url': 'api', 'error': 'unsupported JSON'}])
        self.assertIn('api', output.getvalue())
        self.assertIn('unsupported JSON', output.getvalue())
        self.assertNotIn('SUCCESSFULLY', output.getvalue())

    def test_download_and_analysis_errors_are_both_reported(self):
        output = io.StringIO()
        with redirect_stdout(output):
            main.report_errors([{'url': 'missing', 'content': 'HTTP 404'}],
                               [{'url': 'api', 'error': 'unsupported JSON'}])
        self.assertIn('HTTP 404', output.getvalue())
        self.assertIn('unsupported JSON', output.getvalue())


if __name__ == '__main__':
    unittest.main()
