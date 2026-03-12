# Usage Examples

## Instagram Post

```bash
# Extract images and metadata
python -m social_media_reader "https://www.instagram.com/p/DUaUSgSEvQT/" --no-vision

# Output:
# Detected platform: instagram
# Fetching Instagram post...
#   Username: kalypsodesigns
#   Carousel: True
#   Images: 13

# Just get image URLs
python -m social_media_reader "https://www.instagram.com/p/DUaUSgSEvQT/" --images-only

# Full analysis with Gemini Vision
python -m social_media_reader "https://www.instagram.com/p/DUaUSgSEvQT/"
```

## LinkedIn Post

```bash
# Via URL (uses oEmbed — limited by LinkedIn's auth requirements)
python -m social_media_reader "https://www.linkedin.com/posts/gaurav-surtani_ai-activity-123"

# Via paste mode (more reliable — copy text from browser)
python -m social_media_reader --paste
# Then paste the post text and press Ctrl+D
```

## Video (YouTube, TikTok)

```bash
# Full pipeline: download → frames → transcription → analysis
python -m social_media_reader "https://www.youtube.com/watch?v=VIDEO_ID"

# Skip vision analysis
python -m social_media_reader "https://www.youtube.com/watch?v=VIDEO_ID" --no-vision
```

**Note:** YouTube may require cookies in server environments due to bot detection.

## Python API

```python
from social_media_reader.instagram import extract_instagram_images, get_instagram_metadata
from social_media_reader.linkedin import parse_paste
from social_media_reader.vision import analyze_image, analyze_carousel
from social_media_reader.video import process_video

# Instagram
images = extract_instagram_images("https://www.instagram.com/p/ABC123/")
metadata = get_instagram_metadata("https://www.instagram.com/p/ABC123/")

# LinkedIn paste
result = parse_paste("Author Name\nHeadline\nPost body #hashtag")

# Vision
analysis = analyze_image("/path/to/image.jpg", "What's in this image?")
carousel = analyze_carousel(["/path/1.jpg", "/path/2.jpg"])

# Video
result = process_video("https://youtube.com/watch?v=VIDEO_ID")
print(result["transcription"])
print(result["frame_analysis"])
```

## Bookmarklet (LinkedIn)

1. Add the bookmarklet from `docs/bookmarklet.js` to your browser
2. Navigate to a LinkedIn post
3. Click the bookmarklet → text copied to clipboard
4. Use with `--paste` mode

## iOS Shortcut

See `docs/ios-shortcut.md` for setup instructions.
