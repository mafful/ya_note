from http import HTTPStatus

from pytils.translit import slugify


from .base_module import (
    BaseClass,
    SLUG,
    ADD_URL,
    SUCCESS_URL,
    EDIT_NOTE_MADE_BY_ANFISA_URL,
    DELETE_NOTE_MADE_BY_ANFISA_URL

)
from notes.forms import WARNING
from notes.models import Note


class TestLogic(BaseClass):

    def test_anonym_cant_create_note(self):
        """Анонимный пользователь не может создать заметку"""
        initial_set_of_notes = set(Note.objects.all())
        self.client.post(ADD_URL, data=self.form_data)

        # проверяем, что содержимое "до" и "после" одинаково
        self.assertSetEqual(
            initial_set_of_notes, set(Note.objects.all())
        )

    def test_user_can_create_note(self):
        """Авторизованный пользователь может создать заметку"""
        initial_set_of_notes = set(Note.objects.all())

        response = self.fedor_client.post(ADD_URL, data=self.form_data)
        self.assertRedirects(response, SUCCESS_URL)

        final_set_of_notes = set(Note.objects.all())

        # Find notes added during the test
        added_notes = final_set_of_notes - initial_set_of_notes
        print("Added notes:")
        for note in added_notes:
            print(
                f'- {note.pk},{note.title},{note.text},'
                f'{note.slug},{note.author}'
            )

            self.assertEqual(note.title, self.form_data['title'])
            self.assertEqual(note.text, self.form_data['text'])
            self.assertEqual(note.slug, self.form_data['slug'])
            self.assertEqual(note.author, self.fedor)

    def test_note_without_slug(self):
        initial_set_of_notes = set(Note.objects.all())
        # делаем копию self.form_data
        form_data_wo_slug = {**self.form_data}
        # в дальнейшем передаем ее, а не оригинальную self.form_data
        form_data_wo_slug.pop('slug')
        response = self.fedor_client.post(ADD_URL, data=form_data_wo_slug)
        self.assertRedirects(response, SUCCESS_URL)

        final_set_of_notes = set(Note.objects.all())

        # Find notes added during the test
        added_notes = final_set_of_notes - initial_set_of_notes
        print("Added notes:")
        for note in added_notes:
            print(
                f'- {note.pk},{note.title},'
                f'{note.text},{note.slug},{note.author}'
            )

            self.assertEqual(note.author, self.fedor)
            self.assertEqual(note.title, form_data_wo_slug['title'])
            self.assertEqual(note.text, form_data_wo_slug['text'])

            # Проверка, что slug создан корректно
            expected_slug = slugify(form_data_wo_slug['title'])
            self.assertEqual(note.slug, expected_slug)

    def test_slug_for_uniqness(self):
        """Невозможно создать две заметки с одинаковым slug."""
        initial_set_of_notes = set(Note.objects.all())
        self.form_data['slug'] = SLUG

        response = self.fedor_client.post(ADD_URL, data=self.form_data)
        self.assertFormError(
            response,
            'form',
            'slug',
            errors=(self.note_made_by_anfisa.slug + WARNING)
        )
        self.assertEqual(initial_set_of_notes, set(Note.objects.all()))

    def test_author_can_delete_note(self):
        """Автор может удалить свою заметку"""
        notes_count_before = Note.objects.all().count()

        response = self.anfisa_client.delete(
            DELETE_NOTE_MADE_BY_ANFISA_URL)
        self.assertRedirects(response, SUCCESS_URL)

        notes_count_after = Note.objects.all().count()
        self.assertEqual(notes_count_after, notes_count_before - 1)

        self.assertFalse(Note.objects.filter(
            pk=self.note_made_by_anfisa.pk).exists())

    def test_user_cant_delete_note_of_another_user(self):
        """Пользователь не может удалить чужой комментарий"""
        initial_number_of_notes = Note.objects.all().count()

        response = self.fedor_client.delete(
            DELETE_NOTE_MADE_BY_ANFISA_URL)

        self.assertEqual(response.status_code, HTTPStatus.NOT_FOUND)
        self.assertEqual(initial_number_of_notes, Note.objects.count())

        note_trying_to_be_deleted = Note.objects.get(
            pk=self.note_made_by_anfisa.pk)
        self.assertEqual(note_trying_to_be_deleted.author,
                         self.note_made_by_anfisa.author)
        self.assertEqual(note_trying_to_be_deleted.pk,
                         self.note_made_by_anfisa.pk)
        self.assertEqual(note_trying_to_be_deleted.title,
                         self.note_made_by_anfisa.title)
        self.assertEqual(note_trying_to_be_deleted.text,
                         self.note_made_by_anfisa.text)
        self.assertEqual(note_trying_to_be_deleted.slug,
                         self.note_made_by_anfisa.slug)

    def test_author_can_edit_note(self):
        """Редактировать заметки может их автор"""
        response = self.anfisa_client.post(
            EDIT_NOTE_MADE_BY_ANFISA_URL, data=self.form_data)
        self.assertRedirects(response, SUCCESS_URL)

        edited_note = Note.objects.get(pk=self.note_made_by_anfisa.pk)
        self.assertEqual(edited_note.author, self.anfisa)
        self.assertEqual(edited_note.title, self.form_data['title'])
        self.assertEqual(edited_note.text, self.form_data['text'])
        self.assertEqual(edited_note.slug, self.form_data['slug'])

    def test_user_cant_edit_note_of_another_user(self):
        """
        Комментарий одного пользователя недоступенн
        для редактирование другим пользователем
        """
        # Выполняем запрос на редактирование от имени другого пользователя.
        response = self.fedor_client.post(
            EDIT_NOTE_MADE_BY_ANFISA_URL, data=self.form_data)
        # Проверяем, что вернулась 404 ошибка.
        self.assertEqual(response.status_code, HTTPStatus.NOT_FOUND)

        updated_note = Note.objects.get(pk=self.note_made_by_anfisa.pk)

        self.assertEqual(updated_note.title,
                         self.note_made_by_anfisa.title)
        self.assertEqual(updated_note.text, self.note_made_by_anfisa.text)
        self.assertEqual(updated_note.author,
                         self.note_made_by_anfisa.author)
        self.assertEqual(updated_note.slug, self.note_made_by_anfisa.slug)
