# Social Media Reader

Extract and understand social media content using embed scraping + vision models.

## What It Does

Given a social media URL (Instagram, LinkedIn, Facebook), this tool:
1. **Extracts images/media** from the post using embed page scraping
2. **Analyzes content** with Gemini vision models
3. **Returns a summary** of what the post contains

## Supported Platforms

| Platform  | Status | Method |
|-----------|--------|--------|
| Instagram | ✅ Working | Embed page HTML scraping |
| LinkedIn  | 🔄 Partial | oEmbed API |
| Facebook  | 🔄 Experimental | yt-dlp / embed |

## Installation

```bash
pip install -r requirements.txt
```

## Usage

```bash
python -m social_media_reader https://www.instagram.com/p/DUaUSgSEvQT/
```

## Architecture

```
social_media_reader/
├── __init__.py       # Package init
├── instagram.py      # Instagram embed scraper
├── linkedin.py       # LinkedIn oEmbed/scraper
├── vision.py         # Gemini vision analysis
├── cli.py            # CLI interface
└── __main__.py       # Entry point
```

## Requirements

- Python 3.9+
- Gemini API key (set `GEMINI_API_KEY` env var or pass via config)

## License

MIT
