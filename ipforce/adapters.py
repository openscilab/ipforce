# -*- coding: utf-8 -*-
"""IPForce Adapters to force IPv4 or IPv6 for requests."""
import socket
from typing import Any, List, Tuple
from requests.adapters import HTTPAdapter
from threading import Lock

# ============================================================================
# Base adapter (not thread-safe)
# ============================================================================


class IPv4TransportAdapter(HTTPAdapter):
    """A custom HTTPAdapter that enforces the use of IPv4 for DNS resolution during HTTP(S) requests using the requests library."""

    def send(self, *args: list, **kwargs: dict) -> Any:
        """
        Override send method to apply the monkey patch only during the request.

        :param args: additional list arguments for the send method
        :param kwargs: additional keyword arguments for the send method
        """
        original_getaddrinfo = socket.getaddrinfo

        def ipv4_only_getaddrinfo(*gargs: list, **gkwargs: dict) -> List[Tuple]:
            """
            Filter getaddrinfo to return only IPv4 addresses.

            :param gargs: additional list arguments for the original_getaddrinfo function
            :param gkwargs: additional keyword arguments for the original_getaddrinfo function
            """
            results = original_getaddrinfo(*gargs, **gkwargs)
            return [res for res in results if res[0] == socket.AF_INET]

        socket.getaddrinfo = ipv4_only_getaddrinfo
        try:
            response = super().send(*args, **kwargs)
        finally:
            socket.getaddrinfo = original_getaddrinfo
        return response


class IPv6TransportAdapter(HTTPAdapter):
    """A custom HTTPAdapter that enforces the use of IPv6 for DNS resolution during HTTP(S) requests using the requests library."""

    def send(self, *args: list, **kwargs: dict) -> Any:
        """
        Override send method to apply the monkey patch only during the request.

        :param args: additional list arguments for the send method
        :param kwargs: additional keyword arguments for the send method
        """
        original_getaddrinfo = socket.getaddrinfo

        def ipv6_only_getaddrinfo(*gargs: list, **gkwargs: dict) -> List[Tuple]:
            """
            Filter getaddrinfo to return only IPv6 addresses.

            :param gargs: additional list arguments for the original_getaddrinfo function
            :param gkwargs: additional keyword arguments for the original_getaddrinfo function
            """
            results = original_getaddrinfo(*gargs, **gkwargs)
            return [res for res in results if res[0] == socket.AF_INET6]

        socket.getaddrinfo = ipv6_only_getaddrinfo
        try:
            response = super().send(*args, **kwargs)
        finally:
            socket.getaddrinfo = original_getaddrinfo
        return response


# ============================================================================
# Lock-based thread-safe adapters
#
# A process-wide lock serializes access to the global socket.getaddrinfo
# patch. Correct under all conditions, but serializes DNS resolution
# across threads.
# ============================================================================

_adapter_lock = Lock()


class _BaseLockAdapter(HTTPAdapter):
    """Base class for lock-based thread-safe adapters."""

    _family = socket.AF_UNSPEC

    def send(self, *args: list, **kwargs: dict) -> Any:
        """
        Thread-safe send that acquires a lock before patching getaddrinfo.

        :param args: additional list arguments for the send method
        :param kwargs: additional keyword arguments for the send method
        """
        with _adapter_lock:
            original_getaddrinfo = socket.getaddrinfo
            family = self._family

            def filtered_getaddrinfo(*gargs: list, **gkwargs: dict) -> List[Tuple]:
                """Filter getaddrinfo results to the target address family.

                :param gargs: additional list arguments for the original_getaddrinfo function
                :param gkwargs: additional keyword arguments for the original_getaddrinfo function
                """
                results = original_getaddrinfo(*gargs, **gkwargs)
                return [r for r in results if r[0] == family]

            socket.getaddrinfo = filtered_getaddrinfo
            try:
                return super().send(*args, **kwargs)
            finally:
                socket.getaddrinfo = original_getaddrinfo


class IPv4LockAdapter(_BaseLockAdapter):
    """Thread-safe HTTPAdapter that enforces IPv4 using a global lock.

    All requests across all threads are serialized through a single lock,
    ensuring no race conditions on socket.getaddrinfo. Best suited for
    low-concurrency use cases where simplicity is preferred.
    """

    _family = socket.AF_INET


class IPv6LockAdapter(_BaseLockAdapter):
    """Thread-safe HTTPAdapter that enforces IPv6 using a global lock.

    All requests across all threads are serialized through a single lock,
    ensuring no race conditions on socket.getaddrinfo. Best suited for
    low-concurrency use cases where simplicity is preferred.
    """

    _family = socket.AF_INET6


