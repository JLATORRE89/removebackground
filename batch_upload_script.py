import requests
import jwt
import datetime
import base64
import os
import glob

# ==== Configuration ====
API_URL = 'http://localhost:5000/api/remove-background'
IMAGE_DIR = './images_to_process'   # Folder with input images
OUTPUT_DIR = './output_results'     # Where to save processed results
JWT_SECRET = 'shared-secret-change-in-production'

# ==== Resize Settings ====
resize_option = 'custom'     # Options: original, half, quarter, custom, 720p, 1080p, 4k, etc.
resize_width = '800'         # Required if resize_option == 'custom'
resize_height = '600'

# ==== Generate JWT Token ====
payload = {
    'user_id': '123',
    'username': 'batchuser',
    'tier': 't3',  # Try 't1', 't2', or 't3'
    'exp': datetime.datetime.utcnow() + datetime.timedelta(hours=1)
}
token = jwt.encode(payload, JWT_SECRET, algorithm='HS256')
headers = {
    'Authorization': f'Bearer {token}'
}

# ==== Prepare output folder ====
os.makedirs(OUTPUT_DIR, exist_ok=True)

# ==== Find image files ====
image_paths = []
image_extensions = ['*.jpg', '*.jpeg', '*.png', '*.webp']
for ext in image_extensions:
    image_paths.extend(glob.glob(os.path.join(IMAGE_DIR, ext)))

if not image_paths:
    print("❌ No images found in", IMAGE_DIR)
    exit()

# ==== Process each image ====
for image_path in image_paths:
    image_name = os.path.basename(image_path)
    print(f"\n📤 Uploading: {image_name}")

    files = {
        'image': open(image_path, 'rb')
    }
    data = {
        'resize': resize_option
    }

    if resize_option == 'custom':
        data['width'] = resize_width
        data['height'] = resize_height

    try:
        response = requests.post(API_URL, headers=headers, files=files, data=data)
        result = response.json()

        if response.status_code == 200 and result.get("status") == "success":
            result_id = result.get("result_id")
            download_links = result.get("download_links", {})

            for fmt, data_uri in download_links.items():
                base64_data = data_uri.split(',')[1]
                ext = 'jpg' if fmt == 'jpeg' else fmt
                out_filename = f"{os.path.splitext(image_name)[0]}_{fmt}_{result_id}.{ext}"
                out_path = os.path.join(OUTPUT_DIR, out_filename)

                with open(out_path, 'wb') as out_file:
                    out_file.write(base64.b64decode(base64_data))

                print(f"✅ Saved {fmt.upper()} -> {out_path}")
        else:
            print(f"⚠️ Failed for {image_name}:", result.get("error", "Unknown error"))

    except Exception as e:
        print(f"❌ Exception while processing {image_name}:", str(e))

"""
Example Directory Structure:
Assuming the script is named `batch_upload_script.py` and is located in the root directory of your project, the directory structure would look like this:

```
your_project/
├── images_to_process/
│   ├── pic1.jpg
│   ├── pic2.webp
│   └── pic3.png
├── output_results/
│   └── (automatically created/saved results here)
└── batch_upload_script.py
"""