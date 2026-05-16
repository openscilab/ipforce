"""Unit and concurrency tests for Lock-based thread-safe adapters."""
import contextlib
import socket
import threading
import unittest
from concurrent.futures import ThreadPoolExecutor, as_completed
from unittest.mock import patch, MagicMock

from requests.adapters import HTTPAdapter

from ipforce.adapters import IPv4LockAdapter, IPv6LockAdapter, _adapter_lock

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


class TestIPv4LockAdapter(unittest.TestCase):
    """Test cases for IPv4LockAdapter."""

    def setUp(self):
        """Set up test fixtures."""
        self.adapter = IPv4LockAdapter()

    def test_ipv4_filtering_during_send(self):
        """Test that IPv4LockAdapter filters only IPv4 addresses during send."""
        captured = []

        def mock_super_send(*args, **kwargs):
            captured.extend(socket.getaddrinfo('example.com', 80))
            return MagicMock()

        with patch('socket.getaddrinfo', return_value=MIXED_ADDR_RESULTS):
            with patch.object(HTTPAdapter, 'send', mock_super_send):
                self.adapter.send(MagicMock())

        self.assertEqual(len(captured), 2)
        for result in captured:
            self.assertEqual(result[0], socket.AF_INET)

    def test_cleanup_after_send(self):
        """Test that getaddrinfo is restored after send."""
        original = socket.getaddrinfo

        with patch.object(HTTPAdapter, 'send', return_value=MagicMock()):
            self.adapter.send(MagicMock())

        self.assertEqual(socket.getaddrinfo, original)

    def test_cleanup_on_exception(self):
        """Test that getaddrinfo is restored even when send raises."""
        original = socket.getaddrinfo

        with patch.object(HTTPAdapter, 'send', side_effect=Exception("error")):
            with self.assertRaises(Exception):
                self.adapter.send(MagicMock())

        self.assertEqual(socket.getaddrinfo, original)

    def test_lock_is_acquired_during_send(self):
        """Test that the adapter lock is held during the send call."""
        lock_was_held = []

        def mock_super_send(*args, **kwargs):
            lock_was_held.append(_adapter_lock.locked())
            return MagicMock()

        with patch.object(HTTPAdapter, 'send', mock_super_send):
            self.adapter.send(MagicMock())

        self.assertTrue(lock_was_held[0])


class TestIPv6LockAdapter(unittest.TestCase):
    """Test cases for IPv6LockAdapter."""

    def setUp(self):
        """Set up test fixtures."""
        self.adapter = IPv6LockAdapter()

    def test_ipv6_filtering_during_send(self):
        """Test that IPv6LockAdapter filters only IPv6 addresses during send."""
        captured = []

        def mock_super_send(*args, **kwargs):
            captured.extend(socket.getaddrinfo('example.com', 80))
            return MagicMock()

        with patch('socket.getaddrinfo', return_value=MIXED_ADDR_RESULTS):
            with patch.object(HTTPAdapter, 'send', mock_super_send):
                self.adapter.send(MagicMock())

        self.assertEqual(len(captured), 2)
        for result in captured:
            self.assertEqual(result[0], socket.AF_INET6)

    def test_cleanup_after_send(self):
        """Test that getaddrinfo is restored after send."""
        original = socket.getaddrinfo

        with patch.object(HTTPAdapter, 'send', return_value=MagicMock()):
            self.adapter.send(MagicMock())

        self.assertEqual(socket.getaddrinfo, original)


# ============================================================================
# Concurrency tests
# ============================================================================


def _run_concurrent_lock_test(adapter, expected_family):
    """Run a barrier-synchronised concurrency test for a lock adapter."""
    barrier = threading.Barrier(NUM_THREADS)
    lock = threading.Lock()
    results = []
    errors = []

    mock_gai = MagicMock(return_value=MIXED_ADDR_RESULTS)

    def mock_super_send(*args, **kwargs):
        captured = list(socket.getaddrinfo('example.com', 80))
        for r in captured:
            if r[0] != expected_family:
                with lock:
                    errors.append(
                        "Expected family {exp}, got {got}".format(exp=expected_family, got=r[0]),
                    )
        with lock:
            results.append(len(captured))
        return MagicMock()

    def worker(_idx):
        barrier.wait()
        for _ in range(SENDS_PER_THREAD):
            adapter.send(MagicMock())

    with patch('socket.getaddrinfo', mock_gai):
        with patch.object(HTTPAdapter, 'send', mock_super_send):
            with ThreadPoolExecutor(max_workers=NUM_THREADS) as pool:
                futures = [pool.submit(worker, i) for i in range(NUM_THREADS)]
                for f in as_completed(futures):
                    f.result()

    return results, errors


class TestLockAdapterConcurrency(unittest.TestCase):
    """Verify IPv4LockAdapter / IPv6LockAdapter under thread contention."""

    def test_concurrent_ipv4_sends(self):
        """Multiple threads using IPv4LockAdapter simultaneously."""
        results, errors = _run_concurrent_lock_test(
            IPv4LockAdapter(), socket.AF_INET,
        )
        self.assertEqual(errors, [])
        self.assertEqual(len(results), NUM_THREADS * SENDS_PER_THREAD)

    def test_concurrent_ipv6_sends(self):
        """Multiple threads using IPv6LockAdapter simultaneously."""
        results, errors = _run_concurrent_lock_test(
            IPv6LockAdapter(), socket.AF_INET6,
        )
        self.assertEqual(errors, [])

    def test_getaddrinfo_restored_after_concurrent_sends(self):
        """Verify socket.getaddrinfo is pristine after concurrent lock-adapter sends."""
        original = socket.getaddrinfo
        adapter = IPv4LockAdapter()
        barrier = threading.Barrier(NUM_THREADS)

        def worker(_idx):
            barrier.wait()
            for _ in range(SENDS_PER_THREAD):
                adapter.send(MagicMock())

        with patch.object(HTTPAdapter, 'send', return_value=MagicMock()):
            with ThreadPoolExecutor(max_workers=NUM_THREADS) as pool:
                futures = [pool.submit(worker, i) for i in range(NUM_THREADS)]
                for f in as_completed(futures):
                    f.result()

        self.assertIs(socket.getaddrinfo, original)

    def test_mixed_ipv4_ipv6_lock_adapters(self):
        """IPv4 and IPv6 lock adapters running concurrently filter correctly."""
        lock4 = IPv4LockAdapter()
        lock6 = IPv6LockAdapter()
        barrier = threading.Barrier(NUM_THREADS)
        data_lock = threading.Lock()
        errors = []
        completed = []

        mock_gai = MagicMock(return_value=MIXED_ADDR_RESULTS)

        def mock_super_send(*args, **kwargs):
            results = socket.getaddrinfo('example.com', 80)
            families = set(r[0] for r in results)
            if len(families) > 1:
                with data_lock:
                    errors.append("Mixed families in single send: {f}".format(f=families))
            return MagicMock()

        def v4_worker():
            barrier.wait()
            for _ in range(SENDS_PER_THREAD):
                lock4.send(MagicMock())
            with data_lock:
                completed.append('v4')

        def v6_worker():
            barrier.wait()
            for _ in range(SENDS_PER_THREAD):
                lock6.send(MagicMock())
            with data_lock:
                completed.append('v6')

        with patch('socket.getaddrinfo', mock_gai):
            with patch.object(HTTPAdapter, 'send', mock_super_send):
                with ThreadPoolExecutor(max_workers=NUM_THREADS) as pool:
                    half = NUM_THREADS // 2
                    futures = (
                        [pool.submit(v4_worker) for _ in range(half)] +
                        [pool.submit(v6_worker) for _ in range(NUM_THREADS - half)]
                    )
                    for f in as_completed(futures):
                        f.result()

        self.assertEqual(errors, [])
        self.assertEqual(len(completed), NUM_THREADS)
