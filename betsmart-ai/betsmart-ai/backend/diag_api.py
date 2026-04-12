"""Diagnose The Odds API connectivity issues"""
import urllib.request
import urllib.error
import ssl
import socket
import os
from dotenv import load_dotenv

load_dotenv(os.path.join(os.path.dirname(__file__), ".env"))
api_key = os.environ.get("ODDS_API_KEY")

# API keys
keys = {
    "ENV key": api_key,
}

print("=== DNS Resolution ===")
try:
    ip = socket.gethostbyname("api.the-odds-api.com")
    print(f"Resolved: api.the-odds-api.com -> {ip}")
except Exception as e:
    print(f"DNS FAILED: {e}")

print("\n=== Testing HTTP (no SSL) ===")
try:
    url = f"http://api.the-odds-api.com/v4/sports/?apiKey={api_key}"
    req = urllib.request.Request(url, headers={"User-Agent": "curl/7.68.0"})
    with urllib.request.urlopen(req, timeout=10) as r:
        print(f"HTTP OK! Status: {r.status}")
except Exception as e:
    print(f"HTTP FAILED: {type(e).__name__}: {e}")

print("\n=== Testing HTTPS (SSL unverified) ===")
ctx = ssl.create_default_context()
ctx.check_hostname = False
ctx.verify_mode = ssl.CERT_NONE
for name, key in keys.items():
    url = f"https://api.the-odds-api.com/v4/sports/?apiKey={key}"
    try:
        req = urllib.request.Request(url, headers={"User-Agent": "curl/7.68.0"})
        with urllib.request.urlopen(req, context=ctx, timeout=10) as r:
            data = r.read(200)
            print(f"{name}: HTTPS OK! Status={r.status}, data={data[:80]}")
    except Exception as e:
        print(f"{name}: HTTPS FAILED: {type(e).__name__}: {e}")

print("\n=== Testing /v4/sports endpoint (minimal) ===")
import requests
requests.packages.urllib3.disable_warnings()
for name, key in keys.items():
    try:
        r = requests.get(
            f"https://api.the-odds-api.com/v4/sports/?apiKey={key}",
            timeout=10,
            verify=False,
            headers={"User-Agent": "curl/7.68.0", "Accept": "application/json"}
        )
        print(f"{name}: status={r.status_code}, response[:80]={r.text[:80]}")
    except Exception as e:
        print(f"{name}: FAILED: {type(e).__name__}: {e}")
