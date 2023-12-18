from django.conf import settings

from .base_module import (
    BaseClass,
    LIST_URL,
    ADD_URL,
    EDIT_AUTHOR_NOTE_URL,
)
from notes.forms import NoteForm


class TestContent(BaseClass):

    def test_notes_count(self):
        """Количество заметок на странице ЗАМЕТОК"""
        expected_count = settings.NOTES_COUNT_ON_HOME_PAGE
        response = self.spam_author_client.get(LIST_URL)
        notes_count = len(response.context['object_list'])
        self.assertEqual(notes_count, expected_count)

    def test_add_edit_page_contain_noteform(self):
        """
        на страницах создания и редактирования заметки
        передается форма.
        """
        for url in (EDIT_AUTHOR_NOTE_URL, ADD_URL):
            url = url
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
        url = LIST_URL
        response = self.author_client.get(url)
        object_list = response.context['object_list']
        notes = [
            note for note in object_list if note.author
            == self.note_author.author
        ]
        self.assertEqual(len(notes), 1)
        self.assertEqual(len(notes), len([note for note in object_list]))
        self.assertEqual(notes[0].author, self.note_author.author)
        self.assertEqual(notes[0].title, self.note_author.title)
        self.assertEqual(notes[0].text, self.note_author.text)
        self.assertEqual(notes[0].slug, self.note_author.slug)

    def test_notes_list_for_another_author(self):
        """
        Проверяет, что в список заметок другого автора
        не попадают заметки других пользователей.
        Каждая заметка передаётся на страницу в списке
        object_list в словаре context.
        """
        url = LIST_URL
        response = self.another_author_client.get(url)
        object_list = response.context['object_list']

        allowed_author = self.another_author
        self.assertIn(
            allowed_author,
            [note.author for note in object_list],
            f'Only {allowed_author} should be in.'
        )
