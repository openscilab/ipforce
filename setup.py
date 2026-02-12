# -*- coding: utf-8 -*-
"""Setup module."""
from typing import List
try:
    from setuptools import setup
except ImportError:
    from distutils.core import setup


def get_requires() -> List[str]:
    """Read requirements.txt."""
    requirements = open("requirements.txt", "r").read()
    return list(filter(lambda x: x != "", requirements.split()))


def read_description() -> str:
    """Read README.md and CHANGELOG.md."""
    try:
        with open("README.md") as r:
            description = "\n"
            description += r.read()
        with open("CHANGELOG.md") as c:
            description += "\n"
            description += c.read()
        return description
    except Exception:
        return '''IPForce is a Python library that provides HTTP adapters for forcing specific IP protocol versions (IPv4 or IPv6) during HTTP requests.
                It's particularly useful for testing network connectivity, ensuring compatibility with specific network configurations,
                and controlling which IP protocol version is used for DNS resolution and connections.'''


setup(
    name='ipforce',
    packages=['ipforce'],
    version='0.1',
    description='IPForce: Force IPv4/IPv6 in Python HTTP Requests',
    long_description=read_description(),
    long_description_content_type='text/markdown',
    include_package_data=True,
    author='IPForce Development Team',
    author_email='ipforce@openscilab.com',
    url='https://github.com/openscilab/ipforce',
    download_url='https://github.com/openscilab/ipforce/tarball/v0.1',
    keywords="http ipv4 ipv6 network requests adapter dns socket protocol ip-force",
    project_urls={
        'Source': 'https://github.com/openscilab/ipforce'
    },
    install_requires=get_requires(),
    python_requires='>=3.7',
    classifiers=[
        'Development Status :: 2 - Pre-Alpha',
        'Natural Language :: English',
        'License :: OSI Approved :: MIT License',
        'Operating System :: OS Independent',
        'Programming Language :: Python :: 3.7',
        'Programming Language :: Python :: 3.8',
        'Programming Language :: Python :: 3.9',
        'Programming Language :: Python :: 3.10',
        'Programming Language :: Python :: 3.11',
        'Programming Language :: Python :: 3.12',
        'Programming Language :: Python :: 3.13',
        'Programming Language :: Python :: 3.14',
        'Intended Audience :: Developers',
        'Intended Audience :: Education',
        'Topic :: System :: Networking',
        'Topic :: Utilities',
        'Topic :: Internet :: WWW/HTTP',
        'Topic :: Software Development :: Libraries :: Python Modules',
    ],
    license='MIT',
)
