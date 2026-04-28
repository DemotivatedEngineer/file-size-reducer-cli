# Image Size Reducer CLI

A lightweight Command Line Interface (CLI) tool written in Python to easily reduce image file sizes. It uses the Pillow library to intelligently downscale and optimize images, ensuring they meet a target file size while retaining the best possible quality.

## Features
- **EXIF Aware:** Automatically fixes image orientation based on camera EXIF data before processing.
- **Target Sizing:** Compresses images to a specific maximum file size (in KB).
- **Smart Compression:** Uses a two-pass approach (Quality reduction followed by LANCZOS downsampling) if a file size target is hard to reach.
- **Safe Saving:** Generates a new file with a `_compressed` suffix so your original files are never accidentally overwritten.

## Requirements
- Python 3.6+
- Pillow

## Installation

1. **Clone the repository:**
   ```bash
   git clone https://github.com/yourusername/SizeReducerCLI.git
   cd SizeReducerCLI
   ```

2. **Create a virtual environment (Recommended):**
   ```bash
   python3 -m venv venv
   source venv/bin/activate
   ```

3. **Install dependencies:**
   ```bash
   pip install -r requirements.txt
   ```

## Usage

Run the script via Python, passing the image path and an optional maximum size in KB.

**Basic Optimization (Standard compression without a strict limit):**
```bash
python img-reducer.py my_photo.jpg
```

**Targeting a specific max size (e.g., under 500 KB):**
```bash
python img-reducer.py my_photo.jpg -m 500
```