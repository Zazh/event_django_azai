from PIL import Image, ImageOps
import io
from django.core.files.base import ContentFile
import os

def optimize_image(image_field, max_width=700, quality=85):
    # Открываем и нормализуем ориентацию по EXIF
    img = Image.open(image_field)
    img = ImageOps.exif_transpose(img)

    # Сохраним ICC-профиль, если есть (чтобы цвета не поехали)
    icc_profile = img.info.get("icc_profile")

    # Конвертируем в RGB (прозрачность — на белый фон)
    if img.mode in ('RGBA', 'LA', 'P'):
        if img.mode == 'P':
            img = img.convert('RGBA')
        background = Image.new('RGB', img.size, (255, 255, 255))
        background.paste(img, mask=img.split()[-1] if img.mode == 'RGBA' else None)
        img = background
    elif img.mode != 'RGB':
        img = img.convert('RGB')

    # Ресайз по ширине с сохранением пропорций
    if img.width > max_width:
        ratio = max_width / img.width
        new_height = int(round(img.height * ratio))
        img = img.resize((max_width, new_height), Image.LANCZOS)

    # Сохраняем в WebP (с ICC-профилем, если был)
    output = io.BytesIO()
    save_kwargs = {"format": "WEBP", "quality": quality, "method": 6}
    if icc_profile:
        save_kwargs["icc_profile"] = icc_profile
    img.save(output, **save_kwargs)
    output.seek(0)

    original_name = os.path.splitext(getattr(image_field, "name", "image"))[0]
    new_name = f"{original_name}.webp"
    return ContentFile(output.read(), name=os.path.basename(new_name))