from datetime import timedelta

from django.conf import settings
from django.contrib.auth import get_user_model
from django.test import Client, TestCase
from django.urls import reverse
from django.utils import timezone

from notes.models import Note

User = get_user_model()

NOTE_TEXT = 'Текст заметки'
NEW_NOTE_TEXT = 'Обновлённый комментарий'
SLUG = 'note_for_author'

HOME_URL = reverse('notes:home')
LIST_URL = reverse('notes:list')
ADD_URL = reverse('notes:add')
SUCCESS_URL = reverse('notes:success')
LOGIN_URL = reverse('users:login')
LOGOUT_URL = reverse('users:logout')
SIGNUP_URL = reverse('users:signup')

DETAIL_AUTHOR_NOTE_URL = reverse('notes:detail', args=(SLUG,))
EDIT_AUTHOR_NOTE_URL = reverse('notes:edit', args=(SLUG,))
DELETE_AUTHOR_NOTE_URL = reverse('notes:delete', args=(SLUG,))


class BaseClass(TestCase):

    @classmethod
    def setUpTestData(cls):
        cls.author = User.objects.create(username='Автор')
        cls.author_client = Client()
        cls.author_client.force_login(cls.author)

        cls.another_author = User.objects.create(username='Другой Автор')
        cls.another_author_client = Client()
        cls.another_author_client.force_login(cls.another_author)

        cls.spam_author = User.objects.create(username='Спам Автор')
        cls.spam_author_client = Client()
        cls.spam_author_client.force_login(cls.spam_author)

        cls.note_author = Note.objects.create(
            title='Note for Author',
            text='Text for Author',
            author=cls.author,
            slug=SLUG
        )

        today = timezone.now()
        spam_notes = [
            Note(
                title=f'Сапм заметка {index}',
                text='Спам текст.',
                slug=f'Spam_zametka_{index}',
                author=cls.spam_author,
                created_at=today + timedelta(days=index, minutes=index + 1))
            for index in range(0, settings.NOTES_COUNT_ON_HOME_PAGE)
        ]
        Note.objects.bulk_create(spam_notes)
        cls.note_another_author = Note.objects.create(
            title='Note for Another Author',
            text=NOTE_TEXT,
            author=cls.another_author,
        )

        # Формируем данные для POST-запроса по обновлению комментария.
        cls.form_data = {
            'title': 'Заголовок_форма',
            'text': NOTE_TEXT,
            'slug': 'zagolovok_forma'
        }
