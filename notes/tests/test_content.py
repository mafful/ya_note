from datetime import timedelta

from django.conf import settings
from django.contrib.auth import get_user_model
from django.test import Client, TestCase
from django.utils import timezone
from django.urls import reverse

from notes.models import Note


User = get_user_model()


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
        cls.reader_client = Client()
        cls.reader_client.force_login(cls.another_author)


class TestHomePage(TestCommon):

    @classmethod
    def setUpTestData(cls):
        super().setUpTestData()
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
            for index in range(1, settings.NOTES_COUNT_ON_HOME_PAGE + 1)
        ]
        Note.objects.bulk_create(all_notes)
        cls.response = cls.author_client.get(reverse(cls.LIST_URL))
        cls.object_list = cls.response.context['object_list']

    def test_notes_count(self):
        """Количество заметок на странице ЗАМЕТОК"""
        expected_count = settings.NOTES_COUNT_ON_HOME_PAGE
        # print([note.author for note in object_list])
        # print([note.created_at for note in object_list])
        notes_count = len(self.object_list)
        self.assertEqual(notes_count, expected_count)


class TestDetailPage(TestCommon):
    NOTE_TEXT = 'Текст заметки'

    @classmethod
    def setUpTestData(cls):
        super().setUpTestData()
        # Создаём новость в БД.
        # cls.note = Note.objects.create(
        #     title='Заголовок',
        #     text=cls.NOTE_TEXT,
        #     author=cls.author,
        #     slug='zagolovok'
        # )
        # Create a note for the author
        cls.note_author = Note.objects.create(
            title='Note for Author',
            text='Text for Author',
            author=cls.author,
            slug='note_for_author'
        )

        # Create a note for the reader
        cls.note_another_author = Note.objects.create(
            title='Note for Reader',
            text='Text for Reader',
            author=cls.another_author,
            slug='note_for_another_author'
        )

    def test_edit_page_contain_noteform(self):
        """на страницы создания и редактирования заметки передаются формы."""
        # Формируем URL.
        url = reverse(self.EDIT_URL, args=(self.note_author.slug,))
        response = self.author_client.get(url)
        # Проверяем, есть ли объект формы в словаре контекста:
        self.assertTrue('form' in response.context)
        form = response.context['form']
        self.assertEqual(form['title'].value(), self.note_author.title)
        self.assertEqual(form['text'].value(), self.note_author.text)
        self.assertEqual(form['slug'].value(), self.note_author.slug)

    def test_notes_list_for_different_users(self):
        """
        - в список заметок одного пользователя
        не попадают заметки другого пользователя;
        - отдельная заметка передаётся на страницу
        в списке object_list в словаре context
        """
        for user, should_see_note in (
            (self.author_client, True),
            (self.reader_client, False)
        ):
            with self.subTest(user=user):
                url = reverse(self.LIST_URL)
                response = user.get(url)
                object_list = response.context['object_list']
                note_present = any((
                    note.title == self.note_author.title
                    and note.text == self.note_author.text
                    and note.slug == self.note_author.slug
                ) for note in object_list)
                self.assertEqual(note_present, should_see_note)
