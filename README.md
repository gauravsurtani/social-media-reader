# Social Media Reader

Extract, analyze, and understand social media content from the command line.

## Architecture

```
                    ┌──────────────────────┐
                    │   CLI / __main__.py   │
                    │   Auto-detect URL     │
                    └──────────┬───────────┘
                               │
              ┌────────────────┼────────────────┐
              │                │                │
    ┌─────────▼──────┐ ┌──────▼───────┐ ┌──────▼───────┐
    │  instagram.py  │ │ linkedin.py  │ │   video.py   │
    │  Embed scraper │ │ oEmbed/paste │ │ yt-dlp+ffmpeg│
    └─────────┬──────┘ └──────────────┘ └──────┬───────┘
              │                                 │
              └──────────┐    ┌─────────────────┘
                         │    │
                   ┌─────▼────▼─────┐
                   │   vision.py    │
                   │  Gemini 2.0    │
                   │  Flash API     │
                   └────────────────┘
```

## Supported Platforms

| Platform   | Method                        | Status |
|------------|-------------------------------|--------|
| Instagram  | Embed page scraping           | ✅     |
| LinkedIn   | oEmbed + paste mode           | ✅     |
| YouTube    | yt-dlp + frame extraction     | ⚠️ Needs cookies |
| TikTok     | yt-dlp                        | ⚠️ Needs cookies |
| Twitter/X  | Planned                       | 🔜     |
| Facebook   | Planned                       | 🔜     |

## Quick Start

```bash
# Install dependencies
pip install -r requirements.txt

# Extract Instagram post
python -m social_media_reader "https://www.instagram.com/p/ABC123/"

# LinkedIn via paste mode
python -m social_media_reader --paste

# Images only
python -m social_media_reader "https://www.instagram.com/p/ABC123/" --images-only

# Skip AI vision analysis
python -m social_media_reader "https://www.instagram.com/p/ABC123/" --no-vision
```

## Modules

### `instagram.py`
- Scrapes Instagram embed pages (no auth required)
- Extracts highest-resolution images from carousels
- Returns metadata: username, image count, carousel detection

### `linkedin.py`
- oEmbed API for public articles (limited by LinkedIn auth)
- **Paste mode**: parse raw copied text into structured data (author, headline, body, hashtags)

### `vision.py`
- Google Gemini 2.0 Flash for image understanding
- `analyze_image(path, prompt)` → text description
- `analyze_carousel(paths, prompt)` → combined analysis
- Auto-retry with exponential backoff on rate limits

### `video.py`
- yt-dlp video download (YouTube, TikTok, Instagram, etc.)
- ffmpeg frame extraction (1 frame per 5 seconds)
- Gemini audio transcription
- Combined visual + audio summary pipeline

### `cli.py`
- Unified CLI: `python -m social_media_reader <url>`
- Auto-detects platform from URL
- `--paste` mode for raw text input
- `--no-vision` and `--images-only` flags

## Configuration

### Gemini API Key

Set via environment variable or config file:

```bash
export GEMINI_API_KEY="your-key-here"
```

Or place in `/data/.openclaw/openclaw.json` under `models.providers.gemini.apiKey`.

### YouTube Cookies

YouTube requires authentication in server environments:

```bash
# Export cookies from browser
yt-dlp --cookies-from-browser chrome "URL"
```

## Integration

- **iOS Shortcut**: See `docs/ios-shortcut.md`
- **Browser Bookmarklet**: See `docs/bookmarklet.js` (LinkedIn text extraction)
- **Python API**: See `docs/usage-examples.md`

## Testing

```bash
python tests/test_detect.py     # Platform detection (offline)
python tests/test_instagram.py  # Instagram extraction (requires network)
```

## Requirements

### Required
- Python 3.10+
- curl (for HTTP requests)
- ffmpeg (for video/audio processing)
- Google Gemini API key (for vision/audio analysis)

### Optional
- **yt-dlp** — video downloads (YouTube, TikTok, etc.)
- **faster-whisper** — local audio transcription, no API cost (`pip install faster-whisper`)
- **summarize** — fallback content extraction for blocked URLs (`brew install steipete/tap/summarize`)

## OpenClaw Skill Integrations

This project integrates several [OpenClaw](https://openclaw.com) skills:

| Skill | Status | What it does |
|-------|--------|-------------|
| **faster-whisper** | ✅ Integrated | Local speech-to-text in `video.py`. Tries faster-whisper first (free, offline), falls back to Gemini API. Uses `tiny` model + int8 on CPU. |
| **summarize** | ✅ Integrated | Fallback URL text extraction in `instagram.py`, `linkedin.py`, and `--summarize` CLI flag. For when embed scraping is blocked. |
| **video-frames** | ⏭️ Skipped | Thin ffmpeg wrapper. `video.py` already has a more robust `extract_frames()` with interval calculation, max frames, and duration-aware spacing. |
| **gemini CLI** | ⏭️ Skipped | CLI wrapper around the same Gemini API that `vision.py` already calls directly. Would add indirection with no benefit. |

## License

MIT

## Roadmap

### Phase 1 (Current) ✅
- Instagram embed scraping + vision analysis
- LinkedIn oEmbed + paste mode
- Video processing (yt-dlp + ffmpeg + transcription)
- CLI tool

### Phase 2 (Planned)
- **Android Share Intent app** — "Share to Data" from any app on Pixel, sends content to Telegram bot (Priority — Captain uses Pixel 9 Pro)
- **iOS Shortcut** — same flow for iOS devices
- **Telegram bot integration** — auto-process any URL shared in chat
- **Content tagging + categorization** (Seven's habit layer)
- **Retention quizzes** on consumed content

### Phase 3 (Future)
- Browser extension (Chrome/Firefox) — one-click capture from desktop
- Webhook receiver — accept content pushes from any source
- Multi-model consensus — run multiple vision models for richer analysis
