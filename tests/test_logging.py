import logging
import multiprocessing
import shutil
import subprocess
import sys
import tempfile
import unittest
from concurrent.futures import ProcessPoolExecutor
from pathlib import Path

from app_logging import configure_worker_logging, logger, log_to_file
import main


def write_worker_records(worker):
    for number in range(30):
        logger.info('worker=%d record=%d', worker, number)
    return any(isinstance(handler, logging.FileHandler) for handler in logger.handlers)


class LoggingTests(unittest.TestCase):
    def test_import_has_no_file_console_or_root_logger_side_effects(self):
        with tempfile.TemporaryDirectory() as tmp:
            for name in ('main.py', 'app_logging.py'):
                shutil.copyfile(Path(main.__file__).with_name(name), Path(tmp) / name)
            code = (
                'import logging; root=logging.getLogger(); '
                'handler=logging.NullHandler(); root.addHandler(handler); '
                'before=(root.level,tuple(root.handlers)); import main; '
                'assert before==(root.level,tuple(root.handlers))'
            )
            result = subprocess.run([sys.executable, '-c', code], cwd=tmp,
                                    capture_output=True, text=True, timeout=20)
            self.assertEqual(result.returncode, 0, result.stderr)
            self.assertEqual(result.stdout, '')
            self.assertFalse((Path(tmp) / 'LOG').exists())

    def test_spawn_workers_use_one_rotating_file_owner(self):
        root = logging.getLogger()
        before = (root.level, tuple(root.handlers))
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / 'main.log'
            with log_to_file(path, max_bytes=1024, backup_count=30) as queue:
                with ProcessPoolExecutor(max_workers=3, mp_context=multiprocessing.get_context('spawn'),
                                         initializer=configure_worker_logging, initargs=(queue,)) as pool:
                    futures = [pool.submit(write_worker_records, worker) for worker in range(3)]
                    self.assertEqual([future.result(timeout=20) for future in futures], [False] * 3)
                logger.info('parent marker')
            files = list(Path(tmp).glob('main.log*'))
            self.assertGreater(len(files), 1, 'the test must exercise actual rollover')
            content = ''.join(file.read_text(encoding='utf-8') for file in files)
            self.assertIn('parent marker', content)
            for worker in range(3):
                for number in range(30):
                    self.assertEqual(content.count(f'worker={worker} record={number}\n'), 1)
        self.assertEqual((root.level, tuple(root.handlers)), before)

    def test_exception_restores_caller_handlers_without_closing_them(self):
        class CallerHandler(logging.Handler):
            was_closed = False
            def emit(self, record):
                pass
            def close(self):
                self.was_closed = True
                super().close()

        handler = CallerHandler()
        logger.addHandler(handler)
        before = (logger.level, logger.propagate, tuple(logger.handlers))
        try:
            with tempfile.TemporaryDirectory() as tmp:
                path = Path(tmp) / 'main.log'
                with self.assertRaisesRegex(RuntimeError, 'task failed'):
                    with log_to_file(path):
                        logger.info('before failure')
                        raise RuntimeError('task failed')
                self.assertIn('before failure', path.read_text(encoding='utf-8'))
            self.assertEqual((logger.level, logger.propagate, tuple(logger.handlers)), before)
            self.assertFalse(handler.was_closed)
        finally:
            logger.removeHandler(handler)
            handler.close()

    def test_real_pipeline_drains_worker_logs_before_context_exit(self):
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / 'main.log'
            with log_to_file(path) as queue:
                _, errors, results = main.process_multiple_cpu_bound(
                    [], max_wrks_pool=1, log_queue=queue)
            self.assertEqual(errors, [])
            self.assertEqual(results, [])
            content = path.read_text(encoding='utf-8')
            self.assertIn('Asyncio', content)
            self.assertIn('ThreadPool', content)
            self.assertIn('Sequential Fetch', content)


if __name__ == '__main__':
    unittest.main()
