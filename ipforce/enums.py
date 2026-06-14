# -*- coding: utf-8 -*-
"""IPForce enumerations for IP version and resolution method selection."""
from enum import Enum


class IPVersion(Enum):
    """IP protocol version to enforce for DNS resolution."""

    V4 = "ipv4"
    V6 = "ipv6"


class IPForceMethod(Enum):
    """Thread-safety strategy for address family enforcement."""

    GLOBAL = "global"
    LOCK = "lock"
