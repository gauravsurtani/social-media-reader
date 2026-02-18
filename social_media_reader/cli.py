"""CLI interface for social-media-reader.

Usage:
    python -m social_media_reader <url> [--no-vision] [--paste]
"""

import argparse
import sys
import re
from typing import Optional


def detect_platform(url: str) -> Optional[str]:
    """Auto-detect social media platform from URL."""
    patterns = {
        "instagram": r"(instagram\.com|instagr\.am)/",
        "linkedin": r"linkedin\.com/",
        "youtube": r"(youtube\.com|youtu\.be)/",
        "tiktok": r"tiktok\.com/",
        "twitter": r"(twitter\.com|x\.com)/",
        "facebook": r"(facebook\.com|fb\.com|fb\.watch)/",
    }
    for platform, pattern in patterns.items():
        if re.search(pattern, url, re.IGNORECASE):
            return platform
    return None


def process_instagram(url: str, analyze: bool = True) -> dict:
    """Process an Instagram post URL."""
    from .instagram import extract_instagram_images, get_instagram_metadata

    print("Fetching Instagram post...")
    metadata = get_instagram_metadata(url)
    images = metadata.get("image_urls", [])

    print(f"  Username: {metadata.get('username', 'unknown')}")
    print(f"  Carousel: {metadata.get('is_carousel', False)}")
    print(f"  Images: {len(images)}")

    result = {"platform": "instagram", "metadata": metadata, "images": images}

    if analyze and images:
        print("\nAnalyzing images with Gemini Vision...")
        try:
            # Download images first
            import subprocess
            import tempfile
            import os
            tmp_dir = tempfile.mkdtemp(prefix="smr-ig-")
            local_images = []
            for i, img_url in enumerate(images[:5]):
                local_path = os.path.join(tmp_dir, f"img_{i}.jpg")
                subprocess.run(["curl", "-sL", "-o", local_path, img_url],
                             capture_output=True, timeout=30)
                if os.path.getsize(local_path) > 0:
                    local_images.append(local_path)

            if local_images:
                from .vision import analyze_carousel, analyze_image
                if len(local_images) == 1:
                    analysis = analyze_image(local_images[0], 
                        "Describe this Instagram post image in detail.")
                else:
                    analysis = analyze_carousel(local_images,
                        "These are from an Instagram carousel. Describe each and summarize the theme.")
                result["analysis"] = analysis
                print(f"\nAnalysis:\n{analysis}")
        except Exception as e:
            print(f"  Vision analysis failed: {e}")

    return result


def process_linkedin(url: str, analyze: bool = True) -> dict:
    """Process a LinkedIn post URL."""
    from .linkedin import get_linkedin_oembed

    print("Fetching LinkedIn post...")
    try:
        data = get_linkedin_oembed(url)
        print(f"  Author: {data.get('author_name', 'unknown')}")
        print(f"  Title: {data.get('title', 'N/A')}")
        return {"platform": "linkedin", "oembed": data}
    except Exception as e:
        print(f"  oEmbed failed: {e}")
        print("  Tip: Use --paste mode for LinkedIn content")
        return {"platform": "linkedin", "error": str(e)}


def process_video_url(url: str, analyze: bool = True) -> dict:
    """Process a video URL (YouTube, TikTok, etc.)."""
    from .video import process_video
    return process_video(url, analyze_frames=analyze, transcribe=True)


def process_paste() -> dict:
    """Process pasted text from stdin."""
    from .linkedin import parse_paste
    print("Paste text (Ctrl+D when done):")
    text = sys.stdin.read()
    result = parse_paste(text)
    print("\n--- Parsed Content ---")
    for k, v in result.items():
        print(f"  {k}: {v}")
    return result


def process_url(url: str, analyze: bool = True) -> dict:
    """Process any social media URL."""
    platform = detect_platform(url)

    if platform is None:
        print(f"Unknown platform for: {url}")
        return {"error": "Unknown platform", "url": url}

    print(f"Detected platform: {platform}\n")

    if platform == "instagram":
        return process_instagram(url, analyze)
    elif platform == "linkedin":
        return process_linkedin(url, analyze)
    elif platform in ("youtube", "tiktok"):
        return process_video_url(url, analyze)
    else:
        print(f"Platform '{platform}' not yet fully supported.")
        return {"error": f"Unsupported: {platform}", "url": url}


def main():
    parser = argparse.ArgumentParser(
        description="Extract and analyze social media content",
        prog="social-media-reader",
    )
    parser.add_argument("url", nargs="?", help="Social media post URL")
    parser.add_argument("--no-vision", action="store_true",
                        help="Skip vision analysis")
    parser.add_argument("--paste", action="store_true",
                        help="Read pasted text from stdin instead of URL")
    parser.add_argument("--images-only", action="store_true",
                        help="Only print image URLs")

    args = parser.parse_args()

    if args.paste:
        process_paste()
        return

    if not args.url:
        parser.error("URL required (or use --paste)")

    if args.images_only:
        platform = detect_platform(args.url)
        if platform == "instagram":
            from .instagram import extract_instagram_images
            for img in extract_instagram_images(args.url):
                print(img)
        return

    result = process_url(args.url, analyze=not args.no_vision)
    if result.get("error"):
        sys.exit(1)


if __name__ == "__main__":
    main()
