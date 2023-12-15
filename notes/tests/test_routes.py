# import pytest
from http import HTTPStatus

# Импортируем функцию для определения модели пользователя.
from django.contrib.auth import get_user_model
from django.test import TestCase
# Импортируем функцию reverse().
from django.urls import reverse

from notes.models import Note


# Получаем модель пользователя.
User = get_user_model()


# pytestmark = pytest.mark.skip(reason='ПРОВЕРЕНО')


class TestRoutes(TestCase):
    # Добавляем фикстуру с созданием заметки:
    @classmethod
    def setUpTestData(cls):
        # Создаём двух пользователей с разными именами:
        cls.author = User.objects.create(username='Автор')
        cls.reader = User.objects.create(username='Читатель')
        cls.note = Note.objects.create(
            title='Заголовок',
            text='Текст',
            author=cls.author,
        )

    def answer(self, status_code=None, name=None, user=None, status=None):
        print()
        print(
            f'для {user}, {name} полученный ответ '
            f'запроса: {status_code}, '
            f'сравниваем с HTTPStatus который равен {status}'
        )
        print()

    def test_get_author_name(self):
        """Проверка имени автора заметки"""
        # Retrieve the author name based on cls.note.author_id
        author_name = User.objects.get(id=self.note.author_id).username
        print(f'Author name based on author_id: {author_name}')
        author_name_direct = self.note.author.username
        print(
            f'Author name directly from cls.note.author: {author_name_direct}')

        # Perform your assertions or additional actions as needed
        self.assertEqual(author_name, author_name_direct)

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
        user = self.author
        self.client.force_login(user)

        # Для каждой пары "пользователь - ожидаемый ответ"
        # перебираем имена тестируемых страниц:
        for name in ('notes:list', 'notes:add', 'notes:success'):
            with self.subTest(user=user, name=name):
                url = reverse(name)
                response = self.client.get(url)
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
                print(f'{response.url} соответсвует {redirect_url}')
                self.assertRedirects(response, redirect_url)

    def test_availability_for_note_edit_and_delete(self):
        """Проверка страниц редактирования и удаления заметки"""
        users_status = (
            # автор комментария должен получить ответ OK,
            (self.author, HTTPStatus.OK),
            # читатель должен получить ответ NOT_FOUND.
            (self.reader, HTTPStatus.NOT_FOUND),
        )
        for user, status in users_status:
            # Логиним пользователя в клиенте:
            self.client.force_login(user)
            # Для каждой пары "пользователь - ожидаемый ответ"
            # перебираем имена тестируемых страниц:
            for name in ('notes:detail', 'notes:edit', 'notes:delete'):
                with self.subTest(user=user, name=name):
                    url = reverse(name, args={self.note.slug})
                    response = self.client.get(url)
                    self.assertEqual(response.status_code, status)
