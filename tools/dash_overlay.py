"""Fill a Dash checkout's generated files from a released Dash wheel.

Part of i18n-bugbench (MIT). A Dash checkout has no component packages
(dash/html, dash/dcc, dash/dash_table) or front-end bundles (dash/deps): they
are produced by an npm build of the whole monorepo. This extracts them from a
`dash` wheel, but only into paths that git does not track, so no source file
of the checkout changes. Renderer bundles that the checkout references but the
older wheel doesn't have are written as empty stubs: the Python tests serve
them but never run them.

Usage: python dash_overlay.py <checkout> <directory with one dash-*.whl>
"""

import re
import subprocess
import sys
import zipfile
from pathlib import Path

GENERATED = ("dash/html/", "dash/dcc/", "dash/dash_table/", "dash/deps/", "dash/dash-renderer/build/")


def main() -> None:
    checkout = Path(sys.argv[1]).resolve()
    wheels = sorted(Path(sys.argv[2]).glob("dash-*.whl"))
    if len(wheels) != 1:
        sys.exit(f"expected one dash wheel in {sys.argv[2]}, found {len(wheels)}")
    tracked = set(subprocess.run(["git", "ls-files", *GENERATED], cwd=checkout, capture_output=True,
                                 text=True, check=True).stdout.splitlines())
    copied = 0
    with zipfile.ZipFile(wheels[0]) as wheel:
        for name in wheel.namelist():
            if not name.startswith(GENERATED) or name.endswith("/") or name in tracked:
                continue
            target = checkout / name
            target.parent.mkdir(parents=True, exist_ok=True)
            target.write_bytes(wheel.read(name))
            copied += 1
    stubs = []
    renderer = (checkout / "dash" / "_dash_renderer.py").read_text(encoding="utf-8")
    for rel in sorted(set(re.findall(r'"(dash-renderer/build/[^"]+)"', renderer))):
        target = checkout / "dash" / rel
        if not target.exists():
            target.parent.mkdir(parents=True, exist_ok=True)
            target.write_text("/* i18n-bugbench stub: not in the dash wheel */\n", encoding="utf-8")
            stubs.append(rel)
    print(f"copied {copied} generated files from {wheels[0].name}; stubs: {stubs or 'none'}")


if __name__ == "__main__":
    main()
