from .constants import SEASON_HUB_SLUG
from .models import Contact, Service

# Имя маршрута → активный пункт меню
NAV_BY_URL_NAME = {
    'home': 'home',
    'services_list': 'services',
    'service_detail': 'services',
    'contacts': 'contacts',
}


def site(request):
    """Общее для каркаса (шапка, подвал, боковое меню): сезонный хаб, контакты, активный пункт."""
    season_hub = Service.objects.filter(slug=SEASON_HUB_SLUG, is_active=True).first()
    match = request.resolver_match
    url_name = match.url_name if match and match.namespace == 'contents' else ''
    nav_active = NAV_BY_URL_NAME.get(url_name, '')
    if url_name == 'service_detail' and season_hub:
        # хаб и его концепции подсвечивают «Новый год 2027», остальные услуги — «Услуги»
        slug = match.kwargs.get('slug')
        if slug == season_hub.slug or season_hub.children.filter(slug=slug).exists():
            nav_active = 'season'
    return {
        'season_hub': season_hub,
        'site_contact': Contact.objects.filter(is_active=True).first(),
        'nav_active': nav_active,
    }
