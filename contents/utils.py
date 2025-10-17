from PIL import Image
from io import BytesIO
from django.core.files.base import ContentFile
import os


def optimize_image(image_field, max_width=700, quality=85):
    """
    Оптимизирует изображение: изменяет размер и конвертирует в WebP

    :param image_field: ImageField из модели
    :param max_width: максимальная ширина изображения
    :param quality: качество WebP (1-100)
    :return: оптимизированное изображение
    """
    # Открываем изображение
    img = Image.open(image_field)

    # Конвертируем в RGB если нужно (для PNG с прозрачностью)
    if img.mode in ('RGBA', 'LA', 'P'):
        # Создаем белый фон для прозрачных изображений
        background = Image.new('RGB', img.size, (255, 255, 255))
        if img.mode == 'P':
            img = img.convert('RGBA')
        background.paste(img, mask=img.split()[-1] if img.mode == 'RGBA' else None)
        img = background
    elif img.mode != 'RGB':
        img = img.convert('RGB')

    # Изменяем размер если ширина больше max_width
    if img.width > max_width:
        # Вычисляем новую высоту с сохранением пропорций
        ratio = max_width / img.width
        new_height = int(img.height * ratio)
        img = img.resize((max_width, new_height), Image.LANCZOS)

    # Сохраняем в WebP
    output = BytesIO()
    img.save(output, format='WEBP', quality=quality, method=6)
    output.seek(0)

    # Получаем имя файла и меняем расширение на .webp
    original_name = os.path.splitext(image_field.name)[0]
    new_name = f"{original_name}.webp"

    # Возвращаем ContentFile с новым именем
    return ContentFile(output.read(), name=os.path.basename(new_name))