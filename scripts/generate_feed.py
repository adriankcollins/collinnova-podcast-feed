#!/usr/bin/env python3
"""Generate feed.xml from MP3 files in episodes/ directory."""
import os
import sys
from datetime import datetime, timezone
from email.utils import format_datetime
import re

REPO_BASE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
EPISODES_DIR = os.path.join(REPO_BASE, "episodes")
PUBLIC_BASE = "https://adriankcollins.github.io/collinnova-podcast-feed"

def get_duration(filepath):
    """Use ffprobe to get audio duration in seconds."""
    import subprocess
    try:
        result = subprocess.run(
            ["ffprobe", "-v", "error", "-show_entries", "format=duration",
             "-of", "default=noprint_wrappers=1:nokey=1", filepath],
            capture_output=True, text=True, timeout=10
        )
        return int(float(result.stdout.strip()))
    except Exception:
        return 1800

def fmt_duration(seconds):
    h = seconds // 3600
    m = (seconds % 3600) // 60
    s = seconds % 60
    return f"{h:02d}:{m:02d}:{s:02d}"

def main():
    files = sorted(
        [f for f in os.listdir(EPISODES_DIR) if f.endswith(".mp3")],
        reverse=True
    )

    items = []
    for filename in files:
        filepath = os.path.join(EPISODES_DIR, filename)
        size = os.path.getsize(filepath)

        # Parse date from filename like 2026-05-09_NotebookLM.mp3
        # Use 00:01 UTC so pubDate is always in the PAST by the time the early-morning
        # build runs (~5:20 AM CDT = ~10:20 UTC). Podcast clients (Kortex included)
        # skip episodes whose pubDate is in the future, which broke auto-download.
        m = re.match(r"(\d{4}-\d{2}-\d{2})", filename)
        if m:
            date = datetime.strptime(m.group(1), "%Y-%m-%d").replace(
                tzinfo=timezone.utc, hour=0, minute=1
            )
            title = f"Collinnova Briefing {m.group(1)}"
        else:
            date = datetime.fromtimestamp(os.path.getmtime(filepath), tz=timezone.utc)
            title = filename.replace(".mp3", "")
        # Hard guarantee: never publish a future-dated episode.
        now = datetime.now(tz=timezone.utc)
        if date > now:
            date = now

        pub = format_datetime(date)
        duration = get_duration(filepath)
        guid = f"{PUBLIC_BASE}/episodes/{filename}"
        url = guid

        items.append(f"""    <item>
      <title>{title}</title>
      <description>Daily NotebookLM briefing for Collinnova.</description>
      <pubDate>{pub}</pubDate>
      <guid isPermaLink="true">{guid}</guid>
      <enclosure url="{url}" length="{size}" type="audio/mpeg"/>
      <itunes:duration>{fmt_duration(duration)}</itunes:duration>
      <itunes:explicit>false</itunes:explicit>
    </item>""")

    last_build = format_datetime(datetime.now(tz=timezone.utc))

    feed = f"""<?xml version="1.0" encoding="UTF-8"?>
<rss version="2.0" xmlns:itunes="http://www.itunes.com/dtds/podcast-1.0.dtd" xmlns:atom="http://www.w3.org/2005/Atom">
  <channel>
    <title>Collinnova Briefings</title>
    <link>{PUBLIC_BASE}/</link>
    <atom:link href="{PUBLIC_BASE}/feed.xml" rel="self" type="application/rss+xml"/>
    <description>Daily NotebookLM briefings for Collinnova.</description>
    <language>en-us</language>
    <lastBuildDate>{last_build}</lastBuildDate>
    <itunes:author>Collinnova</itunes:author>
    <itunes:summary>Daily NotebookLM briefings for Collinnova.</itunes:summary>
    <itunes:explicit>false</itunes:explicit>
    <itunes:category text="Business"/>
{chr(10).join(items)}
  </channel>
</rss>
"""

    with open(os.path.join(REPO_BASE, "feed.xml"), "w") as f:
        f.write(feed)

    print(f"Wrote feed.xml with {len(items)} episodes")

if __name__ == "__main__":
    main()
