import pikepdf
from PIL import Image, ImageOps
import io
from pikepdf import Pdf
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


def compress_pdf(pdf_file, quality='ebook'):
    """
    Сжимает PDF файл

    Args:
        pdf_file: Django FieldFile объект
        quality: уровень качества ('screen', 'ebook', 'printer', 'prepress')
                 - screen: 72 dpi (самое сильное сжатие)
                 - ebook: 150 dpi (хорошее сжатие, рекомендуется)
                 - printer: 300 dpi (среднее сжатие)
                 - prepress: 300 dpi (минимальное сжатие)

    Returns:
        ContentFile с сжатым PDF
    """
    try:
        # Открываем PDF
        pdf = Pdf.open(pdf_file)

        # Создаем буфер для сжатого файла
        output_buffer = io.BytesIO()

        # Сохраняем с оптимизацией
        pdf.save(
            output_buffer,
            compress_streams=True,
            stream_decode_level=pikepdf.StreamDecodeLevel.generalized,
            object_stream_mode=pikepdf.ObjectStreamMode.generate,
            recompress_flate=True,
            normalize_content=True,
        )

        pdf.close()

        # Получаем размеры
        original_size = pdf_file.size
        output_buffer.seek(0)
        compressed_size = len(output_buffer.getvalue())

        # Если сжатие дало результат (уменьшило размер более чем на 5%)
        if compressed_size < original_size * 0.95:
            print(f"PDF сжат: {original_size / 1024 / 1024:.2f} MB -> {compressed_size / 1024 / 1024:.2f} MB")
            return ContentFile(output_buffer.getvalue())
        else:
            print("PDF уже оптимизирован, сжатие не требуется")
            return None

    except Exception as e:
        print(f"Ошибка при сжатии PDF: {e}")
        return None