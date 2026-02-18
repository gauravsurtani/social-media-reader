"""
Vision analyzer using Google Gemini API.

Sends images to Gemini's vision model for analysis and description.
Uses only stdlib (urllib, json, base64) - no external dependencies.
"""

import json
import base64
import urllib.request
import urllib.parse
import os
from typing import Optional


GEMINI_MODEL = "gemini-3-flash-preview"
GEMINI_API_URL = "https://generativelanguage.googleapis.com/v1beta/models/{model}:generateContent"


def _get_api_key() -> str:
    """Get Gemini API key from environment or OpenClaw config."""
    key = os.environ.get("GEMINI_API_KEY")
    if key:
        return key

    config_paths = [
        os.path.expanduser("~/.openclaw/openclaw.json"),
        "/data/.openclaw/openclaw.json",
    ]
    for path in config_paths:
        try:
            with open(path) as f:
                config = json.load(f)
            key = config.get("models", {}).get("providers", {}).get("gemini", {}).get("apiKey")
            if key:
                return key
        except (FileNotFoundError, json.JSONDecodeError, KeyError):
            continue

    raise RuntimeError("No Gemini API key found. Set GEMINI_API_KEY or configure openclaw.json")


def _download_image(url: str) -> tuple:
    """Download image from URL and return (base64_data, mime_type)."""
    from .utils import validate_url
    url = validate_url(url)
    req = urllib.request.Request(url, headers={"User-Agent": "curl/7.0"})
    with urllib.request.urlopen(req, timeout=30) as resp:
        content_type = resp.headers.get("Content-Type", "image/jpeg")
        data = base64.b64encode(resp.read()).decode("utf-8")
    return data, content_type.split(";")[0]


def _load_image_as_base64(image_path: str) -> tuple:
    """Load a local image file and return (base64_data, mime_type)."""
    ext = os.path.splitext(image_path)[1].lower()
    mime_map = {".jpg": "image/jpeg", ".jpeg": "image/jpeg", ".png": "image/png",
                ".gif": "image/gif", ".webp": "image/webp"}
    mime_type = mime_map.get(ext, "image/jpeg")
    with open(image_path, "rb") as f:
        data = base64.b64encode(f.read()).decode("utf-8")
    return data, mime_type


def _get_image_data(image: str) -> tuple:
    """Get base64 data and mime type from URL or local path."""
    if image.startswith(("http://", "https://")):
        return _download_image(image)
    else:
        return _load_image_as_base64(image)


def analyze_image(
    image: str,
    prompt: str = "Describe this image in detail. What do you see?",
    model: str = GEMINI_MODEL,
) -> str:
    """Analyze a single image using Gemini vision."""
    api_key = _get_api_key()
    img_data, mime_type = _get_image_data(image)

    url = GEMINI_API_URL.format(model=model) + f"?key={api_key}"
    payload = {
        "contents": [{"parts": [
            {"text": prompt},
            {"inline_data": {"mime_type": mime_type, "data": img_data}},
        ]}]
    }

    data = json.dumps(payload).encode("utf-8")
    req = urllib.request.Request(url, data=data, headers={"Content-Type": "application/json"})

    with urllib.request.urlopen(req, timeout=60) as resp:
        result = json.loads(resp.read().decode("utf-8"))

    try:
        return result["candidates"][0]["content"]["parts"][0]["text"]
    except (KeyError, IndexError):
        return f"Error parsing response: {json.dumps(result, indent=2)[:500]}"


def analyze_carousel(
    images: list,
    prompt: str = "These images are from a social media carousel post. Describe what you see across all images and summarize the content.",
    model: str = GEMINI_MODEL,
) -> str:
    """Analyze multiple images as a carousel/collection."""
    if not images:
        return "No images provided."

    images = images[:10]
    api_key = _get_api_key()
    url = GEMINI_API_URL.format(model=model) + f"?key={api_key}"

    parts = [{"text": prompt}]
    for img in images:
        try:
            img_data, mime_type = _get_image_data(img)
            parts.append({"inline_data": {"mime_type": mime_type, "data": img_data}})
        except Exception as e:
            parts.append({"text": f"[Image failed to load: {e}]"})

    payload = {"contents": [{"parts": parts}]}
    data = json.dumps(payload).encode("utf-8")
    req = urllib.request.Request(url, data=data, headers={"Content-Type": "application/json"})

    with urllib.request.urlopen(req, timeout=120) as resp:
        result = json.loads(resp.read().decode("utf-8"))

    try:
        return result["candidates"][0]["content"]["parts"][0]["text"]
    except (KeyError, IndexError):
        return f"Error parsing response: {json.dumps(result, indent=2)[:500]}"


if __name__ == "__main__":
    print("Testing Gemini Vision API...")
    print(f"API Key: {'found' if _get_api_key() else 'missing'}")
    test_url = "https://www.google.com/images/branding/googlelogo/2x/googlelogo_color_272x92dp.png"
    print(f"\nAnalyzing: {test_url}")
    try:
        result = analyze_image(test_url, "What is this image? One sentence.")
        print(f"Result: {result[:300]}")
        print("\n✅ Vision API working!")
    except Exception as e:
        print(f"❌ Error: {e}")
