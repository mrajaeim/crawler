import argparse
import os
from PIL import Image

# Mapping file extensions to Pillow-supported format names
FORMAT_MAP = {
    ".jpg": "JPEG",
    ".jpeg": "JPEG",
    ".png": "PNG",
    ".bmp": "BMP",
    ".tiff": "TIFF",
    ".webp": "WEBP"
}


def convert_image(input_path, output_path):
    """Converts an image from one format to another based on file extensions."""

    # Check if input file exists
    if not os.path.isfile(input_path):
        print(f"Error: File '{input_path}' not found.")
        return

    # Extract input and output file extensions
    input_ext = os.path.splitext(input_path)[1].lower()
    output_ext = os.path.splitext(output_path)[1].lower()

    if input_ext not in FORMAT_MAP or output_ext not in FORMAT_MAP:
        print(f"Error: Unsupported file format! Supported formats: {list(FORMAT_MAP.keys())}")
        return

    try:
        # Open image and convert to RGB if output is JPG (since JPG doesn't support transparency)
        with Image.open(input_path) as img:
            if FORMAT_MAP[output_ext] == "JPEG":
                img = img.convert("RGB")

            # Save image with correct format
            img.save(output_path, FORMAT_MAP[output_ext])
            print(f"Success: Converted '{input_path}' to '{output_path}'")
    except Exception as e:
        print(f"Error: {e}")


def main():
    parser = argparse.ArgumentParser(description="Convert images between formats (JPG, PNG, WEBP, BMP, TIFF).")
    parser.add_argument("input_file", help="Path to the input image file")
    parser.add_argument("output_file", help="Path to save the converted image")

    args = parser.parse_args()
    convert_image(args.input_file, args.output_file)


if __name__ == "__main__":
    main()
