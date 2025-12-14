#!/usr/bin/env python3
"""
Generate Jekyll posts for Facebook embeds based on _data/fb_posts.yml entries.
Optionally fetch recent feed items via the Graph API when --graph is supplied
and FB_ACCESS_TOKEN is available.
"""
from __future__ import annotations

import argparse
import hashlib
import os
import re
import sys
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional

try:
    import yaml
except ImportError:
    print("PyYAML is required. Install it with `pip install pyyaml` and retry.")
    sys.exit(1)

try:
    import requests
except ImportError:  # pragma: no cover - requests only needed for --graph
    requests = None  # type: ignore

SITE_DIR = Path(__file__).resolve().parents[1]
DATA_PATH = SITE_DIR / "_data" / "fb_posts.yml"
POSTS_DIR = SITE_DIR / "_posts"


def load_yaml_entries(path: Path) -> List[Dict]:
    if not path.exists():
        return []
    with path.open("r", encoding="utf-8") as f:
        data = yaml.safe_load(f) or []
    if not isinstance(data, list):
        raise ValueError(f"{path} must contain a list of posts")
    normalized: List[Dict] = []
    for entry in data:
        if not isinstance(entry, dict) or "url" not in entry:
            continue
        normalized.append(entry)
    return normalized


def normalize_permalink(url: str) -> str:
    return url.rstrip("/")


def extract_slug_from_url(url: str) -> str:
    match = re.search(r"/posts/(\d+)", url)
    if match:
        return match.group(1)
    match = re.search(r"/(\d+)(?:/)?$", url)
    if match:
        return match.group(1)
    digest = hashlib.sha256(url.encode("utf-8")).hexdigest()[:10]
    return digest


def sanitize_slug(slug: str) -> str:
    return re.sub(r"[^a-zA-Z0-9\-]+", "-", slug.strip()).strip("-").lower() or "post"


def parse_date(value: str) -> datetime:
    try:
        return datetime.fromisoformat(value)
    except ValueError:
        # Fallback: try only the date part
        return datetime.fromisoformat(value[:10])


def read_existing_posts() -> Dict[str, Path]:
    existing: Dict[str, Path] = {}
    for path in POSTS_DIR.glob("*.md"):
        with path.open("r", encoding="utf-8") as f:
            lines = f.readlines()
        if not lines or not lines[0].startswith("---"):
            continue
        try:
            end = lines[1:].index("---\n") + 1
            front_matter = yaml.safe_load("".join(lines[1:end]))
        except (ValueError, yaml.YAMLError):
            continue
        if isinstance(front_matter, dict) and front_matter.get("fb_permalink"):
            url = normalize_permalink(str(front_matter["fb_permalink"]))
            existing[url] = path
    return existing


def build_post_content(title: str, permalink: str, date: datetime) -> str:
    fm = {
        "layout": "fb_embed_post",
        "title": title,
        "fb_permalink": permalink,
        "categories": ["stpicks"],
        "date": date.date().isoformat(),
    }
    front_matter = yaml.safe_dump(fm, sort_keys=False, allow_unicode=True).strip()
    body = "此篇內容由 FB 內嵌"
    return f"---\n{front_matter}\n---\n\n{body}\n"


def upsert_post(entry: Dict, existing_map: Dict[str, Path]) -> Optional[Path]:
    url_raw = str(entry.get("url", "")).strip()
    if not url_raw:
        return None
    permalink = normalize_permalink(url_raw)
    title = str(entry.get("title") or "STPicks FB Post")
    date_str = str(entry.get("date") or datetime.today().date().isoformat())
    date = parse_date(date_str)

    slug = sanitize_slug(extract_slug_from_url(permalink))
    filename = f"{date.date().isoformat()}-{slug}.md"
    target_path = POSTS_DIR / filename

    if permalink in existing_map:
        target_path = existing_map[permalink]

    content = build_post_content(title, permalink, date)
    target_path.parent.mkdir(parents=True, exist_ok=True)
    with target_path.open("w", encoding="utf-8") as f:
        f.write(content)
    return target_path


def fetch_graph_entries() -> List[Dict]:
    token = os.getenv("FB_ACCESS_TOKEN")
    if not token:
        print("FB_ACCESS_TOKEN not set; skipping Graph fetch.")
        return []
    if requests is None:
        print("requests library not available; skipping Graph fetch.")
        return []

    page_id = os.getenv("FB_PAGE_ID", "stpicks")
    url = f"https://graph.facebook.com/v21.0/{page_id}/feed"
    params = {
        "fields": "permalink_url,created_time",
        "limit": 20,
        "access_token": token,
    }
    resp = requests.get(url, params=params, timeout=30)
    if resp.status_code != 200:
        print(f"Graph API request failed: {resp.status_code} {resp.text}")
        return []
    payload = resp.json()
    entries: List[Dict] = []
    for item in payload.get("data", []):
        permalink_url = item.get("permalink_url")
        created_time = item.get("created_time", "")[:10]
        if not permalink_url:
            continue
        entries.append(
            {
                "url": permalink_url,
                "date": created_time or datetime.today().date().isoformat(),
            }
        )
    return entries


def merge_graph_entries(data_entries: List[Dict], graph_entries: List[Dict]) -> List[Dict]:
    existing_urls = {normalize_permalink(str(item.get("url", ""))) for item in data_entries}
    for entry in graph_entries:
        url = normalize_permalink(str(entry.get("url", "")))
        if not url or url in existing_urls:
            continue
        data_entries.append(entry)
        existing_urls.add(url)
    return data_entries


def write_yaml_entries(path: Path, entries: List[Dict]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8") as f:
        yaml.safe_dump(entries, f, sort_keys=False, allow_unicode=True)


def main(argv: Optional[List[str]] = None) -> int:
    parser = argparse.ArgumentParser(description="Generate Jekyll FB embed posts.")
    parser.add_argument("--graph", action="store_true", help="Fetch feed via Graph API when FB_ACCESS_TOKEN is set.")
    args = parser.parse_args(argv)

    data_entries = load_yaml_entries(DATA_PATH)

    if args.graph:
        graph_entries = fetch_graph_entries()
        if graph_entries:
            data_entries = merge_graph_entries(data_entries, graph_entries)
            write_yaml_entries(DATA_PATH, data_entries)

    existing_map = read_existing_posts()
    created_or_updated: List[Path] = []
    for entry in data_entries:
        path = upsert_post(entry, existing_map)
        if path:
            created_or_updated.append(path)

    if created_or_updated:
        print("Generated/updated posts:")
        for path in created_or_updated:
            print(f" - {path.relative_to(SITE_DIR)}")
    else:
        print("No posts generated or updated.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
