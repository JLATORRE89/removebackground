Help me enhance my Flask-based background removal app. I want to:

Handle image upload directly from the / route (with processing like in /api)

Add drag-and-drop image upload support (in addition to file picker)

Show a real-time preview of the uploaded image before submitting

Display a loading animation while the image is being processed

Use a dropdown to select tier (Basic, Standard, Premium) instead of relying on query params

Save a history of processed images in the session and allow users to re-download them

The frontend uses Jinja2 templates and basic HTML/CSS. The backend is Flask, using rembg and Pillow. Keep the experience lightweight, mobile-friendly, and do not require a login for now.