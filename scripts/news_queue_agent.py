import argparse
import json
import re
import shutil
import subprocess
from datetime import datetime
from pathlib import Path


DEFAULT_SOURCE_DIR = Path("/Users/tmss1988/Desktop/tech e ouro")
DEFAULT_CONTENT_DIR = Path("conteudos")
DISCARDED_DIR_NAME = "_descartadas"
MANIFEST_NAME = "news-queue-manifest.json"
SUPPORTED_SUFFIXES = {".txt", ".rtf", ".pdf", ".png", ".jpg", ".jpeg", ".webp"}
IGNORED_NAMES = {".ds_store"}
MONTHLY_SOURCE_HINTS = {
    "deco",
    "expresso weekly",
    "lux",
    "lux woman",
    "national geografich",
    "nova gente",
    "pc guia",
    "sabado",
    "visao",
}


def should_ignore(path):
    name = path.name.lower()
    stem = path.stem.lower().strip()
    if name in IGNORED_NAMES or name.startswith("."):
        return True
    if any(part.startswith(".") or part == DISCARDED_DIR_NAME for part in path.parts):
        return True
    if "adsense" in name or "goggle" in name or stem.startswith("add") or "video" in stem:
        return True
    return path.suffix.lower() not in SUPPORTED_SUFFIXES


def source_label(source_dir, path):
    try:
        relative = path.relative_to(source_dir)
    except ValueError:
        return path.stem
    if len(relative.parts) > 1:
        return Path(relative.parts[0]).stem
    return path.stem


def is_monthly_source(source_dir, path):
    label = source_label(source_dir, path).lower()
    return any(hint in label for hint in MONTHLY_SOURCE_HINTS)


def max_age_for(source_dir, path, daily_hours, monthly_days):
    if is_monthly_source(source_dir, path):
        return monthly_days * 24 * 60 * 60
    return daily_hours * 60 * 60


def partition_fresh_and_stale(source_dir, files, daily_hours, monthly_days):
    now = datetime.now().timestamp()
    fresh = []
    stale = []
    for path in files:
        age_seconds = now - path.stat().st_mtime
        if age_seconds > max_age_for(source_dir, path, daily_hours, monthly_days):
            stale.append(path)
        else:
            fresh.append(path)
    return fresh, stale


def all_source_files(source_dir):
    return [p for p in source_dir.rglob("*") if p.is_file() and not should_ignore(p)]


def sorted_sources(source_dir, order, max_age_hours=30, monthly_max_age_days=45, include_stale=False):
    files = all_source_files(source_dir)
    fresh, stale = partition_fresh_and_stale(source_dir, files, max_age_hours, monthly_max_age_days)
    files = files if include_stale else fresh
    monthly_priority = lambda p: 1 if is_monthly_source(source_dir, p) else 0
    if order == "oldest-first":
        return sorted(files, key=lambda p: (monthly_priority(p), p.stat().st_mtime, p.name.lower()))
    if order == "newest-first":
        return sorted(files, key=lambda p: (monthly_priority(p), -p.stat().st_mtime, p.name.lower()))
    if order == "name-desc":
        return sorted(files, key=lambda p: (monthly_priority(p), p.name.lower()), reverse=True)
    return sorted(files, key=lambda p: (monthly_priority(p), p.name.lower()))


def slugify(value):
    value = value.lower().strip()
    value = re.sub(r"[^a-z0-9._-]+", "-", value)
    value = re.sub(r"-+", "-", value).strip("-")
    return value or "noticia"


def unique_destination(content_dir, source_path, position):
    timestamp = datetime.now().strftime("%Y%m%d-%H%M%S")
    suffix = source_path.suffix.lower()
    if suffix == ".rtf":
        suffix = ".txt"
    base = slugify(source_path.stem)
    candidate = content_dir / f"fila-{timestamp}-{position:03d}-{base}{suffix}"
    counter = 2
    while candidate.exists():
        candidate = content_dir / f"fila-{timestamp}-{position:03d}-{base}-{counter}{suffix}"
        counter += 1
    return candidate


def unique_discard_destination(source_dir, source_path):
    date_part = datetime.now().strftime("%Y-%m-%d")
    try:
        relative = source_path.relative_to(source_dir)
    except ValueError:
        relative = Path(source_path.name)
    destination = source_dir / DISCARDED_DIR_NAME / date_part / relative
    destination.parent.mkdir(parents=True, exist_ok=True)
    counter = 2
    final = destination
    while final.exists():
        final = destination.with_name(f"{destination.stem}-{counter}{destination.suffix}")
        counter += 1
    return final


def load_manifest(content_dir):
    manifest_path = content_dir / MANIFEST_NAME
    if not manifest_path.exists():
        return []
    try:
        data = json.loads(manifest_path.read_text(encoding="utf-8"))
        return data if isinstance(data, list) else []
    except Exception:
        return []


def save_manifest(content_dir, manifest):
    manifest_path = content_dir / MANIFEST_NAME
    manifest_path.write_text(json.dumps(manifest, indent=2, ensure_ascii=False), encoding="utf-8")


def rtf_to_text(source_path):
    try:
        completed = subprocess.run(
            ["textutil", "-convert", "txt", "-stdout", str(source_path)],
            check=True,
            capture_output=True,
            text=True,
        )
        return completed.stdout
    except Exception:
        raw = source_path.read_text(encoding="utf-8", errors="ignore")
        raw = re.sub(r"\\'[0-9a-fA-F]{2}", " ", raw)
        raw = re.sub(r"\\[a-zA-Z]+-?\d* ?", " ", raw)
        return re.sub(r"[{}]", " ", raw)


def stage_file(source_path, destination):
    if source_path.suffix.lower() == ".rtf":
        destination.write_text(rtf_to_text(source_path).strip() + "\n", encoding="utf-8")
        source_path.unlink()
        return
    shutil.move(str(source_path), str(destination))


def discard_stale_sources(source_dir, max_age_hours, monthly_max_age_days):
    files = all_source_files(source_dir)
    _, stale = partition_fresh_and_stale(source_dir, files, max_age_hours, monthly_max_age_days)
    discarded = []
    for source_path in stale:
        destination = unique_discard_destination(source_dir, source_path)
        shutil.move(str(source_path), str(destination))
        discarded.append((source_path, destination))
    return discarded


def stage_queue(source_dir, content_dir, limit, order, max_age_hours, monthly_max_age_days):
    if not source_dir.exists():
        raise FileNotFoundError(f"Pasta de notícias não encontrada: {source_dir}")
    content_dir.mkdir(parents=True, exist_ok=True)

    discarded = discard_stale_sources(source_dir, max_age_hours, monthly_max_age_days)
    sources = sorted_sources(source_dir, order, max_age_hours, monthly_max_age_days)[:limit]
    manifest = load_manifest(content_dir)
    queued_at = datetime.now().isoformat(timespec="seconds")
    staged = []

    for index, source_path in enumerate(sources, 1):
        destination = unique_destination(content_dir, source_path, index)
        stage_file(source_path, destination)
        entry = {
            "source_path": str(source_path),
            "staged_path": str(destination),
            "staged_name": destination.name,
            "source_label": source_label(source_dir, source_path),
            "queued_at": queued_at,
            "order": order,
            "status": "staged",
        }
        manifest.append(entry)
        staged.append(entry)

    save_manifest(content_dir, manifest)
    return staged, discarded


def main():
    parser = argparse.ArgumentParser(description="Stage desktop news files for Tech & Ouro.")
    parser.add_argument("--source-dir", default=str(DEFAULT_SOURCE_DIR))
    parser.add_argument("--content-dir", default=str(DEFAULT_CONTENT_DIR))
    parser.add_argument("--limit", type=int, default=20)
    parser.add_argument("--max-age-hours", type=int, default=30)
    parser.add_argument("--monthly-max-age-days", type=int, default=45)
    parser.add_argument(
        "--order",
        choices=("oldest-first", "newest-first", "name-asc", "name-desc"),
        default="oldest-first",
        help="oldest-first matches bottom-to-top when Finder shows newest files at the top.",
    )
    parser.add_argument("--dry-run", action="store_true")
    args = parser.parse_args()

    source_dir = Path(args.source_dir).expanduser()
    content_dir = Path(args.content_dir)
    all_files = all_source_files(source_dir) if source_dir.exists() else []
    fresh, stale = partition_fresh_and_stale(
        source_dir, all_files, args.max_age_hours, args.monthly_max_age_days
    )
    candidates = sorted_sources(
        source_dir, args.order, args.max_age_hours, args.monthly_max_age_days
    )[: args.limit] if source_dir.exists() else []

    if args.dry_run:
        print(f"Queue agent: {len(candidates)} file(s) would be staged from {source_dir}.")
        if stale:
            print(f"Queue agent: {len(stale)} stale file(s) would be moved to {DISCARDED_DIR_NAME}.")
        print(f"Queue agent: {len(fresh)} fresh source file(s), {len(stale)} stale source file(s).")
        for path in candidates:
            print(f"- {source_label(source_dir, path)} / {path.name}")
        return

    staged, discarded = stage_queue(
        source_dir,
        content_dir,
        args.limit,
        args.order,
        args.max_age_hours,
        args.monthly_max_age_days,
    )
    if discarded:
        print(f"Queue agent: discarded {len(discarded)} stale file(s) to {DISCARDED_DIR_NAME}.")
    if not staged:
        print(f"Queue agent: no news files to stage in {source_dir}.")
        return

    print(f"Queue agent: staged {len(staged)} file(s) for the news pipeline.")
    for entry in staged:
        print(f"- {Path(entry['source_path']).name} -> {Path(entry['staged_path']).name}")


if __name__ == "__main__":
    main()
