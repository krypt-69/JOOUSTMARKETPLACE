"""
Image Compression Utility
Handles compression of uploaded images for products, rooms, and chat
"""

import os
from PIL import Image
from flask import current_app
import logging

# Compression configuration
COMPRESSION_CONFIG = {
    'max_width': 1200,
    'max_height': 1200,
    'quality': 85,
    'max_size_kb': 500,
    'compress_png': True,  # Convert PNG to JPEG? (saves space but loses transparency)
}

def compress_image(filepath, is_chat_image=False):
    """
    Compress an image file
    
    Args:
        filepath: Path to the image file
        is_chat_image: If True, use different compression settings for chat
    
    Returns:
        dict: {
            'success': bool,
            'original_size': int,  # in bytes
            'compressed_size': int,  # in bytes
            'saved_bytes': int,
            'saved_percent': float,
            'message': str
        }
    """
    try:
        # Get original file size
        original_size = os.path.getsize(filepath)
        original_size_kb = original_size / 1024
        
        # If image is already small (< 100KB), maybe skip compression
        if original_size_kb < 100:
            current_app.logger.info(f"Image already small ({original_size_kb:.1f}KB), skipping compression")
            return {
                'success': True,
                'original_size': original_size,
                'compressed_size': original_size,
                'saved_bytes': 0,
                'saved_percent': 0,
                'message': 'Image already optimized'
            }
        
        # Open and optimize image
        with Image.open(filepath) as img:
            # Get original format
            original_format = img.format
            
            # Convert RGBA to RGB for JPEG (remove transparency)
            if img.mode in ('RGBA', 'LA', 'P'):
                # Create white background for transparency
                if img.mode == 'P':
                    img = img.convert('RGBA')
                
                # Check if image has transparency
                has_transparency = False
                if img.mode == 'RGBA':
                    # Check if any pixel has alpha < 255
                    alpha = img.getchannel('A')
                    if alpha.getextrema()[0] < 255:
                        has_transparency = True
                
                if has_transparency and original_format == 'PNG':
                    # Keep PNG with transparency but compress
                    # Will compress later with PNG optimization
                    pass
                else:
                    # Convert to RGB for JPEG (no transparency)
                    background = Image.new('RGB', img.size, (255, 255, 255))
                    if img.mode == 'RGBA':
                        background.paste(img, mask=img.split()[-1])
                    else:
                        background.paste(img)
                    img = background
            
            # Resize if too large (maintain aspect ratio)
            width, height = img.size
            max_width = COMPRESSION_CONFIG['max_width']
            max_height = COMPRESSION_CONFIG['max_height']
            
            if width > max_width or height > max_height:
                # Calculate new dimensions while maintaining aspect ratio
                ratio = min(max_width / width, max_height / height)
                new_width = int(width * ratio)
                new_height = int(height * ratio)
                img = img.resize((new_width, new_height), Image.Resampling.LANCZOS)
                current_app.logger.info(f"Resized image from {width}x{height} to {new_width}x{new_height}")
            
            # Determine output format and save
            output_format = 'JPEG'  # Default to JPEG for better compression
            output_quality = COMPRESSION_CONFIG['quality']
            
            # For chat images, use slightly lower quality (they're smaller anyway)
            if is_chat_image:
                output_quality = 75
            
            # Keep PNG if it has transparency and original was PNG
            if original_format == 'PNG' and img.mode == 'RGBA':
                output_format = 'PNG'
                # PNG quality is handled differently (0-9 compression)
                # We'll use optimize=True instead
                img.save(filepath, format='PNG', optimize=True)
            else:
                # Save as JPEG
                img.save(filepath, format='JPEG', quality=output_quality, optimize=True)
            
            # Get new file size
            compressed_size = os.path.getsize(filepath)
            saved_bytes = original_size - compressed_size
            saved_percent = (saved_bytes / original_size) * 100 if original_size > 0 else 0
            
            # Log compression results
            current_app.logger.info(
                f"Compressed {filepath}: "
                f"{original_size/1024:.1f}KB -> {compressed_size/1024:.1f}KB "
                f"({saved_percent:.1f}% saved)"
            )
            
            # If still too large (>500KB) and we haven't compressed enough, try one more time with lower quality
            compressed_size_kb = compressed_size / 1024
            if compressed_size_kb > COMPRESSION_CONFIG['max_size_kb'] and output_format == 'JPEG':
                current_app.logger.info(f"Image still large ({compressed_size_kb:.1f}KB), applying extra compression")
                
                # Re-open and compress with lower quality
                with Image.open(filepath) as img2:
                    lower_quality = max(50, output_quality - 15)
                    img2.save(filepath, format='JPEG', quality=lower_quality, optimize=True)
                    
                    # Get final size
                    final_size = os.path.getsize(filepath)
                    final_size_kb = final_size / 1024
                    current_app.logger.info(f"Extra compression: {compressed_size_kb:.1f}KB -> {final_size_kb:.1f}KB")
                    
                    compressed_size = final_size
                    saved_bytes = original_size - compressed_size
                    saved_percent = (saved_bytes / original_size) * 100 if original_size > 0 else 0
            
            return {
                'success': True,
                'original_size': original_size,
                'compressed_size': compressed_size,
                'saved_bytes': saved_bytes,
                'saved_percent': round(saved_percent, 2),
                'message': f"Compressed successfully ({saved_percent:.1f}% saved)"
            }
            
    except Exception as e:
        current_app.logger.error(f"Error compressing image {filepath}: {str(e)}")
        return {
            'success': False,
            'original_size': 0,
            'compressed_size': 0,
            'saved_bytes': 0,
            'saved_percent': 0,
            'message': f"Compression failed: {str(e)}"
        }

def compress_multiple_images(filepaths, is_chat_image=False):
    """
    Compress multiple images
    
    Args:
        filepaths: List of file paths to compress
        is_chat_image: Pass to individual compression
    
    Returns:
        dict: Summary statistics
    """
    results = []
    total_original = 0
    total_compressed = 0
    
    for filepath in filepaths:
        result = compress_image(filepath, is_chat_image)
        results.append(result)
        total_original += result['original_size']
        total_compressed += result['compressed_size']
    
    total_saved = total_original - total_compressed
    total_saved_percent = (total_saved / total_original) * 100 if total_original > 0 else 0
    
    return {
        'success': all(r['success'] for r in results),
        'total_images': len(filepaths),
        'total_original_size': total_original,
        'total_compressed_size': total_compressed,
        'total_saved_bytes': total_saved,
        'total_saved_percent': round(total_saved_percent, 2),
        'results': results
    }

def should_compress_file(filename):
    """
    Check if file should be compressed based on extension
    
    Args:
        filename: Name of the file
    
    Returns:
        bool: True if file should be compressed
    """
    image_extensions = {'.jpg', '.jpeg', '.png', '.gif', '.webp', '.bmp'}
    ext = os.path.splitext(filename)[1].lower()
    return ext in image_extensions