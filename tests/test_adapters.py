import unittest
import socket
from unittest.mock import patch
from ipforce.adapters import IPv4TransportAdapter, IPv6TransportAdapter


class TestIPv4Adapter(unittest.TestCase):
    """Test cases for IPv4HTTPAdapter."""

    def setUp(self):
        """Set up test fixtures."""
        self.adapter = IPv4TransportAdapter()

    def test_ipv4_socket_options(self):
        """Test that IPv4 adapter filters only IPv4 addresses."""
        # Mock socket.getaddrinfo to return mixed results
        mock_results = [
            (socket.AF_INET, socket.SOCK_STREAM, 6, '', ('192.168.1.1', 80)),  # IPv4
            (socket.AF_INET6, socket.SOCK_STREAM, 6, '', ('::1', 80)),         # IPv6
            (socket.AF_INET, socket.SOCK_STREAM, 6, '', ('10.0.0.1', 80)),     # IPv4
        ]
        
        with patch('socket.getaddrinfo', return_value=mock_results):
            # Call the method that patches socket.getaddrinfo
            self.adapter._ipv4_socket_options()
            # Test that the patched function filters correctly
            results = socket.getaddrinfo('example.com', 80)
            self.assertEqual(len(results), 2)  # Only IPv4 results
            for result in results:
                self.assertEqual(result[0], socket.AF_INET)

    def test_cleanup(self):
        """Test that the adapter properly restores original getaddrinfo."""
        original_getaddrinfo = socket.getaddrinfo
        self.adapter._ipv4_socket_options()
        
        # Verify it was patched
        self.assertNotEqual(socket.getaddrinfo, original_getaddrinfo)
        
        # Clean up
        self.adapter.__del__()
        
        # Verify it was restored
        self.assertEqual(socket.getaddrinfo, original_getaddrinfo)


class TestIPv6Adapter(unittest.TestCase):
    """Test cases for IPv6HTTPAdapter."""

    def setUp(self):
        """Set up test fixtures."""
        self.adapter = IPv6TransportAdapter()

    def test_ipv6_socket_options(self):
        """Test that IPv6 adapter filters only IPv6 addresses."""
        # Mock socket.getaddrinfo to return mixed results
        mock_results = [
            (socket.AF_INET, socket.SOCK_STREAM, 6, '', ('192.168.1.1', 80)),  # IPv4
            (socket.AF_INET6, socket.SOCK_STREAM, 6, '', ('::1', 80)),         # IPv6
            (socket.AF_INET6, socket.SOCK_STREAM, 6, '', ('2001:db8::1', 80)), # IPv6
        ]
        
        with patch('socket.getaddrinfo', return_value=mock_results):
            # Call the method that patches socket.getaddrinfo
            self.adapter._ipv6_socket_options()
            
            # Test that the patched function filters correctly
            results = socket.getaddrinfo('example.com', 80)
            self.assertEqual(len(results), 2)  # Only IPv6 results
            for result in results:
                self.assertEqual(result[0], socket.AF_INET6)

    def test_cleanup(self):
        """Test that the adapter properly restores original getaddrinfo."""
        original_getaddrinfo = socket.getaddrinfo
        self.adapter._ipv6_socket_options()
        
        # Verify it was patched
        self.assertNotEqual(socket.getaddrinfo, original_getaddrinfo)
        
        # Clean up
        self.adapter.__del__()
        
        # Verify it was restored
        self.assertEqual(socket.getaddrinfo, original_getaddrinfo)


class TestAdapterIntegration(unittest.TestCase):
    """Integration tests for both adapters."""

    def test_both_adapters_independent(self):
        """Test that both adapters can coexist without interference."""
        ipv4_adapter = IPv4TransportAdapter()
        ipv6_adapter = IPv6TransportAdapter()

        # Both should be able to patch independently
        ipv4_adapter._ipv4_socket_options()
        ipv6_adapter._ipv6_socket_options()

        # Clean up both
        ipv4_adapter.__del__()
        ipv6_adapter.__del__()
