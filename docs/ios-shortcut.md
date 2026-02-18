# iOS Shortcut: Share to Social Media Reader

Build an iOS Shortcut that sends any shared URL to your social-media-reader server for processing.

## Prerequisites

- social-media-reader running on a server with a public endpoint (or via SSH tunnel)
- iOS 15+ with Shortcuts app

## Step-by-Step Setup

### 1. Create the Shortcut

1. Open **Shortcuts** app → tap **+** (new shortcut)
2. Name it: **"Read Post"**

### 2. Accept Share Input

1. Tap **"Add Action"** → search **"Receive"**
2. Select **"Receive input from Share Sheet"**
3. Set input type to **URLs**

### 3. Extract URL

1. Add action: **"Get URLs from Input"**
2. This extracts the shared URL

### 4. Send to Server

**Option A: Local server via SSH**

1. Add action: **"Run Script over SSH"**
2. Configure:
   - Host: your server IP
   - User: your username
   - Script: `cd /path/to/social-media-reader && python -m social_media_reader "SHORTCUT_INPUT" --no-vision`
3. Replace `SHORTCUT_INPUT` with the URL variable from step 3

**Option B: HTTP API endpoint**

If you've set up a web API wrapper:

1. Add action: **"Get Contents of URL"**
2. URL: `https://your-server.com/api/read?url=SHORTCUT_INPUT`
3. Method: GET

### 5. Display Result

1. Add action: **"Show Result"**
2. Pass the output from step 4

### 6. Add to Share Sheet

1. Tap the settings icon (top right)
2. Enable **"Show in Share Sheet"**
3. Set input types: **URLs, Text**

## Usage

1. In any app (Instagram, LinkedIn, Safari), tap **Share**
2. Select **"Read Post"** from your shortcuts
3. See extracted content in a popup

## Tips

- Add a **"Copy to Clipboard"** action after showing results
- Use **"Save to Files"** to archive extracted content
- Chain with **"Add to Notes"** for a reading log
- For vision analysis, remove `--no-vision` (requires Gemini API key on server)
