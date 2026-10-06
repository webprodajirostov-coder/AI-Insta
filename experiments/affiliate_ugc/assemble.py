import argparse
import subprocess
from pathlib import Path


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--output", required=True, type=Path)
    parser.add_argument("clips", nargs="+", type=Path)
    args = parser.parse_args()

    if len(args.clips) < 2:
        raise ValueError("Provide at least two clips")

    args.output.parent.mkdir(parents=True, exist_ok=True)
    concat_file = args.output.parent / "_concat.txt"

    try:
        concat_file.write_text(
            "".join(f"file '{p.resolve().as_posix()}'\n" for p in args.clips),
            encoding="utf-8",
        )
        subprocess.run(
            [
                "ffmpeg", "-y",
                "-f", "concat", "-safe", "0",
                "-i", str(concat_file),
                "-c", "copy",
                str(args.output),
            ],
            check=True,
        )
    finally:
        concat_file.unlink(missing_ok=True)

    print("OUTPUT:", args.output.resolve())
