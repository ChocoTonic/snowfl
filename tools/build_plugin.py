#!/usr/bin/env python3
"""Generate the single-file qBittorrent search plugin from the library core.

Inlines the transport-agnostic body of ``src/snowfl/core.py`` into the
``plugin/shell.py`` template and writes the result to ``engine/snowfl.py`` (the
committed artifact served raw to qBittorrent users).

Deterministic: same inputs -> byte-identical output, so CI can regenerate and
``git diff --exit-code`` to detect a stale artifact. DO NOT edit engine/snowfl.py
by hand. Run via ``make plugin``.
"""

import os
import py_compile
import re

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
CORE = os.path.join(ROOT, "src", "snowfl", "core.py")
SHELL = os.path.join(ROOT, "plugin", "shell.py")
OUT = os.path.join(ROOT, "engine", "snowfl.py")

CORE_MARKER = "# === BEGIN PLUGIN INLINE ==="
CORE_PLACEHOLDER = "# __SNOWFL_CORE__"
VERSION_PLACEHOLDER = "__PLUGIN_VERSION__"


def _read(path):
    with open(path, "r", encoding="utf-8") as f:
        return f.read()


def _core_body(core_src):
    idx = core_src.find(CORE_MARKER)
    if idx == -1:
        raise SystemExit("core.py is missing the marker: " + CORE_MARKER)
    return core_src[idx + len(CORE_MARKER):].strip("\n")


def _plugin_version():
    """Version stamped into the ``# VERSION:`` header.

    Read from the ``PLUGIN_VERSION`` env var so the release workflow can stamp a
    real, monotonic version at publish time. Defaults to ``0.0`` for local/test
    builds (the committed tree no longer carries a version — releases own it).
    """
    return os.environ.get("PLUGIN_VERSION", "0.0").strip()


def generate():
    """Return the generated plugin source as a string (no side effects)."""
    shell_src = _read(SHELL)
    if CORE_PLACEHOLDER not in shell_src:
        raise SystemExit("plugin/shell.py is missing the placeholder: " + CORE_PLACEHOLDER)
    out = shell_src.replace(VERSION_PLACEHOLDER, _plugin_version())
    out = out.replace(CORE_PLACEHOLDER, _core_body(_read(CORE)))
    return out


def main():
    out = generate()
    os.makedirs(os.path.dirname(OUT), exist_ok=True)
    with open(OUT, "w", encoding="utf-8") as f:
        f.write(out)
    py_compile.compile(OUT, doraise=True)
    print("Wrote {0} (VERSION {1})".format(OUT, _plugin_version()))


if __name__ == "__main__":
    main()
