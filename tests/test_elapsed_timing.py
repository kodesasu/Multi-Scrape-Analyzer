"""Exercise elapsed clocks without external network traffic."""
import asyncio
import unittest
from types import SimpleNamespace
from unittest.mock import Mock, patch

import main


class ElapsedTimingTests(unittest.TestCase):
    def test_fetch_helpers_use_monotonic_clock_and_keep_result_keys(self):
        cases = [
            (lambda: main.sequential_fetch([]), "seq_time_threaded"),
            (lambda: main.fetch_multiple_threaded([]), "cpu_time_threaded"),
            (lambda: asyncio.run(main.fetch_multiple_urls_async([])), "cpu_time_async"),
        ]
        for run, key in cases:
            with self.subTest(key=key):
                clock = SimpleNamespace(perf_counter=Mock(side_effect=[10.0, 12.0]))
                with patch.object(main, "time", clock):
                    self.assertEqual(run(), [{key: 2.0}])
                self.assertEqual(clock.perf_counter.call_count, 2)


if __name__ == "__main__":
    unittest.main()
