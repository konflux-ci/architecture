"""Normalize Sourcey-emitted llms.txt URLs to this site's live URL style.

Deterministic, rule-based, no content edits: Sourcey emits `.html`-suffixed,
lowercased paths; the live Eleventy site serves clean trailing-slash URLs and
keeps the `ADR/` directory uppercase. Also absolutizes against the site origin
so the index is consumable away from the site root (MCP docs servers).

Rules (in order), applied only to markdown link targets:
  1. leading `/architecture/adr/`  -> `/architecture/ADR/`
  2. trailing `.html`              -> `/`
  3. leading `/`                   -> `https://konflux-ci.dev/`

Usage: python normalize_llms_urls.py <in> <out>
"""
import re
import sys
from pathlib import Path

ORIGIN = "https://konflux-ci.dev"


def true_case_map(repo: Path) -> dict:
    """lowercase ADR slug -> true-case slug, from the repository tree (deterministic)."""
    out = {}
    for f in (repo / "ADR").glob("*.md"):
        slug = f.name[:-3]
        out[slug.lower()] = slug
    return out


def normalize(text: str, cases: dict) -> str:
    def fix(m):
        url = m.group(2)
        if url.startswith("/architecture/adr/"):
            url = "/architecture/ADR/" + url[len("/architecture/adr/"):]
        if url.endswith(".html"):
            url = url[:-len(".html")] + "/"
        adr = re.match(r"^/architecture/ADR/([^/]+)/$", url)
        if adr and adr.group(1).lower() in cases:
            url = f"/architecture/ADR/{cases[adr.group(1).lower()]}/"
        if url.startswith("/"):
            url = ORIGIN + url
        return f"[{m.group(1)}]({url})"

    return re.sub(r"\[([^\]]*)\]\(([^)]+)\)", fix, text)


if __name__ == "__main__":
    src, dst = Path(sys.argv[1]), Path(sys.argv[2])
    repo = Path(sys.argv[3]) if len(sys.argv) > 3 else Path(".")
    dst.write_text(normalize(src.read_text(encoding="utf-8"), true_case_map(repo)),
                   encoding="utf-8", newline="\n")
    print(f"normalized {src} -> {dst}")
