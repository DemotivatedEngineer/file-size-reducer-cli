from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

from PIL import Image, ImageOps, UnidentifiedImageError

SUPPORTED_FORMATS = {
    ".jpg": "JPEG",
    ".jpeg": "JPEG",
    ".png": "PNG",
    ".webp": "WEBP",
}

QUALITY_FORMATS = {"JPEG", "WEBP"}
MIN_DIMENSION = 100


class CompressionError(RuntimeError):
    """Raised when an image cannot be processed."""


class UnsupportedFormatError(CompressionError):
    """Raised when the input extension is not supported."""


@dataclass(frozen=True)
class ImageReductionResult:
    input_path: Path
    output_path: Path
    size_kb: float
    target_size_kb: int | None
    target_met: bool
    output_format: str


def compress_image(input_path: str | Path, max_size_kb: int | None = None) -> ImageReductionResult:
    source = Path(input_path)
    if not source.exists():
        raise FileNotFoundError(source)
    if not source.is_file():
        raise CompressionError(f"'{source}' is not a file.")
    if max_size_kb is not None and max_size_kb <= 0:
        raise ValueError("max_size_kb must be a positive integer.")

    output_format = _format_for_path(source)
    output_path = _next_output_path(source)

    try:
        with Image.open(source) as opened:
            image = ImageOps.exif_transpose(opened)
            image = _prepare_for_format(image, output_format)

            target_bytes = max_size_kb * 1024 if max_size_kb is not None else None
            final_image = _save_with_target(image, output_path, output_format, target_bytes)
    except UnidentifiedImageError as exc:
        raise CompressionError(f"'{source}' is not a valid image.") from exc
    except OSError as exc:
        raise CompressionError(str(exc)) from exc

    size_kb = output_path.stat().st_size / 1024
    return ImageReductionResult(
        input_path=source,
        output_path=output_path,
        size_kb=size_kb,
        target_size_kb=max_size_kb,
        target_met=target_bytes is None or output_path.stat().st_size <= target_bytes,
        output_format=output_format,
    )


def _format_for_path(path: Path) -> str:
    output_format = SUPPORTED_FORMATS.get(path.suffix.lower())
    if output_format is None:
        supported = ", ".join(sorted(SUPPORTED_FORMATS))
        raise UnsupportedFormatError(
            f"Unsupported image format '{path.suffix or '<none>'}'. "
            f"Supported extensions: {supported}."
        )
    return output_format


def _next_output_path(source: Path) -> Path:
    base = source.with_name(f"{source.stem}_compressed{source.suffix}")
    if not base.exists():
        return base

    counter = 1
    while True:
        candidate = source.with_name(f"{source.stem}_compressed_{counter}{source.suffix}")
        if not candidate.exists():
            return candidate
        counter += 1


def _prepare_for_format(image: Image.Image, output_format: str) -> Image.Image:
    if output_format == "JPEG" and image.mode not in ("RGB", "L"):
        return image.convert("RGB")
    return image.copy()


def _save_with_target(
    image: Image.Image,
    output_path: Path,
    output_format: str,
    target_bytes: int | None,
) -> Image.Image:
    quality = 85 if target_bytes is None else 95
    current = image

    _save(current, output_path, output_format, quality)
    if target_bytes is None:
        return current

    if output_format in QUALITY_FORMATS:
        while output_path.stat().st_size > target_bytes and quality > 10:
            quality -= 5
            _save(current, output_path, output_format, quality)

    while output_path.stat().st_size > target_bytes and min(current.size) > MIN_DIMENSION:
        new_size = (
            max(MIN_DIMENSION, int(current.width * 0.9)),
            max(MIN_DIMENSION, int(current.height * 0.9)),
        )
        if new_size == current.size:
            break

        current = current.resize(new_size, Image.Resampling.LANCZOS)
        _save(current, output_path, output_format, quality)

    return current


def _save(image: Image.Image, output_path: Path, output_format: str, quality: int) -> None:
    options: dict[str, int | bool] = {"optimize": True}
    if output_format == "PNG":
        options["compress_level"] = 9
    elif output_format in QUALITY_FORMATS:
        options["quality"] = quality

    image.save(output_path, format=output_format, **options)
