"""
Video processing pipeline.

Supports:
- URL download via yt-dlp
- Local video file processing
- ffmpeg frame extraction (1 frame every N seconds)
- Audio extraction + transcription via Gemini
- Vision analysis on extracted key frames
- Combined summary output

Dependencies:
- ffmpeg (required for frame/audio extraction)
- yt-dlp (optional, for URL downloads)
"""

import json
import os
import sys
import subprocess
import tempfile
import glob
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
        raise RuntimeError("yt-dlp not installed. Install with: pip install yt-dlp")


def _check_ffmpeg():
    """Verify ffmpeg is available."""
    try:
        subprocess.run(["ffmpeg", "-version"], capture_output=True, timeout=5)
        return True
    except (FileNotFoundError, subprocess.TimeoutExpired):
        return False


# ─── Metadata & Download ───────────────────────────────────────

def extract_video_metadata(url: str) -> dict:
    """Extract metadata from a video URL without downloading."""
    from .utils import validate_url
    url = validate_url(url)
    yt_dlp = _get_yt_dlp()
    ydl_opts = {"quiet": True, "no_warnings": True, "skip_download": True}

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
        return {"url": url, "platform": "unknown", "error": str(e)}


def download_video(url: str, output_dir: Optional[str] = None) -> dict:
    """Download a video from URL via yt-dlp."""
    from .utils import validate_url
    url = validate_url(url)
    yt_dlp = _get_yt_dlp()
    if output_dir is None:
        output_dir = tempfile.mkdtemp(prefix="smr_video_")

    outtmpl = os.path.join(output_dir, "%(title).50s.%(ext)s")
    ydl_opts = {
        "quiet": True, "no_warnings": True,
        "outtmpl": outtmpl,
        "format": "best[filesize<100M]/best",
    }

    try:
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(url, download=True)
            filepath = ydl.prepare_filename(info)
        return {"path": filepath, "title": info.get("title"),
                "duration": info.get("duration"), "success": True}
    except Exception as e:
        return {"url": url, "error": str(e), "success": False}


def get_video_thumbnails(url: str) -> list:
    """Get thumbnail URLs from a video for vision analysis."""
    metadata = extract_video_metadata(url)
    thumbs = metadata.get("thumbnails", [])
    if not thumbs and metadata.get("thumbnail"):
        thumbs = [metadata["thumbnail"]]
    return thumbs


# ─── Frame Extraction ──────────────────────────────────────────

def extract_frames(video_path: str, output_dir: Optional[str] = None,
                   interval: float = 5.0, max_frames: int = 20) -> list:
    """
    Extract frames from a video file using ffmpeg.
    
    Args:
        video_path: Path to video file
        output_dir: Directory to save frames (default: temp dir)
        interval: Seconds between frames (default: 5.0)
        max_frames: Maximum number of frames to extract
    
    Returns:
        List of paths to extracted frame images (JPEG)
    """
    if not _check_ffmpeg():
        raise RuntimeError("ffmpeg not found. Install ffmpeg for frame extraction.")

    if output_dir is None:
        output_dir = tempfile.mkdtemp(prefix="smr_frames_")

    output_pattern = os.path.join(output_dir, "frame_%04d.jpg")

    # Get duration first
    duration = _get_duration(video_path)
    if duration and duration / interval > max_frames:
        interval = duration / max_frames

    cmd = [
        "ffmpeg", "-i", video_path,
        "-vf", f"fps=1/{interval}",
        "-frames:v", str(max_frames),
        "-q:v", "2",  # High quality JPEG
        output_pattern,
        "-y",  # Overwrite
    ]

    result = subprocess.run(cmd, capture_output=True, text=True, timeout=120)
    if result.returncode != 0:
        raise RuntimeError(f"ffmpeg frame extraction failed: {result.stderr[:500]}")

    frames = sorted(glob.glob(os.path.join(output_dir, "frame_*.jpg")))
    return frames


def _get_duration(video_path: str) -> Optional[float]:
    """Get video duration in seconds using ffprobe."""
    try:
        result = subprocess.run(
            ["ffprobe", "-v", "quiet", "-show_entries", "format=duration",
             "-of", "default=noprint_wrappers=1:nokey=1", video_path],
            capture_output=True, text=True, timeout=10
        )
        return float(result.stdout.strip())
    except (ValueError, subprocess.TimeoutExpired, FileNotFoundError):
        return None


# ─── Audio Extraction & Transcription ──────────────────────────

def extract_audio(video_path: str, output_dir: Optional[str] = None) -> str:
    """
    Extract audio track from video as WAV file.
    
    Returns path to extracted audio file.
    """
    if not _check_ffmpeg():
        raise RuntimeError("ffmpeg not found.")

    if output_dir is None:
        output_dir = tempfile.mkdtemp(prefix="smr_audio_")

    audio_path = os.path.join(output_dir, "audio.wav")

    cmd = [
        "ffmpeg", "-i", video_path,
        "-vn",  # No video
        "-acodec", "pcm_s16le",
        "-ar", "16000",  # 16kHz for speech
        "-ac", "1",  # Mono
        audio_path,
        "-y",
    ]

    result = subprocess.run(cmd, capture_output=True, text=True, timeout=120)
    if result.returncode != 0:
        raise RuntimeError(f"Audio extraction failed: {result.stderr[:500]}")

    return audio_path


def _transcribe_with_faster_whisper(audio_path: str, model_name: str = "tiny",
                                     language: Optional[str] = None) -> Optional[str]:
    """
    Transcribe audio using faster-whisper (local, no API cost).
    
    Returns transcription text, or None if faster-whisper is unavailable.
    Uses CPU with int8 quantization by default (no GPU in this environment).
    """
    try:
        # faster-whisper may be installed in /tmp/pylibs2 or system-wide
        for lib_path in ["/tmp/pylibs2", "/tmp/pylibs"]:
            if lib_path not in sys.path:
                sys.path.insert(0, lib_path)

        from faster_whisper import WhisperModel
    except ImportError:
        return None

    try:
        model = WhisperModel(model_name, device="cpu", compute_type="int8")
        kwargs = {"beam_size": 5, "vad_filter": True}
        if language:
            kwargs["language"] = language
        segments, info = model.transcribe(audio_path, **kwargs)
        text = " ".join(s.text for s in segments).strip()
        if not text:
            return "[No speech detected]"
        return text
    except Exception as e:
        print(f"   ⚠️  faster-whisper failed: {e}")
        return None


def _transcribe_with_gemini(audio_path: str) -> str:
    """Transcribe audio using Gemini API (cloud fallback)."""
    import base64
    import urllib.request

    from .vision import _get_api_key, GEMINI_API_URL

    api_key = _get_api_key()

    with open(audio_path, "rb") as f:
        audio_data = base64.b64encode(f.read()).decode("utf-8")

    # Limit to ~10MB of raw audio (~13.3MB base64). Truncate at 4-byte
    # boundary to keep base64 valid, though this still cuts the audio mid-stream.
    max_b64_len = 13_333_336  # 10MB raw ≈ ceil(10M * 4/3), aligned to 4
    if len(audio_data) > max_b64_len:
        audio_data = audio_data[:max_b64_len]

    url = GEMINI_API_URL.format(model="gemini-3-flash-preview") + f"?key={api_key}"
    payload = {
        "contents": [{"parts": [
            {"text": "Transcribe this audio. Return only the transcription text, nothing else. If there is no speech, return '[No speech detected]'."},
            {"inline_data": {"mime_type": "audio/wav", "data": audio_data}},
        ]}]
    }

    data = json.dumps(payload).encode("utf-8")
    req = urllib.request.Request(url, data=data, headers={"Content-Type": "application/json"})

    try:
        with urllib.request.urlopen(req, timeout=120) as resp:
            result = json.loads(resp.read().decode("utf-8"))
        return result["candidates"][0]["content"]["parts"][0]["text"]
    except Exception as e:
        return f"[Transcription failed: {e}]"


def transcribe_audio(audio_path: str, model: str = "tiny",
                     language: Optional[str] = None) -> str:
    """
    Transcribe audio with graceful fallback:
    1. Try faster-whisper (local, fast, no API cost)
    2. Fall back to Gemini API if faster-whisper unavailable
    
    Args:
        audio_path: Path to WAV audio file
        model: faster-whisper model name (default: tiny for speed on CPU)
        language: Language code (e.g. 'en') or None for auto-detect
    
    Returns:
        Transcription text
    """
    # Check file size — skip if too small (likely silent)
    file_size = os.path.getsize(audio_path)
    if file_size < 1000:
        return "[No audio or silent video]"

    # Try faster-whisper first (local, no API cost)
    result = _transcribe_with_faster_whisper(audio_path, model_name=model, language=language)
    if result is not None:
        print(f"   (transcribed with faster-whisper, model={model})")
        return result

    # Fall back to Gemini API
    print("   (faster-whisper unavailable, using Gemini API)")
    return _transcribe_with_gemini(audio_path)


# ─── Full Processing Pipeline ─────────────────────────────────

def process_video_file(video_path: str, frame_interval: float = 5.0,
                       analyze_frames: bool = True, transcribe: bool = True) -> dict:
    """
    Full video processing pipeline.
    
    1. Extract frames every N seconds
    2. Extract and transcribe audio
    3. Analyze key frames with vision model
    4. Combine into summary
    
    Args:
        video_path: Path to local video file
        frame_interval: Seconds between extracted frames
        analyze_frames: Whether to run vision analysis on frames
        transcribe: Whether to transcribe audio
    
    Returns:
        dict with: frames, transcription, frame_analyses, summary
    """
    result = {
        "video_path": video_path,
        "frames": [],
        "transcription": None,
        "frame_analyses": [],
        "summary": None,
    }

    # 1. Extract frames
    print(f"🎞️  Extracting frames (every {frame_interval}s)...")
    try:
        frames = extract_frames(video_path, interval=frame_interval)
        result["frames"] = frames
        print(f"   Extracted {len(frames)} frames")
    except Exception as e:
        print(f"   ⚠️  Frame extraction failed: {e}")

    # 2. Transcribe audio
    if transcribe:
        print("🎤 Extracting and transcribing audio...")
        try:
            audio_path = extract_audio(video_path)
            transcription = transcribe_audio(audio_path)
            result["transcription"] = transcription
            print(f"   Transcription: {transcription[:200]}...")
        except Exception as e:
            print(f"   ⚠️  Transcription failed: {e}")
            result["transcription"] = f"[Failed: {e}]"

    # 3. Analyze frames with vision
    if analyze_frames and result["frames"]:
        print("🔍 Analyzing frames with Gemini Vision...")
        from .vision import analyze_image, analyze_carousel

        # Analyze a subset of frames (every Nth to limit API calls)
        frames_to_analyze = result["frames"]
        if len(frames_to_analyze) > 8:
            step = len(frames_to_analyze) // 8
            frames_to_analyze = frames_to_analyze[::step][:8]

        try:
            analysis = analyze_carousel(
                frames_to_analyze,
                "These are frames extracted from a video at regular intervals. "
                "Describe what you see in each frame and summarize the overall video content."
            )
            result["frame_analyses"] = [analysis]
            print(f"   Frame analysis complete")
        except Exception as e:
            print(f"   ⚠️  Frame analysis failed: {e}")

    # 4. Build combined summary
    parts = []
    if result.get("transcription") and not result["transcription"].startswith("["):
        parts.append(f"Audio: {result['transcription']}")
    if result.get("frame_analyses"):
        parts.append(f"Visual: {result['frame_analyses'][0]}")
    result["summary"] = "\n\n".join(parts) if parts else "No content extracted"

    return result


def process_video_url(url: str, **kwargs) -> dict:
    """
    Download a video from URL and run full processing pipeline.
    
    Combines download_video() + process_video_file().
    """
    print(f"⬇️  Downloading video from {url}...")
    dl = download_video(url)
    if not dl.get("success"):
        return {"url": url, "error": dl.get("error", "Download failed")}

    print(f"   Downloaded: {dl['path']}")
    return process_video_file(dl["path"], **kwargs)


# ─── Testing ───────────────────────────────────────────────────

if __name__ == "__main__":
    if len(sys.argv) > 1:
        arg = sys.argv[1]
        if arg.startswith(("http://", "https://")):
            if "--meta-only" in sys.argv:
                meta = extract_video_metadata(arg)
                for k, v in meta.items():
                    if v is not None and k != "thumbnails":
                        print(f"  {k}: {str(v)[:100]}")
            else:
                result = process_video_url(arg)
                if result.get("summary"):
                    print(f"\n📝 Summary:\n{result['summary'][:500]}")
        else:
            # Local file
            result = process_video_file(arg)
            if result.get("summary"):
                print(f"\n📝 Summary:\n{result['summary'][:500]}")
    else:
        print("Usage: python -m social_media_reader.video <url_or_file> [--meta-only]")
