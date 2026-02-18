"""LinkedIn post extractor using oEmbed API and paste mode."""

import json
import subprocess
import re
from urllib.parse import quote


def get_linkedin_oembed(url: str) -> dict:
    """Fetch LinkedIn post metadata via oEmbed endpoint.
    
    Args:
        url: LinkedIn post/article URL
        
    Returns:
        dict with keys from oEmbed response (title, author_name, author_url, html, etc.)
    """
    oembed_url = f"https://www.linkedin.com/oembed?url={quote(url, safe='')}&format=json"
    result = subprocess.run(
        ["curl", "-s", "-L", "-H", "User-Agent: curl/7.0", oembed_url],
        capture_output=True, text=True, timeout=30
    )
    if result.returncode != 0:
        raise RuntimeError(f"Failed to fetch oEmbed: {result.stderr}")
    
    try:
        data = json.loads(result.stdout)
    except json.JSONDecodeError:
        raise RuntimeError(f"Invalid JSON from oEmbed endpoint: {result.stdout[:200]}")
    
    return data


def extract_linkedin_post(url: str) -> dict:
    """Extract structured data from a LinkedIn post URL.
    
    Returns:
        dict with: author, title, url, embed_html, raw_oembed
    """
    oembed = get_linkedin_oembed(url)
    
    return {
        "author": oembed.get("author_name", "unknown"),
        "author_url": oembed.get("author_url", ""),
        "title": oembed.get("title", ""),
        "url": url,
        "embed_html": oembed.get("html", ""),
        "raw_oembed": oembed,
    }


def parse_paste(text: str) -> dict:
    """Parse raw pasted LinkedIn post text into structured data.
    
    Handles the typical copy-paste format from LinkedIn:
    - First line(s): author name and headline
    - Then post body
    - May include hashtags, mentions, engagement counts
    
    Args:
        text: Raw pasted text from LinkedIn
        
    Returns:
        dict with: author, headline, body, hashtags, mentions
    """
    lines = text.strip().split("\n")
    if not lines:
        return {"author": "", "headline": "", "body": "", "hashtags": [], "mentions": []}
    
    # First non-empty line is usually the author
    author = ""
    headline = ""
    body_start = 0
    
    for i, line in enumerate(lines):
        line = line.strip()
        if not line:
            continue
        if not author:
            author = line
            body_start = i + 1
            continue
        # Second non-empty line is often the headline/title
        if not headline:
            headline = line
            body_start = i + 1
            break
    
    # Rest is the body
    body_lines = lines[body_start:]
    body = "\n".join(body_lines).strip()
    
    # Extract hashtags
    hashtags = re.findall(r'#(\w+)', text)
    
    # Extract @mentions
    mentions = re.findall(r'@(\w+)', text)
    
    # Remove engagement metrics lines (likes, comments, reposts)
    body = re.sub(r'\n\d+\s*(likes?|comments?|reposts?|reactions?).*', '', body, flags=re.IGNORECASE)
    
    return {
        "author": author,
        "headline": headline,
        "body": body.strip(),
        "hashtags": hashtags,
        "mentions": mentions,
    }


if __name__ == "__main__":
    import sys
    
    if len(sys.argv) > 1 and sys.argv[1] == "--paste":
        print("Paste LinkedIn post text (Ctrl+D when done):")
        text = sys.stdin.read()
        result = parse_paste(text)
        print("\n--- Parsed LinkedIn Post ---")
        for k, v in result.items():
            print(f"  {k}: {v}")
    else:
        test_url = sys.argv[1] if len(sys.argv) > 1 else "https://www.linkedin.com/posts/gaurav-surtani_ai-engineering-activity-7290000000000000000"
        print(f"Testing oEmbed with: {test_url}")
        try:
            result = extract_linkedin_post(test_url)
            print("\n--- LinkedIn Post ---")
            for k, v in result.items():
                if k == "raw_oembed":
                    print(f"  {k}: [full oembed data]")
                else:
                    print(f"  {k}: {v}")
        except Exception as e:
            print(f"oEmbed failed (expected for many URLs): {e}")
            print("Try --paste mode for raw text input")
