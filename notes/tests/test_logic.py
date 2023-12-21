from http import HTTPStatus

from pytils.translit import slugify


from .base_module import (
    User,
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

    def test_anonymous_user_cant_create_note(self):
        """Анонимный пользователь не может создать заметку"""
        initial_set_of_notes = frozenset(Note.objects.all())
        self.client.post(ADD_URL, data=self.form_data)

        # проверяем, что содержимое "до" и "после" одинаково
        self.assertSetEqual(
            initial_set_of_notes, set(Note.objects.all())
        )

    def test_user_can_create_note_first_try(self):
        """Авторизованный пользователь может отправить комментарий"""
        initial_note = self.create_notes_dict()['additional_note']

        response = self.fedor_client.post(ADD_URL, data=self.form_data)
        self.assertRedirects(response, SUCCESS_URL)

        final_note = Note.objects.all().last()

        self.assertEqual(final_note.title, initial_note['title'])
        self.assertEqual(final_note.text, initial_note['text'])
        self.assertEqual(final_note.author, initial_note['author'])
        self.assertEqual(final_note.slug, initial_note['slug'])

    def test_note_without_slug(self):
        # делаем копию self.form_data
        form_data_wo_slug = {**self.form_data}
        # в дальнейшем передаем ее, а не оригинальную self.form_data
        form_data_wo_slug.pop('slug')
        response = self.fedor_client.post(ADD_URL, data=form_data_wo_slug)
        self.assertRedirects(response, SUCCESS_URL)

        new_note = Note.objects.last()
        self.assertEqual(new_note.author, self.fedor)
        self.assertEqual(new_note.title, form_data_wo_slug['title'])
        self.assertEqual(new_note.text, form_data_wo_slug['text'])

        # Проверка, что slug создан корректно
        expected_slug = slugify(form_data_wo_slug['title'])
        self.assertEqual(new_note.slug, expected_slug)

    def test_slug_for_uniqness(self):
        """Невозможно создать две заметки с одинаковым slug."""
        initial_set_of_notes = frozenset(Note.objects.all())
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

        last_note_after = Note.objects.last()
        self.assertEqual(last_note_after.author,
                         self.note_made_by_fedor.author)
        self.assertEqual(last_note_after.pk, self.note_made_by_fedor.pk)
        self.assertEqual(last_note_after.title, self.note_made_by_fedor.title)
        self.assertEqual(last_note_after.text, self.note_made_by_fedor.text)
        self.assertEqual(last_note_after.slug, self.note_made_by_fedor.slug)

    def test_author_can_edit_note(self):
        """Редактировать заметки может их автор"""
        response = self.anfisa_client.post(
            EDIT_NOTE_MADE_BY_ANFISA_URL, data=self.form_data)
        self.assertRedirects(response, SUCCESS_URL)
        user_id = self.anfisa_client.session.get('_auth_user_id')
        user_instance = User.objects.get(pk=user_id)
        username = user_instance.username

        updated_note = Note.objects.filter(author=self.anfisa).last()
        self.assertEqual(updated_note.author.username, username)
        self.assertEqual(updated_note.title, self.form_data['title'])
        self.assertEqual(updated_note.text, self.form_data['text'])
        self.assertEqual(updated_note.slug, self.form_data['slug'])

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
