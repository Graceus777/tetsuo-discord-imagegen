"""
effects/basic_effects.py

Core effect definitions and configurations for image processing system.
Contains effect ordering, default parameters, and animation presets.
"""

from typing import Dict, Any, List, Union, Tuple, Optional
from dataclasses import dataclass

# Effect execution order - maintains consistent layering of effects
EFFECT_ORDER: List[str] = [
    'rgb',       # RGB channel manipulation
    'color',     # Color adjustments
    'glitch',    # Glitch distortion effects
    'chroma',    # Chromatic aberration
    'scan',      # Scan line overlay
    'noise',     # Noise patterns
    'energy',    # Energy distortion
    'pulse',     # Brightness pulsing
    'consciousness'  # Combined psychic effect
]

# Effect parameter definitions and constraints
EFFECT_PARAMS: Dict[str, Dict[str, Any]] = {
    'glitch': {
        'intensity': {
            'min': 0.0,
            'max': 1.0,
            'default': 0.5,
            'type': float,
            'description': 'Glitch effect intensity'
        }
    },
    'chroma': {
        'offset': {
            'min': 0.0,
            'max': 1.0,
            'default': 0.5,
            'type': float,
            'description': 'Chromatic aberration offset'
        }
    },
    'scan': {
        'gap': {
            'min': 1,
            'max': 50,
            'default': 2,
            'type': int,
            'description': 'Pixels between scan lines'
        },
        'opacity': {
            'min': 0.0,
            'max': 1.0,
            'default': 0.5,
            'type': float,
            'description': 'Scan line opacity'
        }
    },
    'noise': {
        'intensity': {
            'min': 0.0,
            'max': 1.0,
            'default': 0.5,
            'type': float,
            'description': 'Noise effect intensity'
        }
    },
    'energy': {
        'intensity': {
            'min': 0.0,
            'max': 1.0,
            'default': 0.5,
            'type': float,
            'description': 'Energy effect intensity'
        }
    },
    'pulse': {
        'intensity': {
            'min': 0.0,
            'max': 1.0,
            'default': 0.5,
            'type': float,
            'description': 'Pulse effect intensity'
        }
    },
    'consciousness': {
        'intensity': {
            'min': 0.0,
            'max': 1.0,
            'default': 0.5,
            'type': float,
            'description': 'Consciousness effect intensity'
        }
    }
}

# Default parameter values for each effect
EFFECT_DEFAULTS: Dict[str, Dict[str, Union[float, int]]] = {
    'glitch': {'intensity': 0.5},
    'chroma': {'offset': 0.5},
    'scan': {'gap': 2, 'opacity': 0.5},
    'noise': {'intensity': 0.5},
    'energy': {'intensity': 0.5},
    'pulse': {'intensity': 0.5},
    'consciousness': {'intensity': 0.5}
}

# Predefined animation presets
ANIMATION_PRESETS: Dict[str, Dict[str, Any]] = {
    'cyberpunk': {
        'params': {
            'glitch': {'intensity': (0.3, 0.8)},
            'chroma': {'offset': (0.2, 0.4)},
            'scan': {'gap': (2, 4), 'opacity': (0.4, 0.6)},
            'consciousness': {'intensity': (0.3, 0.7)}
        },
        'frames': 30,
        'fps': 24,
        'description': 'Cyberpunk-style glitch effect with scanning'
    },
    'psychic': {
        'params': {
            'energy': {'intensity': (0.4, 0.8)},
            'consciousness': {'intensity': (0.5, 0.9)},
            'pulse': {'intensity': (0.2, 0.6)}
        },
        'frames': 30,
        'fps': 24,
        'description': 'Psychic energy visualization'
    },
    'glitch_storm': {
        'params': {
            'glitch': {'intensity': (0.6, 1.0)},
            'noise': {'intensity': (0.3, 0.7)},
            'chroma': {'offset': (0.4, 0.8)}
        },
        'frames': 45,
        'fps': 30,
        'description': 'Intense glitch and noise effects'
    }
}

@dataclass
class EffectParameters:
    """Container for effect parameter validation and defaults."""
    name: str
    params: Dict[str, Any]
    
    def validate(self) -> None:
        """Validate parameters against defined constraints."""
        if self.name not in EFFECT_PARAMS:
            raise ValueError(f"Unknown effect: {self.name}")
            
        effect_config = EFFECT_PARAMS[self.name]
        for param_name, value in self.params.items():
            if param_name not in effect_config:
                raise ValueError(f"Unknown parameter '{param_name}' for effect '{self.name}'")
                
            constraints = effect_config[param_name]
            if isinstance(value, (tuple, list)):
                for v in value:
                    if not (constraints['min'] <= v <= constraints['max']):
                        raise ValueError(
                            f"Value {v} for {self.name}.{param_name} outside valid range "
                            f"[{constraints['min']}, {constraints['max']}]"
                        )
            else:
                if not (constraints['min'] <= value <= constraints['max']):
                    raise ValueError(
                        f"Value {value} for {self.name}.{param_name} outside valid range "
                        f"[{constraints['min']}, {constraints['max']}]"
                    )
    
    def get_defaults(self) -> Dict[str, Any]:
        """Get default parameters for the effect."""
        return EFFECT_DEFAULTS.get(self.name, {})

def validate_preset(preset_name: str) -> None:
    """
    Validate a preset configuration.
    
    Args:
        preset_name: Name of preset to validate
        
    Raises:
        ValueError: If preset is invalid
    """
    if preset_name not in ANIMATION_PRESETS:
        raise ValueError(f"Unknown preset: {preset_name}")
        
    preset = ANIMATION_PRESETS[preset_name]
    for effect_name, params in preset['params'].items():
        effect = EffectParameters(effect_name, params)
        effect.validate()