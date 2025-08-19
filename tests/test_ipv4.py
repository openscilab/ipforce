import requests
import ipaddress
from ipforce import IPv4TransportAdapter


def is_ipv4(ip: str) -> bool:
    """
    Check if the given input is a valid IPv4 address.

    :param ip: input IP
    """
    if not isinstance(ip, str):
        return False
    try:
        _ = ipaddress.IPv4Address(ip)
        return True
    except Exception:
        return False


def test_ipv4_adapter():
    """Test the IPv4 adapter by making a request that will only use IPv4 addresses."""
    print("Testing IPv4 Adapter...")
    
    # Create a session with IPv4 adapter
    with requests.Session() as session:
        ipv4Addapter = IPv4TransportAdapter()
        session.mount('http://', ipv4Addapter)
        session.mount('https://', ipv4Addapter)
        # This will only resolve to IPv4 addresses
        response = session.get('https://ifconfig.co/json', timeout=10)
        response.raise_for_status()
        assert is_ipv4(response.json()['ip'])
