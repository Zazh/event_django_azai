from django.contrib import admin
from .models import (
    HeroBlock, AboutBlock, Benefit,
    Partner, PortfolioBlock, PortfolioItem, Case, Service,
    ServiceAbout, ServiceBenefit, ServiceItem, ServiceLocation, ServiceFormBlock,
    ServiceGallery, ServicePartner,
    Contact, SocialNetwork,


)

class BenefitInline(admin.TabularInline):
    model = Benefit
    extra = 1


@admin.register(HeroBlock)
class HeroBlockAdmin(admin.ModelAdmin):
    list_display = ['seo_title', 'seo_description', 'title', 'button_text', 'is_active', 'order']
    list_filter = ['is_active']
    list_editable = ['is_active', 'order']


@admin.register(AboutBlock)
class AboutBlockAdmin(admin.ModelAdmin):
    list_display = ['title', 'is_active']
    list_filter = ['is_active']
    inlines = [BenefitInline]


@admin.register(Partner)
class PartnerAdmin(admin.ModelAdmin):
    list_display = ['name', 'color', 'is_active', 'order']
    list_filter = ['is_active']
    list_editable = ['order', 'is_active']


class PortfolioItemInline(admin.TabularInline):
    model = PortfolioItem
    extra = 1
    fields = ['image', 'description', 'order', 'is_active']


@admin.register(PortfolioBlock)
class PortfolioBlockAdmin(admin.ModelAdmin):
    list_display = ['title', 'is_active']
    list_filter = ['is_active']
    inlines = [PortfolioItemInline]


@admin.register(Case)
class CaseAdmin(admin.ModelAdmin):
    list_display = ['title', 'button_text', 'is_active', 'order', 'created_at']
    list_filter = ['is_active', 'created_at']
    list_editable = ['is_active', 'order']
    search_fields = ['title', 'description']


# Inline для ServiceAbout
class ServiceBenefitInline(admin.TabularInline):
    model = ServiceBenefit
    extra = 1
    fields = ['number', 'title', 'order']


class ServiceAboutInline(admin.StackedInline):
    model = ServiceAbout
    extra = 0
    fields = ['title', 'description']


# Inline для ServiceItem
class ServiceItemInline(admin.TabularInline):
    model = ServiceItem
    extra = 1
    fields = ['title', 'svg_path', 'description', 'order']


# Inline для ServiceLocation
class ServiceLocationInline(admin.StackedInline):
    model = ServiceLocation
    extra = 0
    fields = ['title', 'description', 'image', 'button_text', 'button_link']


class ServiceFormBlockInline(admin.StackedInline):
    model = ServiceFormBlock
    extra = 0
    fields = ['title', 'subtitle', 'button_text', 'is_active']

# Отдельная админка для ServiceAbout с бенефитами
@admin.register(ServiceAbout)
class ServiceAboutAdmin(admin.ModelAdmin):
    list_display = ['service', 'title']
    search_fields = ['title', 'service__card_title']
    inlines = [ServiceBenefitInline]


# Отдельная админка для ServiceItem
@admin.register(ServiceItem)
class ServiceItemAdmin(admin.ModelAdmin):
    list_display = ['title', 'service', 'order']
    list_filter = ['service']
    list_editable = ['order']
    search_fields = ['title', 'service__card_title']


# Отдельная админка для ServiceLocation
@admin.register(ServiceLocation)
class ServiceLocationAdmin(admin.ModelAdmin):
    list_display = ['service', 'title', 'button_text']
    search_fields = ['title', 'service__card_title']


# Inline для галереи
class ServiceGalleryInline(admin.TabularInline):
    model = ServiceGallery
    extra = 1
    fields = ['image', 'title', 'description', 'orientation', 'order', 'is_active']
    list_editable = ['order', 'is_active']


@admin.register(Service)
class ServiceAdmin(admin.ModelAdmin):
    list_display = ['card_title', 'slug', 'show_on_homepage', 'is_active', 'order', 'created_at']
    list_filter = ['is_active', 'show_on_homepage', 'created_at']
    list_editable = ['show_on_homepage', 'is_active', 'order']
    search_fields = ['card_title', 'card_description', 'hero_title']
    prepopulated_fields = {'slug': ('card_title',)}

    # Добавляем галерею в inline блоки
    inlines = [
        ServiceAboutInline,
        ServiceItemInline,
        ServiceLocationInline,
        ServiceGalleryInline,
        ServiceFormBlockInline
    ]

    fieldsets = (
        ('SEO', {
            'fields': ('seo_title', 'seo_description')
        }),
        ('Карточка услуги', {
            'fields': ('card_image', 'card_title', 'card_description', 'card_tags')
        }),
        ('Hero блок (детальная страница)', {
            'fields': ('hero_title', 'hero_subtitle', 'hero_button_text', 'hero_button_link')
        }),
        ('Услуги блок (заголовок)', {
            'fields': ('service_title',)
        }),
        ('Настройки', {
            'fields': ('slug', 'show_on_homepage', 'order', 'is_active')
        }),
    )

@admin.register(ServicePartner)
class ServicePartnerAdmin(admin.ModelAdmin):
    list_display = ['name', 'color', 'is_active', 'order']
    list_filter = ['is_active']
    list_editable = ['order', 'is_active']
    search_fields = ['name']


class SocialNetworkInline(admin.TabularInline):
    model = SocialNetwork
    extra = 1
    fields = ['name', 'link', 'svg_path', 'order']


@admin.register(Contact)
class ContactAdmin(admin.ModelAdmin):
    list_display = ['company_name', 'email', 'phone', 'is_active']
    list_filter = ['is_active']
    inlines = [SocialNetworkInline]

    fieldsets = (
        ('Основная информация', {
            'fields': ('company_name', 'email', 'phone')
        }),
        ('Адрес и карта', {
            'fields': ('address', 'map_link')
        }),
        ('Настройки', {
            'fields': ('is_active',)
        }),
    )

@admin.register(SocialNetwork)
class SocialNetworkAdmin(admin.ModelAdmin):
    list_display = ['name', 'contact', 'link', 'order']
    list_filter = ['contact']
    list_editable = ['order']
    search_fields = ['name', 'contact__company_name']


@admin.register(ServiceFormBlock)
class ServiceFormBlockAdmin(admin.ModelAdmin):
    list_display = ['service', 'title', 'button_text', 'is_active']
    list_filter = ['is_active']
    search_fields = ['title', 'service__card_title']