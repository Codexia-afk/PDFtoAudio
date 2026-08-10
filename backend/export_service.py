from typing import List, Dict, Any


def generate_rss_podcast_feed(doc_id: str, doc_title: str, audio_url: str, description: str = "") -> str:
    """Generates a valid RSS 2.0 Podcast XML feed for podcast player compatibility."""
    desc = description or f"AI Podcast episode generated from document '{doc_title}'."
    rss_xml = f"""<?xml version="1.0" encoding="UTF-8"?>
<rss version="2.0" xmlns:itunes="http://www.itunes.com/dtds/podcast-1.0.dtd">
  <channel>
    <title>PDFtoAudio Studio — {doc_title}</title>
    <link>{audio_url}</link>
    <language>en-us</language>
    <itunes:author>PDFtoAudio Studio</itunes:author>
    <description>{desc}</description>
    <item>
      <title>{doc_title} (AI Episode)</title>
      <description>{desc}</description>
      <enclosure url="{audio_url}" length="1048576" type="audio/mpeg" />
      <guid>{audio_url}</guid>
      <pubDate>Tue, 11 Aug 2026 00:00:00 GMT</pubDate>
    </item>
  </channel>
</rss>
"""
    return rss_xml.strip()
