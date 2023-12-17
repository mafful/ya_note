
from http import HTTPStatus

from pytils.translit import slugify

from .base_module import MyBaseClass
from notes.forms import WARNING
from notes.models import Note


class TestCommon(MyBaseClass):

    def test_anonymous_user_cant_create_note(self):
        """Анонимный пользователь не может создать заметку"""
        notes_before_count = Note.objects.all().count()
        url = self.add_url
        self.client.post(url, data=self.form_data)
        notes_after_count = Note.objects.all().count()
        self.assertEqual(notes_after_count, notes_before_count)

        initial_note_author = Note.objects.filter(
            title=self.note_author.title,
            text=self.note_author.text,
            author=self.note_author.author
        ).first()

        initial_note_another_author = Note.objects.filter(
            title=self.note_another_author.title,
            text=self.note_another_author.text,
            author=self.note_another_author.author
        ).first()

        self.assertIsNotNone(initial_note_author)
        self.assertIsNotNone(initial_note_another_author)

    def test_user_can_create_note(self):
        """Авторизованный пользователь может отправить комментарий"""
        url = self.add_url
        response = self.another_author_client.post(url, data=self.form_data)
        self.assertRedirects(response, self.success_url)
        # Считаем количество комментариев.
        notes_related_to_another_author = Note.objects.filter(
            author=self.another_author)
        self.assertEqual(
            notes_related_to_another_author.count(),
            self.initial_number_another_author_notes + 1)
        # # Получаем объект комментария из базы.
        note = Note.objects.last()
        # Проверяем, что все атрибуты комментария совпадают с ожидаемыми.
        self.assertEqual(note.title, self.form_data['title'])
        self.assertEqual(note.text, self.form_data['text'])
        self.assertEqual(note.slug, self.form_data['slug'])
        self.assertEqual(note.author, self.another_author)

    def test_note_without_slug(self):
        url = self.add_url
        form_data = self.form_data
        form_data.pop('slug')
        response = self.another_author_client.post(url, data=form_data)
        self.assertRedirects(response, self.success_url)
        another_author_notes = Note.objects.filter(
            author=self.another_author)
        self.assertEqual(
            another_author_notes.count(),
            self.initial_number_another_author_notes + 1)
        # Получаем созданную заметку из базы методом last(),
        # который вернет последний объект из запроса
        # или None, если объектов нет,
        # а также проверяем, что возвращаемая заметка
        new_note = another_author_notes.last()
        if new_note is not None:
            # Здесь вы можете выполнять проверки для новой заметки
            expected_slug = slugify(self.form_data['title'])
            assert new_note.slug == expected_slug
            assert new_note.title == self.form_data['title']
            assert new_note.text == self.form_data['text']
        else:
            self.fail("Не удалось получить созданную заметку.")

    def test_slug_for_uniqness(self):
        """-Невозможно создать две заметки с одинаковым slug."""
        url = self.add_url
        self.form_data['slug'] = self.note_author.slug
        response = self.author_client.post(url, data=self.form_data)
        self.assertFormError(
            response, 'form', 'slug', errors=(self.note_author.slug + WARNING)
        )
        another_author_notes = Note.objects.filter(
            author=self.another_author)
        self.assertEqual(
            another_author_notes.count(),
            self.initial_number_another_author_notes)

    def test_author_can_delete_note(self):
        """автор может удалить свой заметки"""
        # От имени автора комментария отправляем DELETE-запрос на удаление.
        response = self.author_client.delete(self.delete_author_note_url)
        # Заодно проверим статус-коды ответов.
        self.assertRedirects(response, self.success_url)
        # Считаем количество комментариев в системе.
        notes_count = Note.objects.filter(
            author=self.author).count()
        # Ожидаем ноль комментариев в системе.
        self.assertEqual(
            notes_count,
            self.initial_number_author_notes - 1)

    def test_user_cant_delete_note_of_another_user(self):
        """пользователь не может удалить чужой комментарий"""
        self.assertEqual(
            Note.objects.filter(author=self.another_author).count(),
            self.initial_number_another_author_notes)
        response = self.another_author_client.delete(
            self.delete_author_note_url
        )
        # Проверяем, что вернулась 404 ошибка.
        self.assertEqual(response.status_code, HTTPStatus.NOT_FOUND)
        self.assertEqual(
            Note.objects.filter(author=self.another_author).count(),
            self.initial_number_another_author_notes)
        note_after = Note.objects.get(pk=self.note_author.pk)
        assert note_after.slug == self.note_author.slug
        assert note_after.title == self.note_author.title
        assert note_after.text == self.note_author.text
        assert note_after.author == self.note_author.author

    def test_author_can_edit_note(self):
        """редактировать заметки может только их автор"""
        url = self.edit_author_note_url
        print(url)
        print(self.author)
        response = self.author_client.get(url)
        self.assertEqual(response.status_code, HTTPStatus.OK)

        # Отправляем POST-запрос с обновленными данными.
        response_post = self.author_client.post(url, data=self.form_data)
        self.assertRedirects(response_post, self.success_url)

        # Получаем обновленную заметку из базы данных.
        updated_note = Note.objects.get(pk=self.note_author.pk)

        # Проверяем, что данные в базе соответствуют ожидаемым изменениям.
        self.assertEqual(updated_note.title, self.form_data['title'])
        self.assertEqual(updated_note.text, self.form_data['text'])
        self.assertEqual(updated_note.slug, self.form_data['slug'])

    def test_user_cant_edit_note_of_another_user(self):
        """редактирование комментария недоступно для другого пользователя"""
        # Выполняем запрос на редактирование от имени другого пользователя.
        existing_note = Note.objects.get(pk=self.note_author.pk)
        response = self.another_author_client.post(
            self.edit_author_note_url, data=self.form_data)
        # Проверяем, что вернулась 404 ошибка.
        self.assertEqual(response.status_code, HTTPStatus.NOT_FOUND)
        # Обновляем объект комментария.
        self.note_author.refresh_from_db()
        # Проверяем, что текст остался тем же, что и был.
        self.assertEqual(existing_note.text, self.note_author.text)
        self.assertEqual(existing_note.title, self.note_author.title)
        self.assertEqual(existing_note.slug, self.note_author.slug)
        self.assertEqual(existing_note.author, self.note_author.author)
