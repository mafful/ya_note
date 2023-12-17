from datetime import timedelta

from django.conf import settings
from django.utils import timezone

from .base_module import MyBaseClass
from notes.models import Note
from notes.forms import NoteForm


class TestHomePage(MyBaseClass):

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
            for index in range(1, settings.NOTES_COUNT_ON_HOME_PAGE)
        ]
        Note.objects.bulk_create(all_notes)

    def test_notes_count(self):
        """Количество заметок на странице ЗАМЕТОК"""
        expected_count = settings.NOTES_COUNT_ON_HOME_PAGE
        response = self.author_client.get(self.list_url)
        notes_count = len(response.context['object_list'])
        self.assertEqual(notes_count, expected_count)

    def test_edit_page_contain_noteform(self):
        """на страницы редактирования заметки передается форма."""
        url = self.edit_author_note_url
        response = self.author_client.get(url)
        self.assertTrue('form' in response.context)

        form = response.context['form']
        self.assertIsInstance(form, NoteForm)

    def test_notes_list_for_author(self):
        """
        Проверяет, что в список заметок пользователя
        попадают только его собственные заметки.
        Каждая заметка передаётся на страницу в списке
        object_list в словаре context.
        """
        url = self.list_url
        response = self.author_client.get(url)
        object_list = response.context['object_list']

        # Проверяем, что только заметки автора присутствуют в списке
        for note in object_list:
            self.assertEqual(note.author, self.author)
            self.assertEqual(note.title, note.title)
            self.assertEqual(note.text, note.text)
            self.assertEqual(note.slug, note.slug)

    def test_notes_list_for_another_author(self):
        """
        Проверяет, что в список заметок другого автора
        не попадают заметки других пользователей.
        Каждая заметка передаётся на страницу в списке
        object_list в словаре context.
        """
        url = self.list_url
        response = self.another_author_client.get(url)
        object_list = response.context['object_list']

        # Проверяем, что заметки других пользователей
        # отсутствуют в списке
        for note in object_list:
            self.assertNotEqual(note.author, self.author)
