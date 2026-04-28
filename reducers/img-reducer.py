#!/usr/bin/env python3
import os
import argparse
from PIL import Image, ImageOps

def compress_image(input_path, max_size_kb=None):
    # Check if the file exists
    if not os.path.exists(input_path):
        print(f"❌ Error: File '{input_path}' not found.")
        return

    # Generate the new filename (e.g., image.jpg -> image_compressed.jpg)
    file_name, ext = os.path.splitext(input_path)
    output_path = f"{file_name}_compressed{ext}"

    try:
        with Image.open(input_path) as img:
            # Correct image orientation based on EXIF data before processing
            img = ImageOps.exif_transpose(img)

            # Handle formats that don't support alpha channels when saving as JPEG
            if img.mode in ("RGBA", "P") and ext.lower() in ('.jpg', '.jpeg'):
                img = img.convert("RGB")

            if max_size_kb is not None:
                target_bytes = max_size_kb * 1024
                quality = 95
                step = 5
                
                # First pass: try reducing quality (Works best for JPEG/WebP)
                img.save(output_path, optimize=True, quality=quality)
                
                while os.path.getsize(output_path) > target_bytes and quality > 10:
                    quality -= step
                    img.save(output_path, optimize=True, quality=quality)
                
                # Second pass: If it's STILL too big (or it's a PNG which ignores 'quality'), reduce dimensions
                current_img = img
                scale_factor = 0.9
                
                while os.path.getsize(output_path) > target_bytes and current_img.size[0] > 100:
                    new_width = int(current_img.size[0] * scale_factor)
                    new_height = int(current_img.size[1] * scale_factor)
                    
                    # Resize using LANCZOS for high-quality downsampling
                    current_img = current_img.resize((new_width, new_height), Image.Resampling.LANCZOS)
                    current_img.save(output_path, optimize=True, quality=quality)
                
                final_size = os.path.getsize(output_path) / 1024
                if final_size > max_size_kb:
                    print(f"⚠️ Warning: Reached minimum dimensions. Lowest size achieved: {final_size:.2f} KB")
                else:
                    print(f"✅ Success! Compressed image saved to '{output_path}' ({final_size:.2f} KB)")

            else:
                # Default behavior if no max size is provided (General optimization)
                img.save(output_path, optimize=True, quality=85)
                final_size = os.path.getsize(output_path) / 1024
                print(f"✅ Success! Optimized image saved to '{output_path}' ({final_size:.2f} KB)")

    except Exception as e:
        print(f"❌ An error occurred while processing the image: {e}")

def main():
    # Setup Argument Parser
    parser = argparse.ArgumentParser(
        description="A lightweight CLI tool to reduce image file size."
    )
    parser.add_argument(
        "file_path", 
        help="Path to the input image file (e.g., photo.jpg)"
    )
    parser.add_argument(
        "-m", "--max-size", 
        type=int, 
        help="Optional: Maximum target file size in KB", 
        default=None
    )

    args = parser.parse_args()
    compress_image(args.file_path, args.max_size)

if __name__ == "__main__":
    main()
