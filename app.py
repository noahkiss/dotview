import mimetypes
import os
from pathlib import Path

from flask import Flask, abort, render_template

app = Flask(__name__)

REPO_DIR = Path(os.environ.get("DOTVIEW_REPO_DIR", "/data/repo"))

# Extensions highlight.js handles well — everything else gets rendered as plaintext
HIGHLIGHT_LANGS = {
    ".py": "python",
    ".js": "javascript",
    ".ts": "typescript",
    ".sh": "bash",
    ".bash": "bash",
    ".zsh": "bash",
    ".fish": "fish",
    ".rb": "ruby",
    ".go": "go",
    ".rs": "rust",
    ".toml": "toml",
    ".yaml": "yaml",
    ".yml": "yaml",
    ".json": "json",
    ".md": "markdown",
    ".html": "xml",
    ".xml": "xml",
    ".css": "css",
    ".scss": "scss",
    ".sql": "sql",
    ".lua": "lua",
    ".vim": "vim",
    ".dockerfile": "dockerfile",
    ".tf": "hcl",
    ".hcl": "hcl",
    ".nix": "nix",
    ".conf": "ini",
    ".ini": "ini",
    ".cfg": "ini",
    ".env": "bash",
}

# Files to skip in listings
SKIP_NAMES = {".git"}

# Max file size to render (1 MB)
MAX_FILE_SIZE = 1_000_000


def resolve_path(rel_path: str) -> Path:
    """Resolve a relative path within the repo, preventing traversal."""
    full = (REPO_DIR / rel_path).resolve()
    if not str(full).startswith(str(REPO_DIR.resolve())):
        abort(403)
    return full


def get_entries(directory: Path) -> list[dict]:
    """List directory contents, sorted dirs-first then alphabetically."""
    entries = []
    for item in sorted(directory.iterdir(), key=lambda p: (not p.is_dir(), p.name.lower())):
        if item.name in SKIP_NAMES:
            continue
        entries.append(
            {
                "name": item.name + ("/" if item.is_dir() else ""),
                "is_dir": item.is_dir(),
                "path": str(item.relative_to(REPO_DIR)),
            }
        )
    return entries


def detect_language(path: Path) -> str:
    """Detect highlight.js language from file extension or name."""
    name = path.name.lower()

    # Handle extensionless known files
    if name == "dockerfile":
        return "dockerfile"
    if name == "makefile":
        return "makefile"
    if name in ("brewfile", "gemfile", "rakefile", "vagrantfile"):
        return "ruby"

    ext = path.suffix.lower()
    return HIGHLIGHT_LANGS.get(ext, "plaintext")


@app.route("/")
@app.route("/<path:filepath>")
def browse(filepath: str = ""):
    path = resolve_path(filepath)

    if not path.exists():
        abort(404)

    # Breadcrumbs
    parts = Path(filepath).parts if filepath else ()
    crumbs = [{"name": "root", "path": ""}]
    for i, part in enumerate(parts):
        crumbs.append({"name": part, "path": "/".join(parts[: i + 1])})

    if path.is_dir():
        entries = get_entries(path)
        return render_template("tree.html", entries=entries, crumbs=crumbs, current=filepath)

    # File view
    if path.stat().st_size > MAX_FILE_SIZE:
        return render_template(
            "file.html",
            content="File too large to display.",
            lang="plaintext",
            crumbs=crumbs,
            filename=path.name,
        )

    # Check if binary
    mime, _ = mimetypes.guess_type(str(path))
    if mime and not mime.startswith("text") and mime != "application/json":
        return render_template(
            "file.html",
            content=f"Binary file ({mime})",
            lang="plaintext",
            crumbs=crumbs,
            filename=path.name,
        )

    try:
        content = path.read_text(errors="replace")
    except Exception:
        content = "Unable to read file."

    lang = detect_language(path)
    return render_template("file.html", content=content, lang=lang, crumbs=crumbs, filename=path.name)
