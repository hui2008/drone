#!/usr/bin/env python3
# AP_FLAKE8_CLEAN

import argparse
import csv
import json
import re
import shutil
import subprocess
import sys
from concurrent.futures import ThreadPoolExecutor, as_completed
from pathlib import Path


OTHER_VEHICLES = {
    "ArduCopter",
    "ArduPlane",
    "ArduSub",
    "AntennaTracker",
    "Blimp",
}


def parse_args():
    parser = argparse.ArgumentParser(
        description="Generate an organized readable preprocessed Rover SITL study bundle"
    )
    parser.add_argument(
        "--build",
        default="build/sitl",
        help="build directory containing compile_commands.json (default: build/sitl)",
    )
    parser.add_argument(
        "--output",
        default="build/sitl/rover-learning-bundle",
        help="output directory for the generated bundle",
    )
    parser.add_argument(
        "--jobs",
        type=int,
        default=4,
        help="number of preprocessing workers (default: 4)",
    )
    return parser.parse_args()


def repo_root():
    return Path(__file__).resolve().parents[2]


def load_compile_commands(build_dir):
    with (build_dir / "compile_commands.json").open(encoding="utf-8") as handle:
        return json.load(handle)


def relative_entry_path(root, entry):
    source_path = (Path(entry["directory"]) / entry["file"]).resolve()
    try:
        return source_path.relative_to(root)
    except ValueError:
        return None


def include_in_bundle(relpath):
    if relpath is None or relpath.suffix != ".cpp":
        return False
    if any(part in {"examples", "tests"} for part in relpath.parts):
        return False
    if relpath.parts[0] in OTHER_VEHICLES:
        return False
    if relpath.parts[0] == "Rover":
        return True
    if relpath.parts[0] == "libraries":
        return True
    if relpath.parts[0] == "build" and len(relpath.parts) >= 3 and relpath.parts[1] == "sitl" and relpath.parts[2] == "libraries":
        return True
    return False


def classify(relpath):
    if relpath.parts[0] == "Rover":
        return "vehicle"
    if relpath.parts[0] == "libraries":
        return "libraries"
    return "generated"


def ensure_preprocessed(root, build_dir, relpath):
    subprocess.run(
        [
            sys.executable,
            str(root / "Tools/scripts/preprocess_source.py"),
            str(relpath),
            "--build",
            str(build_dir.relative_to(root)),
        ],
        cwd=root,
        check=True,
        stdout=subprocess.DEVNULL,
    )


def make_readable(src, dst):
    dst.parent.mkdir(parents=True, exist_ok=True)
    last_blank = False
    with src.open(encoding="utf-8") as fin, dst.open("w", encoding="utf-8") as fout:
        for line in fin:
            if line.startswith("#"):
                continue
            if line.strip() == "":
                if last_blank:
                    continue
                fout.write("\n")
                last_blank = True
                continue
            fout.write(line.rstrip() + "\n")
            last_blank = False


def process_one(root, build_dir, out_root, relpath):
    ensure_preprocessed(root, build_dir, relpath)
    filtered = build_dir / relpath.parent / (relpath.name + ".filtered.ii")
    readable = out_root / "preprocessed" / relpath.parent / (relpath.name + ".readable.ii")
    make_readable(filtered, readable)
    with readable.open(encoding="utf-8") as handle:
        line_count = sum(1 for _ in handle)
    return {
        "path": relpath.as_posix(),
        "category": classify(relpath),
        "readable_path": readable.relative_to(out_root).as_posix(),
        "lines": line_count,
        "bytes": readable.stat().st_size,
    }


def write_manifest(out_root, rows):
    manifest_dir = out_root / "manifests"
    manifest_dir.mkdir(parents=True, exist_ok=True)
    manifest_path = manifest_dir / "files.csv"
    with manifest_path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=["category", "path", "readable_path", "lines", "bytes"])
        writer.writeheader()
        writer.writerows(rows)
    return manifest_path


def write_tree_index(out_root, rows):
    sections = {"vehicle": [], "libraries": [], "generated": []}
    for row in rows:
        sections[row["category"]].append(row)

    lines = [
        "# Rover Learning Bundle",
        "",
        "This bundle is generated from `build/sitl/compile_commands.json`.",
        "It contains readable preprocessed compile units selected for Rover SITL study.",
        "",
        "## Contents",
        "",
        "- `preprocessed/`: readable `.ii` files with preprocessor markers removed",
        "- `manifests/files.csv`: machine-readable file inventory",
        "- `notes/`: architecture notes and Mermaid diagrams",
        "",
        "## Counts",
        "",
        f"- Vehicle compile units: {len(sections['vehicle'])}",
        f"- Library compile units: {len(sections['libraries'])}",
        f"- Generated compile units: {len(sections['generated'])}",
        "",
        "## Layout",
        "",
        "- `preprocessed/Rover/`: Rover vehicle translation units",
        "- `preprocessed/libraries/`: shared library translation units linked into Rover SITL",
        "- `preprocessed/build/sitl/libraries/`: generated sources compiled for this build",
        "",
        "## Key Starting Points",
        "",
        "- `preprocessed/Rover/Rover.cpp.readable.ii`",
        "- `preprocessed/Rover/system.cpp.readable.ii`",
        "- `preprocessed/Rover/mode.cpp.readable.ii`",
        "- `preprocessed/libraries/AP_HAL_SITL/HAL_SITL_Class.cpp.readable.ii`",
        "- `preprocessed/libraries/AP_HAL_SITL/Scheduler.cpp.readable.ii`",
        "- `preprocessed/libraries/AP_Vehicle/AP_Vehicle.cpp.readable.ii`",
        "",
        "## Notes",
        "",
        "The readable files preserve the compiler-visible code after preprocessing,",
        "but they do not merge all `.cpp` files into one monolithic file. C++ still",
        "builds each translation unit separately.",
    ]
    index_path = out_root / "INDEX.md"
    index_path.write_text("\n".join(lines) + "\n", encoding="utf-8")
    return index_path


def extract_scheduler_tasks(source_text):
    tasks = []
    in_table = False
    for line in source_text.splitlines():
        if "Rover::scheduler_tasks[]" in line:
            in_table = True
            continue
        if in_table and line.strip() == "};":
            break
        if in_table and "SCHED_TASK" in line:
            cleaned = line.strip().rstrip(",")
            args = cleaned.split("(", 1)[1].rsplit(")", 1)[0]
            parts = [part.strip() for part in args.split(",")]
            if cleaned.startswith("SCHED_TASK_CLASS(") and len(parts) >= 6:
                tasks.append(
                    {
                        "name": f"{parts[0]}::{parts[2]}",
                        "rate_hz": parts[3],
                        "budget_us": parts[4],
                        "priority": parts[5],
                    }
                )
            elif cleaned.startswith("SCHED_TASK(") and len(parts) >= 4:
                tasks.append(
                    {
                        "name": parts[0],
                        "rate_hz": parts[1],
                        "budget_us": parts[2],
                        "priority": parts[3],
                    }
                )
    return tasks


def extract_mode_numbers(mode_header_text):
    match = re.search(r"enum class Number\s*:\s*[^{]+\{(.*?)\};", mode_header_text, re.S)
    if not match:
        return []
    body = match.group(1)
    modes = []
    for line in body.splitlines():
        line = line.split("//", 1)[0].strip().rstrip(",")
        if not line or line.startswith("#"):
            continue
        if not line or "=" in line:
            name = line.split("=", 1)[0].strip()
        else:
            name = line
        if name:
            modes.append(name)
    return modes


def write_notes(root, out_root):
    notes_dir = out_root / "notes"
    notes_dir.mkdir(parents=True, exist_ok=True)

    rover_cpp = (root / "Rover/Rover.cpp").read_text(encoding="utf-8")
    rover_system = (root / "Rover/system.cpp").read_text(encoding="utf-8")
    rover_mode_h = (root / "Rover/mode.h").read_text(encoding="utf-8")
    tasks = extract_scheduler_tasks(rover_cpp)
    modes = extract_mode_numbers(rover_mode_h)

    startup = """# Startup Path

The Rover SITL entry path is:

1. `Rover/Rover.cpp` uses `AP_HAL_MAIN_CALLBACKS(&rover)`.
2. `libraries/AP_HAL/AP_HAL_Main.h` expands that into `main()`.
3. `main()` calls `hal.run(argc, argv, &rover)`.
4. For SITL, `hal` is `HAL_SITL` from `libraries/AP_HAL_SITL/HAL_SITL_Class.cpp`.
5. `HAL_SITL::run()` initializes drivers, then calls `callbacks->setup()`.
6. `AP_Vehicle::setup()` runs vehicle-independent startup, then calls `Rover::init_ardupilot()`.
7. The main loop repeatedly calls `callbacks->loop()`, which reaches `AP_Vehicle::loop()` and `scheduler.loop()`.

```mermaid
flowchart TD
    A[Rover/Rover.cpp\\nAP_HAL_MAIN_CALLBACKS(&rover)] --> B[libraries/AP_HAL/AP_HAL_Main.h\\nmain()]
    B --> C[hal.run(argc, argv, &rover)]
    C --> D[libraries/AP_HAL_SITL/HAL_SITL_Class.cpp\\nHAL_SITL::run]
    D --> E[AP_Vehicle::setup]
    E --> F[Rover::init_ardupilot]
    D --> G[while true]
    G --> H[AP_Vehicle::loop]
    H --> I[AP_Scheduler::loop]
    I --> J[Rover scheduled tasks]
```
"""

    scheduler_lines = [
        "# Scheduler Overview",
        "",
        "The Rover task table lives in `Rover/Rover.cpp` as `Rover::scheduler_tasks[]`.",
        "These entries are interleaved with the base vehicle scheduler tasks in `AP_Vehicle`.",
        "",
        "## First Tasks In Priority Order",
        "",
    ]
    for task in tasks[:20]:
        scheduler_lines.append(
            f"- `{task['name']}` at `{task['rate_hz']} Hz`, budget `{task['budget_us']} us`, priority `{task['priority']}`"
        )
    scheduler_lines.extend(
        [
            "",
            "## High-Level Runtime Flow",
            "",
            "```mermaid",
            "flowchart TD",
            "    A[AP_Vehicle::loop] --> B[AP_Scheduler::loop]",
            "    B --> C[read_radio]",
            "    B --> D[ahrs_update]",
            "    B --> E[update_current_mode]",
            "    B --> F[set_servos]",
            "    B --> G[gcs update_receive/update_send]",
            "    B --> H[sensor, logging, failsafe tasks]",
            "```",
            "",
            "## Files To Read",
            "",
            "- `preprocessed/Rover/Rover.cpp.readable.ii`",
            "- `preprocessed/libraries/AP_Vehicle/AP_Vehicle.cpp.readable.ii`",
            "- `preprocessed/libraries/AP_HAL_SITL/Scheduler.cpp.readable.ii`",
        ]
    )

    mode_lines = [
        "# Modes And Mode Switching",
        "",
        "Mode support is centered on `Rover/mode.cpp`, the individual `Rover/mode_*.cpp` files,",
        "and `Rover/system.cpp` for switching through `Rover::set_mode(...)`.",
        "",
        "## Declared Mode Numbers",
        "",
    ]
    for mode in modes:
        mode_lines.append(f"- `{mode}`")
    mode_lines.extend(
        [
            "",
            "## Mode Switch Call Map",
            "",
            "```mermaid",
            "flowchart TD",
            "    A[RC/GCS/failsafe/mission event] --> B[Rover::set_mode]",
            "    B --> C[mode_from_mode_num]",
            "    C --> D[Mode::enter]",
            "    D --> E[Mode::_enter subclass hook]",
            "    B --> F[control_mode updated]",
            "    F --> G[Rover::update_current_mode]",
            "    G --> H[current mode _update / navigation logic]",
            "```",
            "",
            "## Useful Files",
            "",
            "- `preprocessed/Rover/system.cpp.readable.ii`",
            "- `preprocessed/Rover/mode.cpp.readable.ii`",
            "- `preprocessed/Rover/mode_auto.cpp.readable.ii`",
            "- `preprocessed/Rover/mode_guided.cpp.readable.ii`",
            "- `preprocessed/Rover/mode_rtl.cpp.readable.ii`",
        ]
    )

    runtime = """# HAL And SITL Runtime

The concrete `AP_HAL::Scheduler` implementation for Rover SITL is not in `Rover.cpp`.
It lives in `libraries/AP_HAL_SITL/Scheduler.cpp`, and the HAL instance is assembled in
`libraries/AP_HAL_SITL/HAL_SITL_Class.cpp`.

```mermaid
flowchart TD
    A[AP_HAL::get_HAL] --> B[HAL_SITL singleton]
    B --> C[sitlScheduler]
    B --> D[sitlRCInput]
    B --> E[sitlRCOutput]
    B --> F[sitlGPIO]
    B --> G[sitlAnalogIn]
    C --> H[libraries/AP_HAL_SITL/Scheduler.cpp]
```

Useful files:

- `preprocessed/libraries/AP_HAL_SITL/HAL_SITL_Class.cpp.readable.ii`
- `preprocessed/libraries/AP_HAL_SITL/Scheduler.cpp.readable.ii`
- `preprocessed/libraries/AP_HAL/Scheduler.cpp.readable.ii`
- `preprocessed/libraries/AP_Vehicle/AP_Vehicle.cpp.readable.ii`
"""

    (notes_dir / "startup.md").write_text(startup, encoding="utf-8")
    (notes_dir / "scheduler.md").write_text("\n".join(scheduler_lines) + "\n", encoding="utf-8")
    (notes_dir / "modes.md").write_text("\n".join(mode_lines) + "\n", encoding="utf-8")
    (notes_dir / "runtime.md").write_text(runtime, encoding="utf-8")


def main():
    args = parse_args()
    root = repo_root()
    build_dir = (root / args.build).resolve()
    out_root = (root / args.output).resolve()

    if out_root.exists():
        shutil.rmtree(out_root)
    out_root.mkdir(parents=True, exist_ok=True)

    commands = load_compile_commands(build_dir)
    relpaths = []
    for entry in commands:
        relpath = relative_entry_path(root, entry)
        if include_in_bundle(relpath):
            relpaths.append(relpath)
    relpaths = sorted(set(relpaths))

    rows = []
    with ThreadPoolExecutor(max_workers=max(1, args.jobs)) as executor:
        futures = {executor.submit(process_one, root, build_dir, out_root, relpath): relpath for relpath in relpaths}
        for future in as_completed(futures):
            rows.append(future.result())

    rows.sort(key=lambda row: (row["category"], row["path"]))
    write_manifest(out_root, rows)
    write_tree_index(out_root, rows)
    write_notes(root, out_root)

    print(f"Generated {len(rows)} readable preprocessed files in {out_root}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
