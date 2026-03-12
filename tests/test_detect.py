"""Tests for platform detection."""
import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from social_media_reader.cli import detect_platform


def test_instagram():
    assert detect_platform("https://www.instagram.com/p/ABC123/") == "instagram"
    assert detect_platform("https://instagr.am/p/ABC123/") == "instagram"
    assert detect_platform("https://www.instagram.com/reel/XYZ/") == "instagram"


def test_linkedin():
    assert detect_platform("https://www.linkedin.com/posts/user_activity-123") == "linkedin"
    assert detect_platform("https://linkedin.com/in/someone/") == "linkedin"


def test_youtube():
    assert detect_platform("https://www.youtube.com/watch?v=abc") == "youtube"
    assert detect_platform("https://youtu.be/abc") == "youtube"


def test_facebook():
    assert detect_platform("https://www.facebook.com/post/123") == "facebook"
    assert detect_platform("https://fb.watch/abc/") == "facebook"


def test_tiktok():
    assert detect_platform("https://www.tiktok.com/@user/video/123") == "tiktok"


def test_twitter():
    assert detect_platform("https://twitter.com/user/status/123") == "twitter"
    assert detect_platform("https://x.com/user/status/123") == "twitter"


def test_unknown():
    assert detect_platform("https://example.com/page") is None


if __name__ == "__main__":
    for name, func in list(globals().items()):
        if name.startswith("test_") and callable(func):
            func()
            print(f"  ✅ {name}")
    print("\nAll tests passed!")
