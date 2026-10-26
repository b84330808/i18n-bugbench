"""Run OpenCC's test/testcases/testcases.json against a checkout without a C++ build.

Part of i18n-bugbench (MIT). The conversion engine comes from the `opencc`
package on PyPI; the dictionaries and configs come from the checkout. They are
built the way data/CMakeLists.txt builds them with OPENCC_DICT_FORMAT=text:
the raw .txt dictionaries are used as they are, the generated ones are made
with the checkout's own scripts, and every config's ocd2 references are
rewritten to text. Everything is packed into a resource zip for
`opencc.OpenCC(config, resource_zip=...)`.

Usage: python opencc_testcases.py <checkout> [--only-prefix P ...] [--skip-prefix P ...]
"""

from __future__ import annotations

import argparse
import importlib.util
import json
import re
import shutil
import subprocess
import sys
import tempfile
import zipfile
from collections import defaultdict
from pathlib import Path

REVERSED = {
    "TWVariantsRev": "TWVariants",
    "HKVariantsRev": "HKVariants",
    "JPShinjitaiCharactersRev": "JPShinjitaiCharacters",
    "SealCharactersRev": "SealCharacters",
    "SealVariantsRev": "SealVariants",
}


def to_text(value):
    """Same rewrite as data/scripts/convert_config_dict_format.py with `text`."""
    if isinstance(value, dict):
        out = {}
        for key, child in value.items():
            if key == "type" and child == "ocd2":
                out[key] = "text"
            elif key == "file" and isinstance(child, str) and child.endswith(".ocd2"):
                out[key] = child[: -len(".ocd2")] + ".txt"
            else:
                out[key] = to_text(child)
        return out
    if isinstance(value, list):
        return [to_text(v) for v in value]
    return value


def load_testcases(path: Path) -> list[dict]:
    # testcases.json allows comments and trailing commas; strip them like
    # python/tests/test_opencc.py does.
    content = path.read_text(encoding="utf-8")
    pattern = re.compile(r'"(?:[^"\\]|\\.)*"|(/\*[\s\S]*?\*/|//.*)|(,\s*(?=[\]}]))')
    clean = pattern.sub(lambda m: "" if (m.group(1) or m.group(2)) else m.group(0), content)
    return json.loads(clean)["cases"]


def pack(work: Path, zip_path: Path) -> None:
    with zipfile.ZipFile(zip_path, "w", compression=zipfile.ZIP_STORED) as z:
        for f in sorted(work.iterdir()):
            z.write(f, f.name)


def opencc_cli() -> Path | None:
    import opencc

    bindir = Path(opencc.__file__).parent / "clib" / "bin"
    for name in ("opencc.exe", "opencc"):
        if (bindir / name).exists():
            return bindir / name
    return None


def build_resources(checkout: Path, work: Path) -> Path:
    data = checkout / "data"
    scripts = data / "scripts"
    for f in (data / "dictionary").glob("*.txt"):
        shutil.copy(f, work / f.name)
    py = sys.executable
    subprocess.run([py, str(scripts / "extract_tofu_risk.py"), str(work / "TSCharacters.txt"),
                    str(work / "TSCharactersExt.txt")], check=True)
    for out, src in REVERSED.items():
        if (work / f"{src}.txt").exists():
            subprocess.run([py, str(scripts / "reverse.py"), str(work / f"{src}.txt"),
                            str(work / f"{out}.txt")], check=True)
    for cfg in (data / "config").glob("*.json"):
        if cfg.name.startswith("opencc_config"):
            continue
        config = json.loads(cfg.read_text(encoding="utf-8"))
        (work / cfg.name).write_text(json.dumps(to_text(config), ensure_ascii=False, indent=2),
                                     encoding="utf-8")

    zip_path = work.parent / "resources.zip"
    generator = scripts / "generate_st_phrases_from_regional_phrases.py"
    if generator.exists():
        out = work / "STPhrases_GeneratedFromRegionalPhrases.txt"
        cli = opencc_cli()
        if cli is not None:
            subprocess.run([py, str(generator), "--input", str(work / "HKPhrases.txt"),
                            "--input", str(work / "TWPhrases.txt"), "--output", str(out),
                            "--opencc", str(cli), "--config", str(work / "t2s.json"),
                            "--dict-dir", str(work)], check=True)
        else:
            # No CLI in the wheel: run the generator with the Python binding instead.
            import opencc

            pack(work, zip_path)
            converter = opencc.OpenCC("t2s.json", resource_zip=str(zip_path))
            sys.path.insert(0, str(scripts))
            spec = importlib.util.spec_from_file_location("gen_st_phrases", generator)
            mod = importlib.util.module_from_spec(spec)
            spec.loader.exec_module(mod)
            mod.convert_keys = lambda _cli, _cfg, _dir, keys: [converter.convert(k) for k in keys]
            sys.argv = [str(generator), "--input", str(work / "HKPhrases.txt"), "--input",
                        str(work / "TWPhrases.txt"), "--output", str(out), "--opencc", "python",
                        "--config", str(work / "t2s.json"), "--dict-dir", str(work)]
            if mod.main():
                sys.exit("generating STPhrases_GeneratedFromRegionalPhrases failed")
    pack(work, zip_path)
    return zip_path


def main() -> None:
    sys.stdout.reconfigure(encoding="utf-8", errors="backslashreplace")
    p = argparse.ArgumentParser()
    p.add_argument("checkout")
    p.add_argument("--only-prefix", action="append", default=[])
    p.add_argument("--skip-prefix", action="append", default=[])
    args = p.parse_args()
    checkout = Path(args.checkout).resolve()

    import opencc

    cases = load_testcases(checkout / "test" / "testcases" / "testcases.json")
    if args.only_prefix:
        cases = [c for c in cases if c.get("id", "").startswith(tuple(args.only_prefix))]
    if args.skip_prefix:
        cases = [c for c in cases if not c.get("id", "").startswith(tuple(args.skip_prefix))]
    if not cases:
        sys.exit("no test cases selected")

    with tempfile.TemporaryDirectory() as tmp:
        work = Path(tmp) / "resources"
        work.mkdir()
        zip_path = build_resources(checkout, work)
        converters: dict[str, opencc.OpenCC] = {}
        failures = checked = 0
        by_config = defaultdict(list)
        for case in cases:
            for cfg, expected in case.get("expected", {}).items():
                by_config[cfg].append((case.get("id", "?"), case["input"], expected))
        for cfg, items in sorted(by_config.items()):
            converters[cfg] = opencc.OpenCC(f"{cfg}.json", resource_zip=str(zip_path))
            for case_id, text, expected in items:
                checked += 1
                got = converters[cfg].convert(text)
                if got != expected:
                    failures += 1
                    print(f"FAIL {case_id} [{cfg}]\n  input:    {text}\n  expected: {expected}\n  got:      {got}")
    print(f"{checked - failures}/{checked} conversions match (opencc {opencc.__version__})")
    sys.exit(1 if failures else 0)


if __name__ == "__main__":
    main()
