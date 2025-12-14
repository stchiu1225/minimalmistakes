import hashlib
import re
import sys
from datetime import date
from pathlib import Path
from typing import Optional
from urllib.parse import parse_qs, unquote, urlparse

import requests
from bs4 import BeautifulSoup

IFRAME_HTML_LIST = [
    """
<iframe src="https://www.facebook.com/plugins/post.php?href=https%3A%2F%2Fwww.facebook.com%2Fstpicks%2Fphotos%2Fa.157112844447947%2F205558836270014%2F%3Ftype%3D3&show_text=true&width=500" width="500" height="514" style="border:none;overflow:hidden" scrolling="no" frameborder="0" allowfullscreen="true" allow="autoplay; clipboard-write; encrypted-media; picture-in-picture; web-share"></iframe>
""",
    """
<iframe src="https://www.facebook.com/plugins/post.php?href=https%3A%2F%2Fwww.facebook.com%2Fphoto%2F%3Ffbid%3D205551016270796%26set%3Da.157112844447947&show_text=true&width=500" width="500" height="659" style="border:none;overflow:hidden" scrolling="no" frameborder="0" allowfullscreen="true" allow="autoplay; clipboard-write; encrypted-media; picture-in-picture; web-share"></iframe>
""",
    """
<iframe src="https://www.facebook.com/plugins/post.php?href=https%3A%2F%2Fwww.facebook.com%2Fphoto%2F%3Ffbid%3D205553796270518%26set%3Da.157112844447947&show_text=true&width=500" width="500" height="476" style="border:none;overflow:hidden" scrolling="no" frameborder="0" allowfullscreen="true" allow="autoplay; clipboard-write; encrypted-media; picture-in-picture; web-share"></iframe>
""",
    """
<iframe src="https://www.facebook.com/plugins/post.php?href=https%3A%2F%2Fwww.facebook.com%2Fphoto%2F%3Ffbid%3D206079942884570%26set%3Da.157112844447947&show_text=true&width=500" width="500" height="680" style="border:none;overflow:hidden" scrolling="no" frameborder="0" allowfullscreen="true" allow="autoplay; clipboard-write; encrypted-media; picture-in-picture; web-share"></iframe>
""",
    """
<iframe src="https://www.facebook.com/plugins/post.php?href=https%3A%2F%2Fwww.facebook.com%2Fphoto%2F%3Ffbid%3D206338106192087%26set%3Da.157112844447947&show_text=true&width=500" width="500" height="476" style="border:none;overflow:hidden" scrolling="no" frameborder="0" allowfullscreen="true" allow="autoplay; clipboard-write; encrypted-media; picture-in-picture; web-share"></iframe>
""",
    """
<iframe src="https://www.facebook.com/plugins/post.php?href=https%3A%2F%2Fwww.facebook.com%2Fphoto%2F%3Ffbid%3D206688842823680%26set%3Da.157112844447947&show_text=true&width=500" width="500" height="516" style="border:none;overflow:hidden" scrolling="no" frameborder="0" allowfullscreen="true" allow="autoplay; clipboard-write; encrypted-media; picture-in-picture; web-share"></iframe>
""",
    """
<iframe src="https://www.facebook.com/plugins/post.php?href=https%3A%2F%2Fwww.facebook.com%2Fphoto%2F%3Ffbid%3D206882906137607%26set%3Da.157112844447947&show_text=true&width=500" width="500" height="660" style="border:none;overflow:hidden" scrolling="no" frameborder="0" allowfullscreen="true" allow="autoplay; clipboard-write; encrypted-media; picture-in-picture; web-share"></iframe>
""",
    """
<iframe src="https://www.facebook.com/plugins/post.php?href=https%3A%2F%2Fwww.facebook.com%2Fphoto%2F%3Ffbid%3D207183949440836%26set%3Da.157112844447947&show_text=true&width=500" width="500" height="607" style="border:none;overflow:hidden" scrolling="no" frameborder="0" allowfullscreen="true" allow="autoplay; clipboard-write; encrypted-media; picture-in-picture; web-share"></iframe>
""",
    """
<iframe src="https://www.facebook.com/plugins/post.php?href=https%3A%2F%2Fwww.facebook.com%2Fstpicks%2Fposts%2F209013199257911&show_text=true&width=500" width="500" height="593" style="border:none;overflow:hidden" scrolling="no" frameborder="0" allowfullscreen="true" allow="autoplay; clipboard-write; encrypted-media; picture-in-picture; web-share"></iframe>
""",
    """
<iframe src="https://www.facebook.com/plugins/post.php?href=https%3A%2F%2Fwww.facebook.com%2Fphoto%2F%3Ffbid%3D210082259151005%26set%3Da.157112844447947&show_text=true&width=500" width="500" height="535" style="border:none;overflow:hidden" scrolling="no" frameborder="0" allowfullscreen="true" allow="autoplay; clipboard-write; encrypted-media; picture-in-picture; web-share"></iframe>
""",
    """
<iframe src="https://www.facebook.com/plugins/post.php?href=https%3A%2F%2Fwww.facebook.com%2Fphoto%2F%3Ffbid%3D212124598946771%26set%3Da.157112844447947&show_text=true&width=500" width="500" height="588" style="border:none;overflow:hidden" scrolling="no" frameborder="0" allowfullscreen="true" allow="autoplay; clipboard-write; encrypted-media; picture-in-picture; web-share"></iframe>
""",
    """
<iframe src="https://www.facebook.com/plugins/post.php?href=https%3A%2F%2Fwww.facebook.com%2Fstpicks%2Fposts%2F212686328890598&show_text=true&width=500" width="500" height="572" style="border:none;overflow:hidden" scrolling="no" frameborder="0" allowfullscreen="true" allow="autoplay; clipboard-write; encrypted-media; picture-in-picture; web-share"></iframe>
""",
    """
<iframe src="https://www.facebook.com/plugins/post.php?href=https%3A%2F%2Fwww.facebook.com%2Fphoto%2F%3Ffbid%3D213687298790501%26set%3Da.157112844447947&show_text=true&width=500" width="500" height="728" style="border:none;overflow:hidden" scrolling="no" frameborder="0" allowfullscreen="true" allow="autoplay; clipboard-write; encrypted-media; picture-in-picture; web-share"></iframe>
""",
    """
<iframe src="https://www.facebook.com/plugins/post.php?href=https%3A%2F%2Fwww.facebook.com%2Fphoto%2F%3Ffbid%3D214237998735431%26set%3Da.157112844447947&show_text=true&width=500" width="500" height="701" style="border:none;overflow:hidden" scrolling="no" frameborder="0" allowfullscreen="true" allow="autoplay; clipboard-write; encrypted-media; picture-in-picture; web-share"></iframe>
""",
]

SITE_DATE = date(2025, 12, 14)
IMAGES_DIR = Path("assets/images/stpicks")
POSTS_DIR = Path("_posts")

HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0 Safari/537.36"
}


def sanitize_slug(raw: str) -> str:
    slug = re.sub(r"[^a-zA-Z0-9]+", "-", raw).strip("-")
    return slug.lower() or "post"


def extract_slug(post_url: str) -> str:
    parsed = urlparse(post_url)
    qs = parse_qs(parsed.query)
    if "fbid" in qs and qs["fbid"]:
        return sanitize_slug(qs["fbid"][0])

    path_parts = parsed.path.strip("/").split("/")
    if "posts" in path_parts:
        idx = path_parts.index("posts")
        if idx + 1 < len(path_parts):
            return sanitize_slug(path_parts[idx + 1])

    digit_match = re.search(r"(\d{5,})", parsed.path)
    if digit_match:
        return sanitize_slug(digit_match.group(1))

    return hashlib.sha1(post_url.encode("utf-8")).hexdigest()[:12]


def extract_title(description: Optional[str], fallback_index: int) -> tuple[str, bool]:
    if description:
        match = re.search(r"\[(.+?)\]", description)
        if match:
            return match.group(1).strip(), False
    return f"Inspiration of the week {fallback_index:02d}", True


def download_image(image_url: str, slug: str) -> Optional[str]:
    try:
        response = requests.get(image_url, headers=HEADERS, timeout=20)
        response.raise_for_status()
    except Exception as exc:  # noqa: BLE001
        print(f"[warn] Failed to download image for slug={slug}: {exc}")
        return None

    content_type = response.headers.get("Content-Type", "").split(";")[0].strip()
    ext_map = {
        "image/jpeg": "jpg",
        "image/jpg": "jpg",
        "image/png": "png",
        "image/webp": "webp",
    }
    ext = ext_map.get(content_type, "jpg")

    IMAGES_DIR.mkdir(parents=True, exist_ok=True)
    filename = f"{slug}.{ext}"
    filepath = IMAGES_DIR / filename
    try:
        with open(filepath, "wb") as f:
            f.write(response.content)
    except Exception as exc:  # noqa: BLE001
        print(f"[warn] Failed to save image for slug={slug}: {exc}")
        return None

    return filename


def parse_iframe_src(html: str) -> Optional[str]:
    soup = BeautifulSoup(html, "html.parser")
    iframe = soup.find("iframe")
    if iframe and iframe.has_attr("src"):
        return iframe["src"]
    return None


def main() -> int:
    POSTS_DIR.mkdir(parents=True, exist_ok=True)
    fallback_counter = 1

    for iframe_html in IFRAME_HTML_LIST:
        src = parse_iframe_src(iframe_html)
        if not src:
            print("[warn] Skipping iframe without src")
            continue

        parsed_src = urlparse(src)
        href_param = parse_qs(parsed_src.query).get("href", [])
        if not href_param:
            print(f"[warn] No href found in src: {src}")
            continue

        post_url = unquote(href_param[0])
        slug = extract_slug(post_url)

        description = None
        image_url = None
        try:
            resp = requests.get(post_url, headers=HEADERS, timeout=20)
            resp.raise_for_status()
            soup = BeautifulSoup(resp.text, "html.parser")
            desc_tag = soup.find("meta", property="og:description")
            if desc_tag and desc_tag.has_attr("content"):
                description = desc_tag["content"]
            image_tag = soup.find("meta", property="og:image")
            if image_tag and image_tag.has_attr("content"):
                image_url = image_tag["content"]
        except Exception as exc:  # noqa: BLE001
            print(f"[warn] Failed to fetch post URL {post_url}: {exc}")

        title, used_fallback = extract_title(description, fallback_counter)
        if used_fallback:
            print(f"[warn] Title fallback used for slug={slug}")
            fallback_counter += 1

        image_filename = None
        if image_url:
            image_filename = download_image(image_url, slug)
        else:
            print(f"[warn] No image URL found for slug={slug}, falling back to iframe")

        filename = f"{SITE_DATE.strftime('%Y-%m-%d')}-{slug}.md"
        post_path = POSTS_DIR / filename

        front_matter = (
            "---\n"
            "layout: single\n"
            f"title: \"{title}\"\n"
            f"date: {SITE_DATE.isoformat()}\n"
            "categories: [stpicks]\n"
            "---\n\n"
        )

        if image_filename:
            rel_path = f"/assets/images/stpicks/{image_filename}"
            body = (
                f"![{title}]({{ \"{rel_path}\" | relative_url }})\n\n"
                f"[Open on Facebook]({post_url})\n"
            )
            saved_asset = rel_path
        else:
            body = (
                "<div class=\"fb-embed-wrap\">\n"
                f"  {iframe_html.strip()}\n"
                "</div>\n\n"
                f"[Open on Facebook]({post_url})\n"
            )
            saved_asset = "iframe"

        with open(post_path, "w", encoding="utf-8") as f:
            f.write(front_matter + body)

        print(f"[info] Generated {post_path} | title='{title}' | asset={saved_asset}")

    return 0


if __name__ == "__main__":
    sys.exit(main())
