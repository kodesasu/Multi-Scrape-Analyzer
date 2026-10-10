"""One parent-owned rotating log file, fed by process-safe queue handlers."""
import logging
import multiprocessing
from contextlib import contextmanager
from logging.handlers import QueueHandler, QueueListener, RotatingFileHandler
from pathlib import Path


logger = logging.getLogger("multi_scrape_analyzer")
logger.addHandler(logging.NullHandler())


def configure_worker_logging(log_queue):
    """Called once in each spawned worker, before it accepts tasks."""
    for handler in tuple(logger.handlers):
        logger.removeHandler(handler)
        handler.close()
    logger.addHandler(QueueHandler(log_queue) if log_queue is not None else logging.NullHandler())
    logger.setLevel(logging.DEBUG)
    logger.propagate = False


@contextmanager
def log_to_file(path, *, max_bytes=5 * 1024 * 1024, backup_count=3):
    """Stop worker pools before leaving this context so queued records drain."""
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    handler = RotatingFileHandler(path, maxBytes=max_bytes, backupCount=backup_count,
                                  encoding="utf-8")
    handler.setFormatter(logging.Formatter(
        "%(asctime)s - %(processName)s - %(name)s - %(levelname)s - %(message)s"))
    try:
        log_queue = multiprocessing.get_context("spawn").Queue()
    except BaseException:
        handler.close()
        raise
    queue_handler = QueueHandler(log_queue)
    listener = QueueListener(log_queue, handler)
    previous = (logger.level, logger.propagate, tuple(logger.handlers))
    started = False
    try:
        listener.start()
        started = True
        # Caller-owned handlers are detached, not closed, and restored below.
        for old in previous[2]:
            logger.removeHandler(old)
        logger.addHandler(queue_handler)
        logger.setLevel(logging.DEBUG)
        logger.propagate = False
        yield log_queue
    finally:
        logger.removeHandler(queue_handler)
        for old in previous[2]:
            if old not in logger.handlers:
                logger.addHandler(old)
        logger.setLevel(previous[0])
        logger.propagate = previous[1]
        try:
            if started:
                listener.stop()
        finally:
            queue_handler.close()
            log_queue.close()
            log_queue.join_thread()
            handler.close()
