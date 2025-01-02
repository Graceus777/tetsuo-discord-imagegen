"""
effects/advanced_effects.py

Implementation of advanced image processing effects.
These effects are used by the EffectProcessor class to create various visual transformations.
"""

from typing import Tuple, Optional, Union, Dict, Any
import numpy as np
from PIL import Image, ImageDraw, ImageEnhance, ImageFilter
import colorsys
import math



def create_channel_pass_frame(base_image: Image.Image, offset_values: Tuple[float, float]) -> Image.Image:
    """Create a frame with RGB channel offsets"""
    img = base_image.convert('RGBA')
    width, height = img.size
    
    r, g, b, a = img.split()
    
    g_offset = int(offset_values[0] * width) % width
    b_offset = int(offset_values[1] * width) % width
    
    # Create output image
    result = Image.new('RGBA', (width, height), (0, 0, 0, 0))
    
    # Create wrapped green channel
    g_temp = Image.new('L', (width, height))
    g_temp.paste(g.crop((0, 0, width - g_offset, height)), (g_offset, 0))
    g_temp.paste(g.crop((width - g_offset, 0, width, height)), (0, 0))
    
    # Create wrapped blue channel
    b_temp = Image.new('L', (width, height))
    b_temp.paste(b.crop((0, 0, width - b_offset, height)), (b_offset, 0))
    b_temp.paste(b.crop((width - b_offset, 0, width, height)), (0, 0))
    
    # Merge channels back together
    result = Image.merge('RGBA', (r, g_temp, b_temp, a))
    return result

def apply_glitch_effect(
    image: Image.Image,
    intensity: float = 0.5,
    seed: Optional[int] = None
) -> Image.Image:
    """
    Apply digital glitch effect to the image.
    
    Args:
        image: Input PIL Image
        intensity: Effect intensity (0.0 to 1.0)
        seed: Optional random seed for reproducible results
        
    Returns:
        PIL Image with glitch effect applied
    """
    if not 0 <= intensity <= 1:
        raise ValueError("Intensity must be between 0 and 1")
        
    # Set random seed if provided
    if seed is not None:
        np.random.seed(seed)
    
    # Convert to numpy array for efficient processing
    arr = np.array(image)
    height = arr.shape[0]
    
    # Number of glitch lines based on intensity
    num_lines = int(intensity * height * 0.1)  # Up to 10% of height
    
    # Create glitch effects
    for _ in range(num_lines):
        # Random line position and offset
        y = np.random.randint(0, height-1)
        offset = np.random.randint(-int(intensity * 20), int(intensity * 20))
        
        # Shift line horizontally
        if 0 <= y < height:
            arr[y, :] = np.roll(arr[y, :], offset, axis=0)
            
        # Add color shifting for stronger glitches
        if intensity > 0.7 and np.random.random() < 0.3:
            channel = np.random.randint(0, 3)
            arr[y, :, channel] = np.roll(arr[y, :, channel], offset * 2)
    
    return Image.fromarray(arr)

def apply_chromatic_aberration(
    image: Image.Image,
    offset: float = 0.5
) -> Image.Image:
    """
    Apply RGB channel offset (chromatic aberration).
    
    Args:
        image: Input PIL Image
        offset: Maximum pixel offset (0.0 to 1.0)
        
    Returns:
        PIL Image with chromatic aberration applied
    """
    if not 0 <= offset <= 1:
        raise ValueError("Offset must be between 0 and 1")
    
    # Split into RGB channels
    r, g, b = image.split()
    
    # Calculate pixel offsets based on image size
    width, _ = image.size
    max_offset = int(width * offset * 0.1)  # Up to 10% of width
    
    # Create new image with offset channels
    result = Image.merge('RGB', (
        r.transform(r.size, Image.AFFINE, (1, 0, -max_offset, 0, 1, 0)),  # Red left
        g,  # Green center
        b.transform(b.size, Image.AFFINE, (1, 0, max_offset, 0, 1, 0))    # Blue right
    ))
    
    return result

def apply_scan_lines(
    image: Image.Image,
    gap: int = 2,
    opacity: float = 0.5
) -> Image.Image:
    """
    Apply scan line effect to the image.
    
    Args:
        image: Input PIL Image
        gap: Pixels between scan lines
        opacity: Line opacity (0.0 to 1.0)
        
    Returns:
        PIL Image with scan lines applied
    """
    if gap < 1:
        raise ValueError("Gap must be at least 1 pixel")
    if not 0 <= opacity <= 1:
        raise ValueError("Opacity must be between 0 and 1")
    
    # Create scan line overlay
    overlay = Image.new('RGBA', image.size, (0, 0, 0, 0))
    draw = ImageDraw.Draw(overlay)
    
    # Draw horizontal lines
    for y in range(0, image.size[1], gap):
        alpha = int(opacity * 255)
        draw.line([(0, y), (image.size[0], y)], fill=(0, 0, 0, alpha))
    
    # Convert image to RGBA if necessary
    if image.mode != 'RGBA':
        image = image.convert('RGBA')
    
    # Composite with original
    return Image.alpha_composite(image, overlay)

def apply_noise_effect(
    image: Image.Image,
    intensity: float = 0.5,
    seed: Optional[int] = None
) -> Image.Image:
    """
    Add noise to the image.
    
    Args:
        image: Input PIL Image
        intensity: Noise intensity (0.0 to 1.0)
        seed: Optional random seed for reproducible results
        
    Returns:
        PIL Image with noise applied
    """
    if not 0 <= intensity <= 1:
        raise ValueError("Intensity must be between 0 and 1")
    
    if seed is not None:
        np.random.seed(seed)
    
    # Convert to numpy array
    arr = np.array(image)
    
    # Generate noise for each channel
    noise = np.random.normal(0, intensity * 50, arr.shape)
    noisy = np.clip(arr + noise, 0, 255).astype(np.uint8)
    
    return Image.fromarray(noisy)

def apply_energy_effect(
    image: Image.Image,
    intensity: float = 0.5
) -> Image.Image:
    """
    Apply energy distortion effect.
    
    Args:
        image: Input PIL Image
        intensity: Effect intensity (0.0 to 1.0)
        
    Returns:
        PIL Image with energy effect applied
    """
    if not 0 <= intensity <= 1:
        raise ValueError("Intensity must be between 0 and 1")
    
    # Convert to numpy array
    arr = np.array(image)
    
    # Create displacement map
    x = np.arange(arr.shape[1])
    y = np.arange(arr.shape[0])
    X, Y = np.meshgrid(x, y)
    
    # Generate distortion pattern
    distortion = np.sin(X * 0.1 + Y * 0.1) * intensity * 30
    
    # Apply to each channel
    for c in range(3):
        arr[:,:,c] = np.clip(arr[:,:,c] + distortion, 0, 255)
    
    return Image.fromarray(arr.astype(np.uint8))

def apply_pulse_effect(
    image: Image.Image,
    intensity: float = 0.5
) -> Image.Image:
    """
    Apply pulsing effect through brightness modulation.
    
    Args:
        image: Input PIL Image
        intensity: Effect intensity (0.0 to 1.0)
        
    Returns:
        PIL Image with pulse effect applied
    """
    if not 0 <= intensity <= 1:
        raise ValueError("Intensity must be between 0 and 1")
    
    enhancer = ImageEnhance.Brightness(image)
    pulse_factor = 1.0 + intensity
    return enhancer.enhance(pulse_factor)

def apply_consciousness_effect(
    image: Image.Image,
    intensity: float = 0.5
) -> Image.Image:
    """
    Apply consciousness effect (combination of energy, pulse, and chromatic aberration).
    
    Args:
        image: Input PIL Image
        intensity: Effect intensity (0.0 to 1.0)
        
    Returns:
        PIL Image with consciousness effect applied
    """
    if not 0 <= intensity <= 1:
        raise ValueError("Intensity must be between 0 and 1")
    
    # Apply multiple effects in sequence
    result = apply_energy_effect(image, intensity * 0.5)
    result = apply_pulse_effect(result, intensity * 0.3)
    
    if intensity > 0.5:
        result = apply_chromatic_aberration(result, intensity * 0.4)
    
    return result

def create_effect_mask(
    size: Tuple[int, int],
    effect_type: str = 'radial',
    intensity: float = 0.5
) -> Image.Image:
    """
    Create effect mask for partial effect application.
    
    Args:
        size: (width, height) of the mask
        effect_type: Type of mask ('radial', 'linear', or 'noise')
        intensity: Mask intensity (0.0 to 1.0)
        
    Returns:
        PIL Image mask
    """
    if not 0 <= intensity <= 1:
        raise ValueError("Intensity must be between 0 and 1")
    
    mask = Image.new('L', size, 0)
    draw = ImageDraw.Draw(mask)
    
    if effect_type == 'radial':
        # Radial gradient from center
        center = (size[0] // 2, size[1] // 2)
        max_radius = math.sqrt(center[0]**2 + center[1]**2)
        for r in range(int(max_radius)):
            opacity = int(255 * (1 - r / max_radius) * intensity)
            draw.ellipse([
                center[0] - r, center[1] - r,
                center[0] + r, center[1] + r
            ], fill=opacity)
            
    elif effect_type == 'linear':
        # Linear gradient
        for x in range(size[0]):
            opacity = int(255 * (x / size[0]) * intensity)
            draw.line([(x, 0), (x, size[1])], fill=opacity)
            
    elif effect_type == 'noise':
        # Random noise pattern
        arr = np.random.rand(*size) * intensity * 255
        mask = Image.fromarray(arr.astype(np.uint8))
        
    return mask