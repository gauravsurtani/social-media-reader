# iOS Shortcut: "Share to Data" — Capture & Send to Telegram

An iOS Shortcut that captures content (text, screenshots, URLs) from **any** app and sends it to a Telegram bot for processing. Works with LinkedIn, Instagram, Safari, or any app with a Share Sheet.

## Why This Approach?

LinkedIn and many apps block server-side scraping. But you can see the content on your phone. This shortcut captures what's on your screen and sends it to your Telegram bot (Data) for AI-powered analysis.

## Prerequisites

- iOS 16+ with Shortcuts app
- A Telegram bot token (e.g., Data bot: `@commander_data_clawdbot`)
- Your Telegram chat ID (for DM delivery)

## Shortcut Actions (Step by Step)

### Create New Shortcut
1. Open **Shortcuts** → tap **+**
2. Name: **"Share to Data"**
3. Tap ⓘ → enable **Show in Share Sheet**
4. Input types: **URLs, Text, Images, Media**

### Action 1: Receive Input
```
Receive [Any] input from [Share Sheet]
If there's no input: [Continue]
```

### Action 2: Set Variable — Shared Content
```
Set variable [SharedContent] to [Shortcut Input]
```

### Action 3: Take Screenshot (Optional)
For LinkedIn posts where text isn't shareable:
```
If [SharedContent] [does not have any value]
  Take Screenshot
  Set variable [Screenshot] to [Screenshot]
End If
```

### Action 4: Get Text from Input
```
Get [Text] from [SharedContent]
Set variable [PostText] to [Text]
```

### Action 5: Get URLs from Input
```
Get [URLs] from [SharedContent]
Set variable [PostURL] to [URLs]
```

### Action 6: Build Message
```
Text:
---
📱 Shared from iOS

URL: [PostURL]

Content:
[PostText]
---

Set variable [Message] to [Text]
```

### Action 7: Send Text to Telegram Bot
```
Get Contents of URL:
  URL: https://api.telegram.org/bot<YOUR_BOT_TOKEN>/sendMessage
  Method: POST
  Headers: Content-Type = application/json
  Request Body (JSON):
    {
      "chat_id": "<YOUR_CHAT_ID>",
      "text": [Message],
      "parse_mode": "Markdown"
    }
```

### Action 8: Send Screenshot to Telegram (if taken)
```
If [Screenshot] [has any value]
  Get Contents of URL:
    URL: https://api.telegram.org/bot<YOUR_BOT_TOKEN>/sendPhoto
    Method: POST
    Request Body (Form):
      chat_id: <YOUR_CHAT_ID>
      photo: [Screenshot]
      caption: "Screenshot from iOS Share"
End If
```

### Action 9: Send Images/Media (if shared)
```
Get [Images] from [SharedContent]
If [Images] [has any value]
  Repeat with each [Image] in [Images]
    Get Contents of URL:
      URL: https://api.telegram.org/bot<YOUR_BOT_TOKEN>/sendPhoto
      Method: POST
      Request Body (Form):
        chat_id: <YOUR_CHAT_ID>
        photo: [Repeat Item]
        caption: "Image from shared post"
  End Repeat
End If
```

### Action 10: Confirmation
```
Show Notification: "Sent to Data ✅"
```

## Configuration

Replace these placeholders:
- `<YOUR_BOT_TOKEN>` — Your Telegram bot HTTP API token
- `<YOUR_CHAT_ID>` — Your personal Telegram user ID (get it by messaging `@userinfobot`)

## Usage Workflows

### LinkedIn Post (text visible)
1. Open LinkedIn post → tap **Share** → **"Share to Data"**
2. Shortcut captures shared text + URL → sends to Telegram

### LinkedIn Post (text not in share)
1. Open LinkedIn post → take a manual screenshot
2. Open Screenshots → **Share** → **"Share to Data"**
3. Screenshot sent to Telegram → Data uses Gemini Vision to read it

### Instagram Post
1. Open post → tap **Share** → **"Share to Data"**
2. URL captured → Data runs embed scraper server-side

### Any Webpage (Safari)
1. Tap **Share** → **"Share to Data"**
2. URL + page title sent to Telegram

## Advanced: Screen Recording for LinkedIn Carousels

For multi-slide LinkedIn carousels:

1. Start iOS screen recording
2. Slowly swipe through all carousel slides
3. Stop recording → **Share** video → **"Share to Data"**
4. Data receives video → extracts frames every 5s → analyzes each with Vision

This uses the video processing pipeline in `social_media_reader/video.py`.

## Telegram Bot Processing

On the server side, Data (or your bot) receives the message and can:

```python
# When bot receives a URL
from social_media_reader import cli
result = cli.process_url(url, analyze=True)

# When bot receives a photo
from social_media_reader.vision import analyze_image
analysis = analyze_image(photo_path, "What does this social media post say?")

# When bot receives a video (screen recording)
from social_media_reader.video import process_video_file
result = process_video_file(video_path)
```
