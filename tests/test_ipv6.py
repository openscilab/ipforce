import requests
import ipaddress
from ipforce import IPv6HTTPAdapter


def is_ipv6(ip: str) -> bool:
    """
    Check if the given input is a valid IPv6 address.

    :param ip: input IP
    """
    if not isinstance(ip, str):
        return False
    try:
        _ = ipaddress.IPv6Address(ip)
        return True
    except Exception:
        return False


def test_ipv6_adapter():
    """Test the IPv6 adapter by making a request that will only use IPv6 addresses."""
    print("\nTesting IPv6 Adapter...")
    
    # Create a session with IPv6 adapter
    with requests.Session() as session:
        ipv6Addapter = IPv6HTTPAdapter()
        session.mount('http://', ipv6Addapter)
        session.mount('https://', ipv6Addapter)
        # This will only resolve to IPv6 addresses
        response = session.get('https://ifconfig.co/json', timeout=10)
        response.raise_for_status()
        assert is_ipv6(response.json()['ip'])
