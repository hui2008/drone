#!/usr/bin/env python3
# AP_FLAKE8_CLEAN

import argparse
import json
import os
import subprocess
import sys
from pathlib import Path


def parse_args():
    parser = argparse.ArgumentParser(
        description="Generate preprocess views for a source file using compile_commands.json"
    )
    parser.add_argument("source", help="source file path, relative to repo root or absolute")
    parser.add_argument(
        "--build",
        default="build/sitl",
        help="build directory containing compile_commands.json (default: build/sitl)",
    )
    return parser.parse_args()


def repo_root():
    return Path(__file__).resolve().parents[2]


def load_compile_commands(build_dir):
    path = build_dir / "compile_commands.json"
    with path.open(encoding="utf-8") as handle:
        return json.load(handle)


def resolve_source(root, source):
    path = Path(source)
    if path.is_absolute():
        return path.resolve()
    return (root / path).resolve()


def find_entry(commands, source_path):
    source_str = str(source_path)
    for entry in commands:
        directory = Path(entry["directory"]).resolve()
        file_path = (directory / entry["file"]).resolve()
        if file_path == source_path:
            return entry, entry["file"]
    for entry in commands:
        directory = Path(entry["directory"]).resolve()
        file_path = (directory / entry["file"]).resolve()
        if file_path.as_posix().endswith(source_path.as_posix()):
            return entry, entry["file"]
    raise FileNotFoundError(f"no compile_commands.json entry found for {source_str}")


def preprocess(entry, file_key, source_path, root, build_dir):
    args = list(entry["arguments"])
    source_rel = source_path.relative_to(root)
    output_base = build_dir / source_rel.parent / source_rel.name
    output_base.parent.mkdir(parents=True, exist_ok=True)

    full_output = output_base.with_suffix(output_base.suffix + ".full.ii")
    full_args = [value for value in args if value not in (file_key, "-c") and not value.startswith("-o")]
    full_args.extend(["-E", file_key, "-o", str(output_base.parent.relative_to(build_dir) / full_output.name)])
    subprocess.run(full_args, cwd=build_dir, check=True)

    return full_output


def filter_ardupilot_only(full_output):
    filtered_output = full_output.with_name(full_output.name.replace(".full.ii", ".filtered.ii"))
    keep = True

    with full_output.open(encoding="utf-8") as src, filtered_output.open("w", encoding="utf-8") as dst:
        for line in src:
            if line.startswith("#"):
                keep = False
                parts = line.split('"')
                if len(parts) >= 3:
                    filename = parts[1]
                    if (
                        filename.startswith("../")
                        or filename.startswith("libraries/")
                        or filename.startswith("modules/")
                        or filename.startswith("build/")
                        or filename == "ap_config.h"
                    ):
                        keep = True
            if keep:
                dst.write(line)

    return filtered_output


def filter_source_only(full_output, file_key):
    source_output = full_output.with_name(full_output.name.replace(".full.ii", ".source_only.ii"))
    keep = False

    with full_output.open(encoding="utf-8") as src, source_output.open("w", encoding="utf-8") as dst:
        for line in src:
            if line.startswith("#"):
                parts = line.split('"')
                keep = len(parts) >= 3 and parts[1] == file_key
            if keep:
                dst.write(line)

    return source_output


def main():
    args = parse_args()
    root = repo_root()
    build_dir = (root / args.build).resolve()
    commands = load_compile_commands(build_dir)
    source_path = resolve_source(root, args.source)
    entry, file_key = find_entry(commands, source_path)

    full_output = preprocess(entry, file_key, source_path, root, build_dir)
    filtered_output = filter_ardupilot_only(full_output)
    source_output = filter_source_only(full_output, file_key)

    print(full_output)
    print(filtered_output)
    print(source_output)
    return 0


if __name__ == "__main__":
    sys.exit(main())
