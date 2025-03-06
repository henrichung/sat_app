"""
Safe wrapper for PIL/Pillow that handles missing libraries gracefully
"""
import os
import sys

# Set environment variables to avoid using problematic libraries
os.environ['PILLOW_DISABLE_ACCELERATION'] = '1'

# Import PIL modules with fallbacks
try:
    from PIL import Image, ImageDraw, ImageFont
    HAS_PIL = True
except ImportError as e:
    print(f"Warning: PIL import error: {e}. Some image features may not work.")
    HAS_PIL = False
    
    # Create dummy classes
    class DummyImage:
        """Dummy Image class when PIL is not available"""
        @staticmethod
        def new(*args, **kwargs):
            """Return a dummy image"""
            return DummyImage()
            
        def save(self, *args, **kwargs):
            """Dummy save method"""
            print("Warning: PIL not available. Cannot save image.")
            
    # Create dummy modules
    Image = DummyImage
    ImageDraw = type('DummyImageDraw', (), {})
    ImageFont = type('DummyImageFont', (), {})

def is_available():
    """Check if PIL is available"""
    return HAS_PIL
    
def get_image():
    """Get the Image module"""
    return Image
    
def get_draw():
    """Get the ImageDraw module"""
    return ImageDraw
    
def get_font():
    """Get the ImageFont module"""
    return ImageFont