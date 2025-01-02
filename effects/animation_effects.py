"""
effects/animation_effects.py

Animation-specific effect utilities and frame generation functions.
Works in conjunction with basic_effects.py and advanced_effects.py to create animated effects.
"""

from typing import Dict, Any, List, Tuple, Optional, Union, Callable
import numpy as np
from PIL import Image, ImageChops, ImageEnhance
from pathlib import Path
import math



from .advanced_effects import (
    apply_glitch_effect,
    apply_chromatic_aberration,
    apply_scan_lines,
    apply_noise_effect,
    apply_energy_effect,
    apply_pulse_effect,
    apply_consciousness_effect,
    create_channel_pass_frame
)

from .basic_effects import (
    EFFECT_PARAMS,
    EFFECT_DEFAULTS,
    ANIMATION_PRESETS
)

def ease_value(value: float, easing_type: str = 'linear') -> float:
    """
    Apply easing function to a value.
    
    Args:
        value: Input value between 0 and 1
        easing_type: Type of easing function to apply
            Options: 'linear', 'ease_in', 'ease_out', 'ease_in_out',
                    'bounce', 'elastic'
    
    Returns:
        Eased value between 0 and 1
    """
    if not 0 <= value <= 1:
        raise ValueError("Value must be between 0 and 1")

    if easing_type == 'linear':
        return value
    elif easing_type == 'ease_in':
        return value * value
    elif easing_type == 'ease_out':
        return 1 - (1 - value) * (1 - value)
    elif easing_type == 'ease_in_out':
        if value < 0.5:
            return 2 * value * value
        else:
            return 1 - (-2 * value + 2) ** 2 / 2
    elif easing_type == 'bounce':
        n1 = 7.5625
        d1 = 2.75
        
        if value < 1 / d1:
            return n1 * value * value
        elif value < 2 / d1:
            value -= 1.5 / d1
            return n1 * value * value + 0.75
        elif value < 2.5 / d1:
            value -= 2.25 / d1
            return n1 * value * value + 0.9375
        else:
            value -= 2.625 / d1
            return n1 * value * value + 0.984375
    elif easing_type == 'elastic':
        if value == 0 or value == 1:
            return value
            
        p = 0.3
        s = p / 4
        return -(2 ** (-10 * value)) * math.sin((value - s) * (2 * math.pi) / p) + 1
    else:
        raise ValueError(f"Unknown easing type: {easing_type}")

def interpolate_parameters(
    start_params: Dict[str, Any],
    end_params: Dict[str, Any],
    progress: float,
    easing_type: str = 'linear'
) -> Dict[str, Any]:
    """
    Interpolate between two sets of effect parameters.
    
    Args:
        start_params: Starting parameter values
        end_params: Ending parameter values
        progress: Animation progress (0 to 1)
        easing_type: Type of easing to apply
        
    Returns:
        Interpolated parameters
    """
    if not 0 <= progress <= 1:
        raise ValueError("Progress must be between 0 and 1")
        
    eased_progress = ease_value(progress, easing_type)
    result = {}
    
    for key in set(start_params) | set(end_params):
        start_val = start_params.get(key, 0)
        end_val = end_params.get(key, 0)
        
        if isinstance(start_val, (int, float)) and isinstance(end_val, (int, float)):
            result[key] = start_val + (end_val - start_val) * eased_progress
        elif isinstance(start_val, tuple) and isinstance(end_val, tuple):
            result[key] = tuple(
                s + (e - s) * eased_progress
                for s, e in zip(start_val, end_val)
            )
        else:
            result[key] = end_val if eased_progress > 0.5 else start_val
            
    return result
def interpolate_keyframes(keyframes: List[float], total_frames: int) -> List[float]:
    """Interpolate between keyframe values"""
    if len(keyframes) < 2:
        return [keyframes[0]] * total_frames
        
    segments = len(keyframes) - 1
    frames_per_segment = total_frames // segments
    
    interpolated = []
    for i in range(segments):
        start_val = keyframes[i]
        end_val = keyframes[i + 1]
        
        # Calculate frames for this segment
        if i == segments - 1:
            segment_frames = total_frames - len(interpolated)
        else:
            segment_frames = frames_per_segment
            
        for frame in range(segment_frames):
            progress = frame / segment_frames
            value = start_val + (end_val - start_val) * progress
            interpolated.append(value)
            
    return interpolated

def generate_channel_pass_frames(
    base_image: Image.Image,
    params: Dict[str, Any],
    num_frames: int = 60
) -> List[Image.Image]:
    """Generate frames with RGB channel offset animation"""
    frames = []
    base_image = ImageUtils.ensure_even_dimensions(base_image)
    
    # Get keyframe values
    g_keyframes = params.get('g_values', [0, 0.2, 0])
    b_keyframes = params.get('b_values', [0, 0.3, 0])
    
    # Interpolate keyframe values
    g_values = interpolate_keyframes(g_keyframes, num_frames)
    b_values = interpolate_keyframes(b_keyframes, num_frames)
    
    for i in range(num_frames):
        # Create frame with current offset values
        frame = create_channel_pass_frame(base_image, (g_values[i], b_values[i]))
        frames.append(frame)
        
    return frames
def create_animation_frame(
    base_image: Image.Image,
    effects: List[Tuple[str, Dict[str, Any]]],
    progress: float,
    easing_type: str = 'linear'
) -> Image.Image:
    """
    Create a single animation frame with multiple effects.
    
    Args:
        base_image: Base image to apply effects to
        effects: List of (effect_name, parameters) tuples
        progress: Animation progress (0 to 1)
        easing_type: Type of easing to apply
        
    Returns:
        Processed frame image
    """
    if not 0 <= progress <= 1:
        raise ValueError("Progress must be between 0 and 1")
        
    frame = base_image.copy()
    
    for effect_name, params in effects:
        # Get effect function
        effect_map = {
            'glitch': apply_glitch_effect,
            'chroma': apply_chromatic_aberration,
            'scan': apply_scan_lines,
            'noise': apply_noise_effect,
            'energy': apply_energy_effect,
            'pulse': apply_pulse_effect,
            'consciousness': apply_consciousness_effect
        }
        
        if effect_name not in effect_map:
            raise ValueError(f"Unknown effect: {effect_name}")
            
        effect_func = effect_map[effect_name]
        
        # Interpolate parameters if they're animated
        frame_params = {}
        for param_name, param_value in params.items():
            if isinstance(param_value, tuple) and len(param_value) == 2:
                start, end = param_value
                eased_progress = ease_value(progress, easing_type)
                frame_params[param_name] = start + (end - start) * eased_progress
            else:
                frame_params[param_name] = param_value
        
        # Apply effect
        frame = effect_func(frame, **frame_params)
    
    return frame

def create_transition_frame(
    image1: Image.Image,
    image2: Image.Image,
    progress: float,
    transition_type: str = 'dissolve',
    easing_type: str = 'linear'
) -> Image.Image:
    """
    Create transition frame between two images.
    
    Args:
        image1: Starting image
        image2: Ending image
        progress: Transition progress (0 to 1)
        transition_type: Type of transition effect
        easing_type: Type of easing to apply
        
    Returns:
        Transition frame
    """
    if not 0 <= progress <= 1:
        raise ValueError("Progress must be between 0 and 1")
        
    if image1.size != image2.size:
        image2 = image2.resize(image1.size, Image.Resampling.LANCZOS)
    
    eased_progress = ease_value(progress, easing_type)
    
    if transition_type == 'dissolve':
        return Image.blend(image1, image2, eased_progress)
    elif transition_type == 'slide':
        width, height = image1.size
        offset = int(width * eased_progress)
        frame = Image.new('RGBA', image1.size)
        frame.paste(image1, (-offset, 0))
        frame.paste(image2, (width - offset, 0))
        return frame
    elif transition_type == 'zoom':
        scale = 1 + eased_progress
        sized_frame = image1.resize(
            (int(width * scale), int(height * scale)),
            Image.Resampling.LANCZOS
        )
        frame = Image.new('RGBA', image1.size)
        frame.paste(
            sized_frame,
            (int((width - sized_frame.width) / 2),
             int((height - sized_frame.height) / 2))
        )
        return Image.blend(frame, image2, eased_progress)
    else:
        raise ValueError(f"Unknown transition type: {transition_type}")

def apply_animation_preset(
    base_image: Image.Image,
    preset_name: str,
    progress: float,
    custom_params: Optional[Dict[str, Any]] = None
) -> Image.Image:
    """
    Apply predefined animation preset to image.
    
    Args:
        base_image: Base image to apply preset to
        preset_name: Name of animation preset
        progress: Animation progress (0 to 1)
        custom_params: Optional parameter overrides
        
    Returns:
        Processed frame image
    """
    if preset_name not in ANIMATION_PRESETS:
        raise ValueError(f"Unknown preset: {preset_name}")
        
    preset = ANIMATION_PRESETS[preset_name].copy()
    if custom_params:
        preset['params'].update(custom_params)
    
    effects = [(name, params) for name, params in preset['params'].items()]
    return create_animation_frame(base_image, effects, progress)