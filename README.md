# Social Media Reader

Extract and understand social media content using embed scraping + vision models.

Give it a social media URL → get images, metadata, and AI-powered content analysis.

## Supported Platforms

| Platform | Images | Metadata | Vision Analysis | Notes |
|----------|--------|----------|-----------------|-------|
| **Instagram** | ✅ | ✅ | ✅ | Embed scraping, no auth needed |
| **YouTube** | ✅ thumbnails | ✅ | ✅ | Via yt-dlp |
| **Facebook** | ✅ thumbnails | ✅ | ✅ | Via yt-dlp (public posts only) |
| **TikTok** | ✅ thumbnails | ✅ | ✅ | Via yt-dlp |
| **LinkedIn** | ⚠️ limited | ⚠️ limited | ⚠️ | Blocked without auth, OG tags only |

## Quick Start

```bash
# Clone
git clone https://github.com/gauravsurtani/social-media-reader.git
cd social-media-reader

# Install dependencies
pip install yt-dlp  # optional, for video platforms

# Set Gemini API key (for vision analysis)
export GEMINI_API_KEY="your-key-here"

# Run
python -m social_media_reader https://www.instagram.com/p/DUaUSgSEvQT/
```

## Usage

```bash
# Full analysis (extract + vision)
python -m social_media_reader <url>

# Skip vision analysis (just extract images/metadata)
python -m social_media_reader <url> --no-vision

# Only print image URLs
python -m social_media_reader <url> --images-only
```

## Examples

### Instagram Carousel
```
$ python -m social_media_reader https://www.instagram.com/p/DUaUSgSEvQT/

🌐 Detected platform: instagram

📸 Fetching Instagram post...
   Username: kalypsodesigns
   Images found: 13

🔍 Analyzing images with Gemini Vision...

📝 Analysis:
Image 1: "agent skills." in bold font against black background...
Image 2: "It took 3 years to create this post."...
```

### YouTube Video
```
$ python -m social_media_reader https://www.youtube.com/watch?v=dQw4w9WgXcQ --no-vision

🌐 Detected platform: youtube

🎬 Fetching video metadata...
   Title: Rick Astley - Never Gonna Give You Up (4K Remaster)
   Uploader: Rick Astley
   Duration: 3:33
   Views: 1,743,330,732
```

## Architecture

```
social_media_reader/
├── __init__.py
├── __main__.py          # Entry point for python -m
├── cli.py               # CLI interface + platform routing
├── instagram.py         # Instagram embed scraper
├── linkedin.py          # LinkedIn extractor (limited)
├── video.py             # yt-dlp based video/metadata extractor
└── vision.py            # Gemini Vision API integration
```

### How It Works

1. **Platform Detection** — URL pattern matching to identify the source
2. **Content Extraction** — Platform-specific scraping:
   - Instagram: Fetches embed page with simple User-Agent, parses `display_resources` JSON for highest-resolution images
   - LinkedIn: Attempts OG tags and oEmbed (mostly blocked)
   - Video platforms: yt-dlp for metadata and thumbnails
3. **Vision Analysis** — Sends extracted images to Gemini 2.0 Flash for AI description

### Key Discovery: Instagram Embed Scraping

Instagram serves **server-side rendered HTML** to simple User-Agents (like `curl/7.0`) but a **React SPA** to browser User-Agents. The SSR version contains embedded JSON with `display_resources` arrays that include multiple resolution variants of each image. We parse these to get the highest quality images without any authentication.

## API Key Setup

The vision analyzer needs a Google Gemini API key. Options:

1. **Environment variable**: `export GEMINI_API_KEY="your-key"`
2. **OpenClaw config**: Key at `models.providers.gemini.apiKey` in `openclaw.json`

Get a key at: https://aistudio.google.com/apikey

## Dependencies

- **Python 3.10+** (stdlib only for core functionality)
- **yt-dlp** (optional) — for YouTube, Facebook, TikTok support
- **No other dependencies** — Instagram and vision modules use only stdlib (`urllib`, `json`, `base64`)

## Running Tests

```bash
python tests/test_detect.py      # Platform detection (offline)
python tests/test_instagram.py   # Instagram scraping (needs network)
```

## Known Limitations

- **LinkedIn** is heavily restricted without authentication. The module documents all attempted approaches and their failure modes.
- **Instagram Reels/Videos** via yt-dlp require auth cookies. Image posts work without auth.
- **Rate limiting** — Instagram may rate-limit embed requests. No retry logic yet.
- **Ephemeral URLs** — Instagram CDN URLs expire after some time.

## License

MIT
