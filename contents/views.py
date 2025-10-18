from django.shortcuts import render, get_object_or_404
from .models import HeroBlock, AboutBlock, Partner, PortfolioBlock, Case, Service, ServicePartner, ServicePartner, Contact


def home_page(request):
    """Главная страница"""
    context = {
        'hero': HeroBlock.objects.filter(is_active=True).first(),
        'about': AboutBlock.objects.filter(is_active=True).first(),
        'partners': Partner.objects.filter(is_active=True),
        'portfolio': PortfolioBlock.objects.filter(is_active=True).first(),
        'cases': Case.objects.filter(is_active=True),
        'services': Service.objects.filter(is_active=True, show_on_homepage=True)[:10],
    }
    return render(request, 'contents/home.html', context)

def services_list(request):
    """Страница всех услуг"""
    services = Service.objects.filter(is_active=True)
    context = {
        'services': services,
    }
    return render(request, 'contents/services.html', context)


def service_detail(request, slug):
    """Детальная страница услуги"""
    service = get_object_or_404(Service, slug=slug, is_active=True)
    context = {
        'service': service,
        'partners': ServicePartner.objects.filter(is_active=True),

    }
    return render(request, 'contents/service_detail.html', context)


def contact_page(request):
    """Страница контактов"""
    contact = Contact.objects.filter(is_active=True).first()
    context = {
        'contact': contact,
    }
    return render(request, 'contents/contact.html', context)