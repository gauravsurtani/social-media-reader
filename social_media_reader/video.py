"""
Video/Facebook content extractor using yt-dlp.

Supports downloading videos and extracting metadata from platforms
that yt-dlp supports (Facebook, Instagram Reels, YouTube, TikTok, etc.)

## What Works:
- Video metadata extraction (title, description, thumbnail, duration)
- Video download to local file
- Thumbnail extraction for vision analysis
- Works with any yt-dlp supported platform

## What Doesn't Work (yet):
- Audio transcription (would need Whisper, heavy dependency)
- Facebook login-gated content
"""

import json
import os
import sys
import tempfile
from typing import Optional

# Support custom install prefix for yt-dlp
_PYLIB = "/tmp/pylibs"
if _PYLIB not in sys.path:
    sys.path.insert(0, _PYLIB)


def _get_yt_dlp():
    """Import yt-dlp with graceful fallback."""
    try:
        import yt_dlp
        return yt_dlp
    except ImportError:
        raise RuntimeError(
            "yt-dlp not installed. Install with: pip install yt-dlp"
        )


def extract_video_metadata(url: str) -> dict:
    """
    Extract metadata from a video URL without downloading.
    
    Returns dict with: title, description, thumbnail, duration,
    uploader, view_count, platform, formats, etc.
    """
    yt_dlp = _get_yt_dlp()

    ydl_opts = {
        "quiet": True,
        "no_warnings": True,
        "extract_flat": False,
        "skip_download": True,
    }

    try:
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(url, download=False)

        return {
            "platform": info.get("extractor", "unknown"),
            "title": info.get("title"),
            "description": info.get("description", "")[:1000],
            "thumbnail": info.get("thumbnail"),
            "thumbnails": [t.get("url") for t in info.get("thumbnails", []) if t.get("url")],
            "duration": info.get("duration"),
            "duration_string": info.get("duration_string"),
            "uploader": info.get("uploader"),
            "uploader_url": info.get("uploader_url"),
            "view_count": info.get("view_count"),
            "like_count": info.get("like_count"),
            "upload_date": info.get("upload_date"),
            "url": url,
            "webpage_url": info.get("webpage_url"),
            "has_video": bool(info.get("formats")),
        }
    except Exception as e:
        return {
            "url": url,
            "platform": "unknown",
            "error": str(e),
        }


def download_video(url: str, output_dir: Optional[str] = None, max_filesize: str = "50M") -> dict:
    """
    Download a video to a local file.
    
    Args:
        url: Video URL
        output_dir: Directory to save to (default: temp dir)
        max_filesize: Max file size (e.g., "50M", "100M")
    
    Returns dict with: path, title, duration, thumbnail, etc.
    """
    yt_dlp = _get_yt_dlp()

    if output_dir is None:
        output_dir = tempfile.mkdtemp(prefix="smr_video_")

    output_template = os.path.join(output_dir, "%(title)s.%(ext)s")

    ydl_opts = {
        "quiet": True,
        "no_warnings": True,
        "outtmpl": output_template,
        "max_filesize": _parse_filesize(max_filesize),
        "format": "best[filesize<50M]/best",
    }

    try:
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(url, download=True)
            filepath = ydl.prepare_filename(info)

        return {
            "path": filepath,
            "title": info.get("title"),
            "duration": info.get("duration"),
            "thumbnail": info.get("thumbnail"),
            "platform": info.get("extractor", "unknown"),
            "success": True,
        }
    except Exception as e:
        return {"url": url, "error": str(e), "success": False}


def get_video_thumbnails(url: str) -> list:
    """Get thumbnail URLs from a video for vision analysis."""
    metadata = extract_video_metadata(url)
    thumbnails = metadata.get("thumbnails", [])
    if not thumbnails and metadata.get("thumbnail"):
        thumbnails = [metadata["thumbnail"]]
    return thumbnails


def _parse_filesize(size_str: str) -> int:
    """Parse filesize string like '50M' to bytes."""
    size_str = size_str.strip().upper()
    multipliers = {"K": 1024, "M": 1024**2, "G": 1024**3}
    if size_str[-1] in multipliers:
        return int(float(size_str[:-1]) * multipliers[size_str[-1]])
    return int(size_str)


# --- Testing ---
if __name__ == "__main__":
    # Test with a public video
    test_urls = [
        # Public Instagram reel
        "https://www.instagram.com/reel/DGkJhJdMVFr/",
    ]

    for url in test_urls:
        print(f"\n{'='*60}")
        print(f"URL: {url}")
        print(f"{'='*60}")
        metadata = extract_video_metadata(url)
        for k, v in metadata.items():
            if v is not None and k != "thumbnails":
                val = str(v)[:100]
                print(f"  {k}: {val}")
        thumbs = metadata.get("thumbnails", [])
        print(f"  thumbnails: {len(thumbs)} found")
