# Fix PIL import issue for PyInstaller
import sys
import os

# Add PIL directory to sys.modules
if hasattr(sys, '_MEIPASS'):
    os.environ['PILLOW_DISABLE_JPEG2K'] = '1'
    os.environ['PILLOW_DISABLE_LIBTIFF'] = '1'
    os.environ['PILLOW_DISABLE_WEBP'] = '1'
    os.environ['PILLOW_DISABLE_OPENEXR'] = '1'

    import PIL
    import PIL.Image