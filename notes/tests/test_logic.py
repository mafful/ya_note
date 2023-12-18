
from http import HTTPStatus

from pytils.translit import slugify

from .base_module import (
    BaseClass,
    SLUG,
    ADD_URL,
    SUCCESS_URL,
    EDIT_AUTHOR_NOTE_URL,
    DELETE_AUTHOR_NOTE_URL

)
from notes.forms import WARNING
from notes.models import Note


class TestLogic(BaseClass):

    def test_anonymous_user_cant_create_note(self):
        """Анонимный пользователь не может создать заметку"""
        notes_before = Note.objects.all()
        url = ADD_URL
        self.client.post(url, data=self.form_data)
        notes_after = Note.objects.all()
        self.assertEqual(
            len(notes_after), len(notes_before)
        )
        attributes_to_check = ['author', 'title', 'text', 'slug']
        for attribute in attributes_to_check:
            with self.subTest(attribute=attribute):
                before_values = [
                    getattr(note, attribute) for note in notes_before
                ]
                after_values = [
                    getattr(note, attribute) for note in notes_after
                ]
                self.assertEqual(
                    before_values,
                    after_values,
                    f'{attribute} values should match.'
                )

    def test_user_can_create_note(self):
        """Авторизованный пользователь может отправить комментарий"""
        url = ADD_URL
        response = self.another_author_client.post(url, data=self.form_data)
        self.assertRedirects(response, SUCCESS_URL)
        notes_related_to_another_author = Note.objects.filter(
            author=self.another_author)
        self.assertEqual(
            notes_related_to_another_author.count(), 2)
        # # Получаем объект комментария из базы.
        new_note = notes_related_to_another_author.latest('created_at')
        if new_note is not None:
            attributes_to_check = ['author', 'title', 'text', 'slug']
            for attribute in attributes_to_check:
                with self.subTest(note_id=new_note.id, attribute=attribute):
                    note_value = getattr(new_note, attribute)
                    form_data_value = self.form_data.get(attribute)
                    if attribute == 'author':
                        self.assertIsNone(
                            form_data_value, (
                                f'{attribute} values for note '
                                f'{new_note.id} should match.'
                            )
                        )
                    else:
                        self.assertEqual(
                            note_value,
                            form_data_value, (
                                f'{attribute} values for note '
                                f'{new_note.id} should match.'
                            )
                        )

    def test_note_without_slug(self):
        url = ADD_URL
        form_data = self.form_data
        form_data.pop('slug')
        response = self.another_author_client.post(url, data=form_data)
        self.assertRedirects(response, SUCCESS_URL)
        another_author_notes = Note.objects.filter(
            author=self.another_author)
        self.assertEqual(
            another_author_notes.count(), 2)
        new_note = another_author_notes.latest('created_at')

        if new_note is not None:
            attributes_to_check = ['author', 'title', 'text', 'slug']
            for attribute in attributes_to_check:
                with self.subTest(note_id=new_note.id, attribute=attribute):
                    note_value = getattr(new_note, attribute)
                    form_data_value = self.form_data.get(attribute)

                    if attribute == 'author':
                        self.assertIsNone(
                            form_data_value, (
                                f'{attribute} values for note '
                                f'{new_note.id} should match.'
                            )
                        )
                    elif attribute == 'slug':
                        expected_slug = slugify(form_data['title'])
                        self.assertEqual(
                            note_value, expected_slug
                        )
                    else:
                        self.assertEqual(
                            note_value,
                            form_data_value, (
                                f'{attribute} values for note '
                                f'{new_note.id} should match.'
                            )
                        )

    def test_slug_for_uniqness(self):
        """-Невозможно создать две заметки с одинаковым slug."""
        last_ID_before_try = Note.objects.filter(
            author=self.another_author).latest('created_at').id
        url = ADD_URL
        self.form_data['slug'] = SLUG
        response = self.another_author_client.post(url, data=self.form_data)
        self.assertFormError(
            response, 'form', 'slug', errors=(self.note_author.slug + WARNING)
        )
        self.assertEqual(
            Note.objects.filter(
                author=self.another_author).count(), 1)
        last_ID_after_try = Note.objects.filter(
            author=self.another_author).latest('created_at').id
        self.assertEqual(last_ID_before_try, last_ID_after_try)

    def test_author_can_delete_note(self):
        """автор может удалить свой заметки"""
        # От имени автора комментария отправляем DELETE-запрос на удаление.
        response = self.author_client.delete(DELETE_AUTHOR_NOTE_URL)
        # Заодно проверим статус-коды ответов.
        self.assertRedirects(response, SUCCESS_URL)
        # Считаем количество комментариев в системе.
        notes_count = Note.objects.filter(
            author=self.author).count()
        # Ожидаем ноль комментариев в системе.
        self.assertEqual(
            notes_count, 0)

    def test_user_cant_delete_note_of_another_user(self):
        """пользователь не может удалить чужой комментарий"""
        self.assertEqual(
            Note.objects.filter(author=self.another_author).count(), 1)

        response = self.another_author_client.delete(
            DELETE_AUTHOR_NOTE_URL)

        self.assertEqual(response.status_code, HTTPStatus.NOT_FOUND)

        self.assertEqual(
            Note.objects.filter(author=self.another_author).count(), 1)

        note_after = Note.objects.get(pk=self.note_author.pk)

        attributes_to_check = ['pk', 'author', 'title', 'text', 'slug']
        for attribute in attributes_to_check:
            with self.subTest(attribute=attribute):
                before_values = getattr(self.note_author, attribute)
                after_values = getattr(note_after, attribute)
                self.assertEqual(before_values, after_values,
                                 f"{attribute} values should match.")

    def test_author_can_edit_note(self):
        """редактировать заметки может только их автор"""
        url = EDIT_AUTHOR_NOTE_URL

        response_post = self.author_client.post(url, data=self.form_data)
        self.assertRedirects(response_post, SUCCESS_URL)

        updated_note = Note.objects.get(pk=self.note_author.pk)
        attributes_to_check = ['author', 'title', 'text', 'slug']
        for attribute in attributes_to_check:
            note_value = getattr(updated_note, attribute)
            form_data_value = self.form_data.get(attribute)
            with self.subTest(attribute=attribute):
                if attribute == 'author':
                    self.assertIsNone(
                        form_data_value, (
                            f'{attribute} value for note '
                            f'{updated_note.id} should be None.'
                        )
                    )
                else:
                    self.assertEqual(
                        form_data_value,
                        note_value,
                        f'{attribute} values should match.')

    def test_user_cant_edit_note_of_another_user(self):
        """редактирование комментария недоступно для другого пользователя"""
        # Выполняем запрос на редактирование от имени другого пользователя.
        original_note = self.note_author

        response = self.another_author_client.post(
            EDIT_AUTHOR_NOTE_URL, data=self.form_data)
        # Проверяем, что вернулась 404 ошибка.
        self.assertEqual(response.status_code, HTTPStatus.NOT_FOUND)

        # # Обновляем объект из базы.
        original_note.refresh_from_db()
        note_from_db = original_note

        # Проверяем, что текст остался тем же, что и был.
        attributes_to_check = ['pk', 'author', 'title', 'text', 'slug']

        for attribute in attributes_to_check:
            note_from_db_values = getattr(
                note_from_db, attribute)
            original_values = getattr(self.note_author, attribute)

            with self.subTest(attribute=attribute):
                self.assertEqual(
                    note_from_db_values,
                    original_values,
                    f'{attribute} values should match.')
