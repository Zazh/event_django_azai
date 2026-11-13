"""Сид сезона 2026–2027: хаб «Новый год 2027», три концепции, цифры, главная, контакты.

    python manage.py seed_season2027 [--pdf-dir <каталог с PDF заказчицы>]

Идемпотентна: второй запуск подряд ничего не меняет. Страницы концепций принадлежат сиду —
повторный запуск возвращает их к состоянию из репо (правки админки на них перезаписываются),
поэтому после релиза команду не запускать. На dev-стенде запускать в контейнере: медиа — том.
"""
import re
import unicodedata
from pathlib import Path

from django.core.files import File
from django.core.files.base import ContentFile
from django.core.management.base import BaseCommand, CommandError
from django.db import transaction

from contents.models import (
    AboutBlock, Benefit, Contact, HeroBlock, Service, ServiceAbout, ServiceBenefit,
    ServiceFormBlock, ServiceGallery, ServiceItem, ServiceProgramItem,
)
from contents.seed import season2027 as data

IMAGES_DIR = Path(__file__).resolve().parents[2] / 'seed' / 'images'


def set_fields(obj, values):
    """Выставляет поля объекта; возвращает имена изменившихся."""
    changed = []
    for name, value in values.items():
        if getattr(obj, name) != value:
            setattr(obj, name, value)
            changed.append(name)
    return changed


def seed_image(name):
    return ContentFile((IMAGES_DIR / name).read_bytes(), name=name)


def image_key(field_file):
    """Имя загруженной картинки без каталога и расширения.

    Сигнал пережимает картинку в WebP, хранилище при совпадении имён дописывает суффикс
    `_xxxxxxx` — оба отличия от имени файла сида отбрасываются.
    """
    if not field_file:
        return ''
    stem = Path(field_file.name).stem
    match = re.fullmatch(r'(.+)_[A-Za-z0-9]{7}', stem)
    if match and (IMAGES_DIR / f'{match.group(1)}.jpg').exists():
        return match.group(1)
    return stem


def image_matches(field_file, seed_name):
    """Картинка в базе — та же, что в сиде, и файл на месте."""
    return (
        bool(field_file)
        and image_key(field_file) == Path(seed_name).stem
        and field_file.storage.exists(field_file.name)
    )


def find_file(directory, name):
    """Файл по имени без учёта нормализации юникода (macOS хранит «й» как «и» + бреве)."""
    wanted = unicodedata.normalize('NFC', name)
    for entry in Path(directory).iterdir():
        if unicodedata.normalize('NFC', entry.name) == wanted:
            return entry
    return None


def ordered(rows):
    """Строки сида с порядком 10, 20, 30…"""
    return [(*row, (index + 1) * 10) for index, row in enumerate(rows)]


class Command(BaseCommand):
    help = 'Заводит страницы и цифры сезона 2026–2027 (идемпотентно).'

    def add_arguments(self, parser):
        parser.add_argument(
            '--pdf-dir',
            help='Каталог с PDF-презентациями концепций. Не задан — PDF не трогаются.',
        )

    def handle(self, *args, **options):
        self.pdf_dir = options.get('pdf_dir')
        if self.pdf_dir and not Path(self.pdf_dir).is_dir():
            raise CommandError(f'Каталог с PDF не найден: {self.pdf_dir}')
        self.created, self.updated, self.notes = [], [], []

        with transaction.atomic():
            hub = self.seed_hub()
            for concept in data.CONCEPTS:
                self.seed_concept(concept, hub)
            self.seed_placement()
            self.pin_stats_order()
            self.seed_service_stats()
            self.seed_home()
            self.seed_contact()

        for label in self.created:
            self.stdout.write(f'  + {label}')
        for label in self.updated:
            self.stdout.write(f'  ~ {label}')
        for note in self.notes:
            self.stdout.write(self.style.WARNING(f'  ! {note}'))
        self.stdout.write(self.style.SUCCESS(
            f'Сид сезона 2027: создано {len(self.created)}, обновлено {len(self.updated)}'
        ))

    # --- учёт ---------------------------------------------------------------------------

    def mark(self, label, created=False):
        (self.created if created else self.updated).append(label)

    # --- хаб ----------------------------------------------------------------------------

    def seed_hub(self):
        spec = data.HUB
        hub = Service.objects.filter(slug=spec['slug']).first()
        created = hub is None
        if created:
            hub = Service(slug=spec['slug'], **spec['create_defaults'])
            hub.card_image = seed_image(spec['create_image'])
        changed = set_fields(hub, {**spec['fields'], 'parent_id': None})
        if hub.pdf_file:
            # PDF «Новый год 2026» снимается; файл на диске остаётся
            hub.pdf_file = None
            changed.append('pdf_file')
        if created or changed:
            hub.save()
            self.mark(f'страница {hub.slug} (хаб)' + ('' if created else f': {", ".join(changed)}'), created)
        self.sync_program(hub, spec['program'])
        return hub

    # --- концепции ----------------------------------------------------------------------

    def seed_concept(self, spec, hub):
        service = Service.objects.filter(slug=spec['slug']).first()
        created = service is None
        if created:
            service = Service(slug=spec['slug'])
        changed = set_fields(service, {**data.CONCEPT_COMMON, **spec['fields'], 'parent_id': hub.pk})
        if not image_matches(service.card_image, spec['card_image']):
            if service.card_image:
                service.card_image.delete(save=False)
            service.card_image = seed_image(spec['card_image'])
            changed.append('card_image')
        if self.attach_pdf(service, *spec['pdf']):
            changed.append('pdf_file')
        if created or changed:
            service.save()
            self.mark(f'страница {service.slug}' + ('' if created else f': {", ".join(changed)}'), created)

        self.sync_about(service, spec['about'])
        self.sync_items(service, spec['items'])
        self.sync_program(service, spec['program'])
        self.sync_gallery(service, spec['gallery'])
        self.sync_form(service, spec['form'])

    def attach_pdf(self, service, source_name, clean_name):
        """Прикрепляет PDF под чистым именем; True — файл страницы изменился."""
        if not self.pdf_dir:
            return False
        source = find_file(self.pdf_dir, source_name)
        if source is None:
            self.notes.append(f'{service.slug}: PDF «{source_name}» не найден в {self.pdf_dir}')
            return False
        current = service.pdf_file
        storage = current.storage
        target = current.field.generate_filename(service, clean_name)
        if (
            current and current.name == target and storage.exists(target)
            and storage.size(target) == source.stat().st_size
        ):
            return False
        if storage.exists(target):
            storage.delete(target)  # имя должно остаться чистым, без суффикса хранилища
        with source.open('rb') as handle:
            service.pdf_file.save(clean_name, File(handle), save=False)
        return True

    # Дочерние блоки концепций заменяются целиком, если отличаются от сида.

    def sync_about(self, service, spec):
        benefits = ordered(spec['benefits'])
        about = ServiceAbout.objects.filter(service=service).first()
        if about is not None:
            same = (
                (about.title, about.description) == (spec['title'], spec['description'])
                and [(b.number, b.title, b.order) for b in about.benefits.order_by('order', 'id')] == benefits
            )
            if same:
                return
            about.delete()
        about = ServiceAbout.objects.create(
            service=service, title=spec['title'], description=spec['description']
        )
        ServiceBenefit.objects.bulk_create([
            ServiceBenefit(service_about=about, number=number, title=title, order=order)
            for number, title, order in benefits
        ])
        self.mark(f'{service.slug}: о концепции и цифры')

    def sync_items(self, service, rows):
        desired = ordered(rows)
        existing = [(i.title, i.description, i.order) for i in service.items.order_by('order', 'id')]
        if existing == desired and not service.items.exclude(svg_path='').exists():
            return
        service.items.all().delete()
        ServiceItem.objects.bulk_create([
            ServiceItem(service=service, title=title, description=description, order=order)
            for title, description, order in desired
        ])
        self.mark(f'{service.slug}: ключевые фишки')

    def sync_program(self, service, rows):
        desired = ordered(rows)
        existing = [(p.label, p.title, p.description, p.order) for p in service.program.all()]
        if existing == desired:
            return
        service.program.all().delete()
        ServiceProgramItem.objects.bulk_create([
            ServiceProgramItem(service=service, label=label, title=title, description=description, order=order)
            for label, title, description, order in desired
        ])
        self.mark(f'{service.slug}: шаги программы')

    def sync_gallery(self, service, rows):
        desired = ordered(rows)
        existing = list(service.gallery.order_by('order', 'id'))
        same = len(existing) == len(desired) and all(
            image_matches(row.image, image)
            and (row.title, row.description, row.orientation, row.order, row.is_active)
            == (title, title, orientation, order, True)
            for row, (image, title, orientation, order) in zip(existing, desired)
        )
        if same:
            return
        for row in existing:
            row.image.delete(save=False)
            row.delete()
        for image, title, orientation, order in desired:
            # по одной: картинку пережимает сигнал pre_save
            ServiceGallery.objects.create(
                service=service, image=seed_image(image), title=title, description=title,
                orientation=orientation, order=order,
            )
        self.mark(f'{service.slug}: галерея')

    def sync_form(self, service, spec):
        values = {
            'title': spec['title'],
            'subtitle': data.FORM_SUBTITLE,
            'button_text': data.PRESENTATION_BUTTON,
            'is_active': True,
        }
        form = ServiceFormBlock.objects.filter(service=service).first()
        if form is None:
            ServiceFormBlock.objects.create(service=service, **values)
            self.mark(f'{service.slug}: блок формы')
        elif set_fields(form, values):
            form.save()
            self.mark(f'{service.slug}: блок формы')

    # --- остальные услуги и цифры -------------------------------------------------------

    def seed_placement(self):
        for slug, values in data.SERVICE_PLACEMENT.items():
            service = Service.objects.filter(slug=slug).first()
            if service is None:
                continue
            changed = set_fields(service, values)
            if changed:
                service.save(update_fields=changed)
                self.mark(f'страница {slug}: {", ".join(changed)}')

    def pin_stats_order(self):
        """Закрепляет порядок цифр, который сайт показывает сейчас, — до их правки.

        У прежних страниц порядок не задан (везде 0) и держится на порядке строк в базе;
        обновление строки его меняет, и цифры на странице переставляются.
        """
        for about in ServiceAbout.objects.select_related('service'):
            rows = list(about.benefits.all())  # Meta.ordering = ['order']: при равенстве — как отдаёт база
            if len({row.order for row in rows}) == len(rows):
                continue
            for index, row in enumerate(rows):
                row.order = (index + 1) * 10
            ServiceBenefit.objects.bulk_update(rows, ['order'])
            self.mark(f'{about.service.slug}: порядок цифр закреплён')

    def seed_service_stats(self):
        """Прежние общие цифры компании на страницах услуг → новые (по старому значению)."""
        benefits = ServiceBenefit.objects.select_related('service_about__service')
        for benefit in benefits:
            slug = benefit.service_about.service.slug
            number = benefit.number.strip()
            new = (
                data.SERVICE_STAT_REPLACEMENTS_BY_SLUG.get(slug, {}).get(number)
                or data.SERVICE_STAT_REPLACEMENTS.get(number)
            )
            if new:
                benefit.number, benefit.title = new
                benefit.save(update_fields=['number', 'title'])
                self.mark(f'{slug}: цифра {number} → {new[0]}')

    def seed_home(self):
        about = AboutBlock.objects.filter(is_active=True).first() or AboutBlock.objects.first()
        created = about is None
        if created:
            about = AboutBlock()
        changed = set_fields(about, data.HOME_ABOUT)
        if created or changed:
            about.save()
            self.mark('главная: блок «О нас»', created)
        desired = ordered(data.HOME_STATS)
        existing = [(b.number, b.title, b.order) for b in about.benefits.order_by('order', 'id')]
        if existing != desired:
            about.benefits.all().delete()
            Benefit.objects.bulk_create([
                Benefit(about_block=about, number=number, title=title, order=order)
                for number, title, order in desired
            ])
            self.mark('главная: шесть цифр компании')

        hero = HeroBlock.objects.filter(is_active=True).first() or HeroBlock.objects.first()
        created = hero is None
        if created:
            hero = HeroBlock(**data.HOME_HERO['create_defaults'])
        changed = set_fields(hero, data.HOME_HERO['fields'])
        if created or changed:
            hero.save()
            self.mark('главная: hero', created)

    def seed_contact(self):
        contact = Contact.objects.filter(is_active=True).first()
        if contact is None:
            self.notes.append('контакты: активной записи нет — второй телефон и филиал не заведены')
            return
        changed = set_fields(contact, data.CONTACT)
        if changed:
            contact.save(update_fields=changed)
            self.mark(f'контакты: {", ".join(changed)}')
