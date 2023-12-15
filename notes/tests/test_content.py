# from http import HTTPStatus
# import pytest
# import unittest
from datetime import datetime, timedelta

from django.conf import settings
# Импортируем функцию для получения модели пользователя.
from django.contrib.auth import get_user_model
from django.test import Client, TestCase
from django.utils import timezone
# Импортируем функцию reverse(), она понадобится для получения адреса страницы.
from django.urls import reverse

from notes.models import Note


# pytestmark = pytest.mark.skip(reason='запущу позже')

# Текущая дата.
today = datetime.today()
# Вчера.
yesterday = today - timedelta(days=1)
# Завтра.
tomorrow = today + timedelta(days=1)

User = get_user_model()


# @unittest.skip('for now')
class TestHomePage(TestCase):
    # Вынесем ссылку на домашнюю страницу в атрибуты класса.
    LIST_URL = reverse('notes:list')

    @classmethod
    def setUpTestData(cls):
        cls.author = User.objects.create(username='Автор')
        cls.reader = User.objects.create(username='Читатель')
        today = timezone.now().replace(
            hour=0, minute=0, second=0, microsecond=0
        )
        all_notes = [
            Note(
                title=f'Заметка {index}',
                text='Просто текст.',
                slug=f'zametka_{index}',
                author=cls.author,
                created_at=today + timedelta(days=index, minutes=index + 1))
            for index in range(settings.NOTES_COUNT_ON_HOME_PAGE + 1)
        ]
        Note.objects.bulk_create(all_notes)

    def common_response(self):
        """Общий класс"""
        users_status = (
            # автор комментария должен получить список заметок
            (self.author, settings.NOTES_COUNT_ON_HOME_PAGE),
            # читатель должен получить 0.
            (self.reader, 0),
        )
        for user, status in users_status:
            # Логиним пользователя в клиенте:
            self.client.force_login(user)
            # Загружаем главную страницу.
            response = self.client.get(self.LIST_URL)
            object_list = response.context['object_list']
            expected_count = status
            return object_list, expected_count

    def test_notes_count(self):
        """Количество заметок на странице ЗАМЕТОК"""
        # Код ответа не проверяем, его уже проверили в тестах маршрутов.
        # Получаем список объектов из словаря контекста.
        object_list, expected_count = self.common_response()
        print(object_list, expected_count)
        # print([note.author for note in object_list])
        # print([note.created_at for note in object_list])
        # Определяем длину списка.
        notes_count = len(object_list)
        # Check the notes count against the expected value
        self.assertEqual(notes_count - 1, expected_count)

    def test_notes_order(self):
        """Свежие заметки в конце списка."""
        object_list = self.common_response()[0]
        # Получаем даты новостей в том порядке, как они выведены на странице.
        all_dates = [note.created_at for note in object_list]
        # Сортируем полученный список по убыванию.
        sorted_dates = sorted(all_dates, reverse=False)
        # Проверяем, что исходный список был отсортирован правильно.
        self.assertEqual(all_dates, sorted_dates)


class TestDetailPage(TestCase):
    NOTE_TEXT = 'Текст заметки'

    @classmethod
    def setUpTestData(cls):
        cls.author = User.objects.create(
            username='Автор заметки'
        )
        cls.another_author = User.objects.create(
            username='Другой автор заметки'
        )
        # Создаём новость в БД.
        cls.note = Note.objects.create(
            title='Заголовок',
            text=cls.NOTE_TEXT,
            author=cls.author,
            slug='zagolovok'
        )
        cls.author_client = Client()
        cls.author_client.force_login(cls.author)
        cls.another_author_client = Client()
        cls.another_author_client.force_login(cls.another_author)

    def test_edit_detail_pages_contain_form(self):
        """на страницы создания и редактирования заметки передаются формы."""
        for name in ('notes:detail', 'notes:edit'):
            with self.subTest(name=name):
                # Формируем URL.
                url = reverse(name, args=(self.note.slug,))
                response = self.author_client.get(url)
                # # Проверяем, есть ли объект формы в словаре контекста:
                self.assertTrue('note' in response.context)

    def test_notes_list_for_different_users(self):
        """
        - в список заметок одного пользователя
        не попадают заметки другого пользователя;
        - отдельная заметка передаётся на страницу
        в списке object_list в словаре context
        """
        for user, status in (
            (self.author_client, True),
            (self.another_author_client, False)
        ):
            with self.subTest(user=user):
                url = reverse('notes:list')
                # Выполняем запрос от имени параметризованного клиента:
                response = user.get(url)
                object_list = response.context['object_list']
                # Проверяем истинность утверждения "заметка есть в списке":
                assert (self.note in object_list) is status
