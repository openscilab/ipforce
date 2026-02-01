<div align="center">
<img src="https://github.com/openscilab/ipforce/raw/main/otherfiles/logo.png" width="350">
<h1>IPForce: TODO</h1>
<br/>
<a href="https://badge.fury.io/py/ipforce"><img src="https://badge.fury.io/py/ipforce.svg" alt="PyPI version"></a>
<a href="https://www.python.org/"><img src="https://img.shields.io/badge/built%20with-Python3-green.svg" alt="built with Python3"></a>
<a href="https://github.com/openscilab/ipforce"><img alt="GitHub repo size" src="https://img.shields.io/github/repo-size/openscilab/ipforce"></a>
<a href="https://discord.gg/TODO"><img src="https://img.shields.io/discord/TODO" alt="Discord Channel"></a>
</div>			
				
## Overview

<p align="justify">					
<b>IPForce</b> is a Python library that provides HTTP adapters for forcing specific IP protocol versions (IPv4 or IPv6) during HTTP requests. It's particularly useful for testing network connectivity, ensuring compatibility with specific network configurations, and controlling which IP protocol version is used for DNS resolution and connections.
</p>

<table>
	<tr>
		<td align="center">PyPI Counter</td>
		<td align="center"><a href="http://pepy.tech/project/ipforce"><img src="http://pepy.tech/badge/ipforce"></a></td>
	</tr>
	<tr>
		<td align="center">Github Stars</td>
		<td align="center"><a href="https://github.com/openscilab/ipforce"><img src="https://img.shields.io/github/stars/openscilab/ipforce.svg?style=social&label=Stars"></a></td>
	</tr>
</table>


<table>
	<tr> 
		<td align="center">Branch</td>
		<td align="center">main</td>	
		<td align="center">dev</td>	
	</tr>
	<tr>
		<td align="center">CI</td>
		<td align="center"><img src="https://github.com/openscilab/ipforce/actions/workflows/test.yml/badge.svg?branch=main"></td>
		<td align="center"><img src="https://github.com/openscilab/ipforce/actions/workflows/test.yml/badge.svg?branch=dev"></td>
	</tr>
</table>

<table>
	<tr> 
		<td align="center">Code Quality</td>
		<td align="center"><a href="https://app.codacy.com/gh/openscilab/ipforce/dashboard?utm_source=gh&utm_medium=referral&utm_content=&utm_campaign=Badge_grade"><img src="https://app.codacy.com/project/badge/Grade/cb2ab6584eb443b8a33da4d4252480bc"/></a></td>
		<td align="center"><a href="https://www.codefactor.io/repository/github/openscilab/ipforce"><img src="https://www.codefactor.io/repository/github/openscilab/ipforce/badge" alt="CodeFactor"></a></td>
	</tr>
</table>


## Installation		

### Source Code
- Download [Version 0.1](https://github.com/openscilab/ipforce/archive/v0.1.zip) or [Latest Source](https://github.com/openscilab/ipforce/archive/dev.zip)
- `pip install .`				

### PyPI
- Check [Python Packaging User Guide](https://packaging.python.org/installing/)     
- `pip install ipforce==0.1`						

## Usage
### Enforce IPv4

Use when you need to ensure connections only use IPv4 addresses, useful for legacy systems that don't support IPv6, networks with IPv4-only infrastructure, or testing IPv4 connectivity.

```python
import requests
from ipforce import IPv4TransportAdapter

# Create a session that will only use IPv4 addresses
session = requests.Session()
session.mount('http://', IPv4TransportAdapter())
session.mount('https://', IPv4TransportAdapter())

# All requests through this session will only resolve to IPv4 addresses
response = session.get('https://ifconfig.co/json')
```

### Enforce IPv6

Use when you need to ensure connections only use IPv6 addresses, useful for modern networks with IPv6 infrastructure, testing IPv6 connectivity, or applications requiring IPv6-specific features.

```python
import requests
from ipforce import IPv6TransportAdapter

# Create a session that will only use IPv6 addresses
session = requests.Session()
session.mount('http://', IPv6TransportAdapter())
session.mount('https://', IPv6TransportAdapter())

# All requests through this session will only resolve to IPv6 addresses
response = session.get('https://ifconfig.co/json')
```

> [!WARNING]
> Current adapters are NOT thread-safe! They modify the global `socket.getaddrinfo` function, which can cause issues in multi-threaded applications.

## Issues & Bug Reports			

Just fill an issue and describe it. We'll check it ASAP!

- Please complete the issue template

You can also join our discord server

<a href="https://discord.gg/TODO">
  <img src="https://img.shields.io/discord/TODO.svg?style=for-the-badge" alt="Discord Channel">
</a>

## Show Your Support
								
<h3>Star This Repo</h3>					

Give a ⭐️ if this project helped you!

<h3>Donate to Our Project</h3>	

If you do like our project and we hope that you do, can you please support us? Our project is not and is never going to be working for profit. We need the money just so we can continue doing what we do ;-)			

<a href="https://openscilab.com/#donation" target="_blank"><img src="https://github.com/openscilab/ipforce/raw/main/otherfiles/donation.png" height="90px" width="270px" alt="IPForce Donation"></a>
