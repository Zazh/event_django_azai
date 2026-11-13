import io
import shutil
import tempfile
import unicodedata
from pathlib import Path

from django.apps import apps
from django.contrib.auth import get_user_model
from django.core.exceptions import ValidationError
from django.core.files.uploadedfile import SimpleUploadedFile
from django.core.management import call_command
from django.db.models import CharField, TextField
from django.test import TestCase, override_settings
from django.urls import reverse
from PIL import Image

from .constants import SEASON_HUB_SLUG
from .models import (
    AboutBlock, Benefit, Contact, HeroBlock, Service, ServiceAbout, ServiceBenefit,
    ServiceFormBlock, ServiceProgramItem,
)
from .seed import season2027 as seed_data

TEST_MEDIA_ROOT = tempfile.mkdtemp(prefix='dne-test-media-')


def png_file(name='card.png'):
    """Маленькая настоящая картинка: сигнал pre_save пережимает её в WebP."""
    buf = io.BytesIO()
    Image.new('RGB', (4, 4), (96, 13, 21)).save(buf, 'PNG')
    return SimpleUploadedFile(name, buf.getvalue(), content_type='image/png')


def make_service(slug, **kwargs):
    defaults = dict(
        card_image=png_file(),
        card_title=slug,
        card_description='Описание',
        card_tags='тег',
        hero_title=slug,
        hero_subtitle='Подзаголовок',
    )
    defaults.update(kwargs)
    return Service.objects.create(slug=slug, **defaults)


@override_settings(MEDIA_ROOT=TEST_MEDIA_ROOT)
class MediaTestCase(TestCase):
    """Тесты с картинками пишут во временный каталог, а не в media/."""

    @classmethod
    def tearDownClass(cls):
        super().tearDownClass()
        shutil.rmtree(TEST_MEDIA_ROOT, ignore_errors=True)


class ServiceStructureTests(MediaTestCase):
    def test_new_fields_defaults(self):
        service = make_service('obychnaya')
        self.assertEqual(service.direction, 'events')
        self.assertEqual(service.badge, '')
        self.assertEqual(service.price_from, '')
        self.assertEqual(service.accent, '')
        self.assertEqual(service.program_title, '')
        self.assertIsNone(service.parent)

    def test_children_returns_child_pages(self):
        hub = make_service('hub')
        first = make_service('first', parent=hub)
        second = make_service('second', parent=hub)
        make_service('other')
        self.assertCountEqual(hub.children.all(), [first, second])

    def test_clean_rejects_self_parent(self):
        service = make_service('sama')
        service.parent = service
        with self.assertRaises(ValidationError) as ctx:
            service.clean()
        self.assertIn('parent', ctx.exception.message_dict)

    def test_clean_rejects_second_level(self):
        hub = make_service('hub')
        child = make_service('child', parent=hub)
        grandchild = make_service('grandchild')
        grandchild.parent = child
        with self.assertRaises(ValidationError) as ctx:
            grandchild.clean()
        self.assertIn('parent', ctx.exception.message_dict)

    def test_clean_rejects_parent_becoming_child(self):
        hub = make_service('hub')
        make_service('child', parent=hub)
        other = make_service('other')
        hub.parent = other
        with self.assertRaises(ValidationError):
            hub.clean()

    def test_clean_accepts_one_level(self):
        hub = make_service('hub')
        child = make_service('child')
        child.parent = hub
        child.clean()  # не падает

    def test_program_items_ordered(self):
        service = make_service('s-programmoy')
        ServiceProgramItem.objects.create(service=service, label='03', title='Третий', order=30)
        ServiceProgramItem.objects.create(service=service, label='01', title='Первый', order=10)
        ServiceProgramItem.objects.create(service=service, label='02', title='Второй', order=20)
        self.assertEqual([p.label for p in service.program.all()], ['01', '02', '03'])

    def test_service_item_without_icon(self):
        service = make_service('s-fishkami')
        item = service.items.create(title='Фишка', description='Без иконки')
        item.full_clean()  # svg_path необязателен
        self.assertEqual(item.svg_path, '')


class AdminSmokeTests(MediaTestCase):
    @classmethod
    def setUpTestData(cls):
        cls.admin_user = get_user_model().objects.create_superuser('admin', 'a@example.com', 'pass')
        cls.hub = make_service('hub')
        cls.child = make_service('child', parent=cls.hub)
        ServiceProgramItem.objects.create(service=cls.hub, label='01', title='Шаг', order=10)
        cls.contact = Contact.objects.create(
            company_name='ТОО', email='a@example.com', phone='+7 701 000 0000',
            address='Астана', map_link='https://example.com/map',
        )

    def setUp(self):
        self.client.force_login(self.admin_user)

    def test_service_changelist(self):
        response = self.client.get(reverse('admin:contents_service_changelist'))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'DN Events')

    def test_service_change_form_has_season_section_and_program_inline(self):
        response = self.client.get(reverse('admin:contents_service_change', args=[self.hub.pk]))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Сезон и структура')
        for field in ('direction', 'parent', 'badge', 'price_from', 'accent', 'program_title'):
            self.assertContains(response, f'name="{field}"')
        self.assertContains(response, 'name="program-0-label"')

    def test_parent_choices_exclude_child_pages(self):
        response = self.client.get(reverse('admin:contents_service_add'))
        choices = response.context['adminform'].form.fields['parent'].queryset
        self.assertIn(self.hub, choices)
        self.assertNotIn(self.child, choices)

    def test_contact_changelist_and_form(self):
        response = self.client.get(reverse('admin:contents_contact_changelist'))
        self.assertEqual(response.status_code, 200)
        response = self.client.get(reverse('admin:contents_contact_change', args=[self.contact.pk]))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'name="phone_extra"')
        self.assertContains(response, 'name="branches"')


class SeedSeason2027Tests(MediaTestCase):
    CONCEPT_SLUGS = ['legends', 'teleport-2037', 'immersive-show']

    def run_seed(self, **options):
        out = io.StringIO()
        call_command('seed_season2027', stdout=out, **options)
        return out.getvalue()

    @staticmethod
    def row_counts():
        return {model.__name__: model.objects.count() for model in apps.get_app_config('contents').get_models()}

    def test_empty_database_creates_hub_and_concepts(self):
        self.run_seed()
        hub = Service.objects.get(slug=SEASON_HUB_SLUG)
        self.assertIsNone(hub.parent)
        self.assertEqual(hub.direction, 'events')
        self.assertEqual(hub.program_title, 'Как мы работаем')
        self.assertEqual([step.label for step in hub.program.all()], ['01', '02', '03'])
        hub.full_clean()

        concepts = list(Service.objects.filter(parent=hub).order_by('order'))
        self.assertEqual([c.slug for c in concepts], self.CONCEPT_SLUGS)
        for concept in concepts:
            with self.subTest(concept=concept.slug):
                self.assertEqual(concept.badge, 'Новинка 2027')
                self.assertEqual(concept.price_from, 'от 6 000 000 ₸')
                self.assertTrue(concept.accent)
                self.assertTrue(concept.show_on_homepage)
                self.assertGreaterEqual(concept.items.count(), 4)
                self.assertGreaterEqual(concept.program.count(), 10)
                self.assertGreaterEqual(concept.gallery.count(), 3)
                self.assertTrue(concept.about.benefits.count() <= 4)
                self.assertEqual(concept.form_block.button_text, 'Получить презентацию')
                self.assertFalse(concept.items.exclude(svg_path='').exists())
                # админка должна суметь сохранить всё, что завёл сид
                concept.full_clean()
                concept.about.full_clean()
                concept.form_block.full_clean()
                for row in [*concept.items.all(), *concept.program.all(), *concept.gallery.all()]:
                    row.full_clean()

    def test_second_run_changes_nothing(self):
        self.run_seed()
        before = self.row_counts()
        output = self.run_seed()
        self.assertEqual(self.row_counts(), before)
        self.assertIn('создано 0, обновлено 0', output)

    def test_old_company_stats_replaced(self):
        old = [('1000+', 'Проведенных мероприятий'), ('395', 'Корпоративов и банкетов'),
               ('184', 'Тимбилдингов и квестов'), ('282', 'Корпоративного утренника')]
        about_block = AboutBlock.objects.create(title='Dana Nurzhuma Event', description='Старое')
        for number, title in old:
            Benefit.objects.create(about_block=about_block, number=number, title=title)
        teambuilding = make_service('korporativy-i-timbildingi')
        about = ServiceAbout.objects.create(service=teambuilding, title='О нас', description='Текст')
        for number, title in old:
            ServiceBenefit.objects.create(service_about=about, number=number, title=title)
        matinee = make_service('detskie-novogodnie-utrenniki')
        matinee_about = ServiceAbout.objects.create(service=matinee, title='О нас', description='Текст')
        for number, title in [('45', 'Шоу (мин)'), ('1000+', 'Проведенных ивентов'), ('282', 'Провели утренников')]:
            ServiceBenefit.objects.create(service_about=matinee_about, number=number, title=title)

        self.run_seed()

        about_block.refresh_from_db()
        self.assertEqual(about_block.title, 'Больше, чем события')
        self.assertEqual(
            [b.number for b in about_block.benefits.all()], ['334', '114', '92', '186', '102', '22']
        )
        for number in ('1000+', '395', '184'):
            self.assertFalse(Benefit.objects.filter(number=number).exists(), number)
            self.assertFalse(ServiceBenefit.objects.filter(number=number).exists(), number)
        self.assertCountEqual(
            about.benefits.values_list('number', 'title'),
            [('102', 'Корпоративных клиента'), ('334', 'Корпоративных мероприятия'),
             ('114', 'Тимбилдингов и квестов'), ('92', 'Бизнес-мероприятия')],
        )
        # порядок цифр на странице — прежний (по id), а не как отдаст база после обновления
        self.assertEqual([b.number for b in about.benefits.all()], ['102', '334', '114', '92'])
        # «282» на утренниках — цифра самой услуги, остаётся
        self.assertCountEqual(matinee_about.benefits.values_list('number', flat=True), ['45', '102', '282'])
        self.assertEqual(Service.objects.get(pk=teambuilding.pk).order, 20)
        self.assertEqual(Service.objects.get(pk=matinee.pk).order, 30)

    def test_existing_hub_keeps_content_and_loses_pdf(self):
        hub = make_service(
            SEASON_HUB_SLUG, card_description='Прежнее описание',
            pdf_file=SimpleUploadedFile('ny2026.pdf', b'%PDF-1.4'),
        )
        hub.items.create(title='Оформление локации', description='Что входит', svg_path='<svg></svg>')
        self.run_seed()
        hub.refresh_from_db()
        self.assertFalse(hub.pdf_file)
        self.assertEqual(hub.card_title, 'Новый год 2027 — корпоратив под ключ')
        self.assertEqual(hub.card_description, 'Прежнее описание')
        self.assertEqual(hub.items.count(), 1)
        self.assertEqual(hub.price_from, 'от 6 000 000 ₸')

    def test_home_and_contact_updated(self):
        hero = HeroBlock.objects.create(
            title='Создаём праздники', subtitle='Старый', button_text='Кнопка', button_link='источник'
        )
        contact = Contact.objects.create(
            company_name='ТОО', email='dananurzhumaevents@mail.ru', phone='+7 701 263 5557',
            address='г. Астана', map_link='https://example.com/map',
        )
        self.run_seed()
        hero.refresh_from_db()
        contact.refresh_from_db()
        self.assertIn('Новый год 2027', hero.title)
        self.assertEqual(hero.button_text, 'Кнопка')
        self.assertEqual(contact.phone_extra, '+7 778 002 5557')
        self.assertIn('Алматы', contact.branches)
        self.assertEqual(contact.phone, '+7 701 263 5557')

    def test_pdf_attached_under_clean_name(self):
        with tempfile.TemporaryDirectory() as pdf_dir:
            # имя как на macOS — в разложенной форме юникода
            source = Path(pdf_dir, unicodedata.normalize('NFD', 'Презентация Легенды.pdf'))
            source.write_bytes(b'%PDF-1.4 legends')
            output = self.run_seed(pdf_dir=pdf_dir)
            legends = Service.objects.get(slug='legends')
            self.assertEqual(legends.pdf_file.name, 'services/pdfs/legends-2027.pdf')
            self.assertEqual(legends.pdf_file.read(), b'%PDF-1.4 legends')
            self.assertFalse(Service.objects.get(slug='teleport-2037').pdf_file)
            self.assertIn('не найден', output)  # двух других презентаций в каталоге нет
            # повторный запуск не плодит файлы и строки
            self.assertIn('создано 0, обновлено 0', self.run_seed(pdf_dir=pdf_dir))
            legends.refresh_from_db()
            self.assertEqual(legends.pdf_file.name, 'services/pdfs/legends-2027.pdf')

    def test_without_pdf_dir_pdf_untouched(self):
        self.run_seed()
        legends = Service.objects.get(slug='legends')
        legends.pdf_file = SimpleUploadedFile('manual.pdf', b'%PDF-1.4 manual')
        legends.save()
        self.run_seed()
        legends.refresh_from_db()
        self.assertIn('manual', legends.pdf_file.name)

    def test_no_forbidden_strings_in_content(self):
        self.run_seed()
        for model in apps.get_app_config('contents').get_models():
            names = [f.name for f in model._meta.get_fields() if isinstance(f, (CharField, TextField))]
            for row in model.objects.values(*names):
                for field, value in row.items():
                    for forbidden in seed_data.FORBIDDEN_STRINGS:
                        self.assertNotIn(forbidden, (value or '').lower(), f'{model.__name__}.{field}')


class ServiceDetailTests(MediaTestCase):
    @classmethod
    def setUpTestData(cls):
        cls.hub = make_service(SEASON_HUB_SLUG, program_title='Как мы работаем')
        ServiceProgramItem.objects.create(service=cls.hub, label='01', title='Выбираете концепцию', order=10)
        common = dict(parent=cls.hub, badge='Новинка 2027', price_from='от 6 000 000 ₸')
        cls.teleport = make_service('teleport-2037', card_title='TELEPORT 2037', accent='teleport', order=20, **common)
        cls.legends = make_service(
            'legends', card_title='LEGENDS', accent='legends', order=10, program_title='Программа вечера',
            hero_button_text='Получить презентацию',
            pdf_file=SimpleUploadedFile('legends-2027.pdf', b'%PDF-1.4'), **common,
        )
        ServiceAbout.objects.create(service=cls.legends, title='О концепции', description='Идея')
        ServiceFormBlock.objects.create(service=cls.legends, title='Получите презентацию', subtitle='Оставьте заявку')
        cls.immersive = make_service('immersive-show', card_title='IMMERSIVE SHOW', accent='immersive', order=30, **common)
        cls.hidden = make_service('skrytaya', parent=cls.hub, order=5, is_active=False)
        ServiceProgramItem.objects.create(
            service=cls.legends, label='18:00–19:00', title='Welcome', description='Ожившие легенды', order=10
        )
        cls.legends.items.create(title='Звезда компании', description='Арт-объект')
        cls.plain = make_service('obychnaya-usluga', card_title='Обычная услуга')

    def get(self, service):
        return self.client.get(reverse('contents:service_detail', args=[service.slug]))

    def test_hub_lists_active_concepts_in_order(self):
        response = self.get(self.hub)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(list(response.context['concepts']), [self.legends, self.teleport, self.immersive])
        self.assertIsNone(response.context['parent'])
        self.assertContains(response, 'id="concepts"')
        self.assertContains(response, 'id="program"')
        self.assertContains(response, 'Как мы работаем')
        self.assertContains(response, 'theme-teleport')  # карточка несёт акцент концепции
        self.assertNotContains(response, 'id="other-concepts"')
        self.assertNotContains(response, 'skrytaya')

    def test_concept_page(self):
        response = self.get(self.legends)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.context['parent'], self.hub)
        self.assertEqual(list(response.context['siblings']), [self.teleport, self.immersive])
        self.assertContains(response, 'class="themed theme-legends"')
        self.assertContains(response, 'id="program"')
        self.assertContains(response, '18:00–19:00')
        self.assertContains(response, 'Тайминг предварительный')
        self.assertContains(response, 'id="other-concepts"')
        self.assertContains(response, f'data-pdf-url="{self.legends.pdf_file.url}"')
        self.assertContains(response, 'Новинка 2027')
        self.assertContains(response, 'от 6 000 000 ₸')
        self.assertContains(response, reverse('contents:service_detail', args=[self.hub.slug]))
        self.assertNotContains(response, 'id="concepts"')
        # источник заявки называет концепцию — у кнопок hero и «Заказать проект» и у инлайн-формы
        self.assertContains(response, 'data-source="Скачать Получить презентацию - LEGENDS"')
        self.assertContains(response, 'data-source="Кнопка Заказать проект - LEGENDS"')
        self.assertContains(response, 'data-service-name="LEGENDS"')
        self.assertContains(response, 'О КОНЦЕПЦИИ')
        self.assertContains(response, 'Фишки')

    def test_concept_without_pdf_has_no_pdf_attribute(self):
        response = self.get(self.teleport)
        self.assertEqual(response.status_code, 200)
        self.assertNotContains(response, 'data-pdf-url="/')

    def test_plain_service_has_no_season_sections(self):
        response = self.get(self.plain)
        self.assertEqual(response.status_code, 200)
        self.assertFalse(response.context['concepts'])
        self.assertIsNone(response.context['parent'])
        for marker in ('id="concepts"', 'id="program"', 'id="other-concepts"', 'themed', 'class="badge'):
            self.assertNotContains(response, marker)

    def test_inactive_page_is_404(self):
        self.assertEqual(self.get(self.hidden).status_code, 404)

    def test_concept_of_inactive_parent_has_no_back_link(self):
        Service.objects.filter(pk=self.hub.pk).update(is_active=False)
        response = self.get(self.legends)
        self.assertEqual(response.status_code, 200)
        self.assertIsNone(response.context['parent'])
        self.assertFalse(response.context['siblings'])
