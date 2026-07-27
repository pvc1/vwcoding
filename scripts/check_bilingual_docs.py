#!/usr/bin/env python3
"""Verify that docs/ Markdown pages exist in every configured language.

Default language pages are plain ``name.md``. Translations live next to the
base file with a locale suffix: ``name.en.md``, ``name.de.md``, …

Locales are read from ``mkdocs.yml`` → ``plugins → i18n → languages``.
The default locale needs no suffix; every other locale with ``build:`` not set
to ``false`` must have a matching translation for each base page.
"""

from __future__ import annotations

import argparse
import re
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
DOCS = ROOT / "docs"
MKDOCS = ROOT / "mkdocs.yml"

# BCP-47-ish locale in a suffix filename: name.<lang>.md
_TRANSLATION_NAME = re.compile(
    r"^(?P<stem>.+)\.(?P<lang>[a-z]{2,3}(?:-[A-Za-z0-9]+)?)\.md$"
)

# Pages that intentionally exist in a single language only.
SKIP_STEMS: set[str] = set()


def load_i18n_locales(path: Path = MKDOCS) -> tuple[str, tuple[str, ...]]:
    """Return (default_locale, required_translation_locales) from mkdocs.yml.

    Avoids a PyYAML dependency so the bilingual CI job stays dependency-free.
    """
    text = path.read_text(encoding="utf-8")
    start = text.find("- i18n:")
    if start < 0:
        raise SystemExit(f"No i18n plugin found in {path}")

    rest = text[start:]
    end = re.search(r"\n  - (?!i18n)", rest)
    section = rest[: end.start()] if end else rest

    default = "ru"
    translations: list[str] = []
    for m in re.finditer(
        r"- locale:\s*(\S+)((?:\n(?!\s+- locale:)[^\n]*)*)",
        section,
    ):
        loc = m.group(1)
        block = m.group(2)
        if re.search(r"default:\s*true\b", block):
            default = loc
            continue
        if re.search(r"build:\s*false\b", block):
            continue
        translations.append(loc)

    # Longer tags first so en-GB wins over en when stripping suffixes.
    translations.sort(key=len, reverse=True)
    return default, tuple(translations)


DEFAULT_LANG, REQUIRED_LANGS = load_i18n_locales()


def is_doc(path: Path) -> bool:
    return path.suffix == ".md" and path.is_file()


def lang_suffix(path: Path) -> str | None:
    """Return the translation locale of a file, or None for a base file."""
    m = _TRANSLATION_NAME.match(path.name)
    if not m:
        return None
    lang = m.group("lang")
    if lang == DEFAULT_LANG:
        return None
    return lang


def base_path(path: Path) -> Path:
    """Map any file to its default-language base ``.md`` (idempotent)."""
    lang = lang_suffix(path)
    if lang:
        return path.with_name(path.name[: -len(f".{lang}.md")] + ".md")
    return path


def tr_path(base: Path, lang: str) -> Path:
    return base.with_name(f"{base.stem}.{lang}.md")


def rel(path: Path) -> str:
    return str(path.relative_to(DOCS))


def base_key(path: Path) -> str:
    return str(base_path(path).relative_to(DOCS))


def check_all_pairs() -> list[str]:
    errors: list[str] = []
    for path in sorted(DOCS.rglob("*.md")):
        if not is_doc(path):
            continue
        if base_key(path) in SKIP_STEMS:
            continue
        base = base_path(path)
        lang = lang_suffix(path)
        if lang:
            if not base.exists():
                errors.append(f"Missing {DEFAULT_LANG} base for {rel(path)}")
            continue
        for req in REQUIRED_LANGS:
            if not tr_path(base, req).exists():
                errors.append(f"Missing {req} pair for {rel(base)}")
    return errors


def changed_files(base_ref: str) -> set[Path]:
    result = subprocess.run(
        ["git", "diff", "--name-only", "--diff-filter=ACMR", f"{base_ref}...HEAD"],
        cwd=ROOT,
        capture_output=True,
        text=True,
        check=False,
    )
    if result.returncode != 0:
        raise SystemExit(f"git diff failed: {result.stderr.strip()}")
    files: set[Path] = set()
    for line in result.stdout.splitlines():
        line = line.strip()
        if not line.startswith("docs/") or not line.endswith(".md"):
            continue
        files.add(ROOT / line)
    return files


def check_changed_pairs(base_ref: str) -> list[str]:
    """Keep all language versions in sync within a single PR.

    - If the default-language base changed, every required translation must too.
    - A translation-only edit is allowed as long as the base exists.
    """
    errors: list[str] = []
    changed = changed_files(base_ref)
    touched: set[str] = set()
    for path in changed:
        if not is_doc(path):
            continue
        if base_key(path) in SKIP_STEMS:
            continue
        touched.add(base_key(path))

    for key in sorted(touched):
        base = DOCS / key
        if base in changed:
            for lang in REQUIRED_LANGS:
                tr = tr_path(base, lang)
                if tr not in changed:
                    errors.append(
                        f"{rel(base)} changed without matching update to {rel(tr)}"
                    )
        elif not base.exists():
            for path in changed:
                if base_path(path) == base and lang_suffix(path):
                    errors.append(
                        f"{rel(path)} changed but {DEFAULT_LANG} base "
                        f"{rel(base)} is missing"
                    )
    return errors


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--all",
        action="store_true",
        help="Verify that every docs/*.md base page has all required translations",
    )
    parser.add_argument(
        "--changed",
        metavar="BASE_REF",
        help="On PRs: keep base language and its translations in sync",
    )
    args = parser.parse_args()

    if not args.all and not args.changed:
        args.all = True

    print(
        f"i18n: default={DEFAULT_LANG}, required={','.join(REQUIRED_LANGS) or '(none)'}"
    )

    errors: list[str] = []
    if args.all:
        errors.extend(check_all_pairs())
    if args.changed:
        errors.extend(check_changed_pairs(args.changed))

    if errors:
        print("Bilingual documentation check failed:", file=sys.stderr)
        for err in errors:
            print(f"  - {err}", file=sys.stderr)
        return 1

    print("Bilingual documentation check passed.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
