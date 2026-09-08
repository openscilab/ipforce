# -*- coding: utf-8 -*-
"""ipforce params."""
from enum import Enum

IPFORCE_VERSION = "0.2"
IPFORCE_OVERVIEW = '''OVERVIEW'''
IPFORCE_REPO = "https://github.com/openscilab/ipforce"


class IPVersion(Enum):
    """IP protocol version to enforce for DNS resolution."""

    V4 = "ipv4"
    V6 = "ipv6"


class IPForceMethod(Enum):
    """Thread-safety strategy for address family enforcement."""

    GLOBAL = "global"
    LOCK = "lock"
