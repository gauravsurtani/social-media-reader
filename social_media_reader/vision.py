"""
Vision analyzer using Google Gemini API.

Sends images to Gemini's vision model for analysis and description.
"""

import json
import base64
import urllib.request
import urllib.parse
import os
from typing import Optional, Union


# Default model
GEMINI_MODEL = "gemini-2.0-flash"
GEMINI_API_URL = "https://generativelanguage.googleapis.com/v1beta/models/{model}:generateContent"


def _get_api_key() -> str:
    """
    Get Gemini API key from environment or OpenClaw config.
    
    Checks in order:
    1. GEMINI_API_KEY environment variable
    2. OpenClaw config file
    """
    key = os.environ.get("GEMINI_API_KEY")
    if key:
        return key

    # Try OpenClaw config
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

    raise RuntimeError(
        "No Gemini API key found. Set GEMINI_API_KEY environment variable "
        "or configure it in openclaw.json"
    )


def _load_image_as_base64(image_path: str) -> tuple:
    """Load a local image file and return (base64_data, mime_type)."""
    ext = os.path.splitext(image_path)[1].lower()
    mime_map = {
        ".jpg": "image/jpeg", ".jpeg": "image/jpeg",
        ".png": "image/png", ".gif": "image/gif",
        ".webp": "image/webp",
    }
    mime_type = mime_map.get(ext, "image/jpeg")

    with open(image_path, "rb") as f:
        data = base64.b64encode(f.read()).decode("utf-8")
    return data, mime_type


def _download_image(url: str) -> tuple:
    """Download image from URL and return (base64_data, mime_type)."""
    req = urllib.request.Request(url, headers={"User-Agent": "curl/7.0"})
    with urllib.request.urlopen(req, timeout=30) as resp:
        content_type = resp.headers.get("Content-Type", "image/jpeg")
        data = base64.b64encode(resp.read()).decode("utf-8")
    return data, content_type.split(";")[0]


def analyze_image(
    image: str,
    prompt: str = "Describe this image in detail. What do you see?",
    model: str = GEMINI_MODEL,
) -> str:
    """
    Analyze a single image using Gemini vision.
    
    Args:
        image: Local file path or URL to an image
        prompt: Question/instruction for the vision model
        model: Gemini model to use
    
    Returns:
        Text description/analysis from the model
    """
    api_key = _get_api_key()

    # Load image
    if image.startswith(("http://", "https://")):
        img_data, mime_type = _download_image(image)
    else:
        img_data, mime_type = _load_image_as_base64(image)

    # Build request
    url = GEMINI_API_URL.format(model=model) + f"?key={api_key}"
    payload = {
        "contents": [{
            "parts": [
                {"text": prompt},
                {"inline_data": {"mime_type": mime_type, "data": img_data}},
            ]
        }]
    }

    data = json.dumps(payload).encode("utf-8")
    req = urllib.request.Request(url, data=data, headers={
        "Content-Type": "application/json",
    })

    with urllib.request.urlopen(req, timeout=60) as resp:
        result = json.loads(resp.read().decode("utf-8"))

    # Extract text from response
    try:
        return result["candidates"][0]["content"]["parts"][0]["text"]
    except (KeyError, IndexError):
        return f"Error parsing response: {json.dumps(result, indent=2)[:500]}"


def analyze_carousel(
    images: list,
    prompt: str = "These images are from a social media carousel post. Describe what you see across all images and summarize the content.",
    model: str = GEMINI_MODEL,
) -> str:
    """
    Analyze multiple images as a carousel/collection.
    
    Sends all images in a single request for context-aware analysis.
    
    Args:
        images: List of file paths or URLs
        prompt: Question/instruction for the vision model
        model: Gemini model to use
    
    Returns:
        Combined analysis text
    """
    if not images:
        return "No images provided."

    # For large carousels, limit to first 10 images (API limits)
    images = images[:10]

    api_key = _get_api_key()
    url = GEMINI_API_URL.format(model=model) + f"?key={api_key}"

    parts = [{"text": prompt}]
    for img in images:
        try:
            if img.startswith(("http://", "https://")):
                img_data, mime_type = _download_image(img)
            else:
                img_data, mime_type = _load_image_as_base64(img)
            parts.append({"inline_data": {"mime_type": mime_type, "data": img_data}})
        except Exception as e:
            parts.append({"text": f"[Image failed to load: {e}]"})

    payload = {"contents": [{"parts": parts}]}
    data = json.dumps(payload).encode("utf-8")
    req = urllib.request.Request(url, data=data, headers={
        "Content-Type": "application/json",
    })

    with urllib.request.urlopen(req, timeout=120) as resp:
        result = json.loads(resp.read().decode("utf-8"))

    try:
        return result["candidates"][0]["content"]["parts"][0]["text"]
    except (KeyError, IndexError):
        return f"Error parsing response: {json.dumps(result, indent=2)[:500]}"


# --- Testing ---
if __name__ == "__main__":
    print("Testing Gemini Vision API...")
    print(f"API Key: {'found' if _get_api_key() else 'missing'}")
    
    # Test with a public image URL
    test_url = "https://upload.wikimedia.org/wikipedia/commons/thumb/4/47/PNG_transparency_demonstration_1.png/300px-PNG_transparency_demonstration_1.png"
    
    print(f"\nAnalyzing test image: {test_url}")
    try:
        result = analyze_image(test_url, "What is this image? Describe briefly.")
        print(f"Result: {result[:300]}")
        print("\n✅ Vision API working!")
    except Exception as e:
        print(f"❌ Error: {e}")
