
from http import HTTPStatus

from pytils.translit import slugify
from django.contrib.auth import get_user_model
from django.test import Client, TestCase
from django.urls import reverse

from notes.models import Note
from notes.forms import WARNING

User = get_user_model()


class TestCommon(TestCase):
    # Вынесем ссылку на домашнюю страницу в атрибуты класса.
    ADD_URL = 'notes:add'
    DETAIL_URL = 'notes:detail'
    DELETE_URL = 'notes:delete'
    EDIT_URL = 'notes:edit'
    LIST_URL = 'notes:list'
    SUCCESS_URL = 'notes:success'

    NOTE_TEXT = 'Текст заметки'
    NEW_NOTE_TEXT = 'Обновлённый комментарий'

    @classmethod
    def setUpTestData(cls):
        cls.author = User.objects.create(username='Автор')
        cls.author_client = Client()
        cls.author_client.force_login(cls.author)
        cls.another_author = User.objects.create(username='Другой Автор')
        cls.another_author_client = Client()
        cls.another_author_client.force_login(cls.another_author)

        cls.note = Note.objects.create(
            title='Заголовок',
            text=cls.NOTE_TEXT,
            author=cls.author,
            slug='zagolovok'
        )

        cls.note_url = reverse(cls.DETAIL_URL, args=(cls.note.slug,))
        cls.add_url = reverse(cls.ADD_URL)
        cls.edit_url = reverse(cls.EDIT_URL, args=(cls.note.slug,))
        cls.delete_url = reverse(cls.DELETE_URL, args=(cls.note.slug,))
        cls.success_url = reverse(cls.SUCCESS_URL)

        # Формируем данные для POST-запроса по обновлению комментария.
        cls.form_data = {
            'title': 'Заголовок_форма',
            'text': cls.NOTE_TEXT,
            'slug': 'zagolovok_forma'
        }


class TestNoteCreation(TestCommon):

    def test_anonymous_user_cant_create_note(self):
        """Анонимный пользователь не может создать заметку"""
        notes_count_before = Note.objects.count()
        url = self.add_url
        # Совершаем запрос от анонимного клиента, в POST-запросе отправляем
        # предварительно подготовленные данные формы с текстом комментария.
        self.client.post(url, data=self.form_data)
        notes_count_after = Note.objects.count()
        self.assertEqual(notes_count_after, notes_count_before)

    def test_user_can_create_note(self):
        """Авторизованный пользователь может отправить комментарий"""
        url = self.add_url
        response = self.another_author_client.post(url, data=self.form_data)
        self.assertRedirects(response, self.success_url)
        # Считаем количество комментариев.
        notes_related_to = Note.objects.filter(author=self.another_author)
        self.assertEqual(notes_related_to.count(), 1)
        # # Получаем объект комментария из базы.
        note = Note.objects.filter(author=self.another_author).get()
        # Проверяем, что все атрибуты комментария совпадают с ожидаемыми.
        self.assertEqual(note.text, self.NOTE_TEXT)
        self.assertEqual(note.author, self.another_author)

    def test_slug(self):
        url = reverse(self.ADD_URL)
        form_data = self.form_data
        form_data.pop('slug')
        response = self.another_author_client.post(url, data=form_data)
        self.assertRedirects(response, self.success_url)
        another_author_notes = Note.objects.filter(
            author=self.another_author)
        self.assertEqual(another_author_notes.count(), 1)
        # Получаем созданную заметку из базы:
        new_note = another_author_notes.get()
        # Формируем ожидаемый slug:
        expected_slug = slugify(self.form_data['title'])
        # Проверяем, что slug заметки соответствует ожидаемому:
        assert new_note.slug == expected_slug
        assert new_note.title == self.form_data['title']
        assert new_note.text == self.form_data['text']

    def test_slug_for_uniqness(self):
        """-Невозможно создать две заметки с одинаковым slug."""
        url = reverse(self.ADD_URL)
        self.form_data['slug'] = self.note.slug
        response = self.author_client.post(url, data=self.form_data)
        self.assertFormError(
            response, 'form', 'slug', errors=(self.note.slug + WARNING)
        )
        another_author_notes = Note.objects.filter(
            author=self.another_author)
        self.assertEqual(another_author_notes.count(), 0)


class TestNoteEditDelete(TestCommon):

    def test_author_can_delete_note(self):
        """автор может удалить свой заметки"""
        notes_count = Note.objects.count()
        # В начале теста в БД всегда есть 1 заметка, созданная в setUpTestData.
        self.assertEqual(notes_count, 1)
        # От имени автора комментария отправляем DELETE-запрос на удаление.
        response = self.author_client.delete(self.delete_url)
        # Заодно проверим статус-коды ответов.
        self.assertRedirects(response, self.success_url)
        # Считаем количество комментариев в системе.
        notes_count = Note.objects.count()
        # Ожидаем ноль комментариев в системе.
        self.assertEqual(notes_count, 0)

    def test_user_cant_delete_note_of_another_user(self):
        """пользователь не может удалить чужой комментарий"""
        note_before = Note.objects.all().get()
        # В начале теста в БД всегда есть 1 заметка, созданная в setUpTestData.
        self.assertEqual(Note.objects.all().count(), 1)
        # Выполняем запрос на удаление от пользователя-читателя.
        response = self.another_author_client.delete(self.delete_url)
        # Проверяем, что вернулась 404 ошибка.
        self.assertEqual(response.status_code, HTTPStatus.NOT_FOUND)
        # Убедимся, что комментарий по-прежнему на месте.
        self.assertEqual(Note.objects.all().count(), 1)
        note_after = Note.objects.all().get()
        assert note_after.slug == note_before.slug
        assert note_after.title == note_before.title
        assert note_after.text == note_before.text

    def test_author_can_edit_note(self):
        """редактировать заметки может только их автор"""
        url = self.edit_url
        response = self.author_client.get(url)
        self.assertEqual(response.status_code, HTTPStatus.OK)

    def test_user_cant_edit_note_of_another_user(self):
        """редактирование комментария недоступно для другого пользователя"""
        # Выполняем запрос на редактирование от имени другого пользователя.
        existing_note = Note.objects.get(pk=self.note.pk)
        response = self.another_author_client.post(
            self.edit_url, data=self.form_data)
        # Проверяем, что вернулась 404 ошибка.
        self.assertEqual(response.status_code, HTTPStatus.NOT_FOUND)
        # Обновляем объект комментария.
        self.note.refresh_from_db()
        # Проверяем, что текст остался тем же, что и был.
        self.assertEqual(existing_note.text, self.note.text)
        self.assertEqual(existing_note.title, self.note.title)
        self.assertEqual(existing_note.slug, self.note.slug)
