# import pytest
from http import HTTPStatus

# Импортируем функцию для определения модели пользователя.
from django.contrib.auth import get_user_model
from django.test import Client, TestCase
# Импортируем функцию reverse().
from django.urls import reverse

from notes.models import Note


# Получаем модель пользователя.
User = get_user_model()

LIST_URL = 'notes:list'
EDIT_URL = 'notes:edit'

# pytestmark = pytest.mark.skip(reason='ПРОВЕРЕНО')


class TestCommon(TestCase):
    # Вынесем ссылку на домашнюю страницу в атрибуты класса.
    LIST_URL = 'notes:list'
    EDIT_URL = 'notes:edit'

    @classmethod
    def setUpTestData(cls):
        cls.author = User.objects.create(username='Автор')
        cls.another_author = User.objects.create(username='Другой Автор')
        cls.author_client = Client()
        cls.author_client.force_login(cls.author)
        cls.another_author_client = Client()
        cls.another_author_client.force_login(cls.another_author)


class TestRoutes(TestCommon):
    # Добавляем фикстуру с созданием заметки:
    @classmethod
    def setUpTestData(cls):
        super().setUpTestData()
        cls.note = Note.objects.create(
            title='Note for Author',
            text='Text for Author',
            author=cls.author,
            slug='note_for_author'
        )

    def test_pages_availability(self):
        """Доступность отдельных страниц"""
        urls = (
            ('notes:home', None),
            ('users:login', None),
            ('users:logout', None),
            ('users:signup', None),
        )
        for name, args in urls:
            with self.subTest(name=name):
                url = reverse(name, args=args)
                response = self.client.get(url)
                self.assertEqual(response.status_code, HTTPStatus.OK)

    def test_pages_availability_for_auth_user(self):
        """
        Аутентифицированному пользователю доступна страница
        со списком заметок notes/,
        страница успешного добавления заметки done/,
        страница добавления новой заметки add/.
        """
        for name in ('notes:list', 'notes:add', 'notes:success'):
            with self.subTest(user=self.author_client, name=name):
                url = reverse(name)
                response = self.author_client.get(url)
                self.assertEqual(response.status_code, HTTPStatus.OK)

    def test_redirect_for_anonymous_client(self):
        """Проверка редиректов"""
        # Сохраняем адрес страницы логина:
        login_url = reverse('users:login')
        for name in ('notes:add', 'notes:edit', 'notes:delete'):
            with self.subTest(name=name):
                if 'add' in name:
                    url = reverse(name)
                else:
                    url = reverse(name, args=({'slug': self.note.slug}))
                redirect_url = f'{login_url}?next={url}'
                response = self.client.get(url)
                self.assertRedirects(response, redirect_url)

    def test_availability_for_note_edit_and_delete(self):
        """Проверка страниц редактирования и удаления заметки"""
        for user, status in (
            (self.author_client, HTTPStatus.OK),
            (self.another_author_client, HTTPStatus.NOT_FOUND),
        ):
            for name in ('notes:detail', 'notes:edit', 'notes:delete'):
                with self.subTest(name=name, user=user):
                    url = reverse(name, args=(self.note.slug,))
                    response = user.get(url)
                    self.assertEqual(response.status_code, status)
