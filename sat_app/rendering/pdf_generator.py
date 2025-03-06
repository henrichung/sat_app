"""
PDF Generator module for the SAT Question Bank application.

This module is responsible for:
- Generating PDF worksheets from question data
- Supporting LaTeX equation rendering
- Embedding images
- Creating formatted worksheet layouts
"""
import os
import re
import tempfile
from typing import Dict, Any, List, Optional, Tuple
from datetime import datetime
import io
import hashlib

from reportlab.lib import colors
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.pagesizes import letter
from reportlab.lib.units import inch
from reportlab.platypus import (
    SimpleDocTemplate, Paragraph, Spacer, Image, PageBreak,
    Table, TableStyle, ListFlowable, ListItem
)
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont

# Force PIL to avoid problematic libraries BEFORE importing
import os
os.environ['PILLOW_DISABLE_JPEG2K'] = '1'  # Disable JPEG2000 support
os.environ['PILLOW_DISABLE_LIBTIFF'] = '1' # Disable TIFF library (causes symbol errors)
os.environ['PILLOW_DISABLE_WEBP'] = '1'    # Disable WebP support
os.environ['PILLOW_DISABLE_OPENEXR'] = '1' # Disable OpenEXR

# Use a safe approach for PIL imports
try:
    # First try the direct import with disabled libraries
    from PIL import Image as PILImage
    print("Using direct PIL import with disabled extensions in pdf_generator")
except ImportError as e:
    print(f"Warning: PIL import failed: {e}, using safe wrapper")
    # Fall back to our safe wrapper
    from sat_app.rendering.safe_pillow import get_image
    PILImage = get_image()

# For LaTeX rendering
import sympy
import matplotlib
import matplotlib.pyplot as plt
from matplotlib import mathtext
from matplotlib.font_manager import FontProperties

from ..config.config_manager import ConfigManager
from ..utils.logger import get_logger


class LatexEquationRenderer:
    """
    Handles rendering of LaTeX equations within PDF documents.
    
    Uses SymPy and Matplotlib to render LaTeX equations as high-quality
    images that can be embedded in PDFs.
    """
    
    def __init__(self, config_manager: Optional[ConfigManager] = None):
        """
        Initialize the LaTeX equation renderer.
        
        Args:
            config_manager: Optional configuration manager for customizing rendering
        """
        self.logger = get_logger(__name__)
        self.config_manager = config_manager
        
        # Create a cache directory for rendered equations
        self.cache_dir = os.path.join(
            tempfile.gettempdir(), 
            'sat_app_latex_cache'
        )
        os.makedirs(self.cache_dir, exist_ok=True)
        
        # Configure matplotlib for non-interactive backend
        matplotlib.use('Agg')
        
        # Configure default font properties for equations - smaller font size
        self.font_props = FontProperties(size=10)
        
        # Lower DPI for more proportional equations relative to text
        self.dpi = 150  # Reduced from 300 to create more proportional equations
        
        # Setup equation cache to avoid re-rendering the same equations
        self.equation_cache = {}
        
    def render_latex(self, text: str) -> List[Tuple[str, str, str]]:
        """
        Identify LaTeX equations in text and prepare them for rendering.
        
        Args:
            text: Text containing LaTeX equations (e.g., $x^2 + y^2 = z^2$)
            
        Returns:
            List of tuples containing (equation_text, placeholder, image_path)
            where image_path is the path to the rendered equation image
        """
        # Find all LaTeX equations (enclosed in $ signs)
        equations = []
        pattern = r'\$(.*?)\$'
        
        # Create temp dir for this batch of equations if it doesn't exist
        batch_dir = os.path.join(self.cache_dir, f"batch_{int(datetime.now().timestamp())}")
        os.makedirs(batch_dir, exist_ok=True)
        
        for match in re.finditer(pattern, text):
            equation = match.group(1)
            placeholder = f"[EQUATION_{len(equations)}]"
            
            # Generate a unique filename based on equation content
            equation_hash = hashlib.md5(equation.encode('utf-8')).hexdigest()
            image_path = os.path.join(batch_dir, f"eq_{equation_hash}.png")
            
            # Render the equation to an image
            rendered_path = self.render_equation_image(equation, image_path)
            
            equations.append((equation, placeholder, rendered_path))
            
        return equations
    
    def replace_with_placeholders(self, text: str, equations: List[Tuple[str, str, str]]) -> str:
        """
        Replace LaTeX equations with placeholders.
        
        Args:
            text: Original text with LaTeX equations
            equations: List of (equation, placeholder, image_path) tuples
            
        Returns:
            Text with equations replaced by placeholders
        """
        result = text
        for equation, placeholder, _ in equations:
            result = result.replace(f"${equation}$", placeholder)
        return result

    def render_equation_image(self, equation: str, output_path: str) -> Optional[str]:
        """
        Render a LaTeX equation to an image using SymPy and Matplotlib.
        
        Supports various LaTeX math commands and symbols. The rendered equation
        is saved as a PNG image that can be embedded in the PDF.
        
        Args:
            equation: LaTeX equation string
            output_path: Path to save the rendered image
            
        Returns:
            Path to the rendered image, or None if rendering failed
        """
        # Check if this equation is already in the cache
        equation_hash = hashlib.md5(equation.encode('utf-8')).hexdigest()
        if equation_hash in self.equation_cache and os.path.exists(self.equation_cache[equation_hash]):
            # Copy from cache to the requested output path
            try:
                img = PILImage.open(self.equation_cache[equation_hash])
                img.save(output_path)
                return output_path
            except Exception:
                # If the cached file is corrupt, continue with rendering
                pass
        
        try:
            # Method 1: Use SymPy for standard math equations
            try:
                # Try to use sympy first which handles most math equations well
                with tempfile.NamedTemporaryFile(suffix='.png') as tmp:
                    sympy.preview(
                        f"${equation}$", 
                        viewer='file', 
                        filename=tmp.name, 
                        dvioptions=['-D', str(self.dpi)],
                        euler=False  # Use Computer Modern fonts
                    )
                    # Copy the temporary file to the output path
                    img = PILImage.open(tmp.name)
                    
                    # Resize the image to be more proportional to text
                    # This helps with the large equation issue
                    original_width, original_height = img.size
                    scale_factor = 0.7  # Reduce to 70% of original size
                    new_width = int(original_width * scale_factor)
                    new_height = int(original_height * scale_factor)
                    # Use safer resizing methods with fallbacks
                    try:
                        # Try LANCZOS first (highest quality)
                        resized_img = img.resize((new_width, new_height), PILImage.LANCZOS)
                    except (AttributeError, ImportError) as e:
                        print(f"Warning: LANCZOS resize failed, trying BICUBIC: {e}")
                        try:
                            # Fall back to BICUBIC
                            resized_img = img.resize((new_width, new_height), PILImage.BICUBIC)
                        except (AttributeError, ImportError) as e:
                            print(f"Warning: BICUBIC resize failed, using simple resize: {e}")
                            # Last resort simple resize
                            resized_img = img.resize((new_width, new_height))
                    
                    # Add minimal padding and white background
                    padded = PILImage.new(
                        'RGBA', 
                        (resized_img.width + 6, resized_img.height + 6), 
                        (255, 255, 255, 255)
                    )
                    padded.paste(resized_img, (3, 3))
                    padded.save(output_path)
                    # Add to cache
                    self.equation_cache[equation_hash] = output_path
                    return output_path
            except Exception as e:
                self.logger.warning(f"SymPy rendering failed, falling back to Matplotlib: {str(e)}")
            
            # Method 2: Fallback to Matplotlib for more complex formatting
            fig = plt.figure(figsize=(5, 0.8), dpi=self.dpi)  # Smaller figure size
            fig.patch.set_alpha(0)
            
            # Render the equation using matplotlib's mathtext with smaller font
            plt.text(
                0.5, 0.5, f"${equation}$",
                fontsize=11,  # Reduced from 14
                ha='center', 
                va='center',
                fontproperties=self.font_props
            )
            
            # Remove axes and whitespace
            plt.axis('off')
            plt.tight_layout(pad=0.1)
            
            # Save to the output path
            plt.savefig(output_path, transparent=True, bbox_inches='tight', pad_inches=0.1, dpi=self.dpi)
            plt.close(fig)
            
            # Add to cache
            self.equation_cache[equation_hash] = output_path
            self.logger.info(f"Rendered equation: {equation} to {output_path}")
            return output_path
            
        except Exception as e:
            self.logger.error(f"Error rendering equation '{equation}': {str(e)}")
            
            # If both rendering methods fail, create a simple text-based image as fallback
            try:
                # Create a simple text image as fallback
                fig = plt.figure(figsize=(8, 1), dpi=150)
                plt.text(0.5, 0.5, f"Error: {equation}", color='red', ha='center', va='center')
                plt.axis('off')
                plt.savefig(output_path, bbox_inches='tight')
                plt.close(fig)
                return output_path
            except:
                self.logger.error(f"Even fallback rendering failed for '{equation}'")
                return None
                
    def render_for_preview(self, equation: str) -> Optional[bytes]:
        """
        Render a LaTeX equation for UI preview.
        
        This method creates a PNG image in memory and returns it as bytes
        which can be used directly by PyQt widgets for display.
        
        Args:
            equation: LaTeX equation string
            
        Returns:
            Bytes containing the PNG image data, or None if rendering failed
        """
        try:
            # For UI previews, use the same rendering settings for consistency
            # but with a slightly higher DPI to ensure clarity in the UI
            ui_dpi = self.dpi * 1.2  # Slightly higher DPI for UI preview
            
            # Create a unique cache key that includes UI-specific parameters
            equation_hash = hashlib.md5(f"{equation}_ui_preview".encode('utf-8')).hexdigest()
            
            # Check if we already have this UI preview cached
            preview_path = os.path.join(self.cache_dir, f"ui_preview_{equation_hash}.png")
            if os.path.exists(preview_path):
                with open(preview_path, 'rb') as f:
                    return f.read()
            
            # If not in cache, render a special UI preview version
            try:
                # Try with SymPy first
                with tempfile.NamedTemporaryFile(suffix='.png') as tmp:
                    sympy.preview(
                        f"${equation}$", 
                        viewer='file', 
                        filename=tmp.name, 
                        dvioptions=['-D', str(int(ui_dpi))],
                        euler=False
                    )
                    # Process the rendered image for UI display
                    img = PILImage.open(tmp.name)
                    
                    # Resize for UI display - maintain the scale factor from render_equation_image
                    original_width, original_height = img.size
                    scale_factor = 0.8  # Slightly larger than in PDF for better UI visibility
                    new_width = int(original_width * scale_factor)
                    new_height = int(original_height * scale_factor)
                    # Use safer resizing methods with fallbacks
                    try:
                        # Try LANCZOS first (highest quality)
                        resized_img = img.resize((new_width, new_height), PILImage.LANCZOS)
                    except (AttributeError, ImportError) as e:
                        print(f"Warning: LANCZOS resize failed, trying BICUBIC: {e}")
                        try:
                            # Fall back to BICUBIC
                            resized_img = img.resize((new_width, new_height), PILImage.BICUBIC)
                        except (AttributeError, ImportError) as e:
                            print(f"Warning: BICUBIC resize failed, using simple resize: {e}")
                            # Last resort simple resize
                            resized_img = img.resize((new_width, new_height))
                    
                    # Add minimal padding for UI display
                    padded = PILImage.new(
                        'RGBA', 
                        (resized_img.width + 6, resized_img.height + 6), 
                        (255, 255, 255, 255)
                    )
                    padded.paste(resized_img, (3, 3))
                    padded.save(preview_path)
                    
                    with open(preview_path, 'rb') as f:
                        return f.read()
            except Exception:
                # Fall back to matplotlib
                fig = plt.figure(figsize=(5, 0.8), dpi=ui_dpi)
                fig.patch.set_alpha(0)
                
                plt.text(
                    0.5, 0.5, f"${equation}$",
                    fontsize=10,
                    ha='center', 
                    va='center',
                    fontproperties=self.font_props
                )
                
                plt.axis('off')
                plt.tight_layout(pad=0.1)
                
                plt.savefig(preview_path, transparent=True, bbox_inches='tight', pad_inches=0.1, dpi=ui_dpi)
                plt.close(fig)
                
                with open(preview_path, 'rb') as f:
                    return f.read()
                    
            return None
            
        except Exception as e:
            self.logger.error(f"Error rendering equation preview: {str(e)}")
            return None


class PDFGenerator:
    """
    Generates PDF worksheets from question data.
    
    Key features:
    - Formats questions and answer choices in a readable layout
    - Embeds images for questions and answers
    - Supports LaTeX equation rendering
    - Generates optional answer key
    """
    
    def __init__(self, config_manager: ConfigManager):
        """
        Initialize the PDF generator.
        
        Args:
            config_manager: Configuration manager for retrieving app settings
        """
        self.logger = get_logger(__name__)
        self.config_manager = config_manager
        self.worksheets_dir = config_manager.get_worksheets_dir()
        self.latex_renderer = LatexEquationRenderer()
        
        # Reference to worksheet generator for updating worksheet records
        # This will be set by the main window after initialization
        self.worksheet_generator = None
        
        # Initialize styles
        self.styles = getSampleStyleSheet()
        self._setup_styles()

    def _setup_styles(self) -> None:
        """Setup custom styles for PDF generation."""
        # Modify existing Title style instead of adding it
        self.styles['Title'].fontSize = 16
        self.styles['Title'].spaceAfter = 12
        
        # Add custom styles
        self.styles.add(
            ParagraphStyle(
                'QuestionText',
                parent=self.styles['Normal'],
                fontSize=12,
                spaceAfter=6,
                leading=14
            )
        )
        
        self.styles.add(
            ParagraphStyle(
                'AnswerChoice',
                parent=self.styles['Normal'],
                fontSize=11,
                leftIndent=20,
                leading=13
            )
        )
        
        self.styles.add(
            ParagraphStyle(
                'Description',
                parent=self.styles['Normal'],
                fontSize=10,
                spaceAfter=10,
                leading=12
            )
        )
        
        self.styles.add(
            ParagraphStyle(
                'AnswerKey',
                parent=self.styles['Heading2'],
                fontSize=14,
                spaceAfter=6
            )
        )

    def generate_pdf(self, pdf_data: Dict[str, Any], output_path: Optional[str] = None) -> str:
        """
        Generate a PDF worksheet from the provided data.
        
        Args:
            pdf_data: Dictionary containing worksheet data, including:
                - title: Worksheet title
                - description: Worksheet description
                - questions: List of questions with their properties
                - include_answer_key: Whether to include an answer key
                - answer_key: Dictionary mapping question IDs to correct answers
            output_path: Optional path to save the PDF. If not provided, 
                         a default path in the worksheets directory will be used.
                         
        Returns:
            Path to the generated PDF file
        """
        try:
            # Determine output path if not provided
            if not output_path:
                timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
                filename = f"worksheet_{timestamp}.pdf"
                output_path = os.path.join(self.worksheets_dir, filename)
            
            # Create directory if it doesn't exist
            os.makedirs(os.path.dirname(output_path), exist_ok=True)
            
            # Create PDF document
            doc = SimpleDocTemplate(
                output_path,
                pagesize=letter,
                rightMargin=72,
                leftMargin=72,
                topMargin=72,
                bottomMargin=72
            )
            
            # Build content
            elements = []
            
            # Add title
            title = pdf_data.get('title', 'Untitled Worksheet')
            elements.append(Paragraph(title, self.styles['Title']))
            elements.append(Spacer(1, 0.1 * inch))
            
            # Add description if available
            description = pdf_data.get('description', '')
            if description:
                elements.append(Paragraph(description, self.styles['Description']))
                elements.append(Spacer(1, 0.2 * inch))
            
            # Add questions
            questions = pdf_data.get('questions', [])
            for i, question in enumerate(questions):
                # Add question elements to the PDF
                self._add_question(elements, question, i+1)
                
                # Add space between questions
                if i < len(questions) - 1:
                    elements.append(Spacer(1, 0.3 * inch))
            
            # Add answer key if requested
            if pdf_data.get('include_answer_key', False):
                elements.append(PageBreak())
                elements.append(Paragraph("Answer Key", self.styles['AnswerKey']))
                elements.append(Spacer(1, 0.2 * inch))
                
                # Build answer key
                answer_key = pdf_data.get('answer_key', {})
                answer_data = []
                
                for i, question in enumerate(questions):
                    question_id = str(question.get('id', ''))
                    answer = answer_key.get(question_id, '')
                    answer_data.append([f"{i+1}.", answer])
                
                # Create answer key table
                if answer_data:
                    # Create a table with 5 columns (to show answers in rows of 5)
                    table_data = []
                    row = []
                    
                    for i, (num, answer) in enumerate(answer_data):
                        row.extend([num, answer])
                        if (i + 1) % 5 == 0 or i == len(answer_data) - 1:
                            # Pad the row if needed
                            while len(row) < 10:
                                row.extend(['', ''])
                            table_data.append(row)
                            row = []
                    
                    answer_table = Table(
                        table_data,
                        colWidths=[0.3*inch, 0.5*inch] * 5,
                        style=TableStyle([
                            ('GRID', (0, 0), (-1, -1), 0.5, colors.black),
                            ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
                            ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
                            ('FONTSIZE', (0, 0), (-1, -1), 10),
                        ])
                    )
                    elements.append(answer_table)
            
            # Build the PDF
            doc.build(elements)
            
            # If we have a worksheet generator and the worksheet has an ID, update its PDF path
            worksheet_id = pdf_data.get('worksheet_id')
            if worksheet_id and self.worksheet_generator and self.worksheet_generator.worksheet_repository:
                try:
                    # Get the worksheet
                    worksheet = self.worksheet_generator.worksheet_repository.get_worksheet(worksheet_id)
                    if worksheet:
                        # Update the PDF path
                        worksheet.pdf_path = output_path
                        self.worksheet_generator.worksheet_repository.update_worksheet(worksheet)
                        self.logger.info(f"Updated worksheet {worksheet_id} with PDF path: {output_path}")
                except Exception as e:
                    self.logger.error(f"Error updating worksheet PDF path: {str(e)}")
            
            self.logger.info(f"Generated worksheet PDF: {output_path}")
            return output_path
            
        except Exception as e:
            self.logger.error(f"Error generating worksheet PDF: {str(e)}")
            raise
    
    def _add_question(self, elements: List, question: Dict[str, Any], number: int) -> None:
        """
        Add a question to the PDF elements list.
        
        Args:
            elements: List of PDF elements to append to
            question: Dictionary containing question data
            number: Question number
        """
        # Question number and text
        question_text = question.get('text', '')
        
        # Process any LaTeX equations in the question text
        equations = self.latex_renderer.render_latex(question_text)
        
        if equations:
            # If we have equations, we need to split the text at equation points
            # and add text and equations in sequence
            parts = self._split_text_at_equations(question_text, equations)
            
            # Add the question number paragraph first
            elements.append(Paragraph(f"<b>{number}.</b>", self.styles['QuestionText']))
            
            # Add each text part and its corresponding equation
            for part in parts:
                if part['type'] == 'text' and part['content'].strip():
                    elements.append(Paragraph(part['content'], self.styles['QuestionText']))
                elif part['type'] == 'equation' and part['image_path']:
                    # Add equation image
                    if os.path.exists(part['image_path']):
                        self._add_single_equation_image(elements, part['image_path'])
        else:
            # No equations, just add the text directly
            question_para = Paragraph(f"<b>{number}.</b> {question_text}", self.styles['QuestionText'])
            elements.append(question_para)
        
        # Add question image if available
        image_path = question.get('image_path')
        if image_path and os.path.exists(image_path):
            try:
                # Get image dimensions and resize if needed
                img = PILImage.open(image_path)
                width, height = img.size
                
                # Set maximum width and height
                max_width = 4 * inch
                max_height = 3 * inch
                
                # Calculate aspect ratio
                aspect = width / height
                
                if width > max_width:
                    width = max_width
                    height = width / aspect
                
                if height > max_height:
                    height = max_height
                    width = height * aspect
                
                # Add the image
                img = Image(image_path, width=width, height=height)
                elements.append(img)
                elements.append(Spacer(1, 0.1 * inch))
                
            except Exception as e:
                self.logger.error(f"Error adding question image: {str(e)}")
        
        # Add answer choices
        answers = question.get('answers', [])
        for answer in answers:
            letter = answer.get('letter', '')
            text = answer.get('text', '')
            
            # Process any LaTeX equations in the answer text
            answer_equations = self.latex_renderer.render_latex(text)
            
            if answer_equations:
                # If we have equations, we need to split the text at equation points
                # and add text and equations in sequence
                parts = self._split_text_at_equations(text, answer_equations)
                
                # Add the answer letter paragraph first
                elements.append(Paragraph(f"<b>{letter}.</b>", self.styles['AnswerChoice']))
                
                # Add each text part and its corresponding equation
                for part in parts:
                    if part['type'] == 'text' and part['content'].strip():
                        elements.append(Paragraph(part['content'], self.styles['AnswerChoice']))
                    elif part['type'] == 'equation' and part['image_path']:
                        # Add equation image with indentation
                        if os.path.exists(part['image_path']):
                            self._add_single_equation_image(elements, part['image_path'], indent=True)
            else:
                # No equations, just add the text directly
                answer_para = Paragraph(f"<b>{letter}.</b> {text}", self.styles['AnswerChoice'])
                elements.append(answer_para)
            
            # Add answer image if available
            image_path = answer.get('image_path')
            if image_path and os.path.exists(image_path):
                try:
                    # Get image dimensions and resize if needed
                    img = PILImage.open(image_path)
                    width, height = img.size
                    
                    # Set maximum width and height (slightly smaller than question images)
                    max_width = 3 * inch
                    max_height = 2 * inch
                    
                    # Calculate aspect ratio
                    aspect = width / height
                    
                    if width > max_width:
                        width = max_width
                        height = width / aspect
                    
                    if height > max_height:
                        height = max_height
                        width = height * aspect
                    
                    # Add the image with indent
                    img = Image(image_path, width=width, height=height)
                    
                    # Create a table for proper indentation
                    image_table = Table([[Spacer(1, 0.2 * inch), img]], colWidths=[0.5*inch, None])
                    elements.append(image_table)
                    elements.append(Spacer(1, 0.05 * inch))
                    
                except Exception as e:
                    self.logger.error(f"Error adding answer image: {str(e)}")
            
            elements.append(Spacer(1, 0.05 * inch))
            
    def _split_text_at_equations(self, text: str, equations: List[Tuple[str, str, str]]) -> List[Dict]:
        """
        Split text into parts, with equation placeholders replaced by their images.
        
        Args:
            text: Original text with LaTeX equations
            equations: List of (equation, placeholder, image_path) tuples
            
        Returns:
            List of dictionaries with type ('text' or 'equation') and content
        """
        result = []
        remaining_text = text
        
        # Sort equations by their position in the text
        positions = []
        for eq, placeholder, image_path in equations:
            eq_text = f"${eq}$"
            pos = text.find(eq_text)
            if pos >= 0:
                positions.append((pos, eq_text, image_path))
        
        # Sort by position
        positions.sort(key=lambda x: x[0])
        
        # Go through equations in order of appearance
        last_end = 0
        for pos, eq_text, image_path in positions:
            # Add text before the equation
            if pos > last_end:
                result.append({
                    'type': 'text',
                    'content': text[last_end:pos]
                })
            
            # Add the equation
            result.append({
                'type': 'equation',
                'content': eq_text,
                'image_path': image_path
            })
            
            last_end = pos + len(eq_text)
        
        # Add any remaining text after the last equation
        if last_end < len(text):
            result.append({
                'type': 'text',
                'content': text[last_end:]
            })
        
        return result
    
    def _add_single_equation_image(self, elements: List, image_path: str, indent: bool = False) -> None:
        """
        Add a single equation image to the PDF elements.
        
        Args:
            elements: List of PDF elements to append to
            image_path: Path to the equation image
            indent: Whether to indent the equation (for answer choices)
        """
        try:
            # Get image dimensions
            img = PILImage.open(image_path)
            width, height = img.size
            
            # Calculate appropriate size based on image dimensions
            # Use a more reasonable max width to match text size better
            # Reduced max width to better align with text size
            max_width = 2.5 * inch if not indent else 2.0 * inch
            aspect = width / height
            
            if width > max_width:
                width = max_width
                height = width / aspect
            
            # Create inline-style rendering for equations
            # This helps equations flow better with surrounding text
            reportlab_img = Image(image_path, width=width, height=height)
            
            # Create special styling to make equations appear more inline
            # Adjust vertical alignment to better match text
            if indent:
                # Add indentation for answer choices 
                table = Table([[Spacer(1, 0.2 * inch), reportlab_img]], 
                              colWidths=[0.5*inch, None])
                elements.append(table)
            else:
                # For question text, make equations appear more inline with text
                elements.append(reportlab_img)
            
            # Reduced spacing after equations
            elements.append(Spacer(1, 0.03 * inch))
        except Exception as e:
            self.logger.error(f"Error adding equation image: {str(e)}")
            
    def _add_equation_images(self, elements: List, equations: List[Tuple[str, str, str]], 
                             indent: bool = False) -> None:
        """
        Add rendered equation images to the PDF elements.
        
        Args:
            elements: List of PDF elements to append to
            equations: List of (equation, placeholder, image_path) tuples
            indent: Whether to indent the equations (for answer choices)
        """
        if not equations:
            return
            
        for _, _, image_path in equations:
            if image_path and os.path.exists(image_path):
                self._add_single_equation_image(elements, image_path, indent)