"""Tests for Instagram extractor (requires network)."""
import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from social_media_reader.instagram import extract_instagram_images, get_instagram_metadata

TEST_URL = "https://www.instagram.com/p/DUaUSgSEvQT/"


def test_extract_images():
    images = extract_instagram_images(TEST_URL)
    assert len(images) > 0, "Should find at least one image"
    assert all(url.startswith("https://") for url in images), "All URLs should be HTTPS"
    print(f"  Found {len(images)} images")


def test_metadata():
    meta = get_instagram_metadata(TEST_URL)
    assert meta.get("username") == "kalypsodesigns", f"Expected kalypsodesigns, got {meta.get('username')}"
    print(f"  Username: {meta['username']}")


if __name__ == "__main__":
    for name, func in sorted(globals().items()):
        if name.startswith("test_") and callable(func):
            func()
            print(f"  ✅ {name}")
    print("\nAll Instagram tests passed!")
