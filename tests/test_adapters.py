import unittest
import socket
from unittest.mock import patch, MagicMock
from ipforce.adapters import IPv4TransportAdapter, IPv6TransportAdapter


class TestIPv4Adapter(unittest.TestCase):
    """Test cases for IPv4TransportAdapter."""

    def set_up(self):
        """Set up test fixtures."""
        self.adapter = IPv4TransportAdapter()

    def test_ipv4_filtering_during_send(self):
        """Test that IPv4 adapter filters only IPv4 addresses during send."""
        self.set_up()
        mock_results = [
            (socket.AF_INET, socket.SOCK_STREAM, 6, '', ('192.168.1.1', 80)),  # IPv4
            (socket.AF_INET6, socket.SOCK_STREAM, 6, '', ('::1', 80)),         # IPv6
            (socket.AF_INET, socket.SOCK_STREAM, 6, '', ('10.0.0.1', 80)),     # IPv4
        ]

        original_getaddrinfo = socket.getaddrinfo
        captured_results = []

        def mock_super_send(*args, **kwargs):
            # Capture the filtered results during send
            captured_results.extend(socket.getaddrinfo('example.com', 80))
            return MagicMock()

        with patch('socket.getaddrinfo', return_value=mock_results):
            with patch.object(IPv4TransportAdapter.__bases__[0], 'send', mock_super_send):
                self.adapter.send(MagicMock())

        # Only IPv4 results should be captured
        self.assertEqual(len(captured_results), 2)
        for result in captured_results:
            self.assertEqual(result[0], socket.AF_INET)

    def test_cleanup_after_send(self):
        """Test that the adapter properly restores original getaddrinfo after send."""
        self.set_up()
        original_getaddrinfo = socket.getaddrinfo

        with patch.object(IPv4TransportAdapter.__bases__[0], 'send', return_value=MagicMock()):
            self.adapter.send(MagicMock())

        # Verify it was restored after send
        self.assertEqual(socket.getaddrinfo, original_getaddrinfo)

    def test_cleanup_on_exception(self):
        """Test that the adapter restores original getaddrinfo even if send raises."""
        self.set_up()
        original_getaddrinfo = socket.getaddrinfo

        with patch.object(IPv4TransportAdapter.__bases__[0], 'send', side_effect=Exception("Test error")):
            with self.assertRaises(Exception):
                self.adapter.send(MagicMock())

        # Verify it was restored even after exception
        self.assertEqual(socket.getaddrinfo, original_getaddrinfo)


class TestIPv6Adapter(unittest.TestCase):
    """Test cases for IPv6TransportAdapter."""

    def set_up(self):
        """Set up test fixtures."""
        self.adapter = IPv6TransportAdapter()

    def test_ipv6_filtering_during_send(self):
        """Test that IPv6 adapter filters only IPv6 addresses during send."""
        self.set_up()
        mock_results = [
            (socket.AF_INET, socket.SOCK_STREAM, 6, '', ('192.168.1.1', 80)),  # IPv4
            (socket.AF_INET6, socket.SOCK_STREAM, 6, '', ('::1', 80)),         # IPv6
            (socket.AF_INET6, socket.SOCK_STREAM, 6, '', ('2001:db8::1', 80)), # IPv6
        ]

        captured_results = []

        def mock_super_send(*args, **kwargs):
            # Capture the filtered results during send
            captured_results.extend(socket.getaddrinfo('example.com', 80))
            return MagicMock()

        with patch('socket.getaddrinfo', return_value=mock_results):
            with patch.object(IPv6TransportAdapter.__bases__[0], 'send', mock_super_send):
                self.adapter.send(MagicMock())

        # Only IPv6 results should be captured
        self.assertEqual(len(captured_results), 2)
        for result in captured_results:
            self.assertEqual(result[0], socket.AF_INET6)

    def test_cleanup_after_send(self):
        """Test that the adapter properly restores original getaddrinfo after send."""
        self.set_up()
        original_getaddrinfo = socket.getaddrinfo

        with patch.object(IPv6TransportAdapter.__bases__[0], 'send', return_value=MagicMock()):
            self.adapter.send(MagicMock())

        # Verify it was restored after send
        self.assertEqual(socket.getaddrinfo, original_getaddrinfo)

    def test_cleanup_on_exception(self):
        """Test that the adapter restores original getaddrinfo even if send raises."""
        self.set_up()
        original_getaddrinfo = socket.getaddrinfo

        with patch.object(IPv6TransportAdapter.__bases__[0], 'send', side_effect=Exception("Test error")):
            with self.assertRaises(Exception):
                self.adapter.send(MagicMock())

        # Verify it was restored even after exception
        self.assertEqual(socket.getaddrinfo, original_getaddrinfo)


class TestAdapterIntegration(unittest.TestCase):
    """Integration tests for both adapters."""

    def test_both_adapters_independent(self):
        """Test that both adapters can coexist without interference."""
        ipv4_adapter = IPv4TransportAdapter()
        ipv6_adapter = IPv6TransportAdapter()
        original_getaddrinfo = socket.getaddrinfo

        with patch.object(IPv4TransportAdapter.__bases__[0], 'send', return_value=MagicMock()):
            ipv4_adapter.send(MagicMock())

        with patch.object(IPv6TransportAdapter.__bases__[0], 'send', return_value=MagicMock()):
            ipv6_adapter.send(MagicMock())

        # Verify original is still intact
        self.assertEqual(socket.getaddrinfo, original_getaddrinfo)

    def test_sequential_sends_restore_correctly(self):
        """Test that multiple sequential sends properly restore getaddrinfo."""
        adapter = IPv4TransportAdapter()
        original_getaddrinfo = socket.getaddrinfo

        with patch.object(IPv4TransportAdapter.__bases__[0], 'send', return_value=MagicMock()):
            adapter.send(MagicMock())
            adapter.send(MagicMock())
            adapter.send(MagicMock())

        # Verify original is still intact after multiple sends
        self.assertEqual(socket.getaddrinfo, original_getaddrinfo)
