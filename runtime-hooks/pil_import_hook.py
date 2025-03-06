"""
Runtime hook to ensure PIL/Pillow is properly initialized
"""
import os
import sys

# Force PIL to avoid problematic libraries
os.environ['PILLOW_DISABLE_JPEG2K'] = '1'  # Disable JPEG2000 support
os.environ['PILLOW_DISABLE_LIBTIFF'] = '1' # Disable TIFF library
os.environ['PILLOW_DISABLE_WEBP'] = '1'    # Disable WebP support
os.environ['PILLOW_DISABLE_OPENEXR'] = '1' # Disable OpenEXR
os.environ['PILLOW_DISABLE_ACCELERATION'] = '1'

# Pre-import PIL to initialize it properly
try:
    print("Pre-importing PIL from runtime hook...")
    import PIL
    import PIL.Image
    print(f"PIL successfully imported: {PIL.__file__}")
    print(f"PIL.Image successfully imported: {PIL.Image.__file__}")
except Exception as e:
    print(f"Warning: Error pre-importing PIL: {e}")