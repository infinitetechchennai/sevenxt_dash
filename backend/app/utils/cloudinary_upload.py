import cloudinary
import cloudinary.uploader
import io
from PIL import Image, ImageOps
from app.config import settings

# Configure Cloudinary from env vars
cloudinary.config(
    cloud_name=settings.CLOUDINARY_CLOUD_NAME,
    api_key=settings.CLOUDINARY_API_KEY,
    api_secret=settings.CLOUDINARY_API_SECRET,
    secure=True
)


def upload_image_to_cloudinary(
    file_bytes: bytes,
    folder: str,
    resize_width: int = None,
    aspect_ratio: tuple = None,  # e.g. (1000, 535) for banners
    quality: int = 85,
) -> str:
    """
    Upload an image to Cloudinary and return the secure URL.

    Args:
        file_bytes: Raw image bytes
        folder: Cloudinary folder (e.g. 'products', 'cms/banners')
        resize_width: If set, resize image to this max width (keeps aspect ratio)
        aspect_ratio: If set as (width, height), crop/fit to this exact size
        quality: JPEG quality (default 85)

    Returns:
        Secure Cloudinary URL string
    """
    image = Image.open(io.BytesIO(file_bytes))

    # Convert RGBA/P/LA to RGB
    if image.mode in ("RGBA", "LA", "P"):
        background = Image.new("RGB", image.size, (255, 255, 255))
        if image.mode == "P":
            image = image.convert("RGBA")
        background.paste(image, mask=image.split()[-1] if image.mode in ("RGBA", "LA") else None)
        image = background

    # Apply resize transformations
    if aspect_ratio:
        image = ImageOps.fit(image, aspect_ratio, Image.Resampling.LANCZOS)
    elif resize_width and image.width > resize_width:
        ratio = image.height / image.width
        image = image.resize((resize_width, int(resize_width * ratio)), Image.Resampling.LANCZOS)

    # Save to buffer
    buffer = io.BytesIO()
    image.save(buffer, format="JPEG", quality=quality, optimize=True)
    buffer.seek(0)

    # Upload to Cloudinary
    result = cloudinary.uploader.upload(
        buffer,
        folder=folder,
        resource_type="image",
    )

    return result["secure_url"]


def upload_raw_to_cloudinary(file_bytes: bytes, folder: str, filename: str) -> str:
    """
    Upload any file (PDF, etc.) to Cloudinary as a raw resource and return URL.
    """
    result = cloudinary.uploader.upload(
        file_bytes,
        folder=folder,
        resource_type="raw",
        public_id=filename,
    )
    return result["secure_url"]
