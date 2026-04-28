# Size Reducer CLI

A lightweight Python command line tool for reducing image and PDF file sizes.
It preserves the original file and writes a new file with a `_compressed` suffix.

## Features

- EXIF-aware orientation correction before processing.
- HEIC/HEIF support for iPhone photos.
- Lossless PDF stream compression with pure Python dependencies.
- Optional target size in KB.
- JPEG/WebP/HEIC quality reduction followed by LANCZOS downsampling when needed.
- PNG optimization with lossless compression and downsampling for strict targets.
- Safe output naming that avoids overwriting existing compressed files.

## Requirements

- Python 3.10+
- Pillow 10.0+
- pillow-heif
- pypdf

Supported input/output extensions are `.jpg`, `.jpeg`, `.png`, `.webp`,
`.heic`, `.heif`, and `.pdf`.

## Installation

Install directly from GitHub:

```bash
python3 -m pip install git+https://github.com/YOUR_USERNAME/SizeReducerCLI.git
```

Replace `YOUR_USERNAME` with your actual GitHub username after pushing this
repository to GitHub.

Install from a local clone:

```bash
git clone https://github.com/YOUR_USERNAME/SizeReducerCLI.git
cd SizeReducerCLI
python3 -m pip install .
```

For development, install in editable mode from the repository root:

```bash
python3 -m venv venv
source venv/bin/activate
python3 -m pip install -e .
```

Future PyPI install, after the package is published:

```bash
python3 -m pip install size-reducer-cli
```

## Usage

Optimize an image without a strict size target:

```bash
size-reducer image.jpg
```

Target a maximum size, such as 500 KB:

```bash
size-reducer image.jpg --max-size 500
```

Compress an iPhone HEIC photo while keeping HEIC output:

```bash
size-reducer photo.heic
size-reducer photo.heic --max-size 500
```

Compress a PDF with lossless pure-Python stream compression:

```bash
size-reducer document.pdf
```

The output is written beside the input as `image_compressed.jpg`. If that
file already exists, the CLI writes `image_compressed_1.jpg`, then increments
the suffix as needed.

PDF compression is lossless and portable, but reductions may be modest for
already-optimized PDFs or scanned PDFs made mostly of images.
