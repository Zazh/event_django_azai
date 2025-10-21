from django.db import models
from .utils import compress_pdf

class HeroBlock(models.Model):
    """Главный блок Hero на главной странице"""
    seo_title = models.CharField('SEO Заголовок', max_length=200, blank=True)
    seo_description = models.CharField('SEO Description', max_length=200, blank=True)
    title = models.CharField('Заголовок', max_length=200)
    subtitle = models.TextField('Подзаголовок')
    button_text = models.CharField('Текст кнопки', max_length=100)
    button_link = models.CharField('Ссылка кнопки', max_length=200)
    is_active = models.BooleanField('Активен', default=True)
    order = models.IntegerField('Порядок', default=0)

    class Meta:
        verbose_name = 'Hero блок'
        verbose_name_plural = 'Hero блоки'
        ordering = ['order']

    def __str__(self):
        return self.title


class AboutBlock(models.Model):
    """Блок О нас"""
    title = models.CharField('Заголовок', max_length=200)
    description = models.TextField('Описание')
    is_active = models.BooleanField('Активен', default=True)

    class Meta:
        verbose_name = 'Блок О нас'
        verbose_name_plural = 'Блоки О нас'

    def __str__(self):
        return self.title


class Benefit(models.Model):
    """Преимущества для блока О нас"""
    about_block = models.ForeignKey(
        AboutBlock,
        on_delete=models.CASCADE,
        related_name='benefits',
        verbose_name='Блок О нас'
    )
    number = models.CharField('Цифра', max_length=50)
    title = models.CharField('Заголовок', max_length=200)
    order = models.IntegerField('Порядок', default=0)

    class Meta:
        verbose_name = 'Преимущество'
        verbose_name_plural = 'Преимущества'
        ordering = ['order']

    def __str__(self):
        return f"{self.number} - {self.title}"


class Partner(models.Model):
    """Партнеры"""
    name = models.CharField('Название', max_length=200)
    color = models.CharField('Цвет', max_length=7, default='#000000',
                            help_text='Формат: #RRGGBB')
    svg_path = models.TextField('SVG Path')
    order = models.IntegerField('Порядок', default=0)
    is_active = models.BooleanField('Активен', default=True)

    class Meta:
        verbose_name = 'Партнер'
        verbose_name_plural = 'Партнеры'
        ordering = ['order']

    def __str__(self):
        return self.name


class PortfolioBlock(models.Model):
    """Заголовок блока Портфолио"""
    title = models.CharField('Заголовок', max_length=200)
    is_active = models.BooleanField('Активен', default=True)

    class Meta:
        verbose_name = 'Блок Портфолио'
        verbose_name_plural = 'Блоки Портфолио'

    def __str__(self):
        return self.title


class PortfolioItem(models.Model):
    """Элементы портфолио"""
    portfolio_block = models.ForeignKey(
        PortfolioBlock,
        on_delete=models.CASCADE,
        related_name='items',
        verbose_name='Блок портфолио'
    )
    image = models.ImageField('Картинка', upload_to='portfolio/')
    description = models.TextField('Описание')
    order = models.IntegerField('Порядок', default=0)
    is_active = models.BooleanField('Активен', default=True)

    class Meta:
        verbose_name = 'Элемент портфолио'
        verbose_name_plural = 'Элементы портфолио'
        ordering = ['order']

    def __str__(self):
        return f"Портфолио #{self.id}"

class Case(models.Model):
    """Кейсы на главной странице"""
    title = models.CharField('Заголовок', max_length=200)
    description = models.TextField('Описание')
    button_text = models.CharField('Текст кнопки', max_length=100)
    image = models.ImageField('Картинка', upload_to='cases/')
    order = models.IntegerField('Порядок', default=0)
    is_active = models.BooleanField('Активен', default=True)
    created_at = models.DateTimeField('Дата создания', auto_now_add=True)

    class Meta:
        verbose_name = 'Кейс'
        verbose_name_plural = 'Кейсы'
        ordering = ['order', '-created_at']

    def __str__(self):
        return self.title


class Service(models.Model):
    """Услуги"""
    # Для карточек (главная и страница услуг)
    card_image = models.ImageField('Картинка для карточки', upload_to='services/cards/')
    card_title = models.CharField('Название услуги', max_length=200)
    card_description = models.TextField('Краткое описание')
    card_tags = models.TextField('Теги', help_text='Каждый тег с новой строки')

    seo_title = models.CharField('SEO Заголовок', max_length=200, blank=True)
    seo_description = models.CharField('SEO Description', max_length=200, blank=True)

    # Для детальной страницы (Hero блок)
    hero_title = models.CharField('Hero: Заголовок', max_length=200)
    hero_subtitle = models.TextField('Hero: Подзаголовок')
    hero_button_text = models.CharField('Hero: Текст кнопки', max_length=100, blank=True)
    hero_button_link = models.CharField('Hero: Ссылка кнопки', max_length=200, blank=True)

    service_title = models.CharField('Описание услуги: Заголовок', max_length=200, blank=True)

    # PDF файл для скачивания после заявки
    pdf_file = models.FileField(
        'PDF файл',
        upload_to='services/pdfs/',
        blank=True,
        null=True,
        help_text='Если файл загружен, пользователь получит его после отправки заявки. Файл будет автоматически сжат.'
    )

    # Slug для URL
    slug = models.SlugField('URL слаг', unique=True, max_length=200)

    # Настройки
    show_on_homepage = models.BooleanField('Показывать на главной', default=True)
    order = models.IntegerField('Порядок', default=0)
    is_active = models.BooleanField('Активна', default=True)
    created_at = models.DateTimeField('Дата создания', auto_now_add=True)

    class Meta:
        verbose_name = 'Услуга'
        verbose_name_plural = 'Услуги'
        ordering = ['order', '-created_at']

    def __str__(self):
        return self.card_title

    def get_tags_list(self):
        """Возвращает список тегов"""
        return [tag.strip() for tag in self.card_tags.split('\n') if tag.strip()]

    def save(self, *args, **kwargs):
        """Переопределяем save для сжатия PDF"""
        # Проверяем, загружен ли новый PDF файл
        if self.pdf_file:
            try:
                # Получаем старый объект из БД (если он существует)
                if self.pk:
                    old_instance = Service.objects.get(pk=self.pk)
                    # Проверяем, изменился ли файл
                    if old_instance.pdf_file != self.pdf_file:
                        # Файл изменился, нужно сжать
                        compressed_pdf = compress_pdf(self.pdf_file)
                        if compressed_pdf:
                            # Сохраняем имя файла
                            file_name = self.pdf_file.name
                            # Заменяем файл на сжатый
                            self.pdf_file.save(file_name, compressed_pdf, save=False)
                else:
                    # Новый объект, сжимаем PDF
                    compressed_pdf = compress_pdf(self.pdf_file)
                    if compressed_pdf:
                        file_name = self.pdf_file.name
                        self.pdf_file.save(file_name, compressed_pdf, save=False)
            except Exception as e:
                print(f"Ошибка при обработке PDF: {e}")

        super().save(*args, **kwargs)


class ServiceAbout(models.Model):
    """Блок О нас для услуги"""
    service = models.OneToOneField(
        Service,
        on_delete=models.CASCADE,
        related_name='about',
        verbose_name='Услуга'
    )
    title = models.CharField('Заголовок', max_length=200)
    description = models.TextField('Описание')

    class Meta:
        verbose_name = 'О нас (для услуги)'
        verbose_name_plural = 'О нас (для услуг)'

    def __str__(self):
        return f"О нас: {self.service.card_title}"


class ServiceBenefit(models.Model):
    """Преимущества для блока О нас услуги"""
    service_about = models.ForeignKey(
        ServiceAbout,
        on_delete=models.CASCADE,
        related_name='benefits',
        verbose_name='Блок О нас'
    )
    number = models.CharField('Цифра', max_length=50)
    title = models.CharField('Заголовок', max_length=200)
    order = models.IntegerField('Порядок', default=0)

    class Meta:
        verbose_name = 'Преимущество услуги'
        verbose_name_plural = 'Преимущества услуги'
        ordering = ['order']

    def __str__(self):
        return f"{self.number} - {self.title}"


class ServiceItem(models.Model):
    """Пункты услуги (описание того, что входит в услугу)"""
    service = models.ForeignKey(
        Service,
        on_delete=models.CASCADE,
        related_name='items',
        verbose_name='Услуга'
    )
    title = models.CharField('Заголовок пункта', max_length=200)
    svg_path = models.TextField('SVG Path')
    description = models.TextField('Краткое описание')
    order = models.IntegerField('Порядок', default=0)

    class Meta:
        verbose_name = 'Пункт услуги'
        verbose_name_plural = 'Пункты услуги'
        ordering = ['order']

    def __str__(self):
        return self.title


class ServiceLocation(models.Model):
    """Блок Место проведения"""
    service = models.OneToOneField(
        Service,
        on_delete=models.CASCADE,
        related_name='location',
        verbose_name='Услуга'
    )
    title = models.CharField('Заголовок', max_length=200)
    description = models.TextField('Описание')
    image = models.ImageField('Картинка', upload_to='services/locations/')
    button_text = models.CharField('Текст кнопки', max_length=100)
    button_link = models.CharField('Ссылка кнопки', max_length=200)

    class Meta:
        verbose_name = 'Место проведения'
        verbose_name_plural = 'Места проведения'

    def __str__(self):
        return f"Место: {self.service.card_title}"



class ServiceGallery(models.Model):
    """Галерея для услуги"""
    ORIENTATION_CHOICES = [
        ('tall', 'Вертикальная'),
        ('square', 'Квадратная'),
    ]

    service = models.ForeignKey(
        Service,
        on_delete=models.CASCADE,
        related_name='gallery',
        verbose_name='Услуга'
    )
    image = models.ImageField('Картинка', upload_to='services/gallery/')
    title = models.CharField('Заголовок', max_length=200)
    description = models.TextField('Описание')
    orientation = models.CharField(
        'Ориентация',
        max_length=10,
        choices=ORIENTATION_CHOICES,
        default='square'
    )
    order = models.IntegerField('Порядок', default=0)
    is_active = models.BooleanField('Активна', default=True)

    class Meta:
        verbose_name = 'Элемент галереи'
        verbose_name_plural = 'Галерея услуги'
        ordering = ['order']

    def __str__(self):
        return f"{self.title} ({self.get_orientation_display()})"


class ServicePartner(models.Model):
    """Партнеры для страниц услуг"""
    name = models.CharField('Название', max_length=200)
    color = models.CharField('Цвет', max_length=7, default='#000000',
                            help_text='Формат: #RRGGBB')
    svg_path = models.TextField('SVG Path')
    order = models.IntegerField('Порядок', default=0)
    is_active = models.BooleanField('Активен', default=True)

    class Meta:
        verbose_name = 'Партнер услуг'
        verbose_name_plural = 'Партнеры услуг'
        ordering = ['order']

    def __str__(self):
        return self.name


class ServiceFormBlock(models.Model):
    """Блок с формой заявки для услуги"""
    service = models.OneToOneField(
        Service,
        on_delete=models.CASCADE,
        related_name='form_block',
        verbose_name='Услуга'
    )
    title = models.CharField('Заголовок', max_length=200)
    subtitle = models.TextField('Подзаголовок')
    button_text = models.CharField('Текст кнопки', max_length=100, default='Оставить заявку')
    is_active = models.BooleanField('Активен', default=True)

    class Meta:
        verbose_name = 'Блок формы заявки'
        verbose_name_plural = 'Блоки форм заявок'

    def __str__(self):
        return f"Форма: {self.service.card_title}"


class Contact(models.Model):
    """Контактная информация (единственная запись)"""
    company_name = models.CharField('Название компании', max_length=200)
    email = models.EmailField('Email')
    phone = models.CharField('Телефон', max_length=50)
    address = models.TextField('Адрес')
    map_link = models.URLField('Ссылка на карту', help_text='Google Maps или Яндекс Карты')
    is_active = models.BooleanField('Активен', default=True)

    class Meta:
        verbose_name = 'Контактная информация'
        verbose_name_plural = 'Контактная информация'

    def __str__(self):
        return self.company_name


class SocialNetwork(models.Model):
    """Социальные сети"""
    contact = models.ForeignKey(
        Contact,
        on_delete=models.CASCADE,
        related_name='social_networks',
        verbose_name='Контакты'
    )
    name = models.CharField('Название', max_length=100)
    link = models.URLField('Ссылка')
    svg_path = models.TextField('SVG Path')
    order = models.IntegerField('Порядок', default=0)

    class Meta:
        verbose_name = 'Социальная сеть'
        verbose_name_plural = 'Социальные сети'
        ordering = ['order']

    def __str__(self):
        return self.name