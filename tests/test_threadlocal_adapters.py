"""Unit and concurrency tests for Thread-Local dispatch adapters."""
import socket
import threading
import unittest
from concurrent.futures import ThreadPoolExecutor, as_completed
from unittest.mock import patch, MagicMock

from requests.adapters import HTTPAdapter

import ipforce.adapters as adapters_mod
from ipforce.adapters import (
    IPv4ThreadLocalAdapter, IPv6ThreadLocalAdapter,
    _tl_dispatching_getaddrinfo, _tl_ensure_installed, _tl_storage,
)

MIXED_ADDR_RESULTS = [
    (socket.AF_INET, socket.SOCK_STREAM, 6, '', ('192.168.1.1', 80)),
    (socket.AF_INET6, socket.SOCK_STREAM, 6, '', ('::1', 80)),
    (socket.AF_INET, socket.SOCK_STREAM, 6, '', ('10.0.0.1', 80)),
    (socket.AF_INET6, socket.SOCK_STREAM, 6, '', ('2001:db8::1', 80)),
]

NUM_THREADS = 8
SENDS_PER_THREAD = 20


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


class TestDispatchingGetaddrinfo(unittest.TestCase):
    """Direct tests for _tl_dispatching_getaddrinfo."""

    def test_filters_by_thread_local_family(self):
        """Results are filtered to the family stored in thread-local storage."""
        with patch('ipforce.adapters._tl_original_getaddrinfo', return_value=MIXED_ADDR_RESULTS):
            _tl_storage.family_filter = socket.AF_INET
            try:
                results = _tl_dispatching_getaddrinfo('example.com', 80)
            finally:
                _tl_storage.family_filter = None

        self.assertEqual(len(results), 2)
        self.assertTrue(all(r[0] == socket.AF_INET for r in results))

    def test_returns_all_when_no_filter(self):
        """Without a thread-local filter, all results pass through unchanged."""
        with patch('ipforce.adapters._tl_original_getaddrinfo', return_value=MIXED_ADDR_RESULTS):
            _tl_storage.family_filter = None
            results = _tl_dispatching_getaddrinfo('example.com', 80)

        self.assertEqual(results, MIXED_ADDR_RESULTS)


class TestThreadLocalInstall(unittest.TestCase):
    """Tests for the lazy, idempotent _tl_ensure_installed."""

    def test_installs_dispatcher_once(self):
        """First call records the original getaddrinfo and installs the dispatcher."""
        original_gai = socket.getaddrinfo
        with patch.object(adapters_mod, '_tl_installed', False):
            with patch.object(adapters_mod, '_tl_original_getaddrinfo', None):
                try:
                    _tl_ensure_installed()
                    self.assertIs(socket.getaddrinfo, _tl_dispatching_getaddrinfo)
                    self.assertIs(adapters_mod._tl_original_getaddrinfo, original_gai)
                    self.assertTrue(adapters_mod._tl_installed)
                finally:
                    socket.getaddrinfo = original_gai

    def test_is_idempotent_when_already_installed(self):
        """When already installed, the call returns early without re-patching."""
        sentinel = object()
        with patch.object(adapters_mod, '_tl_installed', True):
            with patch.object(adapters_mod, '_tl_original_getaddrinfo', sentinel):
                _tl_ensure_installed()
                self.assertIs(adapters_mod._tl_original_getaddrinfo, sentinel)

    def test_double_checked_lock_returns_if_installed_while_waiting(self):
        """Inner double-check returns early if install completes while awaiting the lock."""
        original_gai = socket.getaddrinfo

        class _FlippingLock:
            def __enter__(self):
                adapters_mod._tl_installed = True
                return self

            def __exit__(self, *exc):
                return False

        with patch.object(adapters_mod, '_tl_installed', False):
            with patch.object(adapters_mod, '_tl_install_lock', _FlippingLock()):
                try:
                    _tl_ensure_installed()
                    self.assertIs(socket.getaddrinfo, original_gai)
                finally:
                    socket.getaddrinfo = original_gai
