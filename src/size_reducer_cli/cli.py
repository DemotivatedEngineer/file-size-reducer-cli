from __future__ import annotations

import argparse
from collections.abc import Sequence

from .reducer import CompressionError, UnsupportedFormatError, compress_image


def positive_int(value: str) -> int:
    try:
        parsed = int(value)
    except ValueError as exc:
        raise argparse.ArgumentTypeError("must be a positive integer") from exc

    if parsed <= 0:
        raise argparse.ArgumentTypeError("must be a positive integer")
    return parsed


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="A lightweight CLI tool to reduce image file size."
    )
    parser.add_argument(
        "file_path",
        help="Path to the input image file, such as photo.jpg",
    )
    parser.add_argument(
        "-m",
        "--max-size",
        type=positive_int,
        help="Optional maximum target file size in KB",
        default=None,
    )
    return parser


def main(argv: Sequence[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)

    try:
        result = compress_image(args.file_path, args.max_size)
    except FileNotFoundError as exc:
        missing_path = exc.filename or exc.args[0]
        print(f"Error: File '{missing_path}' not found.")
        return 1
    except UnsupportedFormatError as exc:
        print(f"Error: {exc}")
        return 1
    except CompressionError as exc:
        print(f"Error: {exc}")
        return 1

    if result.target_size_kb is not None and not result.target_met:
        print(
            "Warning: Target size was not reached. "
            f"Lowest size achieved: {result.size_kb:.2f} KB"
        )
    elif result.target_size_kb is not None:
        print(
            "Success: Compressed image saved to "
            f"'{result.output_path}' ({result.size_kb:.2f} KB)"
        )
    else:
        print(
            "Success: Optimized image saved to "
            f"'{result.output_path}' ({result.size_kb:.2f} KB)"
        )

    return 0
