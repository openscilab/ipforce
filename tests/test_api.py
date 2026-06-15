"""Tests for the unified IPForceAdapter / IPForceSession API."""
import socket
import warnings
import unittest

from requests.adapters import HTTPAdapter

from ipforce import (
    IPVersion, IPForceMethod,
    IPForceAdapter, IPForceSession,
    IPv4TransportAdapter, IPv6TransportAdapter,
)
from ipforce.adapters import _BaseLockAdapter


class TestIPForceAdapterFactory(unittest.TestCase):
    """Test that IPForceAdapter returns correct adapter types."""

    def test_v4_lock(self):
        adapter = IPForceAdapter(IPVersion.V4, IPForceMethod.LOCK)
        self.assertIsInstance(adapter, _BaseLockAdapter)
        self.assertEqual(adapter._family, socket.AF_INET)

    def test_v6_lock(self):
        adapter = IPForceAdapter(IPVersion.V6, IPForceMethod.LOCK)
        self.assertIsInstance(adapter, _BaseLockAdapter)
        self.assertEqual(adapter._family, socket.AF_INET6)

    def test_v4_global(self):
        adapter = IPForceAdapter(IPVersion.V4, IPForceMethod.GLOBAL)
        self.assertIsInstance(adapter, HTTPAdapter)

    def test_v6_global(self):
        adapter = IPForceAdapter(IPVersion.V6, IPForceMethod.GLOBAL)
        self.assertIsInstance(adapter, HTTPAdapter)

    def test_default_method_is_lock(self):
        adapter = IPForceAdapter(IPVersion.V4)
        self.assertIsInstance(adapter, _BaseLockAdapter)

    def test_invalid_combination_raises(self):
        with self.assertRaises((ValueError, KeyError)):
            IPForceAdapter(IPVersion.V4, "not_a_method")


class TestIPForceSession(unittest.TestCase):
    """Test IPForceSession class."""

    def test_v4_session_mounts_lock_adapter(self):
        with IPForceSession(IPVersion.V4) as session:
            adapter = session.get_adapter('https://example.com')
            self.assertIsInstance(adapter, _BaseLockAdapter)

    def test_v6_session_mounts_lock_adapter(self):
        with IPForceSession(IPVersion.V6) as session:
            adapter = session.get_adapter('https://example.com')
            self.assertIsInstance(adapter, _BaseLockAdapter)
            self.assertEqual(adapter._family, socket.AF_INET6)

    def test_session_with_global_method(self):
        with IPForceSession(IPVersion.V4, method=IPForceMethod.GLOBAL) as session:
            adapter = session.get_adapter('https://example.com')
            self.assertIsInstance(adapter, HTTPAdapter)

    def test_session_context_manager(self):
        with IPForceSession(IPVersion.V4) as session:
            self.assertIsInstance(session, IPForceSession)


class TestDeprecationWarnings(unittest.TestCase):
    """Old v0.1 classes emit DeprecationWarning; new API does not."""

    def test_ipv4_transport_adapter_warns(self):
        with warnings.catch_warnings(record=True) as w:
            warnings.simplefilter("always")
            IPv4TransportAdapter()
        self.assertEqual(len(w), 1)
        self.assertTrue(issubclass(w[0].category, DeprecationWarning))
        self.assertIn("IPForceAdapter", str(w[0].message))

    def test_ipv6_transport_adapter_warns(self):
        with warnings.catch_warnings(record=True) as w:
            warnings.simplefilter("always")
            IPv6TransportAdapter()
        self.assertEqual(len(w), 1)
        self.assertTrue(issubclass(w[0].category, DeprecationWarning))

    def test_new_api_does_not_warn(self):
        with warnings.catch_warnings(record=True) as w:
            warnings.simplefilter("always")
            IPForceAdapter(IPVersion.V4, IPForceMethod.LOCK)
            IPForceAdapter(IPVersion.V4, IPForceMethod.GLOBAL)
            session = IPForceSession(IPVersion.V4)
            session.close()
        dep_warnings = [x for x in w if issubclass(x.category, DeprecationWarning)]
        self.assertEqual(len(dep_warnings), 0)


class TestEnums(unittest.TestCase):
    """Test enum values."""

    def test_ip_version_values(self):
        self.assertEqual(IPVersion.V4.value, "ipv4")
        self.assertEqual(IPVersion.V6.value, "ipv6")

    def test_method_values(self):
        self.assertEqual(IPForceMethod.GLOBAL.value, "global")
        self.assertEqual(IPForceMethod.LOCK.value, "lock")
