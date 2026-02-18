"""Instagram post extractor using embed page scraping."""

import re
import subprocess
import json
from html import unescape
from urllib.parse import urlparse


def _normalize_url(url: str) -> str:
    """Ensure URL is a proper Instagram post URL."""
    url = url.strip().rstrip("/")
    parsed = urlparse(url)
    path = parsed.path.rstrip("/")
    return f"https://www.instagram.com{path}/"


def _fetch_embed_html(url: str) -> str:
    """Fetch the embed page HTML using curl."""
    embed_url = _normalize_url(url) + "embed/"
    result = subprocess.run(
        ["curl", "-s", "-L", "-H",
         "User-Agent: curl/7.0",
         embed_url],
        capture_output=True, text=True, timeout=30
    )
    if result.returncode != 0:
        raise RuntimeError(f"Failed to fetch embed page: {result.stderr}")
    return result.stdout


def _extract_json_data(html: str) -> dict | None:
    """Extract the embedded JSON data from the embed page's script tags.
    
    Instagram embeds contain JSON with display_resources for each image
    in the carousel. The data is inside a ServerJS.handle() call.
    """
    # Look for the large script block containing display_resources
    # It's inside a requireLazy(["TimeSliceImpl","ServerJS"], ...) call
    # and contains escaped JSON with display_resources arrays
    
    # Find all display_resources blocks with their src URLs
    # Pattern: "display_resources":[{"config_width":640,"config_height":853,"src":"https:\/\/..."},...]
    pattern = r'"display_resources":\[(\{[^]]+\})\]'
    matches = re.findall(pattern, html)
    
    return matches


def extract_instagram_images(url: str) -> list[str]:
    """Extract content image URLs from an Instagram post.
    
    Returns the highest resolution version of each unique content image.
    Filters out profile pictures and static assets.
    """
    html = _fetch_embed_html(url)
    return _extract_images_from_html(html)


def _extract_images_from_html(html: str) -> list[str]:
    """Extract content image URLs from embed HTML."""
    
    # Strategy 1: Parse display_resources from embedded JSON
    # The JSON is double-escaped in the HTML, so slashes appear as \\/ or \\\\/ 
    # We try multiple escape patterns
    src_pattern = r'src["\\\s:]+?(https?:[/\\]+scontent[^"\\]+(?:[\\]+[^"\\]+)*)'
    all_srcs = re.findall(src_pattern, html)
    
    # Unescape the URLs (replace any \/ or \\/ patterns with /)
    urls = []
    for u in all_srcs:
        u = re.sub(r'\\+/', '/', u)
        u = unescape(u)
        urls.append(u)
    
    if not urls:
        # Strategy 2: Try finding scontent URLs in HTML attributes (img src, srcset)
        raw_urls = re.findall(r'https://scontent[^"\s,<>]+', html)
        urls = [unescape(u) for u in raw_urls]
    
    if not urls:
        return []
    
    # Group by base image ID (unique filename)
    image_groups: dict[str, list[str]] = {}
    for u in urls:
        # Filter out profile pics (t51.2885-19)
        if "2885-19" in u:
            continue
        match = re.search(r'/(\d+_\d+_\d+_n\.jpg)', u)
        if not match:
            continue
        key = match.group(1)
        image_groups.setdefault(key, []).append(u)
    
    # Pick highest resolution for each image
    best_images = []
    for key, group_urls in image_groups.items():
        best = None
        for preferred in ["p1080x1080", "config_width.*1080", "p750x750"]:
            candidates = [u for u in group_urls if re.search(preferred, u)]
            if candidates:
                best = candidates[0]
                break
        if not best:
            # Pick the one with highest config_width or largest URL (more params = higher res)
            non_thumb = [u for u in group_urls if "s150x150" not in u and "s240x240" not in u]
            best = max(non_thumb, key=len) if non_thumb else max(group_urls, key=len)
        best_images.append(best)
    
    return best_images


def get_instagram_metadata(url: str) -> dict:
    """Extract metadata from an Instagram post embed page.
    
    Returns:
        dict with keys: username, post_url, image_count, is_carousel, image_urls
    """
    html = _fetch_embed_html(url)
    
    # Extract username
    username_match = re.search(r'class="UsernameText">([^<]+)<', html)
    if not username_match:
        username_match = re.search(r'"Username">([^<]+)<', html)
    username = username_match.group(1) if username_match else "unknown"
    
    # Check if carousel (sidecar)
    is_carousel = "Sidecar" in html or "sidecar" in html.lower()
    
    # Extract images from the same HTML
    images = _extract_images_from_html(html)
    
    return {
        "username": username,
        "post_url": _normalize_url(url),
        "image_count": len(images),
        "is_carousel": is_carousel,
        "image_urls": images,
    }


def summarize_url(url: str) -> dict:
    """
    Fallback: use the `summarize` CLI tool to extract content from a URL.
    
    Useful when embed scraping fails (blocked, login-walled, etc.).
    Requires the `summarize` CLI to be installed (brew install steipete/tap/summarize).
    
    Returns:
        dict with: method, text, error (if any)
    """
    import shutil
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
    except Exception as e:
        return {"method": "summarize", "error": str(e)}


if __name__ == "__main__":
    import sys
    test_url = sys.argv[1] if len(sys.argv) > 1 else "https://www.instagram.com/p/DUaUSgSEvQT/"
    print(f"Testing with: {test_url}")
    
    print("\n--- Metadata ---")
    meta = get_instagram_metadata(test_url)
    for k, v in meta.items():
        if k == "image_urls":
            print(f"  {k}: [{len(v)} URLs]")
            for i, u in enumerate(v):
                print(f"    [{i}] {u[:100]}...")
        else:
            print(f"  {k}: {v}")
    
    print("\n--- Images ---")
    images = extract_instagram_images(test_url)
    print(f"Found {len(images)} content images")
    for i, img in enumerate(images):
        print(f"  [{i}] {img[:120]}...")
