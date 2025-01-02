import asyncio
import os
import sys
import random
from pathlib import Path
import discord
from discord.ext import commands
from dotenv import load_dotenv
from PIL import Image
from io import BytesIO
from typing import Tuple, Optional  
from config.config import ConfigManager
from storage.repository import ImageRepository
from interface.command_parser import CommandParser
from core.effect_processor import EffectProcessor
from core.animation_processor import AnimationProcessor
from core.ascii_processor import ASCIIProcessor

# Load environment variables
load_dotenv()
DISCORD_TOKEN = os.getenv('DISCORD_TOKEN')

# Initialize configuration
config = ConfigManager(config_dir="config")
repository = ImageRepository(db_path="image_repository.db", storage_path="image_storage")
command_parser = CommandParser(config)

# Set up Discord bot
intents = discord.Intents.default()
intents.message_content = True
intents.reactions = True
bot = commands.Bot(command_prefix='!', intents=intents, help_command=None)

async def get_input_image(ctx, repository, command) -> Tuple[Optional[bytes], str]:
    """
    Get input image from various sources.
    
    Priority:
    1. Uploaded image
    2. Random image if --random flag
    3. Repository image if remix command
    4. Default input.png
    
    Returns:
        Tuple of (image_bytes, source_description)
    """
    # Check for uploaded image
    if ctx.message.attachments:
        return (await ctx.message.attachments[0].read(), "uploaded image")
        
    # Check for random flag
    if hasattr(command, 'random') and command.random:
        images_dir = Path("images")
        if not images_dir.exists():
            raise ValueError("Images directory not found")
            
        image_files = [f for f in images_dir.glob("*") 
                      if f.suffix.lower() in {'.png', '.jpg', '.jpeg', '.gif'}]
        if not image_files:
            raise ValueError("No images found in images directory")
            
        random_image = random.choice(image_files)
        with open(random_image, 'rb') as f:
            return (f.read(), f"random image: {random_image.name}")
            
    # Check for remix command
    if ctx.message.content.startswith('!remix'):
        try:
            image_id = int(ctx.message.content.split()[1])
            image_data = repository.get_image(image_id)
            if not image_data:
                raise ValueError(f"Image with ID {image_id} not found")
            return (image_data['image'], f"remixed image ID: {image_id}")
        except (IndexError, ValueError) as e:
            raise ValueError("Invalid remix command. Use: !remix <image_id>")
            
    # Default to input.png
    input_path = Path("input.png")
    if not input_path.exists():
        raise ValueError("No image provided and input.png not found")
        
    with open(input_path, 'rb') as f:
        return (f.read(), "input.png")

@bot.event
async def on_ready():
    """Bot startup event handler."""
    print(f'Image processing bot is online as {bot.user}')

@bot.event
async def on_reaction_add(reaction, user):
    """Handle reaction events for message cleanup."""
    if user != bot.user and str(reaction.emoji) == "🗑️":
        if reaction.message.author == bot.user:
            await reaction.message.delete()
@bot.command(name='ascii_animate')
async def ascii_animate_command(ctx, *args):
    try:
        if not ctx.message.attachments:
            await ctx.send("Please attach images for animation")
            return
            
        processor = ASCIIProcessor()
        frames = []
        
        # Convert each image to ASCII frame
        for attachment in ctx.message.attachments:
            image_bytes = await attachment.read()
            img = Image.open(io.BytesIO(image_bytes))
            ascii_lines = processor.convert_to_ascii(img)
            frame = processor.create_frame_image(ascii_lines)
            frames.append(frame)
        
        # Save as animation
        frames[0].save("ascii_animation.gif", save_all=True, append_images=frames[1:], duration=100, loop=0)
        await ctx.send(file=discord.File("ascii_animation.gif"))
            
    except Exception as e:
        await ctx.send(f"Error creating ASCII animation: {str(e)}")
@bot.command(name='image')
async def image_command(ctx, *args):
    """Process an image with effects."""
    try:
        # Parse command
        command = command_parser.parse_command(' '.join(args))
        
        # Get input image
        try:
            image_bytes, source = await get_input_image(ctx, repository, command)
        except ValueError as e:
            await ctx.send(str(e))
            return

        # Process image
        processor = EffectProcessor(image_bytes)
        for effect_name, params in command.effects:
            processor.apply_effect(effect_name, params)

        # Save and send result
        output = processor.get_current_image()
        output_bytes = BytesIO()
        output.save(output_bytes, format='PNG')
        output_bytes.seek(0)
        
        # Store in repository if configured
        if command.tags:
            image_id = repository.store_image(
                image=output_bytes.getvalue(),
                title=f"Processed_{ctx.author.name}",
                creator_id=str(ctx.author.id),
                creator_name=ctx.author.name,
                tags=command.tags,
                parameters=dict(command.effects),
                source_image=source
            )
            await ctx.send(f"Image stored with ID: {image_id}")

        # Send processed image
        output_bytes.seek(0)
        await ctx.send(file=discord.File(output_bytes, filename="processed.png"))

    except Exception as e:
        await ctx.send(f"Error processing image: {str(e)}")

@bot.command(name='remix')
async def remix_command(ctx, image_id: int, *args):
    """Remix an existing processed image."""
    try:
        # Get original image
        image_data = repository.get_image(image_id)
        if not image_data:
            await ctx.send(f"Image with ID {image_id} not found")
            return
            
        # Parse additional effects
        command = command_parser.parse_command(' '.join(args))
        
        # Process image
        processor = EffectProcessor(image_data['image'])
        
        # Apply original effects first
        if 'parameters' in image_data:
            for effect_name, params in image_data['parameters'].items():
                processor.apply_effect(effect_name, params)
                
        # Apply new effects
        for effect_name, params in command.effects:
            processor.apply_effect(effect_name, params)
            
        # Handle output
        output = processor.get_current_image()
        output_bytes = BytesIO()
        output.save(output_bytes, format='PNG')
        output_bytes.seek(0)
        
        if command.tags:
            new_id = repository.store_image(
                image=output_bytes.getvalue(),
                title=f"Remixed_{ctx.author.name}",
                creator_id=str(ctx.author.id),
                creator_name=ctx.author.name,
                tags=command.tags + ['remixed'],
                parameters=dict(command.effects),
                source_image=f"remixed from ID: {image_id}"
            )
            await ctx.send(f"Remixed image stored with ID: {new_id}")
            
        output_bytes.seek(0)
        await ctx.send(file=discord.File(output_bytes, filename="remixed.png"))
        
    except Exception as e:
        await ctx.send(f"Error remixing image: {str(e)}")

@bot.command(name='animate')
async def animate_command(ctx, *args):
    """Create an animation with effects."""
    try:
        # Parse command
        command = command_parser.parse_command(f"animate {' '.join(args)}")
        
        # Get input image
        try:
            image_bytes, source = await get_input_image(ctx, repository, command)
        except ValueError as e:
            await ctx.send(str(e))
            return

        # Create animation
        processor = AnimationProcessor(image_bytes)
        try:
            status_msg = await ctx.send("Generating animation...")
            
            frames = processor.generate_frames(
                effects=command.effects,
                num_frames=command.animation_params.get('frames', 30)
            )
            
            video_path = processor.create_video(
                frame_paths=frames,
                frame_rate=command.animation_params.get('fps', 24)
            )
            
            if video_path and video_path.exists():
                await ctx.send(file=discord.File(str(video_path)))
                if command.tags:
                    with open(video_path, 'rb') as f:
                        video_id = repository.store_image(
                            image=f.read(),
                            title=f"Animation_{ctx.author.name}",
                            creator_id=str(ctx.author.id),
                            creator_name=ctx.author.name,
                            tags=command.tags + ['animation'],
                            parameters=dict(command.effects),
                            source_image=source
                        )
                    await ctx.send(f"Animation stored with ID: {video_id}")
            else:
                await ctx.send("Failed to create animation")
            
            await status_msg.delete()
            
        finally:
            processor.cleanup()

    except Exception as e:
        await ctx.send(f"Error creating animation: {str(e)}")

@bot.command(name='ascii')
async def ascii_command(ctx, *args):
    """Create ASCII art from an image."""
    try:
        # Parse command
        command = command_parser.parse_command(f"ascii {' '.join(args)}")
        
        # Get input image
        try:
            image_bytes, source = await get_input_image(ctx, repository, command)
        except ValueError as e:
            await ctx.send(str(e))
            return

        # Generate ASCII art
        processor = ASCIIProcessor()
        image = Image.open(BytesIO(image_bytes))
        ascii_art = processor.convert_to_ascii(
            image,
            cols=command.ascii_params.get('cols', 80),
            scale=command.ascii_params.get('scale', 0.43),
            detailed=True
        )
        
        # Create and save both text and image versions
        ascii_image = processor.create_frame_image(ascii_art)
        output_bytes = BytesIO()
        ascii_image.save(output_bytes, format='PNG')
        output_bytes.seek(0)
        
        # Store results if tagged
        if command.tags:
            image_id = repository.store_image(
                image=output_bytes.getvalue(),
                title=f"ASCII_{ctx.author.name}",
                creator_id=str(ctx.author.id),
                creator_name=ctx.author.name,
                tags=command.tags + ['ascii'],
                parameters=command.ascii_params,
                source_image=source
            )
            await ctx.send(f"ASCII art stored with ID: {image_id}")

        # Send results
        output_bytes.seek(0)
        await ctx.send(file=discord.File(output_bytes, filename="ascii.png"))
        await ctx.send(file=discord.File('\n'.join(ascii_art).encode(), filename="ascii.txt"))

    except Exception as e:
        await ctx.send(f"Error creating ASCII art: {str(e)}")

@bot.command(name='help')
async def help_command(ctx):
    """Show help information."""
    await ctx.send(command_parser.format_help())

@bot.command(name='examples')
async def examples_command(ctx):
    """Show example commands."""
    examples = command_parser.get_example_commands()
    await ctx.send("Example commands:\n" + "\n".join(examples))

def main():
    """Main entry point."""
    if not DISCORD_TOKEN:
        print("Error: DISCORD_TOKEN not found in .env file")
        sys.exit(1)

    # Create required directories
    Path("config").mkdir(exist_ok=True)
    Path("image_storage").mkdir(exist_ok=True)
    Path("images").mkdir(exist_ok=True)  # For random image selection

    # Windows-specific event loop policy
    if sys.platform.startswith('win'):
        asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())

    print("Starting image processing bot...")
    bot.run(DISCORD_TOKEN)

if __name__ == "__main__":
    main()