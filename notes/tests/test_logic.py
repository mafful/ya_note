from http import HTTPStatus

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

    def test_05_anonymous_user_cant_create_note(self):
        """Анонимный пользователь не может создать заметку"""
        notes_before = set(Note.objects.all())
        self.client.post(ADD_URL, data=self.form_data)
        notes_after = set(Note.objects.all())

        # проверяем, что содержимое "до" и "после" одинаково
        self.assertSetEqual(
            notes_before, notes_after,
            'The set of notes should be the same.'
        )

    def test_06_user_can_create_note(self):
        """Авторизованный пользователь может отправить комментарий"""
        notes_before = Note.objects.filter(author=self.fedor).count()
        last_pk_before = Note.objects.latest('pk').pk

        response = self.fedor_client.post(ADD_URL, data=self.form_data)
        self.assertRedirects(response, SUCCESS_URL)

        notes_after = Note.objects.filter(author=self.fedor).count()
        self.assertEqual(notes_before + 1, notes_after)

        new_note = Note.objects.latest('pk')
        self.assertEqual(last_pk_before + 1, new_note.pk)
        self.assertEqual(new_note.title, self.form_data['title'])
        self.assertEqual(new_note.text, self.form_data['text'])
        self.assertEqual(new_note.author, self.fedor)
        self.assertEqual(new_note.slug, self.form_data['slug'])

    def test_07_note_without_slug(self):
        # делаем копию self.form_data
        form_data_wo_slug = {**self.form_data}
        # в дальнейшем передаем ее, а не оригинальную self.form_data
        form_data_wo_slug.pop('slug')
        response = self.fedor_client.post(ADD_URL, data=form_data_wo_slug)
        self.assertRedirects(response, SUCCESS_URL)

        fedors_notes = Note.objects.filter(author=self.fedor)
        self.assertEqual(fedors_notes.count(), 2)

        new_note = fedors_notes.latest('pk')
        if new_note is not None:
            self.assertEqual(new_note.author, self.fedor)
            self.assertEqual(new_note.title, self.form_data['title'])
            self.assertEqual(new_note.text, self.form_data['text'])
            self.assertEqual(new_note.slug, self.form_data['slug'])

    def test_08_slug_for_uniqness(self):
        """-Невозможно создать две заметки с одинаковым slug."""
        last_note_before = Note.objects.latest('pk')
        self.form_data['slug'] = SLUG

        response = self.fedor_client.post(ADD_URL, data=self.form_data)
        self.assertFormError(
            response,
            'form',
            'slug',
            errors=(self.note_made_by_anfisa.slug + WARNING)
        )
        last_note_after = Note.objects.latest('pk')
        self.assertEqual(last_note_after.title, last_note_before.title)
        self.assertEqual(last_note_after.text, last_note_before.text)
        self.assertEqual(last_note_after.author, last_note_before.author)
        self.assertEqual(last_note_after.slug, last_note_before.slug)

    def test_09_author_can_delete_note(self):
        """автор может удалить свой заметки"""
        notes_count_before = Note.objects.all().count()
        self.assertTrue(Note.objects.filter(
            pk=self.note_made_by_anfisa.pk).exists())

        response = self.anfisa_client.delete(
            DELETE_NOTE_MADE_BY_ANFISA_URL)
        self.assertRedirects(response, SUCCESS_URL)

        notes_count_after = Note.objects.all().count()
        self.assertEqual(notes_count_after, notes_count_before - 1)

        self.assertFalse(Note.objects.filter(
            pk=self.note_made_by_anfisa.pk).exists())

    def test_10_user_cant_delete_note_of_another_user(self):
        """пользователь не может удалить чужой комментарий"""
        notes_count_before = Note.objects.all().count()

        response = self.fedor_client.delete(
            DELETE_NOTE_MADE_BY_ANFISA_URL)

        self.assertEqual(response.status_code, HTTPStatus.NOT_FOUND)

        notes_count_after = Note.objects.all().count()
        self.assertEqual(notes_count_after, notes_count_before)

        note_after = Note.objects.get(pk=self.note_made_by_anfisa.pk)
        self.assertEqual(note_after.title, self.note_made_by_anfisa.title)
        self.assertEqual(note_after.text, self.note_made_by_anfisa.text)
        self.assertEqual(note_after.author, self.note_made_by_anfisa.author)
        self.assertEqual(note_after.slug, self.note_made_by_anfisa.slug)

    def test_11_author_can_edit_note(self):
        """редактировать заметки может только их автор"""
        response_post = self.anfisa_client.post(
            EDIT_NOTE_MADE_BY_ANFISA_URL, data=self.form_data)
        self.assertRedirects(response_post, SUCCESS_URL)

        updated_note = Note.objects.get(pk=self.note_made_by_anfisa.pk)
        self.assertEqual(updated_note.author, self.anfisa)
        self.assertEqual(updated_note.title, self.form_data['title'])
        self.assertEqual(updated_note.text, self.form_data['text'])
        self.assertEqual(updated_note.slug, self.form_data['slug'])

    def test_12_user_cant_edit_note_of_another_user(self):
        """редактирование комментария недоступно для другого пользователя"""
        # Выполняем запрос на редактирование от имени другого пользователя.
        original_note = self.note_made_by_anfisa

        response = self.fedor_client.post(
            EDIT_NOTE_MADE_BY_ANFISA_URL, data=self.form_data)
        # Проверяем, что вернулась 404 ошибка.
        self.assertEqual(response.status_code, HTTPStatus.NOT_FOUND)

        # # Обновляем объект из базы.
        original_note.refresh_from_db()
        note_from_db = original_note
        self.assertEqual(note_from_db.title, self.note_made_by_anfisa.title)
        self.assertEqual(note_from_db.text, self.note_made_by_anfisa.text)
        self.assertEqual(note_from_db.author, self.note_made_by_anfisa.author)
        self.assertEqual(note_from_db.slug, self.note_made_by_anfisa.slug)
