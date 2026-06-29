#!/usr/bin/env python3
from __future__ import annotations

import html
import re
import shutil
from dataclasses import dataclass
from datetime import date
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
CONTENT_DIR = ROOT / "content" / "blog"
OUTPUT_DIR = ROOT / "blog"
CONTENT_CLASSES = {"center", "small", "medium", "large", "pullquote"}


@dataclass(frozen=True)
class Post:
    slug: str
    title: str
    date: str
    summary: str
    image: str
    image_alt: str
    body: str

    @property
    def output_dir(self) -> Path:
        return OUTPUT_DIR / self.slug

    @property
    def url(self) -> str:
        return f"{self.slug}/index.html"

    @property
    def image_from_blog_index(self) -> str:
        return f"../content/blog/{self.slug}/{self.image}"

    @property
    def image_from_article(self) -> str:
        return f"../../content/blog/{self.slug}/{self.image}"


def parse_frontmatter(raw: str) -> tuple[dict[str, str], str]:
    if not raw.startswith("---\n"):
        raise ValueError("Posts must begin with YAML-style front matter.")
    _, frontmatter, body = raw.split("---", 2)
    metadata: dict[str, str] = {}
    for line in frontmatter.strip().splitlines():
        if not line.strip():
            continue
        key, value = line.split(":", 1)
        metadata[key.strip()] = value.strip().strip('"')
    return metadata, body.strip()


def inline_markdown(text: str) -> str:
    escaped = html.escape(text)
    escaped = re.sub(r"\*\*(.+?)\*\*", r"<strong>\1</strong>", escaped)
    escaped = re.sub(r"\[(.+?)\]\((.+?)\)", r'<a href="\2">\1</a>', escaped)
    return escaped


def extract_block_class(lines: list[str]) -> tuple[str | None, list[str]]:
    first = lines[0].strip()
    match = re.fullmatch(r"\{\.([a-z-]+)\}", first)
    if not match:
        return None, lines
    class_name = match.group(1)
    if class_name not in CONTENT_CLASSES:
        allowed = ", ".join(sorted(CONTENT_CLASSES))
        raise ValueError(f"Unsupported content class '.{class_name}'. Supported classes: {allowed}.")
    return class_name, lines[1:]


def markdown_to_html(markdown: str) -> str:
    blocks = re.split(r"\n\s*\n", markdown.strip())
    rendered: list[str] = []
    for block in blocks:
        lines = block.strip().splitlines()
        if not lines:
            continue
        class_name, lines = extract_block_class(lines)
        if not lines:
            continue
        first = lines[0].strip()
        class_attr = f' class="{class_name}"' if class_name else ""
        if first.startswith("## "):
            rendered.append(f"<h2{class_attr}>{inline_markdown(first[3:].strip())}</h2>")
        elif first.startswith("# "):
            rendered.append(f"<h2{class_attr}>{inline_markdown(first[2:].strip())}</h2>")
        elif all(line.startswith("- ") for line in lines):
            items = "".join(f"<li>{inline_markdown(line[2:].strip())}</li>" for line in lines)
            rendered.append(f"<ul{class_attr}>{items}</ul>")
        elif class_name == "pullquote":
            text = " ".join(line.strip() for line in lines)
            rendered.append(f"<blockquote class=\"pullquote\"><p>{inline_markdown(text)}</p></blockquote>")
        elif re.fullmatch(r"!\[(.*?)\]\((.*?)\)", first):
            match = re.fullmatch(r"!\[(.*?)\]\((.*?)\)", first)

            alt = html.escape(match.group(1))
            src = html.escape(match.group(2))

            figure_class = "blog-image"
            if class_name:
                figure_class += f" {class_name}"

            rendered.append(
                f"""
                <figure class="{figure_class}">
                    <img src="{src}" alt="{alt}">
                    <figcaption>{alt}</figcaption>
                </figure>
                """
            )
        else:
            text = " ".join(line.strip() for line in lines)
            rendered.append(f"<p{class_attr}>{inline_markdown(text)}</p>")
    return "\n".join(rendered)


def load_posts() -> list[Post]:
    posts: list[Post] = []
    for folder in sorted(CONTENT_DIR.iterdir()):
        if not folder.is_dir():
            continue
        post_file = folder / "post.md"
        if not post_file.exists():
            continue
        metadata, body = parse_frontmatter(post_file.read_text(encoding="utf-8"))
        posts.append(
            Post(
                slug=folder.name,
                title=metadata["title"],
                date=metadata["date"],
                summary=metadata["summary"],
                image=metadata.get("image", "hero.jpeg"),
                image_alt=metadata.get("image_alt", ""),
                body=body,
            )
        )
    return sorted(posts, key=lambda post: (post.date, post.slug), reverse=True)


def site_header(current: str, prefix: str = "../") -> str:
    home_current = ' aria-current="page"' if current == "home" else ""
    books_current = ' aria-current="page"' if current == "books" else ""
    blog_current = ' aria-current="page"' if current == "blog" else ""
    return f"""
    <header class="site-header">
      <div class="nav-wrap">
        <a class="brand" href="{prefix}index.html">GJ Herman</a>
        <nav class="nav-links" aria-label="Primary navigation">
          <a href="{prefix}index.html"{home_current}>Home</a>
          <a href="{prefix}books/index.html"{books_current}>Books</a>
          <a href="{prefix}blog/index.html"{blog_current}>Blog</a>
          <a class="external-link shudder" href="https://killingname.com">SHUDDER</a>
          <a class="external-link" href="https://arc-world.com">ARCWORLD</a>
        </nav>
      </div>
    </header>"""


def site_footer(prefix: str = "../") -> str:
    year = date.today().year
    return f"""
    <footer class="site-footer">
      <div class="footer-inner">
        <div>
          <strong>GJ Herman</strong><br>
          <span>Copyright &copy; {year} GJ Herman</span>
        </div>
        <nav class="footer-links" aria-label="Footer navigation">
          <a href="https://www.facebook.com/arcworldpublishing/" class="fb-link" target="_blank" rel="noopener noreferrer">
            <svg viewBox="0 0 24 24" xmlns="http://w3.org">
                <path d="M24 12.073c0-6.627-5.373-12-12-12s-12 5.373-12 12c0 5.99 4.388 10.954 10.125 11.854v-8.385H7.078v-3.47h3.047V9.43c0-3.007 1.792-4.669 4.533-4.669 1.312 0 2.686.235 2.686.235v2.953H15.83c-1.491 0-1.956.925-1.956 1.874v2.25h3.328l-.532 3.47h-2.796v8.385C19.612 23.027 24 18.062 24 12.073z"/>
            </svg>
          </a>
          <a href="{prefix}index.html">Home</a>
          <a href="{prefix}books/index.html">Books</a>
          <a href="{prefix}impressum/index.html">Impressum</a>
          <a href="https://killingname.com">SHUDDER</a>
          <a href="https://arc-world.com">ARCWORLD</a>
        </nav>
      </div>
    </footer>"""


def render_index(posts: list[Post]) -> str:
    cards = "\n".join(
        f"""
          <a class="post-card" href="{post.url}">
            <img src="{post.image_from_blog_index}" alt="{html.escape(post.image_alt)}">
            <div class="post-card-body">
              <p class="meta">{html.escape(post.date)}</p>
              <h3>{html.escape(post.title)}</h3>
              <p>{html.escape(post.summary)}</p>
            </div>
          </a>"""
        for post in posts
    )
    return f"""<!doctype html>
<html lang="en">
  <head>
    <meta charset="utf-8">
    <meta name="viewport" content="width=device-width, initial-scale=1">
    <title>Blog | GJ Herman</title>
    <meta name="description" content="Notes, updates, and essays from GJ Herman.">
    <link rel="stylesheet" href="../assets/css/styles.css">
  </head>
  <body>
{site_header("blog")}
    <main>
      <section class="section">
        <div class="section-inner">
          <div class="section-heading">
            <div>
              <p class="eyebrow">Journal</p>
              
            </div>
            <p class="right">Random thoughts and book releases by the author.</p>
          </div>
          <div class="blog-grid">
{cards}
          </div>
        </div>
      </section>
    </main>
{site_footer()}
  </body>
</html>
"""


def render_article(post: Post) -> str:
    body = markdown_to_html(post.body)
    return f"""<!doctype html>
<html lang="en">
  <head>
    <meta charset="utf-8">
    <meta name="viewport" content="width=device-width, initial-scale=1">
    <title>{html.escape(post.title)} | GJ Herman</title>
    <meta name="description" content="{html.escape(post.summary)}">
    <link rel="stylesheet" href="../../assets/css/styles.css">
  </head>
  <body>
{site_header("blog", "../../")}
    <main>
      <section class="article-hero" style="--article-image: url('{post.image_from_article}')">
        <div class="article-hero-content">
          <p class="eyebrow">{html.escape(post.date)}</p>
          <h1>{html.escape(post.title)}</h1>
          <p class="hero-deck">{html.escape(post.summary)}</p>
        </div>
      </section>
      <article class="article-body">
{body}
      </article>
    </main>
{site_footer("../../")}
  </body>
</html>
"""


def confirm_clean() -> bool:
    if not OUTPUT_DIR.exists() or not any(OUTPUT_DIR.iterdir()):
        return True
    answer = input(f"Delete generated '{OUTPUT_DIR.relative_to(ROOT)}' directory before rebuilding? [y/N] ")
    return answer.strip().lower() in {"y", "yes"}


def clean_output() -> None:
    if OUTPUT_DIR.exists():
        shutil.rmtree(OUTPUT_DIR)


def build(clean: bool = True, assume_yes: bool = False) -> None:
    if clean:
        if assume_yes or confirm_clean():
            clean_output()
        else:
            raise SystemExit("Build cancelled; generated blog directory was not changed.")
    OUTPUT_DIR.mkdir(exist_ok=True)
    posts = load_posts()
    (OUTPUT_DIR / "index.html").write_text(render_index(posts), encoding="utf-8")
    for post in posts:
        post.output_dir.mkdir(exist_ok=True)

        source_dir = CONTENT_DIR / post.slug

        # Copy all images from content/blog/<slug>/
        for image in source_dir.iterdir():
            if image.suffix.lower() in {".jpg", ".jpeg", ".png", ".webp", ".gif"}:
                shutil.copy2(image, post.output_dir / image.name)

        (post.output_dir / "index.html").write_text(
            render_article(post),
            encoding="utf-8"
        )
    print(f"Built {len(posts)} blog posts into {OUTPUT_DIR.relative_to(ROOT)}")


if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(description="Build static blog pages from content/blog.")
    parser.add_argument("--yes", action="store_true", help="Clean generated blog output without asking.")
    parser.add_argument("--no-clean", action="store_true", help="Rebuild without deleting existing generated files first.")
    args = parser.parse_args()
    build(clean=not args.no_clean, assume_yes=args.yes)