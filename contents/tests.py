import io
import shutil
import tempfile

from django.contrib.auth import get_user_model
from django.core.exceptions import ValidationError
from django.core.files.uploadedfile import SimpleUploadedFile
from django.test import TestCase, override_settings
from django.urls import reverse
from PIL import Image

from .models import Contact, Service, ServiceProgramItem

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
