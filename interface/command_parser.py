from typing import Dict, Any, List, Tuple, Optional, Union
from pathlib import Path
from dataclasses import dataclass, field
import logging
from config.config import ConfigManager

@dataclass
class ParsedCommand:
    """Structured representation of a parsed command."""
    command: str = "image"  # Changed default from 'process' to 'image'
    effects: List[Tuple[str, Dict[str, Any]]] = field(default_factory=list)
    animation_params: Dict[str, Any] = field(default_factory=dict)
    ascii_params: Dict[str, Any] = field(default_factory=dict)
    output_params: Dict[str, Any] = field(default_factory=dict)
    preset_name: Optional[str] = None
    tags: List[str] = field(default_factory=list)
    random: bool = False

class CommandParser:
    """Parses and validates user commands for image processing."""
    
    def __init__(self, config: ConfigManager):
        self.config = config
        self.logger = logging.getLogger('CommandParser')
        
        self.patterns = {
            'effect': r'--(\w+)(?:\s+(\d*\.?\d+)|\s+\[([^\]]+)\])',
            'animation': r'--(?:frames|fps)\s+(\d+)',
            'ascii': r'--(?:cols|scale)\s+(\d*\.?\d+)',
            'tag': r'#(\w+)',
            'preset': r'--preset\s+(\w+)',
            'output': r'--(?:format|quality)\s+(\w+)',
            'random': r'--random'
        }

    def parse_command(self, command_str: str) -> ParsedCommand:
        """Parse command string into structured format."""
        result = ParsedCommand()
        parts = command_str.split()
        
        if parts and not parts[0].startswith('--'):
            result.command = parts.pop(0).lower()
        
        i = 0
        while i < len(parts):
            part = parts[i]
            
            # Handle random flag
            if part == '--random':
                result.random = True
                i += 1
                continue
                
            # Handle preset
            if part == '--preset' and i + 1 < len(parts):
                preset_name = parts[i + 1]
                try:
                    preset = self.config.get_preset(preset_name)
                    result.preset_name = preset_name
                    result.effects.extend([
                        (effect, params) 
                        for effect, params in preset['params'].items()
                    ])
                    i += 2
                    continue
                except KeyError:
                    raise ValueError(f"Unknown preset: {preset_name}")
            
            # Handle effects
            if part.startswith('--') and part[2:] in self.config.effect_params:
                effect_name = part[2:]
                if i + 1 >= len(parts):
                    raise ValueError(f"Missing value for effect: {effect_name}")
                    
                value = parts[i + 1]
                if value.startswith('[') and value.endswith(']'):
                    # Handle range values
                    values = [float(x.strip()) for x in value[1:-1].split(',')]
                    if len(values) != 2:
                        raise ValueError(f"Invalid range for {effect_name}: {value}")
                    params = {'intensity': tuple(values)}
                else:
                    # Handle single value
                    params = {'intensity': float(value)}
                
                self.config.validate_params(effect_name, params)
                result.effects.append((effect_name, params))
                i += 2
                continue
            
            # Handle animation parameters
            if part in ['--frames', '--fps']:
                param_name = part[2:]
                if i + 1 >= len(parts):
                    raise ValueError(f"Missing value for {param_name}")
                value = int(parts[i + 1])
                
                if param_name == 'frames':
                    if not (self.config.animation.min_frames <= value <= self.config.animation.max_frames):
                        raise ValueError(f"Frames must be between {self.config.animation.min_frames} and {self.config.animation.max_frames}")
                elif param_name == 'fps':
                    if not (self.config.animation.min_fps <= value <= self.config.animation.max_fps):
                        raise ValueError(f"FPS must be between {self.config.animation.min_fps} and {self.config.animation.max_fps}")
                
                result.animation_params[param_name] = value
                i += 2
                continue
            
            # Handle ASCII parameters
            if part in ['--cols', '--scale']:
                param_name = part[2:]
                if i + 1 >= len(parts):
                    raise ValueError(f"Missing value for {param_name}")
                value = float(parts[i + 1])
                
                if param_name == 'cols':
                    if not (0 < value <= self.config.ascii.max_cols):
                        raise ValueError(f"Columns must be between 1 and {self.config.ascii.max_cols}")
                elif param_name == 'scale':
                    if not (0 < value <= 2.0):
                        raise ValueError("Scale must be between 0 and 2.0")
                
                result.ascii_params[param_name] = value
                i += 2
                continue
            
            # Handle tags
            if part.startswith('#'):
                result.tags.append(part[1:])
                i += 1
                continue
            
            # Handle output format
            if part == '--format' and i + 1 < len(parts):
                format_value = parts[i + 1].upper()
                if format_value not in ['PNG', 'JPEG', 'GIF']:
                    raise ValueError("Supported formats: PNG, JPEG, GIF")
                result.output_params['format'] = format_value
                i += 2
                continue
            
            # Unknown parameter
            raise ValueError(f"Unknown parameter: {part}")
        
        self._validate_command(result)
        return result

    def _validate_command(self, parsed: ParsedCommand) -> None:
        """Validate parsed command for consistency."""
        if parsed.command not in ['image', 'animate', 'ascii', 'remix']:
            raise ValueError(f"Unknown command: {parsed.command}")
        
        if parsed.command == 'animate' and not parsed.animation_params and not parsed.preset_name:
            parsed.animation_params['frames'] = self.config.animation.default_frames
            parsed.animation_params['fps'] = self.config.animation.default_fps
        
        if parsed.command == 'ascii' and not parsed.ascii_params:
            parsed.ascii_params['cols'] = self.config.ascii.default_cols
            parsed.ascii_params['scale'] = self.config.ascii.default_scale

    def format_help(self) -> str:
        """Generate help text for available commands."""
        help_text = [
            "Available Commands:",
            "  !image [options] - Process image with effects",
            "  !animate [options] - Create animation",
            "  !ascii [options] - Generate ASCII art",
            "  !remix <id> [options] - Remix existing image",
            "",
            "Input Options:",
            "  --random - Use random image from images folder",
            "  Upload an image with command",
            "  Default: uses input.png from current directory",
            "",
            "Effect Options:"
        ]
        
        for effect, params in self.config.effect_params.items():
            param_desc = []
            for param, config in params.items():
                if isinstance(config, dict) and 'min' in config:
                    param_desc.append(f"{param}=[{config['min']}-{config['max']}]")
            help_text.append(f"  --{effect} {' '.join(param_desc)}")
        
        help_text.extend([
            "",
            "Animation Options:",
            f"  --frames [{self.config.animation.min_frames}-{self.config.animation.max_frames}]",
            f"  --fps [{self.config.animation.min_fps}-{self.config.animation.max_fps}]",
            "",
            "ASCII Options:",
            f"  --cols [1-{self.config.ascii.max_cols}]",
            "  --scale [0.1-2.0]",
            "",
            "Other Options:",
            "  --preset <name> - Use predefined effect combination",
            "  --format <PNG|JPEG|GIF> - Set output format",
            "  #tag - Add tag to output"
        ])
        
        return "\n".join(help_text)

    def get_example_commands(self) -> List[str]:
        """Get list of example commands."""
        return [
            "!image --glitch 0.5 --chroma 0.3 #cyberpunk",
            "!image --random --preset psychic",
            "!animate --preset psychic --frames 30 --fps 24",
            "!ascii --cols 120 --scale 0.5",
            "!remix 123 --glitch [0.3,0.8] --chroma [0.2,0.4]"
        ]