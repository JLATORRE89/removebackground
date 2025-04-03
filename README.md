# Background Removal Web Application

A Flask-based web application that removes backgrounds from images using the rembg library. The application offers both a web interface and a REST API for integrating with other services.

## Features

- **Background Removal**: Easily remove backgrounds from uploaded images.
- **Multiple Output Formats**: Download processed images in PNG, WebP, and JPEG formats (depending on tier).
- **Resize Options**: Various resizing options including original size, half size, quarter size, and custom dimensions.
- **Video Format Sizes**: Standard video resolution options (720p, 1080p, 1440p, 4K) for perfect social media uploads.
- **Tiered Access**: Three different subscription tiers (Basic, Standard, Premium) with progressive features.
- **JWT Authentication**: Secure API access with JWT token authentication.

## System Requirements

- Python 3.6+
- Flask
- PIL (Pillow)
- rembg
- PyJWT

## Installation

1. Clone the repository:
   ```
   git clone https://github.com/yourusername/background-removal-app.git
   cd background-removal-app
   ```

2. Create and activate a virtual environment:
   ```
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   ```

3. Install dependencies:
   ```
   pip install flask pillow rembg pyjwt
   ```

4. Run the application:
   ```
   python app.py
   ```

5. Access the web interface at http://localhost:5000

## Configuration

You can configure the application using environment variables:

- `JWT_SECRET_KEY`: Secret key for JWT token generation and validation
- `OUTPUT_FOLDER`: Directory for storing processed images
- `MAX_CONTENT_LENGTH`: Maximum upload file size (default: 16MB)

## API Usage

The application provides a REST API for background removal:

### Remove Background Endpoint

```
POST /api/remove-background
```

#### Headers
- `Authorization`: Bearer token with JWT

#### Request Body
- `image`: Image file to process (multipart/form-data)
- `resize`: Resize option (original, half, quarter, custom, 720p, 1080p, 1440p, 4k)
- `width`: Custom width (if resize=custom)
- `height`: Custom height (if resize=custom)

#### Example Request
```python
import requests
import jwt
import datetime

# Create JWT token
payload = {
    'user_id': '123',
    'username': 'testuser',
    'tier': 't2',  # t1, t2, or t3
    'exp': datetime.datetime.utcnow() + datetime.timedelta(hours=1)
}
token = jwt.encode(payload, 'shared-secret-change-in-production', algorithm='HS256')

# API request
url = 'http://localhost:5000/api/remove-background'
headers = {'Authorization': f'Bearer {token}'}
files = {'image': open('test_image.jpg', 'rb')}
data = {'resize': 'original'}

response = requests.post(url, headers=headers, files=files, data=data)
result = response.json()
```

#### Response
```json
{
  "status": "success",
  "result_id": "8f7d2a5e-4b3c-4b1a-8c1e-9c8f2a5e4b3c",
  "image_data": {
    "png": "base64_encoded_image_data",
    "webp": "base64_encoded_image_data"
  },
  "download_links": {
    "png": "data:image/png;base64,base64_encoded_image_data",
    "webp": "data:image/webp;base64,base64_encoded_image_data"
  },
  "file_sizes": {
    "png": "1.2 MB",
    "webp": "423.5 KB"
  },
  "original_width": 1920,
  "original_height": 1080,
  "tier": "t2",
  "username": "testuser"
}
```

## Tier Features

### Basic (t1)
- PNG and WebP formats
- Original, half, and quarter size options

### Standard (t2)
- PNG and WebP formats
- Original, half, quarter, and custom size options
- Video formats: 720p, 1080p

### Premium (t3)
- PNG, WebP, and JPEG formats
- Original, half, quarter, and custom size options
- Video formats: 720p, 1080p, 1440p, 4K

## License

[MIT License](LICENSE)

## Credits

- Background removal powered by the [rembg](https://github.com/danielgatis/rembg) library
- Built with Flask web framework