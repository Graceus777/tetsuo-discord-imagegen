import numpy as np
import io
import math
import os
import sys
from pathlib import Path
from typing import List, Optional, Tuple, Dict, Any
from PIL import Image, ImageEnhance, ImageDraw, ImageFont
from .image_processor import BaseImageProcessor

class ASCIIProcessor:
    def __init__(self):
        self.basic_chars = list(' .:-=+*#%@')
        self.detailed_chars = list(' .,:;irsXA253hMHGS#9B&@')
        self.default_font_size = 14
        self.font = self._find_monospace_font(self.default_font_size)
        self.char_width, self.char_height = self._measure_char_size(self.font)

    def _find_system_fonts(self) -> str:
        """Find system fonts directory based on OS"""
        if sys.platform == "win32":
            return r"C:\Windows\Fonts"
        elif sys.platform == "darwin":
            return "/Library/Fonts"
        else:
            return "/usr/share/fonts"

    def _find_monospace_font(self, size: int) -> ImageFont.FreeTypeFont:
        """Try to find and load a monospace font"""
        fonts_dir = self._find_system_fonts()
        
        font_files = {
            'windows': [
                os.path.join(fonts_dir, "consola.ttf"),
                os.path.join(fonts_dir, "cour.ttf"),
                os.path.join(fonts_dir, "lucon.ttf")
            ],
            'fallback': [
                "/usr/share/fonts/truetype/dejavu/DejaVuSansMono.ttf",
                "/usr/share/fonts/TTF/DejaVuSansMono.ttf",
                "/Library/Fonts/Courier New.ttf"
            ]
        }
        
        for font_path in font_files['windows']:
            try:
                return ImageFont.truetype(font_path, size)
            except:
                continue
        
        for font_path in font_files['fallback']:
            try:
                return ImageFont.truetype(font_path, size)
            except:
                continue
        
        return ImageFont.load_default()

    def _measure_char_size(self, font: ImageFont.FreeTypeFont) -> Tuple[int, int]:
        """Measure the exact width and height of a character"""
        img = Image.new('RGB', (100, 100))
        draw = ImageDraw.Draw(img)
        bbox = draw.textbbox((0, 0), 'M', font=font)
        return bbox[2] - bbox[0], bbox[3] - bbox[1]

    def convert_to_ascii(self, image: Image.Image, cols: int = 120, 
                        scale: float = 0.43, detailed: bool = True) -> List[str]:
        """Convert image to ASCII art with improved quality"""
        if image.mode not in ['L', 'RGB']:
            image = image.convert('RGB')
        
        image = image.convert('L')
        
        width, height = image.size
        w = width / cols
        h = w / scale
        rows = int(height / h)
        
        if cols > width or rows > height:
            image = image.resize((cols, rows), Image.Resampling.LANCZOS)
        else:
            image = image.resize((cols, rows), Image.Resampling.NEAREST)
        
        chars = self.detailed_chars if detailed else self.basic_chars
        
        pixels = np.array(image)
        ascii_lines = []
        for row in pixels:
            ascii_line = ''
            for pixel in row:
                char_idx = int((pixel / 255) * (len(chars) - 1))
                ascii_line += chars[char_idx]
            ascii_lines.append(ascii_line)
        
        return ascii_lines

    def create_frame_image(self, ascii_lines: List[str], 
                          font_size: Optional[int] = None,
                          bg_color: str = 'black', 
                          text_color: str = 'white',
                          padding: int = 20,
                          line_spacing: float = 1.2) -> Image.Image:
        """Create frame with improved character positioning and quality"""
        if font_size and font_size != self.default_font_size:
            font = self._find_monospace_font(font_size)
            char_width, char_height = self._measure_char_size(font)
        else:
            font = self.font
            char_width, char_height = self.char_width, self.char_height

        max_line_length = max(len(line) for line in ascii_lines)
        width = (max_line_length * char_width) + (padding * 2)
        height = (len(ascii_lines) * char_height * line_spacing) + (padding * 2)
        
        image = Image.new('RGB', (int(width), int(height)), color=bg_color)
        draw = ImageDraw.Draw(image)
        
        for y, line in enumerate(ascii_lines):
            for x, char in enumerate(line):
                if char != ' ':
                    pos_x = padding + (x * char_width)
                    pos_y = padding + (y * char_height * line_spacing)
                    draw.text((pos_x, pos_y), char, fill=text_color, font=font)
        
        enhancer = ImageEnhance.Contrast(image)
        image = enhancer.enhance(1.2)
        
        width, height = image.size
        new_width = width if width % 2 == 0 else width + 1
        new_height = height if height % 2 == 0 else height + 1
        
        if new_width != width or new_height != height:
            new_image = Image.new('RGB', (new_width, new_height), color=bg_color)
            new_image.paste(image, ((new_width - width) // 2, (new_height - height) // 2))
            image = new_image
        
        return image