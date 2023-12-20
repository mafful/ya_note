from http import HTTPStatus

from django.utils import timezone
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

    def test_anonymous_user_cant_create_note(self):
        """Анонимный пользователь не может создать заметку"""
        initial_set_of_notes = set(Note.objects.all())
        self.client.post(ADD_URL, data=self.form_data)
        final_set_of_notes = set(Note.objects.all())

        # проверяем, что содержимое "до" и "после" одинаково
        self.assertSetEqual(
            initial_set_of_notes, final_set_of_notes
        )

    def test_user_can_create_note_first_try(self):
        """Авторизованный пользователь может отправить комментарий"""
        initial_number_of_notes = Note.objects.count()

        response = self.fedor_client.post(ADD_URL, data=self.form_data)
        self.assertRedirects(response, SUCCESS_URL)

        final_number_of_notes = Note.objects.count()
        self.assertEqual(initial_number_of_notes + 1, final_number_of_notes)

        new_note_1 = Note.objects.filter(
            title=self.form_data['title'],
            text=self.form_data['text'],
            author=self.fedor,
            slug=self.form_data['slug'],
            created_at__lte=timezone.now(),
        ).order_by('-created_at').first()
        self.assertEqual(new_note_1.title, self.form_data['title'])
        self.assertEqual(new_note_1.text, self.form_data['text'])
        self.assertEqual(new_note_1.author, self.fedor)
        self.assertEqual(new_note_1.slug, self.form_data['slug'])

    def test_user_can_create_note_second_try(self):
        """Авторизованный пользователь может отправить комментарий"""
        initial_notes = set(Note.objects.all())

        copy_of_form_data = {**self.form_data}
        copy_of_form_data['author'] = self.fedor

        response = self.fedor_client.post(ADD_URL, data=self.form_data)
        self.assertRedirects(response, SUCCESS_URL)

        final_notes_set = set(Note.objects.all())

        new_note_2 = Note.objects.filter(
            slug=copy_of_form_data['slug']).first()
        self.assertIsNotNone(new_note_2)
        self.assertIsNotNone(new_note_2.pk)
        updated_notes_set = set(initial_notes | {new_note_2})
        self.assertEqual(updated_notes_set, final_notes_set)

        self.assertIn(
            (new_note_2.author, new_note_2.title, new_note_2.slug),
            {(note.author, note.title, note.slug) for note in final_notes_set}
        )
        self.assertEqual(new_note_2.title, self.form_data['title'])
        self.assertEqual(new_note_2.text, self.form_data['text'])
        self.assertEqual(new_note_2.author, self.fedor)
        self.assertEqual(new_note_2.slug, self.form_data['slug'])

    def test_note_without_slug(self):
        # делаем копию self.form_data
        form_data_wo_slug = {**self.form_data}
        # в дальнейшем передаем ее, а не оригинальную self.form_data
        form_data_wo_slug.pop('slug')
        response = self.fedor_client.post(ADD_URL, data=form_data_wo_slug)
        self.assertRedirects(response, SUCCESS_URL)

        new_notes = Note.objects.filter(title=form_data_wo_slug['title'])
        self.assertEqual(new_notes.count(), 1)

        new_note = new_notes.first()
        self.assertEqual(new_note.author, self.fedor)
        self.assertEqual(new_note.title, form_data_wo_slug['title'])
        self.assertEqual(new_note.text, form_data_wo_slug['text'])

        # Проверка, что slug создан корректно
        expected_slug = slugify(form_data_wo_slug['title'])
        self.assertEqual(new_note.slug, expected_slug)

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

        final_set_of_notes = set(Note.objects.all())
        self.assertEqual(initial_set_of_notes, final_set_of_notes)

    def test_author_can_delete_note(self):
        """автор может удалить свою заметку"""
        notes_count_before = Note.objects.all().count()
        # self.assertTrue(Note.objects.filter(
        #     pk=self.note_made_by_anfisa.pk).exists())

        response = self.anfisa_client.delete(
            DELETE_NOTE_MADE_BY_ANFISA_URL)
        self.assertRedirects(response, SUCCESS_URL)

        notes_count_after = Note.objects.all().count()
        self.assertEqual(notes_count_after, notes_count_before - 1)

        self.assertFalse(Note.objects.filter(
            pk=self.note_made_by_anfisa.pk).exists())

    def test_user_cant_delete_note_of_another_user(self):
        """пользователь не может удалить чужой комментарий"""
        initial_number_of_notes = Note.objects.all().count()

        response = self.fedor_client.delete(
            DELETE_NOTE_MADE_BY_ANFISA_URL)

        self.assertEqual(response.status_code, HTTPStatus.NOT_FOUND)
        self.assertEqual(initial_number_of_notes, Note.objects.count())

        last_note_after = Note.objects.get(pk=self.note_made_by_fedor.pk)
        self.assertEqual(last_note_after.title, self.note_made_by_fedor.title)
        self.assertEqual(last_note_after.text, self.note_made_by_fedor.text)
        self.assertEqual(last_note_after.author,
                         self.note_made_by_fedor.author)
        self.assertEqual(last_note_after.slug, self.note_made_by_fedor.slug)

    def test_author_can_edit_note(self):
        """редактировать заметки может их автор"""
        response_post = self.anfisa_client.post(
            EDIT_NOTE_MADE_BY_ANFISA_URL, data=self.form_data)
        self.assertRedirects(response_post, SUCCESS_URL)

        updated_note = Note.objects.get(pk=self.note_made_by_anfisa.pk)
        self.assertEqual(updated_note.author, self.anfisa)
        self.assertEqual(updated_note.title, self.form_data['title'])
        self.assertEqual(updated_note.text, self.form_data['text'])
        self.assertEqual(updated_note.slug, self.form_data['slug'])

    def test_user_cant_edit_note_of_another_user(self):
        """
        комментарий одного пользователя недоступенн
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
