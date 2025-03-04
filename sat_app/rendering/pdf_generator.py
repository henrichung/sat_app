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
from PIL import Image as PILImage

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
        
        # Configure default font properties for equations
        self.font_props = FontProperties(size=12)
        self.dpi = 300  # High resolution for equations
        
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
                    # Add padding and white background
                    padded = PILImage.new(
                        'RGBA', 
                        (img.width + 10, img.height + 10), 
                        (255, 255, 255, 255)
                    )
                    padded.paste(img, (5, 5))
                    padded.save(output_path)
                    # Add to cache
                    self.equation_cache[equation_hash] = output_path
                    return output_path
            except Exception as e:
                self.logger.warning(f"SymPy rendering failed, falling back to Matplotlib: {str(e)}")
            
            # Method 2: Fallback to Matplotlib for more complex formatting
            fig = plt.figure(figsize=(10, 1), dpi=self.dpi)
            fig.patch.set_alpha(0)
            
            # Render the equation using matplotlib's mathtext
            plt.text(
                0.5, 0.5, f"${equation}$",
                fontsize=14, 
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
            # Use cached version if available
            equation_hash = hashlib.md5(equation.encode('utf-8')).hexdigest()
            
            if equation_hash in self.equation_cache and os.path.exists(self.equation_cache[equation_hash]):
                with open(self.equation_cache[equation_hash], 'rb') as f:
                    return f.read()
            
            # If not in cache, render to a temporary file
            with tempfile.NamedTemporaryFile(suffix='.png', delete=False) as tmp:
                output_path = tmp.name
            
            # Render the equation (this will also cache it)
            result_path = self.render_equation_image(equation, output_path)
            
            if result_path and os.path.exists(result_path):
                with open(result_path, 'rb') as f:
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
        processed_text = self.latex_renderer.replace_with_placeholders(question_text, equations)
        
        # Create the question text paragraph
        question_para = Paragraph(f"<b>{number}.</b> {processed_text}", self.styles['QuestionText'])
        elements.append(question_para)
        
        # Add rendered equation images
        self._add_equation_images(elements, equations)
        
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
            processed_answer = self.latex_renderer.replace_with_placeholders(text, answer_equations)
            
            answer_para = Paragraph(f"<b>{letter}.</b> {processed_answer}", self.styles['AnswerChoice'])
            elements.append(answer_para)
            
            # Add rendered equation images with indentation
            self._add_equation_images(elements, answer_equations, indent=True)
            
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
                try:
                    # Get image dimensions
                    img = PILImage.open(image_path)
                    width, height = img.size
                    
                    # Calculate appropriate size based on image dimensions
                    # Limit width while maintaining aspect ratio
                    max_width = 3.5 * inch if not indent else 3 * inch
                    aspect = width / height
                    
                    if width > max_width:
                        width = max_width
                        height = width / aspect
                    
                    reportlab_img = Image(image_path, width=width, height=height)
                    
                    if indent:
                        # Add indentation for answer choices
                        table = Table([[Spacer(1, 0.2 * inch), reportlab_img]], 
                                      colWidths=[0.5*inch, None])
                        elements.append(table)
                    else:
                        elements.append(reportlab_img)
                    
                    elements.append(Spacer(1, 0.05 * inch))
                except Exception as e:
                    self.logger.error(f"Error adding equation image: {str(e)}")