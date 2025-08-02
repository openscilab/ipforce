import socket
from typing import List, Tuple
from urllib3 import PoolManager
from requests.adapters import HTTPAdapter
from requests.sessions import Session

class IPv4HTTPAdapter(HTTPAdapter):
    """A custom HTTPAdapter that enforces the use of IPv4 for DNS resolution during HTTP(S) requests using the requests library."""

    def init_poolmanager(self, connections: int, maxsize: int, block: bool = False, **kwargs: dict) -> None:
        """
        Initialize the connection pool manager using a temporary override of socket.getaddrinfo to ensure only IPv4 addresses are used.
        This is necessary to ensure that the requests library uses IPv4 addresses for DNS resolution, which is required for some APIs.
        :param connections: the number of connection pools to cache
        :param maxsize: the maximum number of connections to save in the pool
        :param block: whether the connections should block when reaching the max size
        :param kwargs: additional keyword arguments for the PoolManager
        """
        self.poolmanager = PoolManager(
            num_pools=connections,
            maxsize=maxsize,
            block=block,
            socket_options=self._ipv4_socket_options(),
            **kwargs
        )

    def _ipv4_socket_options(self) -> list:
        """
        Temporarily patches socket.getaddrinfo to filter only IPv4 addresses (AF_INET).

        :return: an empty list of socket options; DNS patching occurs here
        """
        original_getaddrinfo = socket.getaddrinfo

        def ipv4_only_getaddrinfo(*args: list, **kwargs: dict) -> List[Tuple]:
            results = original_getaddrinfo(*args, **kwargs)
            return [res for res in results if res[0] == socket.AF_INET]

        self._original_getaddrinfo = socket.getaddrinfo
        socket.getaddrinfo = ipv4_only_getaddrinfo

        return []

    def __del__(self) -> None:
        """Restores the original socket.getaddrinfo function upon adapter deletion."""
        if hasattr(self, "_original_getaddrinfo"):
            socket.getaddrinfo = self._original_getaddrinfo

    @staticmethod
    def get_ipv4_enforced_session() -> Session:
        """
        Returns a requests.Session with IPv4HTTPAdapter mounted for both HTTP and HTTPS.
        All requests made with this session will use IPv4 for DNS resolution.

        :return: requests.Session object with IPv4 enforced
        """
        session = Session()
        adapter = IPv4HTTPAdapter()
        session.mount("http://", adapter)
        session.mount("https://", adapter)
        return session
