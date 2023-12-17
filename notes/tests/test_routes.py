# import pytest
from http import HTTPStatus

from .base_module import MyBaseClass


class TestRoutes(MyBaseClass):

    def test_pages_availability(self):
        """Доступность отдельных страниц"""
        urls = (
            ('home', None),
            ('login', None),
            ('logout', None),
            ('signup', None),
        )
        for name, args in urls:
            with self.subTest(name=name):
                url = getattr(self, f'{name}_url')
                print(url)
                response = self.client.get(url, args=args)
                self.assertEqual(response.status_code, HTTPStatus.OK)

    def test_pages_availability_for_auth_user(self):
        """
        Аутентифицированному пользователю доступна страница
        со списком заметок notes/,
        страница успешного добавления заметки done/,
        страница добавления новой заметки add/.
        """
        for name in ('list', 'add', 'success'):
            with self.subTest(user=self.author_client, name=name):
                url = getattr(self, f'{name}_url')
                response = self.author_client.get(url)
                self.assertEqual(response.status_code, HTTPStatus.OK)

    def test_redirect_for_anonymous_client(self):
        """Проверка редиректов"""
        # Сохраняем адрес страницы логина:
        for name in ('add', 'edit', 'delete'):
            with self.subTest(name=name):
                if 'add' in name:
                    url = getattr(self, f'{name}_url')
                else:
                    url = getattr(self, f'{name}_author_note_url')

                response = self.client.get(url)
        redirect_url = f'{self.login_url}?next={url}'
        self.assertRedirects(response, redirect_url)

    def test_availability_for_note_edit_and_delete(self):
        """Проверка страниц редактирования и удаления заметки"""
        for user, status in (
            (self.author_client, HTTPStatus.OK),
            (self.another_author_client, HTTPStatus.NOT_FOUND),
        ):
            for name in ('detail', 'edit', 'delete'):
                with self.subTest(name=name, user=user):
                    url = getattr(self, f'{name}_author_note_url')
                    response = user.get(url)
                    self.assertEqual(response.status_code, status)
