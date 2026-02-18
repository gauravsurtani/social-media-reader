"""
CLI interface for social-media-reader.

Usage:
    python -m social_media_reader <url> [--no-vision] [--images-only]
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
        "facebook": r"(facebook\.com|fb\.com|fb\.watch)/",
        "twitter": r"(twitter\.com|x\.com)/",
        "youtube": r"(youtube\.com|youtu\.be)/",
        "tiktok": r"tiktok\.com/",
    }
    for platform, pattern in patterns.items():
        if re.search(pattern, url, re.IGNORECASE):
            return platform
    return None


def process_instagram(url: str, analyze: bool = True) -> dict:
    """Process an Instagram post URL."""
    from .instagram import extract_instagram_images, get_instagram_metadata

    print("📸 Fetching Instagram post...")
    metadata = get_instagram_metadata(url)
    images = extract_instagram_images(url)

    print(f"   Username: {metadata.get('username', 'unknown')}")
    print(f"   Post type: {metadata.get('post_type', 'unknown')}")
    print(f"   Images found: {len(images)}")

    result = {"platform": "instagram", "metadata": metadata, "images": images}

    if analyze and images:
        print("\n🔍 Analyzing images with Gemini Vision...")
        from .vision import analyze_carousel, analyze_image

        if len(images) == 1:
            analysis = analyze_image(images[0], "Describe this social media post image in detail.")
        else:
            analysis = analyze_carousel(
                images[:5],
                "These images are from an Instagram carousel post. "
                "Describe what each image shows and summarize the overall content/theme."
            )
        result["analysis"] = analysis
        print(f"\n📝 Analysis:\n{analysis}")

    return result


def process_linkedin(url: str, analyze: bool = True) -> dict:
    """Process a LinkedIn post URL."""
    from .linkedin import extract_linkedin_metadata

    print("💼 Fetching LinkedIn post...")
    metadata = extract_linkedin_metadata(url)

    if metadata.get("method") == "failed":
        print(f"   ⚠️  {metadata.get('error', 'Extraction failed')}")
    else:
        print(f"   Method: {metadata.get('method')}")
        if metadata.get("title"):
            print(f"   Title: {metadata['title']}")
        if metadata.get("description"):
            print(f"   Description: {metadata['description'][:200]}")

    result = {"platform": "linkedin", "metadata": metadata}

    images = metadata.get("images", [])
    if analyze and images:
        from .vision import analyze_image
        print(f"\n🔍 Analyzing {len(images)} image(s)...")
        analysis = analyze_image(images[0], "Describe this LinkedIn post image.")
        result["analysis"] = analysis
        print(f"\n📝 Analysis:\n{analysis}")

    return result


def process_video(url: str, analyze: bool = True) -> dict:
    """Process a video URL (YouTube, Facebook, TikTok, etc.) via yt-dlp."""
    from .video import extract_video_metadata, get_video_thumbnails

    print("🎬 Fetching video metadata...")
    metadata = extract_video_metadata(url)

    if metadata.get("error"):
        print(f"   ⚠️  {metadata['error'][:200]}")
    else:
        print(f"   Platform: {metadata.get('platform', 'unknown')}")
        print(f"   Title: {metadata.get('title', 'unknown')}")
        print(f"   Uploader: {metadata.get('uploader', 'unknown')}")
        print(f"   Duration: {metadata.get('duration_string', 'unknown')}")
        if metadata.get("view_count"):
            print(f"   Views: {metadata['view_count']:,}")

    result = {"platform": metadata.get("platform", "video"), "metadata": metadata}

    thumbnails = get_video_thumbnails(url)
    if analyze and thumbnails:
        print("\n🔍 Analyzing video thumbnail with Gemini Vision...")
        from .vision import analyze_image
        analysis = analyze_image(
            thumbnails[-1],
            "This is a video thumbnail from social media. Describe what you see."
        )
        result["analysis"] = analysis
        print(f"\n📝 Thumbnail Analysis:\n{analysis}")

    return result


def process_url(url: str, analyze: bool = True) -> dict:
    """Process any social media URL."""
    platform = detect_platform(url)

    if platform is None:
        print(f"❓ Could not detect platform for: {url}")
        return {"error": "Unknown platform", "url": url}

    print(f"🌐 Detected platform: {platform}\n")

    handlers = {
        "instagram": process_instagram,
        "linkedin": process_linkedin,
        "youtube": process_video,
        "facebook": process_video,
        "tiktok": process_video,
    }

    handler = handlers.get(platform)
    if handler:
        return handler(url, analyze=analyze)
    else:
        print(f"⚠️  Platform '{platform}' not yet supported.")
        print(f"   Supported: {', '.join(handlers.keys())}")
        return {"error": f"Unsupported platform: {platform}", "url": url}


def main():
    parser = argparse.ArgumentParser(
        description="Extract and analyze social media content",
        prog="social-media-reader",
    )
    parser.add_argument("url", help="Social media post URL")
    parser.add_argument("--no-vision", action="store_true",
                        help="Skip vision analysis (just extract images/metadata)")
    parser.add_argument("--images-only", action="store_true",
                        help="Only print image URLs")

    args = parser.parse_args()

    if args.images_only:
        platform = detect_platform(args.url)
        if platform == "instagram":
            from .instagram import extract_instagram_images
            for img in extract_instagram_images(args.url):
                print(img)
        elif platform == "linkedin":
            from .linkedin import get_linkedin_images
            for img in get_linkedin_images(args.url):
                print(img)
        elif platform in ("youtube", "facebook", "tiktok"):
            from .video import get_video_thumbnails
            for img in get_video_thumbnails(args.url):
                print(img)
        return

    result = process_url(args.url, analyze=not args.no_vision)
    if result.get("error"):
        sys.exit(1)


if __name__ == "__main__":
    main()
