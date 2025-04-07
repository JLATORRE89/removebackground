from flask import Flask, request, jsonify, render_template, redirect, url_for, session
from rembg import remove
from PIL import Image, UnidentifiedImageError
from io import BytesIO
import base64
import time
import uuid
import os
import jwt
from werkzeug.utils import secure_filename

app = Flask(__name__)
app.secret_key = os.urandom(24)

# Configuration
app.config['JWT_SECRET_KEY'] = os.environ.get('JWT_SECRET_KEY', 'shared-secret-change-in-production')
app.config['OUTPUT_FOLDER'] = os.environ.get('OUTPUT_FOLDER', 'output')
app.config['MAX_CONTENT_LENGTH'] = 16 * 1024 * 1024  # 16MB max upload size

# Store processed images temporarily (for API use)
TEMP_STORAGE = {}

# Define feature tiers
TIERS = {
    't1': {
        'title': 'Basic',
        'formats': ['png', 'webp'],  # WebP available in all tiers
        'resize_options': ['original', 'half', 'quarter'],
        'video_formats': []
    },
    't2': {
        'title': 'Standard',
        'formats': ['png', 'webp'],
        'resize_options': ['original', 'half', 'quarter', 'custom'],
        'video_formats': ['720p', '1080p']
    },
    't3': {
        'title': 'Premium',
        'formats': ['png', 'webp', 'jpeg'],
        'resize_options': ['original', 'half', 'quarter', 'custom'],
        'video_formats': ['720p', '1080p', '1440p', '4k']
    }
}

# Default to highest tier if no tier is specified
DEFAULT_TIER = 't1'

# API endpoint for background removal
@app.route('/api/remove-background', methods=['POST'])
def api_remove_background():
    """API endpoint for background removal with JWT authentication"""
    # Verify JWT token
    auth_header = request.headers.get('Authorization')
    if not auth_header or not auth_header.startswith('Bearer '):
        return jsonify({"error": "Missing or invalid authorization"}), 401
    
    token = auth_header.split(' ')[1]
    
    try:
        # Verify and decode the token
        payload = jwt.decode(token, app.config['JWT_SECRET_KEY'], algorithms=["HS256"])
        
        # Extract user info and tier
        user_id = payload.get('user_id')
        username = payload.get('username')
        tier = payload.get('tier', DEFAULT_TIER)
        
        # Validate tier
        if tier not in TIERS:
            tier = DEFAULT_TIER
        
        tier_features = TIERS[tier]
        
        # Check if image file was uploaded
        if 'image' not in request.files:
            return jsonify({"error": "No image file uploaded"}), 400
        
        image_file = request.files['image']
        if image_file.filename == '':
            return jsonify({"error": "No image selected"}), 400
        
        try:
            # Read the image file
            file = image_file.read()
            
            # Process with rembg
            result_bytes = remove(file)
            
            # Convert to PIL Image
            result = Image.open(BytesIO(result_bytes))
            
            # Store original dimensions
            original_width, original_height = result.size
            
            # Handle resize options based on tier
            resize = request.form.get('resize', 'original')
            
            # Validate resize option is available for this tier
            if resize.startswith('custom'):
                if 'custom' not in tier_features['resize_options']:
                    resize = 'original'
            elif resize in tier_features['video_formats']:
                # This is a video format, check if allowed
                if resize not in tier_features['video_formats']:
                    resize = 'original'
            elif resize not in tier_features['resize_options']:
                resize = 'original'
            
            # Apply resize
            if resize == 'custom' and 'custom' in tier_features['resize_options']:
                try:
                    resize_width = request.form.get('width')
                    resize_height = request.form.get('height')
                    new_width = int(resize_width)
                    new_height = int(resize_height)
                    if new_width > 0 and new_height > 0:
                        result = result.resize((new_width, new_height), Image.LANCZOS)
                except (ValueError, TypeError):
                    pass  # Ignore invalid resize values
            elif resize == 'half' and 'half' in tier_features['resize_options']:
                result = result.resize((original_width // 2, original_height // 2), Image.LANCZOS)
            elif resize == 'quarter' and 'quarter' in tier_features['resize_options']:
                result = result.resize((original_width // 4, original_height // 4), Image.LANCZOS)
            # Video formats
            elif resize == '720p' and '720p' in tier_features['video_formats']:
                result = result.resize((1280, 720), Image.LANCZOS)
            elif resize == '1080p' and '1080p' in tier_features['video_formats']:
                result = result.resize((1920, 1080), Image.LANCZOS)
            elif resize == '1440p' and '1440p' in tier_features['video_formats']:
                result = result.resize((2560, 1440), Image.LANCZOS)
            elif resize == '4k' and '4k' in tier_features['video_formats']:
                result = result.resize((3840, 2160), Image.LANCZOS)
            
            # Generate image formats for download based on tier
            image_data = {}
            file_sizes = {}
            download_links = {}
            
            # Generate PNG format (available for all tiers)
            if 'png' in tier_features['formats']:
                png_io = BytesIO()
                result.save(png_io, 'PNG')
                png_io.seek(0)
                png_size = len(png_io.getvalue())
                file_sizes['png'] = format_size(png_size)
                png_data = base64.b64encode(png_io.getvalue()).decode('utf-8')
                image_data['png'] = png_data
                download_links['png'] = f"data:image/png;base64,{png_data}"
            
            # Generate WebP format (available in all tiers)
            if 'webp' in tier_features['formats']:
                webp_io = BytesIO()
                result.save(webp_io, 'WEBP', quality=90)
                webp_io.seek(0)
                webp_size = len(webp_io.getvalue())
                file_sizes['webp'] = format_size(webp_size)
                webp_data = base64.b64encode(webp_io.getvalue()).decode('utf-8')
                image_data['webp'] = webp_data
                download_links['webp'] = f"data:image/webp;base64,{webp_data}"
            
            # Generate JPEG format (t3 only)
            if 'jpeg' in tier_features['formats']:
                if result.mode == 'RGBA':
                    jpeg_image = Image.new('RGB', result.size, (255, 255, 255))
                    jpeg_image.paste(result, (0, 0), result)
                else:
                    jpeg_image = result.convert('RGB')
                
                jpeg_io = BytesIO()
                jpeg_image.save(jpeg_io, 'JPEG', quality=90)
                jpeg_io.seek(0)
                jpeg_size = len(jpeg_io.getvalue())
                file_sizes['jpeg'] = format_size(jpeg_size)
                jpeg_data = base64.b64encode(jpeg_io.getvalue()).decode('utf-8')
                image_data['jpeg'] = jpeg_data
                download_links['jpeg'] = f"data:image/jpeg;base64,{jpeg_data}"
            
            # Create a result ID for this processing
            result_id = str(uuid.uuid4())
            
            # Create response data
            response_data = {
                "status": "success",
                "result_id": result_id,
                "image_data": image_data,
                "download_links": download_links,
                "file_sizes": file_sizes,
                "original_width": original_width,
                "original_height": original_height,
                "tier": tier,
                "username": username
            }
            
            return jsonify(response_data)
            
        except Exception as e:
            return jsonify({"error": f"Error processing image: {str(e)}"}), 500
            
    except jwt.ExpiredSignatureError:
        return jsonify({"error": "Token expired"}), 401
    except jwt.InvalidTokenError:
        return jsonify({"error": "Invalid token"}), 401

def format_size(size_bytes):
    """Format file size to human-readable format"""
    if size_bytes < 1024:
        return f"{size_bytes} bytes"
    elif size_bytes < 1024 * 1024:
        return f"{size_bytes / 1024:.1f} KB"
    else:
        return f"{size_bytes / (1024 * 1024):.1f} MB"

# Clean up old temporary storage periodically
def cleanup_old_storage():
    """Remove items older than 30 minutes from temporary storage"""
    current_time = time.time()
    keys_to_delete = []
    
    for key, data in TEMP_STORAGE.items():
        # Remove if older than 30 minutes (1800 seconds)
        if current_time - data.get('timestamp', 0) > 1800:
            keys_to_delete.append(key)
    
    for key in keys_to_delete:
        TEMP_STORAGE.pop(key, None)

# Direct access routes (for testing only)
@app.route('/', methods=['GET'])
def home():
    tier = DEFAULT_TIER
    tier_features = TIERS[tier]
    return render_template('index.html', tier=tier, tier_features=tier_features)

@app.route('/api_info', methods=['GET'])
def api_info():  # ✅ different name
    return render_template('api_info.html')

@app.route('/api', methods=['GET', 'POST'])
def api_ui():
    """JWT-protected web UI for the API with tier-based controls"""
    error = None
    image_data = None
    download_links = {}
    file_sizes = {}
    original_width = None
    original_height = None

    # --- JWT authentication ---
    auth_header = request.headers.get('Authorization')
    if not auth_header or not auth_header.startswith('Bearer '):
        return "Unauthorized: Missing or invalid authorization header", 401

    token = auth_header.split(' ')[1]
    try:
        payload = jwt.decode(token, app.config['JWT_SECRET_KEY'], algorithms=["HS256"])
        username = payload.get('username', 'anonymous')
        tier = payload.get('tier', DEFAULT_TIER)
        if tier not in TIERS:
            tier = DEFAULT_TIER
        tier_features = TIERS[tier]
    except jwt.ExpiredSignatureError:
        return "Unauthorized: Token expired", 401
    except jwt.InvalidTokenError:
        return "Unauthorized: Invalid token", 401

    if request.method == 'POST':
        try:
            image_file = request.files.get('image')
            if not image_file or image_file.filename == '':
                error = "Please upload an image."
                return render_template('index.html', error=error, tier=tier, tier_features=tier_features)

            file = image_file.read()
            result_bytes = remove(file)
            result = Image.open(BytesIO(result_bytes))

            original_width, original_height = result.size
            resize = request.form.get('resize', 'original')

            # Resize logic
            if resize == 'custom' and 'custom' in tier_features['resize_options']:
                try:
                    new_width = int(request.form.get('width'))
                    new_height = int(request.form.get('height'))
                    if new_width > 0 and new_height > 0:
                        result = result.resize((new_width, new_height), Image.LANCZOS)
                except Exception:
                    pass
            elif resize == 'half' and 'half' in tier_features['resize_options']:
                result = result.resize((original_width // 2, original_height // 2), Image.LANCZOS)
            elif resize == 'quarter' and 'quarter' in tier_features['resize_options']:
                result = result.resize((original_width // 4, original_height // 4), Image.LANCZOS)
            elif resize == '720p' and '720p' in tier_features['video_formats']:
                result = result.resize((1280, 720), Image.LANCZOS)
            elif resize == '1080p' and '1080p' in tier_features['video_formats']:
                result = result.resize((1920, 1080), Image.LANCZOS)
            elif resize == '1440p' and '1440p' in tier_features['video_formats']:
                result = result.resize((2560, 1440), Image.LANCZOS)
            elif resize == '4k' and '4k' in tier_features['video_formats']:
                result = result.resize((3840, 2160), Image.LANCZOS)

            # Format outputs
            if 'png' in tier_features['formats']:
                png_io = BytesIO()
                result.save(png_io, 'PNG')
                png_io.seek(0)
                file_sizes['png'] = format_size(len(png_io.getvalue()))
                png_data = base64.b64encode(png_io.getvalue()).decode('utf-8')
                download_links['png'] = f"data:image/png;base64,{png_data}"

            if 'webp' in tier_features['formats']:
                webp_io = BytesIO()
                result.save(webp_io, 'WEBP', quality=90)
                webp_io.seek(0)
                file_sizes['webp'] = format_size(len(webp_io.getvalue()))
                webp_data = base64.b64encode(webp_io.getvalue()).decode('utf-8')
                download_links['webp'] = f"data:image/webp;base64,{webp_data}"

            if 'jpeg' in tier_features['formats']:
                if result.mode == 'RGBA':
                    jpeg_image = Image.new('RGB', result.size, (255, 255, 255))
                    jpeg_image.paste(result, (0, 0), result)
                else:
                    jpeg_image = result.convert('RGB')
                jpeg_io = BytesIO()
                jpeg_image.save(jpeg_io, 'JPEG', quality=90)
                jpeg_io.seek(0)
                file_sizes['jpeg'] = format_size(len(jpeg_io.getvalue()))
                jpeg_data = base64.b64encode(jpeg_io.getvalue()).decode('utf-8')
                download_links['jpeg'] = f"data:image/jpeg;base64,{jpeg_data}"

            image_data = png_data if 'png' in tier_features['formats'] else None

        except Exception as e:
            error = f"An error occurred: {str(e)}"

    return render_template('index.html',
                           error=error,
                           image_data=image_data,
                           download_links=download_links,
                           file_sizes=file_sizes,
                           original_width=original_width,
                           original_height=original_height,
                           tier=tier,
                           tier_features=tier_features)


if __name__ == '__main__':
    app.run(debug=True)