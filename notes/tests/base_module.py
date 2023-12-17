from django.contrib.auth import get_user_model
from django.test import Client, TestCase
from django.urls import reverse

from notes.models import Note

User = get_user_model()


class MyBaseClass(TestCase):

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

        cls.note_author = Note.objects.create(
            title='Note for Author',
            text='Text for Author',
            author=cls.author,

        )
        cls.initial_number_author_notes = 1

        cls.note_another_author = Note.objects.create(
            title='Note for Another Author',
            text=cls.NOTE_TEXT,
            author=cls.another_author,
        )
        cls.initial_number_another_author_notes = 1

        cls.home_url = reverse('notes:home')
        cls.list_url = reverse('notes:list')
        cls.detail_author_note_url = reverse(
            'notes:detail', args=(cls.note_author.slug,))
        cls.add_url = reverse('notes:add')
        cls.edit_author_note_url = reverse(
            'notes:edit', args=(cls.note_author.slug,))
        cls.delete_author_note_url = reverse(
            'notes:delete', args=(cls.note_author.slug,))
        cls.success_url = reverse('notes:success')
        cls.login_url = reverse('users:login')
        cls.logout_url = reverse('users:logout')
        cls.signup_url = reverse('users:signup')

        # Формируем данные для POST-запроса по обновлению комментария.
        cls.form_data = {
            'title': 'Заголовок_форма',
            'text': cls.NOTE_TEXT,
            'slug': 'zagolovok_forma'
        }
