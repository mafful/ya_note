from django.conf import settings

from .base_module import (
    BaseClass,
    LIST_URL,
    ADD_URL,
    EDIT_NOTE_MADE_BY_ANFISA_URL,
)
from notes.forms import NoteForm


class TestContent(BaseClass):

    def test_01_notes_count(self):
        """Количество заметок на странице ЗАМЕТОК"""
        response = self.spam_client.get(LIST_URL)
        notes_count = len(response.context['object_list'])
        self.assertEqual(notes_count, settings.NOTES_COUNT_ON_HOME_PAGE)

    def test_02_add_edit_page_contain_noteform(self):
        """
        на страницах создания и редактирования заметки
        передается форма.
        """
        for url in (EDIT_NOTE_MADE_BY_ANFISA_URL, ADD_URL):
            response = self.anfisa_client.get(url)
            self.assertTrue('form' in response.context)
            form = response.context['form']
            self.assertIsInstance(form, NoteForm)

    def test_03_notes_list_for_author(self):
        """
        Проверяет, что в список заметок пользователя
        попадают только его собственные заметки.
        Каждая заметка передаётся на страницу в списке
        object_list в словаре context.
        """
        response = self.anfisa_client.get(LIST_URL)
        bunch_of_notes = response.context['object_list']
        self.assertEqual(len(bunch_of_notes), 1)

        attributes_to_check = ['pk', 'author', 'title', 'text', 'slug']
        for attribute in attributes_to_check:
            with self.subTest(attribute=attribute):
                before_values = getattr(self.note_made_by_anfisa, attribute)
                after_values = getattr(bunch_of_notes[0], attribute)
                self.assertEqual(before_values, after_values,
                                 f"{attribute} values should match.")

    def test_04_notes_list_for_another_author(self):
        """
        Проверяет, что в список заметок другого автора
        не попадают заметки других пользователей.
        Каждая заметка передаётся на страницу в списке
        object_list в словаре context.
        """
        response = self.fedor_client.get(LIST_URL)
        bunch_of_notes = response.context['object_list']

        notes_not_expected = [
            self.note_made_by_anfisa,
            self.spam_notes
        ]
        for note in notes_not_expected:
            self.assertNotIn(
                note,
                bunch_of_notes,
                f'The note {notes_not_expected} should not be in.'
            )
