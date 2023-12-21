from django.conf import settings

from .base_module import (
    BaseClass,
    LIST_URL,
    ADD_URL,
    EDIT_NOTE_MADE_BY_ANFISA_URL,
)
from notes.forms import NoteForm


class TestContent(BaseClass):

    def test_notes_count(self):
        """Количество заметок на странице ЗАМЕТОК"""
        response = self.spam_client.get(LIST_URL)
        objects_count = len(response.context['object_list'])
        self.assertEqual(objects_count, settings.NOTES_COUNT_ON_HOME_PAGE)

    def assert_page_contains_noteform(self, url):
        """Проверка наличия NoteForm на странице."""
        response = self.anfisa_client.get(url)
        self.assertIn('form', response.context)
        form = response.context['form']
        self.assertIsInstance(form, NoteForm)

    def test_edit_page_contains_noteform(self):
        """Проверка наличия NoteForm на странице редактирования."""
        url = EDIT_NOTE_MADE_BY_ANFISA_URL
        response = self.anfisa_client.get(url)
        self.assertIn('form', response.context)
        form = response.context['form']
        self.assertIsInstance(form, NoteForm)

    def test_add_page_contains_noteform(self):
        """Проверка наличия NoteForm на странице добавления."""
        url = ADD_URL
        response = self.anfisa_client.get(url)
        self.assertIn('form', response.context)
        form = response.context['form']
        self.assertIsInstance(form, NoteForm)

    def test_notes_list_for_author(self):
        """
        Проверяет, что в список заметок пользователя
        попадают только его собственные заметки.
        Каждая заметка передаётся на страницу в списке
        object_list в словаре context.
        """
        response = self.anfisa_client.get(LIST_URL)
        bunch_of_notes = response.context['object_list']
        self.assertEqual(len(bunch_of_notes), 1)

        note_to_check = bunch_of_notes[0]
        self.assertEqual(note_to_check.title, self.note_made_by_anfisa.title)
        self.assertEqual(note_to_check.text, self.note_made_by_anfisa.text)
        self.assertEqual(note_to_check.author, self.note_made_by_anfisa.author)
        self.assertEqual(note_to_check.slug, self.note_made_by_anfisa.slug)

    def test_notes_list_for_another_author(self):
        """
        Проверяет, что в список заметок другого автора
        не попадают заметки других пользователей.
        """
        response = self.fedor_client.get(LIST_URL)

        self.assertNotIn(
            self.note_made_by_anfisa,
            response.context['object_list']
        )
