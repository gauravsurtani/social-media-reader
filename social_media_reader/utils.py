"""Shared utilities for social-media-reader."""

import re
import shutil
import subprocess
from urllib.parse import urlparse
from typing import Optional


# Allowed URL schemes
_ALLOWED_SCHEMES = {"http", "https"}

# Blocked hosts (SSRF prevention)
_BLOCKED_HOST_PATTERNS = [
    r"^localhost$",
    r"^127\.",
    r"^10\.",
    r"^172\.(1[6-9]|2\d|3[01])\.",
    r"^192\.168\.",
    r"^0\.",
    r"^169\.254\.",  # link-local
    r"^\[::1\]$",
    r"^metadata\.google\.internal$",
]


def validate_url(url: str) -> str:
    """
    Validate and sanitize a URL for safe network requests.

    Checks:
    - Scheme is http/https only
    - Host is not a private/loopback address (SSRF prevention)
    - URL is well-formed

    Returns the validated URL string.
    Raises ValueError if the URL is invalid or targets a blocked host.
    """
    if not isinstance(url, str) or not url.strip():
        raise ValueError("URL must be a non-empty string")

    url = url.strip()
    parsed = urlparse(url)

    if parsed.scheme not in _ALLOWED_SCHEMES:
        raise ValueError(f"URL scheme must be http or https, got: {parsed.scheme!r}")

    if not parsed.hostname:
        raise ValueError("URL must have a hostname")

    hostname = parsed.hostname.lower()
    for pattern in _BLOCKED_HOST_PATTERNS:
        if re.match(pattern, hostname):
            raise ValueError(f"URL targets a blocked host: {hostname}")

    return url


def summarize_url(url: str) -> dict:
    """
    Fallback: use the `summarize` CLI tool to extract content from a URL.

    Useful when scraping fails (blocked, login-walled, etc.).
    Requires the `summarize` CLI to be installed.

    Returns:
        dict with: method, text, error (if any)
    """
    url = validate_url(url)

    if not shutil.which("summarize"):
        return {"method": "summarize", "error": "summarize CLI not installed"}

    try:
        result = subprocess.run(
            ["summarize", url, "--extract-only"],
            capture_output=True, text=True, timeout=60
        )
        if result.returncode == 0 and result.stdout.strip():
            return {"method": "summarize", "text": result.stdout.strip()}
        return {"method": "summarize", "error": f"exit {result.returncode}: {result.stderr[:200]}"}
    except subprocess.TimeoutExpired:
        return {"method": "summarize", "error": "Command timed out after 60s"}
    except Exception as e:
        return {"method": "summarize", "error": str(e)}
