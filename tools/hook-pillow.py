"""
This is a hook file for PyInstaller to properly include Pillow/PIL
"""
from PyInstaller.utils.hooks import collect_dynamic_libs, collect_submodules

# Collect all PIL/Pillow submodules
hiddenimports = collect_submodules('PIL')

# Add core modules explicitly
hiddenimports.extend([
    'PIL._imaging',
    'PIL.Image',
    'PIL.ImageDraw',
    'PIL.ImageFont',
    'PIL.JpegImagePlugin',
    'PIL.PngImagePlugin',
    'PIL.BmpImagePlugin',
    'PIL.GifImagePlugin',
    'PIL.PpmImagePlugin',
    'PIL.TiffImagePlugin',
])

# Collect binary dependencies
binaries = collect_dynamic_libs('PIL')