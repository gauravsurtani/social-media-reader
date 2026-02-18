"""
LinkedIn content extractor with multiple fallback strategies.

LinkedIn aggressively blocks unauthenticated scraping. This module
implements every available workaround:

1. **oEmbed API** — Gets title/author for some URLs (often returns 404)
2. **Paste mode** — Accept raw copy-pasted text and parse it
3. **Screen recording** — Process video of scrolling through a post:
   extract frames with ffmpeg, analyze with Gemini Vision
4. **Screenshot** — Send screenshot image to vision model for OCR

## Honest Status (as of 2025):
- oEmbed: works for ~30% of post URLs, returns 404 for the rest
- Direct fetch: returns 999 (Request Denied) or login redirects
- Embed iframe: returns JS SPA, no server-side content
- Best approach: paste mode or screenshot/screen recording + Vision AI
"""

import json
import re
import subprocess
import urllib.request
import urllib.parse
from typing import Optional


# ─── oEmbed Extraction ─────────────────────────────────────────

def get_linkedin_oembed(url: str) -> dict:
    """
    Fetch LinkedIn post metadata via oEmbed endpoint.
    
    Works for some post/article URLs. Returns 404 for many.
    When it works, returns: title, author_name, author_url, html (embed iframe).
    """
    oembed_url = f"https://www.linkedin.com/oembed?url={urllib.parse.quote(url, safe='')}&format=json"

    req = urllib.request.Request(oembed_url, headers={
        "User-Agent": "curl/7.0",
        "Accept": "application/json",
    })

    try:
        with urllib.request.urlopen(req, timeout=15) as resp:
            data = json.loads(resp.read().decode("utf-8"))
        return {
            "method": "oembed",
            "author": data.get("author_name", ""),
            "author_url": data.get("author_url", ""),
            "title": data.get("title", ""),
            "embed_html": data.get("html", ""),
            "provider": data.get("provider_name", "LinkedIn"),
        }
    except urllib.error.HTTPError as e:
        return {"method": "oembed", "error": f"HTTP {e.code}", "url": url}
    except Exception as e:
        return {"method": "oembed", "error": str(e), "url": url}


def extract_linkedin_metadata(url: str) -> dict:
    """
    Try all available methods to extract LinkedIn content.
    
    Attempts in order:
    1. oEmbed API
    2. Open Graph tags via direct fetch
    
    Returns dict with available fields + method used.
    """
    # Try oEmbed first
    result = get_linkedin_oembed(url)
    if not result.get("error"):
        return result

    # Try OG tags
    try:
        og = _fetch_og_tags(url)
        if og.get("title") or og.get("description"):
            og["method"] = "opengraph"
            og["url"] = url
            return og
    except Exception:
        pass

    # Try summarize CLI as last resort
    summary = summarize_url(url)
    if not summary.get("error"):
        return {
            "method": "summarize",
            "url": url,
            "description": summary["text"][:2000],
            "images": [],
        }

    return {
        "method": "failed",
        "url": url,
        "error": (
            "LinkedIn requires authentication for most content. "
            "Use --paste mode, screenshot, or screen recording instead."
        ),
        "images": [],
    }


def _fetch_og_tags(url: str) -> dict:
    """Fetch Open Graph meta tags from a LinkedIn page."""
    req = urllib.request.Request(url, headers={
        "User-Agent": "Mozilla/5.0 (compatible; Googlebot/2.1; +http://www.google.com/bot.html)",
        "Accept": "text/html",
    })
    with urllib.request.urlopen(req, timeout=15) as resp:
        html = resp.read(100_000).decode("utf-8", errors="replace")

    data = {}
    for key in ("title", "description", "image"):
        match = re.search(
            rf'<meta\s+(?:property|name)="og:{key}"\s+content="([^"]*)"',
            html, re.IGNORECASE
        )
        if match:
            data[key] = match.group(1)

    if data.get("image"):
        data["images"] = [data["image"]]
    else:
        data["images"] = []

    return data


def get_linkedin_images(url: str) -> list:
    """Get image URLs from LinkedIn (usually just OG image if any)."""
    metadata = extract_linkedin_metadata(url)
    return metadata.get("images", [])


# ─── Paste Mode ────────────────────────────────────────────────

def parse_paste(text: str) -> dict:
    """
    Parse raw copy-pasted LinkedIn post text into structured data.
    
    Handles the typical copy-paste format from LinkedIn:
    - First line(s): author name and headline
    - Then post body
    - Hashtags (#tag) and @mentions
    - Engagement metrics at the bottom
    
    Args:
        text: Raw pasted text from LinkedIn
        
    Returns:
        dict with: author, headline, body, hashtags, mentions
    """
    lines = text.strip().split("\n")
    if not lines:
        return {"author": "", "headline": "", "body": "", "hashtags": [], "mentions": []}

    # First non-empty line is usually the author name
    author = ""
    headline = ""
    body_start = 0

    for i, line in enumerate(lines):
        line = line.strip()
        if not line:
            continue
        if not author:
            author = line
            body_start = i + 1
            continue
        if not headline:
            headline = line
            body_start = i + 1
            break

    # Rest is the body
    body = "\n".join(lines[body_start:]).strip()

    # Extract hashtags and mentions
    hashtags = re.findall(r"#(\w+)", text)
    mentions = re.findall(r"@(\w+)", text)

    # Remove engagement metrics (likes, comments, reposts at bottom)
    body = re.sub(
        r"\n\d+\s*(likes?|comments?|reposts?|reactions?|shares?).*$",
        "", body, flags=re.IGNORECASE | re.MULTILINE
    )

    # Remove "...see more" / "...more" patterns
    body = re.sub(r"\.{3}\s*(see )?more\s*$", "", body, flags=re.IGNORECASE)

    return {
        "author": author,
        "headline": headline,
        "body": body.strip(),
        "hashtags": hashtags,
        "mentions": mentions,
    }


# ─── Screenshot / Image Analysis ──────────────────────────────

def analyze_screenshot(image_path: str) -> dict:
    """
    Analyze a screenshot of a LinkedIn post using vision model.
    
    Extracts text content, author info, and post details from the image.
    
    Args:
        image_path: Path to screenshot file (or URL)
    
    Returns:
        dict with: text, author, analysis
    """
    from .vision import analyze_image

    analysis = analyze_image(
        image_path,
        "This is a screenshot of a LinkedIn post. Extract all text content you can read. "
        "Return the result in this format:\n"
        "AUTHOR: [author name]\n"
        "HEADLINE: [author's headline/title]\n"
        "POST TEXT: [full post text]\n"
        "HASHTAGS: [any hashtags]\n"
        "ENGAGEMENT: [likes, comments, etc. if visible]"
    )

    # Parse the structured response
    result = {"raw_analysis": analysis, "method": "screenshot"}
    for field in ("AUTHOR", "HEADLINE", "POST TEXT", "HASHTAGS", "ENGAGEMENT"):
        match = re.search(rf"{field}:\s*(.+?)(?:\n[A-Z]|\Z)", analysis, re.DOTALL)
        if match:
            result[field.lower().replace(" ", "_")] = match.group(1).strip()

    return result


# ─── Screen Recording Processing ──────────────────────────────

def process_screen_recording(video_path: str, frame_interval: float = 3.0) -> dict:
    """
    Process a screen recording of scrolling through a LinkedIn post.
    
    This is the most reliable way to capture LinkedIn content:
    1. User records screen while slowly scrolling through post
    2. We extract frames every N seconds
    3. Vision model reads text from each frame
    4. Deduplicate and combine into full post text
    
    Args:
        video_path: Path to screen recording video
        frame_interval: Seconds between frame extractions
    
    Returns:
        dict with: frames, frame_texts, combined_text, summary
    """
    from .video import extract_frames
    from .vision import analyze_image, analyze_carousel

    result = {
        "method": "screen_recording",
        "video_path": video_path,
        "frames": [],
        "frame_texts": [],
        "combined_text": "",
    }

    # 1. Extract frames
    print(f"🎞️  Extracting frames from screen recording (every {frame_interval}s)...")
    frames = extract_frames(video_path, interval=frame_interval, max_frames=30)
    result["frames"] = frames
    print(f"   Extracted {len(frames)} frames")

    if not frames:
        result["error"] = "No frames extracted"
        return result

    # 2. Analyze frames in batches for text extraction
    print("🔍 Reading text from frames with Gemini Vision...")

    # Use carousel analysis for efficiency (batch frames)
    batch_size = 5
    all_texts = []

    for i in range(0, len(frames), batch_size):
        batch = frames[i:i + batch_size]
        try:
            text = analyze_carousel(
                batch,
                "These are sequential screenshots of a LinkedIn post being scrolled. "
                "Extract ALL visible text from each frame. "
                "Focus on the post content, author name, and any comments. "
                "Return the text in reading order, noting which parts are new vs repeated."
            )
            all_texts.append(text)
        except Exception as e:
            all_texts.append(f"[Frame batch {i//batch_size + 1} failed: {e}]")

    result["frame_texts"] = all_texts

    # 3. Deduplicate and combine
    if all_texts:
        combined = "\n\n---\n\n".join(all_texts)

        # Ask Gemini to deduplicate and produce clean output
        try:
            from .vision import analyze_image as _ai  # reuse for text-only prompt
            # Use a text-only Gemini call for dedup
            import urllib.request
            import base64
            from .vision import _get_api_key, GEMINI_API_URL

            api_key = _get_api_key()
            url = GEMINI_API_URL.format(model="gemini-3-flash-preview") + f"?key={api_key}"
            payload = {
                "contents": [{"parts": [{"text":
                    f"Below are text extractions from sequential screenshots of scrolling through "
                    f"a LinkedIn post. There is significant overlap between frames. "
                    f"Deduplicate and combine into the complete post text, preserving the original "
                    f"content exactly. Remove duplicate passages. Output ONLY the clean post text.\n\n"
                    f"{combined}"
                }]}]
            }
            data = json.dumps(payload).encode("utf-8")
            req = urllib.request.Request(url, data=data, headers={"Content-Type": "application/json"})
            with urllib.request.urlopen(req, timeout=60) as resp:
                r = json.loads(resp.read().decode("utf-8"))
            result["combined_text"] = r["candidates"][0]["content"]["parts"][0]["text"]
        except Exception:
            result["combined_text"] = combined

    print(f"   Done — extracted {len(result['combined_text'])} chars of text")
    return result


# ─── Summarize Fallback ────────────────────────────────────────

def summarize_url(url: str) -> dict:
    """
    Fallback: use the `summarize` CLI tool to extract content from a URL.
    
    Useful when oEmbed and OG scraping both fail (login-walled content).
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


# ─── Testing ───────────────────────────────────────────────────

if __name__ == "__main__":
    import sys

    if len(sys.argv) < 2:
        print("Usage:")
        print("  python -m social_media_reader.linkedin <url>           # Try oEmbed")
        print("  python -m social_media_reader.linkedin --paste         # Paste mode")
        print("  python -m social_media_reader.linkedin --screenshot <image>  # Screenshot OCR")
        print("  python -m social_media_reader.linkedin --recording <video>   # Screen recording")
        sys.exit(1)

    if sys.argv[1] == "--paste":
        print("Paste LinkedIn post text (Ctrl+D when done):")
        text = sys.stdin.read()
        result = parse_paste(text)
        print("\n--- Parsed LinkedIn Post ---")
        for k, v in result.items():
            print(f"  {k}: {v}")

    elif sys.argv[1] == "--screenshot" and len(sys.argv) > 2:
        result = analyze_screenshot(sys.argv[2])
        print("\n--- Screenshot Analysis ---")
        for k, v in result.items():
            if k != "raw_analysis":
                print(f"  {k}: {v}")

    elif sys.argv[1] == "--recording" and len(sys.argv) > 2:
        result = process_screen_recording(sys.argv[2])
        print(f"\n--- Screen Recording Result ---")
        print(f"  Frames: {len(result['frames'])}")
        print(f"  Combined text:\n{result['combined_text'][:500]}")

    else:
        url = sys.argv[1]
        print(f"Trying oEmbed for: {url}")
        result = extract_linkedin_metadata(url)
        for k, v in result.items():
            print(f"  {k}: {v}")
