# -*- coding: utf-8 -*-
"""Unified public API for IPForce adapter and session creation."""
import warnings

from requests import Session
from requests.adapters import HTTPAdapter

from .enums import IPVersion, IPForceMethod
from .adapters import (
    IPv4TransportAdapter, IPv6TransportAdapter,
    IPv4LockAdapter, IPv6LockAdapter,
)

_ADAPTER_REGISTRY = {
    (IPVersion.V4, IPForceMethod.GLOBAL): IPv4TransportAdapter,
    (IPVersion.V6, IPForceMethod.GLOBAL): IPv6TransportAdapter,
    (IPVersion.V4, IPForceMethod.LOCK): IPv4LockAdapter,
    (IPVersion.V6, IPForceMethod.LOCK): IPv6LockAdapter,
}


def IPForceAdapter(
    ip_version: IPVersion,
    method: IPForceMethod = IPForceMethod.LOCK,
) -> HTTPAdapter:
    """Create an HTTP adapter that forces a specific IP version.

    :param ip_version: IPVersion.V4 or IPVersion.V6
    :param method: thread-safety strategy (default: LOCK)
    :return: configured HTTPAdapter instance
    :raises ValueError: if the (ip_version, method) combination is not registered
    """
    adapter_cls = _ADAPTER_REGISTRY.get((ip_version, method))
    if adapter_cls is None:
        raise ValueError("Unsupported combination: {v} + {m}".format(v=ip_version, m=method))
    with warnings.catch_warnings():
        warnings.simplefilter("ignore", DeprecationWarning)
        return adapter_cls()


class IPForceSession(Session):
    """A requests.Session pre-configured to force a specific IP version."""

    def __init__(
        self,
        ip_version: IPVersion,
        method: IPForceMethod = IPForceMethod.LOCK,
    ) -> None:
        super().__init__()
        adapter = IPForceAdapter(ip_version, method)
        self.mount('http://', adapter)
        self.mount('https://', adapter)
