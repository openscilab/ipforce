# -*- coding: utf-8 -*-
"""IPForce Adapters to force IPv4 or IPv6 for requests."""
import socket
import warnings
from typing import Any, List, Tuple
from requests.adapters import HTTPAdapter
from threading import Lock, local

# ============================================================================
# Base adapter (not thread-safe)
# ============================================================================


class IPv4TransportAdapter(HTTPAdapter):
    """A custom HTTPAdapter that enforces the use of IPv4 for DNS resolution during HTTP(S) requests using the requests library."""

    def __init__(self, *args, **kwargs) -> None:
        """Initialize the adapter and emit a deprecation warning."""
        warnings.warn(
            "IPv4TransportAdapter is deprecated, use IPForceAdapter(IPVersion.V4, IPForceMethod.GLOBAL) instead",
            DeprecationWarning,
            stacklevel=2,
        )
        super().__init__(*args, **kwargs)

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

    def __init__(self, *args, **kwargs) -> None:
        """Initialize the adapter and emit a deprecation warning."""
        warnings.warn(
            "IPv6TransportAdapter is deprecated, use IPForceAdapter(IPVersion.V6, IPForceMethod.GLOBAL) instead",
            DeprecationWarning,
            stacklevel=2,
        )
        super().__init__(*args, **kwargs)

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


# ============================================================================
# Thread-local dispatch adapters
#
# A single dispatching getaddrinfo is installed once; each thread stores its
# own target family in thread-local storage, so DNS resolution runs fully
# concurrently without a process-wide lock.
# ============================================================================

_tl_storage = local()
_tl_original_getaddrinfo = None
_tl_installed = False
_tl_install_lock = Lock()


def _tl_dispatching_getaddrinfo(*args: list, **kwargs: dict) -> List[Tuple]:
    """Dispatch getaddrinfo through thread-local family filter."""
    results = _tl_original_getaddrinfo(*args, **kwargs)
    family_filter = getattr(_tl_storage, 'family_filter', None)
    if family_filter is not None:
        return [r for r in results if r[0] == family_filter]
    return results


def _tl_ensure_installed() -> None:
    """Install the thread-local dispatching getaddrinfo (once, lazily)."""
    global _tl_installed, _tl_original_getaddrinfo
    if _tl_installed:
        return
    with _tl_install_lock:
        if _tl_installed:
            return
        _tl_original_getaddrinfo = socket.getaddrinfo
        socket.getaddrinfo = _tl_dispatching_getaddrinfo
        _tl_installed = True


class _BaseThreadLocalAdapter(HTTPAdapter):
    """Base class for thread-local dispatch adapters."""

    _family = socket.AF_UNSPEC

    def send(self, *args: list, **kwargs: dict) -> Any:
        """
        Send with per-thread address family filtering via thread-local storage.

        :param args: additional list arguments for the send method
        :param kwargs: additional keyword arguments for the send method
        """
        _tl_ensure_installed()
        _tl_storage.family_filter = self._family
        try:
            return super().send(*args, **kwargs)
        finally:
            _tl_storage.family_filter = None


class IPv4ThreadLocalAdapter(_BaseThreadLocalAdapter):
    """Thread-safe HTTPAdapter that enforces IPv4 via thread-local dispatch."""

    _family = socket.AF_INET


class IPv6ThreadLocalAdapter(_BaseThreadLocalAdapter):
    """Thread-safe HTTPAdapter that enforces IPv6 via thread-local dispatch."""

    _family = socket.AF_INET6


