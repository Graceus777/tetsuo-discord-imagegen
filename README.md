# Image Processing Bot

A Discord bot for applying various visual effects and animations to images. The bot provides a powerful set of image processing capabilities including glitch effects, animations, and ASCII art conversion.

## Features

### Image Effects
- Glitch distortion with customizable intensity
- Chromatic aberration
- Scan lines with adjustable spacing and opacity
- Dynamic noise patterns
- Energy distortion effects
- Pulse effects with variable intensity
- Consciousness visualization (combined effects)

### Animation Support
- Frame-by-frame animation generation
- Video output with configurable settings
- GIF creation with optimized settings
- Multiple transition types
- Pre-defined animation presets
- Customizable frame rates and durations

### ASCII Art
- Image to ASCII conversion
- Adjustable output size and scale
- Multiple character sets (basic and detailed)
- Support for both light and dark backgrounds
- ASCII animation capabilities

### Configuration
- Customizable effect parameters
- Saveable effect presets
- Adjustable animation settings
- Configurable processing options
- Command aliases and shortcuts

## Installation

1. Clone the repository:
```bash
git clone https://github.com/yourusername/image-processing-bot.git
cd image-processing-bot
```

2. Create and activate a virtual environment:
```bash
python -m venv venv
source venv/bin/activate  # Linux/Mac
.\venv\Scripts\activate   # Windows
```

3. Install required packages:
```bash
pip install -r requirements.txt
```

4. Set up configuration:
```bash
cp .env.example .env
```
Edit `.env` and add your Discord bot token:
```
DISCORD_TOKEN=your_token_here
```

## Required Dependencies

- Python 3.8+
- PIL (Pillow) for image processing
- discord.py for bot functionality
- numpy for numerical operations
- ffmpeg for video processing (must be installed separately)

## Project Structure

```
image-processing-bot/
├── config/
│   ├── __init__.py
│   ├── config.py
│   └── effect_presets.py
├── core/
│   ├── __init__.py
│   ├── animation_processor.py
│   ├── ascii_processor.py
│   ├── effect_processor.py
│   ├── file_manager.py
│   ├── image_processor.py
│   └── utils.py
├── effects/
│   ├── __init__.py
│   ├── advanced_effects.py
│   ├── animation_effects.py
│   └── basic_effects.py
├── interface/
│   ├── __init__.py
│   └── command_parser.py
├── storage/
│   ├── __init__.py
│   └── repository.py
├── bot.py
├── requirements.txt
└── README.md
```

## Usage

1. Start the bot:
```bash
python bot.py
```

2. Available Commands:
```
!process [options] - Process image with effects
!animate [options] - Create animation
!ascii [options] - Generate ASCII art
!help - Show help information
!examples - Show example commands
```

### Example Commands:

```
!process --glitch 0.5 --chroma 0.3 #cyberpunk
!animate --preset psychic --frames 30 --fps 24
!ascii --cols 120 --scale 0.5
!process --random --preset cyberpunk
!animate --glitch [0.3,0.8] --chroma [0.2,0.4]
```

## Effect Parameters

Each effect has configurable parameters:

- **Glitch**: `intensity` (0.0-1.0)
- **Chromatic Aberration**: `offset` (0.0-1.0)
- **Scan Lines**: `gap` (1-50), `opacity` (0.0-1.0)
- **Noise**: `intensity` (0.0-1.0)
- **Energy**: `intensity` (0.0-1.0)
- **Pulse**: `intensity` (0.0-1.0)
- **Consciousness**: `intensity` (0.0-1.0)

## Animation Presets

Built-in presets for quick effects:

- **cyberpunk**: Glitch effects with scan lines
- **psychic**: Energy and consciousness effects
- **glitch_storm**: Intense glitch and noise combination

## Development

### Adding New Effects

1. Define effect parameters in `effects/basic_effects.py`
2. Implement effect logic in `effects/advanced_effects.py`
3. Add animation support in `effects/animation_effects.py`
4. Register effect in `core/effect_processor.py`

### Creating Custom Presets

Create presets in `config/presets.yml`:

```yaml
preset_name:
  params:
    effect_name:
      param_name: value
  frames: 30
  fps: 24
  description: "Preset description"
```

## Contributing

1. Fork the repository
2. Create a feature branch: `git checkout -b feature-name`
3. Commit changes: `git commit -am 'Add feature'`
4. Push to branch: `git push origin feature-name`
5. Submit a Pull Request

## License

This project is licensed under the MIT License - see the LICENSE file for details.

## Acknowledgments

- PIL for image processing capabilities
- discord.py for Discord integration
- ffmpeg for video processing support
- numpy for numerical operations

## Support

For support, please:
1. Check the documentation
2. Search existing issues
3. Create a new issue with:
   - Command used
   - Expected behavior
   - Actual behavior
   - Error messages
   - Sample images (if applicable)
