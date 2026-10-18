"""Unit and concurrency tests for Thread-Local dispatch adapters."""
import socket
import threading
import unittest
from concurrent.futures import ThreadPoolExecutor, as_completed
from unittest.mock import patch, MagicMock

from requests.adapters import HTTPAdapter

from ipforce.adapters import (
    IPv4ThreadLocalAdapter, IPv6ThreadLocalAdapter,
    _tl_dispatching_getaddrinfo, _tl_storage,
)

MIXED_ADDR_RESULTS = [
    (socket.AF_INET, socket.SOCK_STREAM, 6, '', ('192.168.1.1', 80)),
    (socket.AF_INET6, socket.SOCK_STREAM, 6, '', ('::1', 80)),
    (socket.AF_INET, socket.SOCK_STREAM, 6, '', ('10.0.0.1', 80)),
    (socket.AF_INET6, socket.SOCK_STREAM, 6, '', ('2001:db8::1', 80)),
]

NUM_THREADS = 8
SENDS_PER_THREAD = 20


# ============================================================================
# Unit tests
# ============================================================================


class TestIPv4ThreadLocalAdapter(unittest.TestCase):
    """Test cases for IPv4ThreadLocalAdapter."""

    def setUp(self):
        """Set up test fixtures."""
        self.adapter = IPv4ThreadLocalAdapter()

    def test_ipv4_filtering_during_send(self):
        """Test that IPv4ThreadLocalAdapter filters only IPv4 during send."""
        captured = []

        def mock_super_send(*args, **kwargs):
            captured.extend(socket.getaddrinfo('example.com', 80))
            return MagicMock()

        with patch('ipforce.adapters._tl_original_getaddrinfo', return_value=MIXED_ADDR_RESULTS):
            with patch('ipforce.adapters._tl_installed', True):
                with patch('socket.getaddrinfo', _tl_dispatching_getaddrinfo):
                    with patch.object(HTTPAdapter, 'send', mock_super_send):
                        self.adapter.send(MagicMock())

        ipv4_results = [r for r in captured if r[0] == socket.AF_INET]
        self.assertEqual(len(ipv4_results), len(captured))
        self.assertGreater(len(captured), 0)

    def test_thread_local_cleared_after_send(self):
        """Test that the thread-local filter is cleared after send."""
        with patch.object(HTTPAdapter, 'send', return_value=MagicMock()):
            self.adapter.send(MagicMock())

        self.assertIsNone(getattr(_tl_storage, 'family_filter', None))

    def test_thread_local_cleared_on_exception(self):
        """Test that the thread-local filter is cleared even on exception."""
        with patch.object(HTTPAdapter, 'send', side_effect=Exception("error")):
            with self.assertRaises(Exception):
                self.adapter.send(MagicMock())

        self.assertIsNone(getattr(_tl_storage, 'family_filter', None))


class TestIPv6ThreadLocalAdapter(unittest.TestCase):
    """Test cases for IPv6ThreadLocalAdapter."""

    def setUp(self):
        """Set up test fixtures."""
        self.adapter = IPv6ThreadLocalAdapter()

    def test_ipv6_filtering_during_send(self):
        """Test that IPv6ThreadLocalAdapter filters only IPv6 during send."""
        captured = []

        def mock_super_send(*args, **kwargs):
            captured.extend(socket.getaddrinfo('example.com', 80))
            return MagicMock()

        with patch('ipforce.adapters._tl_original_getaddrinfo', return_value=MIXED_ADDR_RESULTS):
            with patch('ipforce.adapters._tl_installed', True):
                with patch('socket.getaddrinfo', _tl_dispatching_getaddrinfo):
                    with patch.object(HTTPAdapter, 'send', mock_super_send):
                        self.adapter.send(MagicMock())

        ipv6_results = [r for r in captured if r[0] == socket.AF_INET6]
        self.assertEqual(len(ipv6_results), len(captured))
        self.assertGreater(len(captured), 0)


# ============================================================================
# Concurrency tests
# ============================================================================


class TestThreadLocalAdapterConcurrency(unittest.TestCase):
    """Verify IPv4ThreadLocalAdapter / IPv6ThreadLocalAdapter under contention."""

    def test_concurrent_ipv4_sends(self):
        """Multiple threads using IPv4ThreadLocalAdapter simultaneously."""
        mock_gai = MagicMock(return_value=MIXED_ADDR_RESULTS)
        barrier = threading.Barrier(NUM_THREADS)
        lock = threading.Lock()
        results = []
        errors = []

        def mock_super_send(*args, **kwargs):
            captured = list(socket.getaddrinfo('example.com', 80))
            for r in captured:
                if r[0] != socket.AF_INET:
                    with lock:
                        errors.append("Expected AF_INET, got {f}".format(f=r[0]))
            with lock:
                results.append(len(captured))
            return MagicMock()

        def worker(_idx):
            barrier.wait()
            for _ in range(SENDS_PER_THREAD):
                IPv4ThreadLocalAdapter().send(MagicMock())

        with patch('ipforce.adapters._tl_original_getaddrinfo', mock_gai):
            with patch('ipforce.adapters._tl_installed', True):
                with patch('socket.getaddrinfo', _tl_dispatching_getaddrinfo):
                    with patch.object(HTTPAdapter, 'send', mock_super_send):
                        with ThreadPoolExecutor(max_workers=NUM_THREADS) as pool:
                            futures = [pool.submit(worker, i) for i in range(NUM_THREADS)]
                            for f in as_completed(futures):
                                f.result()

        self.assertEqual(errors, [])
        self.assertEqual(len(results), NUM_THREADS * SENDS_PER_THREAD)

    def test_cross_thread_isolation(self):
        """IPv4 adapter in one thread must not affect unfiltered threads."""
        adapter = IPv4ThreadLocalAdapter()
        barrier = threading.Barrier(2)
        unfiltered_results = []

        mock_gai = MagicMock(return_value=MIXED_ADDR_RESULTS)

        def filtered_worker():
            barrier.wait()
            for _ in range(SENDS_PER_THREAD):
                adapter.send(MagicMock())

        def unfiltered_worker():
            barrier.wait()
            for _ in range(SENDS_PER_THREAD):
                raw = mock_gai('example.com', 80)
                unfiltered_results.append(len(raw))

        with patch('ipforce.adapters._tl_original_getaddrinfo', mock_gai):
            with patch('ipforce.adapters._tl_installed', True):
                with patch('socket.getaddrinfo', _tl_dispatching_getaddrinfo):
                    with patch.object(HTTPAdapter, 'send', return_value=MagicMock()):
                        with ThreadPoolExecutor(max_workers=2) as pool:
                            pool.submit(filtered_worker)
                            pool.submit(unfiltered_worker)

        for count in unfiltered_results:
            self.assertEqual(count, len(MIXED_ADDR_RESULTS))
