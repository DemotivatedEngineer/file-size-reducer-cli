from __future__ import annotations

import contextlib
import io
import sys
import tempfile
import unittest
from pathlib import Path

from PIL import Image
from pypdf import PdfReader, PdfWriter

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from size_reducer_cli.cli import main
from size_reducer_cli.reducer import compress_file, compress_image, compress_pdf


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

    def test_pdf_compression_creates_readable_pdf(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            pdf_path = Path(tmp) / "document.pdf"
            writer = PdfWriter()
            writer.add_blank_page(width=72, height=72)
            with pdf_path.open("wb") as pdf_file:
                writer.write(pdf_file)

            result = compress_pdf(pdf_path)

            self.assertEqual(result.output_path.name, "document_compressed.pdf")
            self.assertEqual(result.output_format, "PDF")
            self.assertEqual(result.media_type, "pdf")
            self.assertGreaterEqual(len(PdfReader(result.output_path).pages), 1)

    def test_generic_dispatch_handles_pdf(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            pdf_path = Path(tmp) / "document.pdf"
            writer = PdfWriter()
            writer.add_blank_page(width=72, height=72)
            with pdf_path.open("wb") as pdf_file:
                writer.write(pdf_file)

            result = compress_file(pdf_path)

            self.assertEqual(result.media_type, "pdf")
            self.assertTrue(result.output_path.exists())

    def test_cli_dispatch_handles_pdf(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            pdf_path = Path(tmp) / "document.pdf"
            writer = PdfWriter()
            writer.add_blank_page(width=72, height=72)
            with pdf_path.open("wb") as pdf_file:
                writer.write(pdf_file)
            stdout = io.StringIO()

            with contextlib.redirect_stdout(stdout):
                code = main([str(pdf_path)])

            self.assertEqual(code, 0)
            self.assertIn("Optimized PDF saved", stdout.getvalue())
            self.assertTrue((Path(tmp) / "document_compressed.pdf").exists())

    def test_existing_pdf_output_is_not_overwritten(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            pdf_path = Path(tmp) / "document.pdf"
            existing = Path(tmp) / "document_compressed.pdf"
            writer = PdfWriter()
            writer.add_blank_page(width=72, height=72)
            with pdf_path.open("wb") as pdf_file:
                writer.write(pdf_file)
            existing.write_bytes(b"keep me")

            result = compress_pdf(pdf_path)

            self.assertEqual(existing.read_bytes(), b"keep me")
            self.assertEqual(result.output_path.name, "document_compressed_1.pdf")

    def test_unsupported_extension_returns_non_zero(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            text_path = Path(tmp) / "notes.txt"
            text_path.write_text("not reducible", encoding="utf-8")
            stdout = io.StringIO()

            with contextlib.redirect_stdout(stdout):
                code = main([str(text_path)])

            self.assertEqual(code, 1)
            self.assertIn("Unsupported file format", stdout.getvalue())

    @unittest.skipUnless("HEIF" in Image.registered_extensions().values(), "HEIF support unavailable")
    def test_heic_optimization_creates_heic_file(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            image_path = Path(tmp) / "photo.heic"
            Image.new("RGB", (120, 120), "green").save(image_path, format="HEIF")

            result = compress_image(image_path)

            self.assertTrue(result.output_path.exists())
            self.assertEqual(result.output_path.name, "photo_compressed.heic")
            self.assertEqual(result.output_format, "HEIF")
            self.assertEqual(result.media_type, "image")

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
        self.assertIn("size-reducer photo.heic", readme)
        self.assertIn("size-reducer document.pdf", readme)
        self.assertNotIn("reducers/img-reducer.py", readme)


if __name__ == "__main__":
    unittest.main()
