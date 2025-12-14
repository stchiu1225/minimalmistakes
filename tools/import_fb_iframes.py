import hashlib
import re
import sys
from datetime import datetime
from pathlib import Path
from typing import List, Optional
from urllib.parse import parse_qs, unquote, urlparse

import requests
from bs4 import BeautifulSoup

SITE_DIR = Path(__file__).resolve().parent.parent
POSTS_DIR = SITE_DIR / "_posts"
DATE_STR = "2025-12-14"

IFRAMES: List[str] = [
    """<iframe src=\"https://www.facebook.com/plugins/post.php?href=https%3A%2F%2Fwww.facebook.com%2Fstpicks%2Fphotos%2Fa.157112844447947%2F205558836270014%2F%3Ftype%3D3&show_text=true&width=500\" width=\"500\" height=\"514\" style=\"border:none;overflow:hidden\" scrolling=\"no\" frameborder=\"0\" allowfullscreen=\"true\" allow=\"autoplay; clipboard-write; encrypted-media; picture-in-picture; web-share\"></iframe>""",
    """<iframe src=\"https://www.facebook.com/plugins/post.php?href=https%3A%2F%2Fwww.facebook.com%2Fphoto%2F%3Ffbid%3D205551016270796%26set%3Da.157112844447947&show_text=true&width=500\" width=\"500\" height=\"659\" style=\"border:none;overflow:hidden\" scrolling=\"no\" frameborder=\"0\" allowfullscreen=\"true\" allow=\"autoplay; clipboard-write; encrypted-media; picture-in-picture; web-share\"></iframe>""",
    """<iframe src=\"https://www.facebook.com/plugins/post.php?href=https%3A%2F%2Fwww.facebook.com%2Fphoto%2F%3Ffbid%3D205553796270518%26set%3Da.157112844447947&show_text=true&width=500\" width=\"500\" height=\"476\" style=\"border:none;overflow:hidden\" scrolling=\"no\" frameborder=\"0\" allowfullscreen=\"true\" allow=\"autoplay; clipboard-write; encrypted-media; picture-in-picture; web-share\"></iframe>""",
    """<iframe src=\"https://www.facebook.com/plugins/post.php?href=https%3A%2F%2Fwww.facebook.com%2Fphoto%2F%3Ffbid%3D206079942884570%26set%3Da.157112844447947&show_text=true&width=500\" width=\"500\" height=\"680\" style=\"border:none;overflow:hidden\" scrolling=\"no\" frameborder=\"0\" allowfullscreen=\"true\" allow=\"autoplay; clipboard-write; encrypted-media; picture-in-picture; web-share\"></iframe>""",
    """<iframe src=\"https://www.facebook.com/plugins/post.php?href=https%3A%2F%2Fwww.facebook.com%2Fphoto%2F%3Ffbid%3D206338106192087%26set%3Da.157112844447947&show_text=true&width=500\" width=\"500\" height=\"476\" style=\"border:none;overflow:hidden\" scrolling=\"no\" frameborder=\"0\" allowfullscreen=\"true\" allow=\"autoplay; clipboard-write; encrypted-media; picture-in-picture; web-share\"></iframe>""",
    """<iframe src=\"https://www.facebook.com/plugins/post.php?href=https%3A%2F%2Fwww.facebook.com%2Fphoto%2F%3Ffbid%3D206688842823680%26set%3Da.157112844447947&show_text=true&width=500\" width=\"500\" height=\"516\" style=\"border:none;overflow:hidden\" scrolling=\"no\" frameborder=\"0\" allowfullscreen=\"true\" allow=\"autoplay; clipboard-write; encrypted-media; picture-in-picture; web-share\"></iframe>""",
    """<iframe src=\"https://www.facebook.com/plugins/post.php?href=https%3A%2F%2Fwww.facebook.com%2Fphoto%2F%3Ffbid%3D206882906137607%26set%3Da.157112844447947&show_text=true&width=500\" width=\"500\" height=\"660\" style=\"border:none;overflow:hidden\" scrolling=\"no\" frameborder=\"0\" allowfullscreen=\"true\" allow=\"autoplay; clipboard-write; encrypted-media; picture-in-picture; web-share\"></iframe>""",
    """<iframe src=\"https://www.facebook.com/plugins/post.php?href=https%3A%2F%2Fwww.facebook.com%2Fphoto%2F%3Ffbid%3D207183949440836%26set%3Da.157112844447947&show_text=true&width=500\" width=\"500\" height=\"607\" style=\"border:none;overflow:hidden\" scrolling=\"no\" frameborder=\"0\" allowfullscreen=\"true\" allow=\"autoplay; clipboard-write; encrypted-media; picture-in-picture; web-share\"></iframe>""",
    """<iframe src=\"https://www.facebook.com/plugins/post.php?href=https%3A%2F%2Fwww.facebook.com%2Fstpicks%2Fposts%2F209013199257911&show_text=true&width=500\" width=\"500\" height=\"593\" style=\"border:none;overflow:hidden\" scrolling=\"no\" frameborder=\"0\" allowfullscreen=\"true\" allow=\"autoplay; clipboard-write; encrypted-media; picture-in-picture; web-share\"></iframe>""",
    """<iframe src=\"https://www.facebook.com/plugins/post.php?href=https%3A%2F%2Fwww.facebook.com%2Fphoto%2F%3Ffbid%3D210082259151005%26set%3Da.157112844447947&show_text=true&width=500\" width=\"500\" height=\"535\" style=\"border:none;overflow:hidden\" scrolling=\"no\" frameborder=\"0\" allowfullscreen=\"true\" allow=\"autoplay; clipboard-write; encrypted-media; picture-in-picture; web-share\"></iframe>""",
    """<iframe src=\"https://www.facebook.com/plugins/post.php?href=https%3A%2F%2Fwww.facebook.com%2Fphoto%2F%3Ffbid%3D212124598946771%26set%3Da.157112844447947&show_text=true&width=500\" width=\"500\" height=\"588\" style=\"border:none;overflow:hidden\" scrolling=\"no\" frameborder=\"0\" allowfullscreen=\"true\" allow=\"autoplay; clipboard-write; encrypted-media; picture-in-picture; web-share\"></iframe>""",
    """<iframe src=\"https://www.facebook.com/plugins/post.php?href=https%3A%2F%2Fwww.facebook.com%2Fstpicks%2Fposts%2F212686328890598&show_text=true&width=500\" width=\"500\" height=\"572\" style=\"border:none;overflow:hidden\" scrolling=\"no\" frameborder=\"0\" allowfullscreen=\"true\" allow=\"autoplay; clipboard-write; encrypted-media; picture-in-picture; web-share\"></iframe>""",
    """<iframe src=\"https://www.facebook.com/plugins/post.php?href=https%3A%2F%2Fwww.facebook.com%2Fphoto%2F%3Ffbid%3D213687298790501%26set%3Da.157112844447947&show_text=true&width=500\" width=\"500\" height=\"728\" style=\"border:none;overflow:hidden\" scrolling=\"no\" frameborder=\"0\" allowfullscreen=\"true\" allow=\"autoplay; clipboard-write; encrypted-media; picture-in-picture; web-share\"></iframe>""",
    """<iframe src=\"https://www.facebook.com/plugins/post.php?href=https%3A%2F%2Fwww.facebook.com%2Fphoto%2F%3Ffbid%3D214237998735431%26set%3Da.157112844447947&show_text=true&width=500\" width=\"500\" height=\"701\" style=\"border:none;overflow:hidden\" scrolling=\"no\" frameborder=\"0\" allowfullscreen=\"true\" allow=\"autoplay; clipboard-write; encrypted-media; picture-in-picture; web-share\"></iframe>""",
]


def extract_post_url(iframe_html: str) -> Optional[str]:
    soup = BeautifulSoup(iframe_html, "html.parser")
    iframe = soup.find("iframe")
    if not iframe:
        print("[warn] iframe tag not found; skipping entry", file=sys.stderr)
        return None
    src = iframe.get("src")
    if not src:
        print("[warn] iframe src missing; skipping entry", file=sys.stderr)
        return None

    parsed = urlparse(src)
    query = parse_qs(parsed.query)
    href_values = query.get("href")
    if not href_values:
        print(f"[warn] href param missing in src: {src}", file=sys.stderr)
        return None
    return unquote(href_values[0])


def extract_slug(post_url: str, default_token: str) -> str:
    parsed = urlparse(post_url)
    query = parse_qs(parsed.query)
    if "fbid" in query and query["fbid"]:
        return query["fbid"][0]

    slug_patterns = [
        r"/posts/(\d+)",
        r"/photos/[^/]+/(\d+)",
        r"/(\d{5,})/",
        r"/(\d{5,})$",
    ]
    for pattern in slug_patterns:
        match = re.search(pattern, post_url)
        if match:
            return match.group(1)

    digits = re.findall(r"\d{5,}", post_url)
    if digits:
        return digits[0]

    digest = hashlib.sha1(post_url.encode("utf-8")).hexdigest()[:8]
    return f"post-{default_token}-{digest}"


def extract_title(post_url: str, fallback: str) -> str:
    try:
        response = requests.get(post_url, timeout=10)
        response.raise_for_status()
        soup = BeautifulSoup(response.text, "html.parser")
        meta = soup.find("meta", attrs={"property": "og:description"})
        description = meta.get("content") if meta else None
        if description:
            match = re.search(r"\[(.+?)\]", description)
            if match:
                return match.group(1).strip()
    except Exception as exc:  # noqa: BLE001
        print(f"[warn] Failed to fetch description for {post_url}: {exc}", file=sys.stderr)

    print(f"[warn] Falling back to default title for {post_url}", file=sys.stderr)
    return fallback


def build_post_content(iframe_html: str, post_url: str) -> str:
    return (
        "<div class=\"fb-embed-wrap\">\n"
        f"  {iframe_html}\n"
        "</div>\n\n"
        f"<p><a href=\"{post_url}\" target=\"_blank\" rel=\"noopener\">Open on Facebook</a></p>\n"
    )


def write_post(slug: str, title: str, body: str) -> Path:
    POSTS_DIR.mkdir(parents=True, exist_ok=True)
    filename = POSTS_DIR / f"{DATE_STR}-{slug}.md"
    front_matter = (
        "---\n"
        "layout: single\n"
        f"title: \"{title}\"\n"
        f"date: {DATE_STR}\n"
        "categories: [stpicks]\n"
        "---\n\n"
    )
    content = front_matter + body
    filename.write_text(content, encoding="utf-8")
    return filename


def main() -> None:
    today_token = datetime.now().strftime("%H%M%S")
    fallback_counter = 1

    for idx, iframe_html in enumerate(IFRAMES, start=1):
        post_url = extract_post_url(iframe_html)
        if not post_url:
            continue

        fallback_title = f"Inspiration of the week {fallback_counter:02d}"
        title = extract_title(post_url, fallback_title)
        if title == fallback_title:
            fallback_counter += 1

        slug = extract_slug(post_url, default_token=today_token)
        body = build_post_content(iframe_html, post_url)
        path = write_post(slug, title, body)
        print(f"[info] Generated {path.name} — title: {title}")


if __name__ == "__main__":
    main()
