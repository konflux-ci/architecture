"""Normalize Sourcey-emitted llms.txt URLs to this site's live URL style.

Deterministic, rule-based, no content edits: Sourcey emits `.html`-suffixed,
lowercased paths; the live Eleventy site serves clean trailing-slash URLs and
keeps the `ADR/` directory uppercase. Also absolutizes against the site origin
so the index is consumable away from the site root (MCP docs servers).

Rules (in order), applied only to site-internal markdown link targets (external
links and bare anchors are left untouched; URL fragments are preserved):
  1. leading `/architecture/adr/`  -> `/architecture/ADR/`
  2. trailing `.html`              -> `/`
  3. ADR slug case restored from the repository tree (e.g. `...-gcl-...` -> `...-GCL-...`)
  4. leading `/`                   -> `https://konflux-ci.dev/`

Usage: python normalize_llms_urls.py <in> <out> <repo_root>
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
        if not url.startswith("/"):
            return m.group(0)  # external links and anchors are left untouched
        path, sep, frag = url.partition("#")
        if path.startswith("/architecture/adr/"):
            path = "/architecture/ADR/" + path[len("/architecture/adr/"):]
        if path.endswith(".html"):
            path = path[:-len(".html")] + "/"
        adr = re.match(r"^/architecture/ADR/([^/]+)/$", path)
        if adr and adr.group(1).lower() in cases:
            path = f"/architecture/ADR/{cases[adr.group(1).lower()]}/"
        return f"[{m.group(1)}]({ORIGIN}{path}{sep}{frag})"

    return re.sub(r"\[([^\]]*)\]\(([^)]+)\)", fix, text)


if __name__ == "__main__":
    if len(sys.argv) != 4:
        sys.exit("usage: normalize_llms_urls.py <in> <out> <repo_root>")
    src, dst, repo = Path(sys.argv[1]), Path(sys.argv[2]), Path(sys.argv[3])
    if not (repo / "ADR").is_dir():
        sys.exit(f"error: {repo} does not look like the repo root (no ADR/ directory)")
    dst.write_text(normalize(src.read_text(encoding="utf-8"), true_case_map(repo)),
                   encoding="utf-8", newline="\n")
    print(f"normalized {src} -> {dst}")
