"""Fetch contracts verified with local HTTP, process pools, and focused fakes."""
import asyncio
import concurrent.futures
import http.server
import json
import socket
import threading
import time
import unittest
from collections import Counter
from unittest.mock import patch
import main


class FakeResponse:
    def __init__(self, status=200, content_type="text/html; charset=utf-8",
                 body="<p>Hello world</p>", tracker=None):
        self.status = status
        self.status_code = status
        self.headers = {} if content_type is None else {"Content-Type": content_type}
        self.body = body
        self.tracker = tracker

    async def __aenter__(self):
        if self.tracker is not None:
            self.tracker.enter()
            await asyncio.sleep(0.01)
        return self

    async def __aexit__(self, *_):
        if self.tracker is not None:
            self.tracker.leave()

    async def text(self):
        return self.body

    async def json(self):
        return {"ok": True}

    @property
    def text_value(self):
        return self.body


class FakeThreadResponse:
    def __init__(self, status=200, content_type="text/html; charset=utf-8",
                 body="<p>Hello world</p>"):
        self.status_code = status
        self.headers = {} if content_type is None else {"Content-Type": content_type}
        self.text = body

    def json(self):
        return {"ok": True}


class FakeAioSession:
    def __init__(self, responses, tracker=None):
        self.responses = list(responses)
        self.calls = 0
        self.tracker = tracker

    def get(self, _url):
        self.calls += 1
        response = self.responses.pop(0) if self.responses else FakeResponse(tracker=self.tracker)
        response.tracker = self.tracker
        return response


class ActiveTracker:
    def __init__(self):
        self.active = 0
        self.peak = 0
        self.lock = threading.Lock()

    def enter(self):
        with self.lock:
            self.active += 1
            self.peak = max(self.peak, self.active)

    def leave(self):
        with self.lock:
            self.active -= 1


class FetchWrapperTests(unittest.TestCase):
    def run_async_fetch(self, session, url="https://example.test", retries=2):
        return asyncio.run(main.fetch_url_async(session, url, retries, asyncio.Semaphore(1)))

    def test_async_unsupported_and_missing_content_types_return_failure_shape_once(self):
        for content_type in ("image/png", None):
            with self.subTest(content_type=content_type):
                session = FakeAioSession([FakeResponse(content_type=content_type)])
                result = self.run_async_fetch(session)
                self.assertEqual(result["success"], False)
                self.assertEqual(result["url"], "https://example.test")
                self.assertIsInstance(result["content"], str)
                self.assertNotIn("type", result)
                self.assertEqual(session.calls, 1)

    def test_thread_unsupported_content_type_returns_failure_shape_once(self):
        response = FakeThreadResponse(content_type="image/png")
        with patch.object(main.requests, "get", return_value=response) as get:
            result = main.fetch_url_threaded("https://example.test", 2)
        self.assertEqual(result["success"], False)
        self.assertEqual(result["url"], "https://example.test")
        self.assertIn("Unsupported Content-Type", result["content"])
        self.assertEqual(get.call_count, 1)

    def test_case_insensitive_text_type_is_detected(self):
        session = FakeAioSession([FakeResponse(content_type="TEXT/HTML; Charset=UTF-8")])
        result = self.run_async_fetch(session)
        self.assertTrue(result["success"])
        self.assertEqual(result["type"], "TEXT/HTML; Charset=UTF-8")

    def test_json_types_include_structured_suffix(self):
        response = FakeThreadResponse(content_type="application/problem+json; charset=utf-8")
        with patch.object(main.requests, "get", return_value=response):
            result = main.fetch_url_threaded("https://example.test", 1)
        self.assertTrue(result["success"])
        self.assertEqual(result["content"], {"ok": True})

    def test_zero_retry_and_worker_values_are_rejected_not_silently_defaulted(self):
        with self.assertRaisesRegex(ValueError, "max_retry"):
            main.fetch_url_threaded("https://example.test", 0)
        with self.assertRaisesRegex(ValueError, "max_workers"):
            asyncio.run(main.fetch_multiple_urls_async([], max_workers=0))
        with self.assertRaisesRegex(ValueError, "max_workers"):
            main.fetch_multiple_threaded([], max_workers=0)
        with self.assertRaisesRegex(ValueError, "max_wrks_pool"):
            main.process_multiple_cpu_bound([], max_wrks_pool=0)

    def test_invalid_limits_fail_before_starting_processes(self):
        for name in ("max_rty", "max_wrks", "max_wrks_pool"):
            for value in (0, -1, True, 1.5, "2"):
                with self.subTest(name=name, value=value):
                    with patch.object(main, "ProcessPoolExecutor") as pool:
                        with self.assertRaisesRegex(ValueError, name):
                            main.process_multiple_cpu_bound([], **{name: value})
                        pool.assert_not_called()

    def test_empty_timeout_message_remains_informative(self):
        session = FakeAioSession([])
        with patch.object(session, "get", side_effect=TimeoutError()):
            result = self.run_async_fetch(session, retries=1)
        self.assertFalse(result["success"])
        self.assertEqual(result["content"], "TimeoutError")

    def test_async_controller_respects_worker_cap_and_keeps_timing_tail(self):
        tracker = ActiveTracker()

        class SessionContext:
            async def __aenter__(self):
                return FakeAioSession([], tracker)

            async def __aexit__(self, *_):
                pass

        with patch.object(main.aiohttp, "ClientSession", side_effect=lambda **_: SessionContext()):
            result = asyncio.run(main.fetch_multiple_urls_async(
                [f"https://example.test/{i}" for i in range(6)], max_retry=1, max_workers=2))
        self.assertEqual(len(result), 7)
        self.assertIn("cpu_time_async", result[-1])
        self.assertGreaterEqual(tracker.peak, 2)
        self.assertLessEqual(tracker.peak, 2)

    def test_exception_payload_is_safe_for_json_and_process_pool_transport(self):
        with patch.object(main.requests, "get", side_effect=main.requests.ConnectionError("offline")):
            result = main.fetch_url_threaded("https://example.test", 1)
        self.assertEqual(result["content"], "offline")
        json.dumps(result)

        with socket.socket() as probe:
            probe.bind(("127.0.0.1", 0))
            port = probe.getsockname()[1]
        url = f"http://127.0.0.1:{port}/unreachable"
        with concurrent.futures.ProcessPoolExecutor(max_workers=1) as pool:
            transported = pool.submit(main.fetch_url_threaded, url, 1).result(timeout=20)
        self.assertFalse(transported["success"])
        self.assertIsInstance(transported["content"], str)
        json.dumps(transported)


class LocalHandler(http.server.BaseHTTPRequestHandler):
    active = 0
    peak = 0
    lock = threading.Lock()
    hits = Counter()

    def do_GET(self):
        with self.lock:
            type(self).active += 1
            type(self).peak = max(type(self).peak, type(self).active)
            type(self).hits[self.path] += 1
        try:
            time.sleep(0.1)
            if self.path == "/missing-type":
                content_type = None
                payload = b"binary"
            elif self.path == "/image":
                content_type = "image/png"
                payload = b"png"
            elif self.path == "/upper":
                content_type = "TEXT/HTML; Charset=UTF-8"
                payload = b"<p>Hello world</p>"
            elif self.path == "/json":
                content_type = "application/problem+json; charset=utf-8"
                payload = b'{"ok": true}'
            elif self.path == "/badjson":
                content_type = "application/json"
                payload = b'{"not": }'
            else:
                content_type = "text/plain; charset=utf-8"
                payload = b"hello world"
            self.send_response(200)
            if content_type:
                self.send_header("Content-Type", content_type)
            self.send_header("Content-Length", str(len(payload)))
            self.end_headers()
            self.wfile.write(payload)
        finally:
            with self.lock:
                type(self).active -= 1

    def log_message(self, *_):
        pass


class LocalHTTPIntegrationTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.server = http.server.ThreadingHTTPServer(("127.0.0.1", 0), LocalHandler)
        cls.thread = threading.Thread(target=cls.server.serve_forever, daemon=True)
        cls.thread.start()
        cls.base_url = f"http://127.0.0.1:{cls.server.server_port}"

    @classmethod
    def tearDownClass(cls):
        cls.server.shutdown()
        cls.server.server_close()
        cls.thread.join(timeout=2)

    def setUp(self):
        LocalHandler.active = 0
        LocalHandler.peak = 0
        LocalHandler.hits.clear()

    def test_threaded_real_http_content_type_contract(self):
        accepted = main.fetch_url_threaded(self.base_url + "/upper", 1)
        self.assertTrue(accepted["success"])
        self.assertEqual(accepted["type"], "TEXT/HTML; Charset=UTF-8")
        rejected = main.fetch_url_threaded(self.base_url + "/image", 3)
        self.assertFalse(rejected["success"])
        self.assertEqual(LocalHandler.hits["/image"], 1,
                         "non-retryable content type should not trigger network retries")

    def test_async_real_http_content_type_contract(self):
        async def fetch_paths():
            async with main.aiohttp.ClientSession() as session:
                upper = await main.fetch_url_async(session, self.base_url + "/upper", 1,
                                                    asyncio.Semaphore(1))
                image = await main.fetch_url_async(session, self.base_url + "/image", 3,
                                                    asyncio.Semaphore(1))
                structured_json = await main.fetch_url_async(
                    session, self.base_url + "/json", 1, asyncio.Semaphore(1))
            return upper, image, structured_json

        upper, image, structured_json = asyncio.run(fetch_paths())
        self.assertTrue(upper["success"])
        self.assertFalse(image["success"])
        self.assertEqual(LocalHandler.hits["/image"], 1)
        self.assertEqual(structured_json["content"], {"ok": True})

    def test_invalid_json_errors_are_strings_and_cross_process_pool(self):
        url = self.base_url + "/badjson"
        direct = main.fetch_url_threaded(url, 1)
        self.assertFalse(direct["success"])
        self.assertIsInstance(direct["content"], str)
        json.dumps(direct)

        with concurrent.futures.ProcessPoolExecutor(max_workers=1) as pool:
            transported = pool.submit(main.fetch_url_threaded, url, 1).result(timeout=20)
        self.assertFalse(transported["success"])
        self.assertIsInstance(transported["content"], str)
        json.dumps(transported)

    def test_controllers_honor_max_workers(self):
        urls = [self.base_url + f"/slow-{i}" for i in range(8)]
        async_result = asyncio.run(main.fetch_multiple_urls_async(urls, 1, 2))
        self.assertEqual(len(async_result), len(urls) + 1)
        self.assertEqual(async_result[-1].keys(), {"cpu_time_async"})
        self.assertLessEqual(LocalHandler.peak, 2)
        self.assertTrue(all(LocalHandler.hits[f"/slow-{i}"] == 1 for i in range(8)))

        LocalHandler.peak = 0
        threaded_result = main.fetch_multiple_threaded(urls, 1, 2)
        self.assertEqual(len(threaded_result), len(urls) + 1)
        self.assertEqual(threaded_result[-1].keys(), {"cpu_time_threaded"})
        self.assertLessEqual(LocalHandler.peak, 2)
        self.assertTrue(all(LocalHandler.hits[f"/slow-{i}"] == 2 for i in range(8)))


if __name__ == "__main__":
    unittest.main()
