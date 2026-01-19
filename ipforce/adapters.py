# -*- coding: utf-8 -*-
"""IPForce Adapters to force IPv4 or IPv6 for requests."""
import socket
from typing import Any, List, Tuple
from requests.adapters import HTTPAdapter


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
