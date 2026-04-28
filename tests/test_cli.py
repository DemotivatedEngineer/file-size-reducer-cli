from __future__ import annotations

import contextlib
import io
import sys
import tempfile
import unittest
from pathlib import Path

from PIL import Image

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from size_reducer_cli.cli import main
from size_reducer_cli.reducer import compress_image


class CliTests(unittest.TestCase):
    def test_help_returns_success(self) -> None:
        stdout = io.StringIO()
        with self.assertRaises(SystemExit) as raised:
            with contextlib.redirect_stdout(stdout):
                main(["--help"])

        self.assertEqual(raised.exception.code, 0)
        self.assertIn("file_path", stdout.getvalue())

    def test_missing_file_returns_non_zero(self) -> None:
        stdout = io.StringIO()
        with contextlib.redirect_stdout(stdout):
            code = main(["missing.jpg"])

        self.assertEqual(code, 1)
        self.assertIn("not found", stdout.getvalue())

    def test_invalid_max_size_exits(self) -> None:
        stderr = io.StringIO()
        with self.assertRaises(SystemExit) as raised:
            with contextlib.redirect_stderr(stderr):
                main(["photo.jpg", "--max-size", "0"])

        self.assertEqual(raised.exception.code, 2)
        self.assertIn("positive integer", stderr.getvalue())

    def test_jpeg_optimization_creates_compressed_file(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            image_path = Path(tmp) / "photo.jpg"
            Image.new("RGB", (120, 120), "red").save(image_path, format="JPEG")

            result = compress_image(image_path)

            self.assertTrue(result.output_path.exists())
            self.assertEqual(result.output_path.name, "photo_compressed.jpg")
            self.assertEqual(result.output_format, "JPEG")
            self.assertTrue(result.target_met)

    def test_jpeg_target_size_is_met_when_feasible(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            image_path = Path(tmp) / "large.jpg"
            Image.effect_noise((900, 900), 80).convert("RGB").save(
                image_path, format="JPEG", quality=95
            )

            result = compress_image(image_path, max_size_kb=80)

            self.assertLessEqual(result.output_path.stat().st_size, 80 * 1024)
            self.assertTrue(result.target_met)

    def test_png_alpha_is_preserved(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            image_path = Path(tmp) / "icon.png"
            Image.new("RGBA", (64, 64), (255, 0, 0, 100)).save(
                image_path, format="PNG"
            )

            result = compress_image(image_path)

            with Image.open(result.output_path) as output:
                self.assertEqual(output.mode, "RGBA")
                self.assertEqual(output.format, "PNG")

    def test_existing_output_is_not_overwritten(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            image_path = Path(tmp) / "photo.jpg"
            existing = Path(tmp) / "photo_compressed.jpg"
            Image.new("RGB", (64, 64), "blue").save(image_path, format="JPEG")
            existing.write_bytes(b"keep me")

            result = compress_image(image_path)

            self.assertEqual(existing.read_bytes(), b"keep me")
            self.assertEqual(result.output_path.name, "photo_compressed_1.jpg")

    def test_readme_uses_packaged_cli_command(self) -> None:
        readme = (ROOT / "README.md").read_text(encoding="utf-8")

        self.assertIn("size-reducer image.jpg", readme)
        self.assertNotIn("reducers/img-reducer.py", readme)


if __name__ == "__main__":
    unittest.main()
