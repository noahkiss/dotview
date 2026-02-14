import mimetypes
import os
import subprocess
from pathlib import Path

from flask import Flask, abort, jsonify, render_template

app = Flask(__name__)

REPO_DIR = Path(os.environ.get("DOTVIEW_REPO_DIR", "/data/repo")).resolve()

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


@app.template_filter("filesizeformat")
def filesizeformat(size: int) -> str:
    """Convert bytes to human-readable file size."""
    for unit in ("B", "KB", "MB", "GB"):
        if size < 1024:
            if unit == "B":
                return f"{size} {unit}"
            return f"{size:.1f} {unit}"
        size /= 1024
    return f"{size:.1f} TB"


def resolve_path(rel_path: str) -> Path:
    """Resolve a relative path within the repo, preventing traversal."""
    full = (REPO_DIR / rel_path).resolve()
    if not str(full).startswith(str(REPO_DIR.resolve())):
        abort(403)
    return full


def get_repo_info() -> dict:
    """Get current branch and short commit hash."""
    repo = str(REPO_DIR.resolve())
    info = {"branch": "", "commit": ""}
    try:
        info["branch"] = subprocess.run(
            ["git", "rev-parse", "--abbrev-ref", "HEAD"],
            capture_output=True, text=True, cwd=repo,
        ).stdout.strip()
        info["commit"] = subprocess.run(
            ["git", "log", "-1", "--format=%h"],
            capture_output=True, text=True, cwd=repo,
        ).stdout.strip()
    except Exception:
        pass
    return info


def build_tree(directory: Path, expand_to: Path | None = None, expand_all: bool = False) -> list[dict]:
    """Build tree. expand_all=True recurses into every directory."""
    entries = []
    for item in sorted(directory.iterdir(), key=lambda p: (not p.is_dir(), p.name.lower())):
        if item.name in SKIP_NAMES:
            continue
        rel = str(item.relative_to(REPO_DIR))
        node = {
            "name": item.name,
            "path": rel,
            "is_dir": item.is_dir(),
        }
        if item.is_dir():
            if expand_all:
                node["children"] = build_tree(item, expand_all=True)
                node["expanded"] = True
            elif expand_to and (item == expand_to or str(expand_to.resolve()).startswith(str(item.resolve()) + "/")):
                node["children"] = build_tree(item, expand_to)
                node["expanded"] = True
            else:
                node["children"] = []
                node["expanded"] = False
        else:
            try:
                node["size"] = item.stat().st_size
            except OSError:
                node["size"] = 0
        entries.append(node)
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


@app.route("/api/tree")
@app.route("/api/tree/<path:dirpath>")
def api_tree(dirpath: str = ""):
    """Return JSON entries for a directory (lazy-load for sidebar)."""
    path = resolve_path(dirpath)
    if not path.is_dir():
        abort(404)
    entries = []
    for item in sorted(path.iterdir(), key=lambda p: (not p.is_dir(), p.name.lower())):
        if item.name in SKIP_NAMES:
            continue
        rel = str(item.relative_to(REPO_DIR))
        node = {"name": item.name, "path": rel, "is_dir": item.is_dir()}
        if not item.is_dir():
            try:
                node["size"] = item.stat().st_size
            except OSError:
                node["size"] = 0
        entries.append(node)
    return jsonify(entries)


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

    # Build sidebar tree expanding to current path
    tree = build_tree(REPO_DIR, expand_to=path)
    repo_info = get_repo_info()
    repo_name = REPO_DIR.resolve().name

    if path.is_dir():
        full_tree = build_tree(path, expand_all=True)
        return render_template(
            "tree.html", full_tree=full_tree, crumbs=crumbs, current=filepath,
            tree=tree, repo_info=repo_info, repo_name=repo_name,
        )

    # File view
    file_size = path.stat().st_size

    if file_size > MAX_FILE_SIZE:
        return render_template(
            "file.html",
            content="File too large to display.",
            lang="plaintext",
            crumbs=crumbs,
            filename=path.name,
            file_size=file_size,
            line_count=0,
            tree=tree, repo_info=repo_info, repo_name=repo_name,
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
            file_size=file_size,
            line_count=0,
            tree=tree, repo_info=repo_info, repo_name=repo_name,
        )

    try:
        content = path.read_text(errors="replace")
    except Exception:
        content = "Unable to read file."

    lang = detect_language(path)
    line_count = content.count("\n") + (1 if content and not content.endswith("\n") else 0)
    return render_template(
        "file.html", content=content, lang=lang, crumbs=crumbs, filename=path.name,
        file_size=file_size, line_count=line_count,
        tree=tree, repo_info=repo_info, repo_name=repo_name,
    )
