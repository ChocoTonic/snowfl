"""Ensure the generated plugin exists before tests run.

`engine/snowfl.py` is no longer committed — it is a build artifact published via
GitHub Releases. Generate it (dev version 0.0) so the plugin tests have a file to
exercise. Tests import it via the module-level PLUGIN_PATH.
"""

import os
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(ROOT, "tools"))

import build_plugin  # noqa: E402

build_plugin.main()
