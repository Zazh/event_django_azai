from django.shortcuts import render, get_object_or_404
from .constants import DIRECTION_DESCRIPTIONS
from .models import HeroBlock, AboutBlock, Partner, PortfolioBlock, Case, Service, ServicePartner, Contact


def group_by_direction(services):
    """Услуги по направлениям в порядке «DN Events», «DN Production».

    Пустая группа не выводится. Каждой услуге проставляется сквозной номер `number`
    (нумерация аккордеона на главной не начинается заново в каждой группе).
    """
    services = list(services)
    groups = []
    number = 0
    for key, label in Service.DIRECTION_CHOICES:
        items = [service for service in services if service.direction == key]
        if not items:
            continue
        for service in items:
            number += 1
            service.number = number
        groups.append({
            'key': key,
            'label': label,
            'description': DIRECTION_DESCRIPTIONS.get(key, ''),
            'services': items,
        })
    return groups


def catalog_sections(service):
    """Категории каталога: основной список (без раздела), затем разделы в порядке первого появления."""
    sections = {}
    for category in service.categories.all():
        sections.setdefault(category.group.strip(), []).append(category)
    main = sections.pop('', [])
    return (
        ([{'title': '', 'categories': main}] if main else [])
        + [{'title': title, 'categories': categories} for title, categories in sections.items()]
    )


def home_page(request):
    """Главная страница"""
    # Дочерние страницы (концепции) в аккордеон не попадают — они внутри своего хаба
    services = Service.objects.filter(is_active=True, show_on_homepage=True, parent__isnull=True)[:10]
    context = {
        'hero': HeroBlock.objects.filter(is_active=True).first(),
        'about': AboutBlock.objects.filter(is_active=True).first(),
        'partners': Partner.objects.filter(is_active=True),
        'portfolio': PortfolioBlock.objects.filter(is_active=True).first(),
        'cases': Case.objects.filter(is_active=True),
        'novelties': Service.objects.filter(is_active=True, show_on_homepage=True).exclude(badge=''),
        'service_groups': group_by_direction(services),
    }
    return render(request, 'contents/home.html', context)

def services_list(request):
    """Страница всех услуг: по направлениям, без дочерних страниц"""
    services = Service.objects.filter(is_active=True, parent__isnull=True)
    context = {
        'service_groups': group_by_direction(services),
    }
    return render(request, 'contents/services.html', context)


def service_detail(request, slug):
    """Страница услуги: обычная, хаб (есть дочерние страницы) или концепция (есть родитель)"""
    service = get_object_or_404(Service, slug=slug, is_active=True)
    parent = service.parent if service.parent_id and service.parent.is_active else None
    siblings = (
        parent.children.filter(is_active=True).exclude(pk=service.pk)
        if parent else Service.objects.none()
    )
    context = {
        'service': service,
        'partners': ServicePartner.objects.filter(is_active=True),
        'concepts': service.children.filter(is_active=True),
        'parent': parent,
        'siblings': siblings,
        'catalog': catalog_sections(service),
    }
    return render(request, 'contents/service_detail.html', context)


def contact_page(request):
    """Страница контактов"""
    contact = Contact.objects.filter(is_active=True).first()
    context = {
        'contact': contact,
    }
    return render(request, 'contents/contact.html', context)