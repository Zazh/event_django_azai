from django.db.models.signals import pre_save
from django.dispatch import receiver
from .models import PortfolioItem, Case, Service, ServiceGallery, ServiceLocation
from .utils import optimize_image


@receiver(pre_save, sender=PortfolioItem)
def optimize_portfolio_image(sender, instance, **kwargs):
    """Оптимизация изображений для PortfolioItem"""
    if instance.image and not instance.image.name.endswith('.webp'):
        instance.image = optimize_image(instance.image)


@receiver(pre_save, sender=Case)
def optimize_case_image(sender, instance, **kwargs):
    """Оптимизация изображений для Case - 1200px для главной страницы"""
    if instance.image and not instance.image.name.endswith('.webp'):
        instance.image = optimize_image(instance.image, max_width=1200, quality=90)


@receiver(pre_save, sender=Service)
def optimize_service_image(sender, instance, **kwargs):
    """Оптимизация изображений для Service"""
    if instance.card_image and not instance.card_image.name.endswith('.webp'):
        instance.card_image = optimize_image(instance.card_image)


@receiver(pre_save, sender=ServiceGallery)
def optimize_gallery_image(sender, instance, **kwargs):
    """Оптимизация изображений для ServiceGallery"""
    if instance.image and not instance.image.name.endswith('.webp'):
        instance.image = optimize_image(instance.image, max_width=1200, quality=90)


@receiver(pre_save, sender=ServiceLocation)
def optimize_location_image(sender, instance, **kwargs):
    """Оптимизация изображений для ServiceLocation"""
    if instance.image and not instance.image.name.endswith('.webp'):
        instance.image = optimize_image(instance.image)