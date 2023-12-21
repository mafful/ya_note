from django.conf import settings
from django.contrib.auth import get_user_model
from django.test import Client, TestCase
from django.urls import reverse

from notes.models import Note

User = get_user_model()

NOTE_TEXT = 'Текст заметки'
NEW_NOTE_TEXT = 'Обновлённый комментарий'
SLUG = 'note_made_by_anfisa'

HOME_URL = reverse('notes:home')
LIST_URL = reverse('notes:list')
ADD_URL = reverse('notes:add')
SUCCESS_URL = reverse('notes:success')
LOGIN_URL = reverse('users:login')
LOGOUT_URL = reverse('users:logout')
SIGNUP_URL = reverse('users:signup')

DETAIL_NOTE_MADE_BY_ANFISA_URL = reverse('notes:detail', args=(SLUG,))
EDIT_NOTE_MADE_BY_ANFISA_URL = reverse('notes:edit', args=(SLUG,))
DELETE_NOTE_MADE_BY_ANFISA_URL = reverse('notes:delete', args=(SLUG,))


class BaseClass(TestCase):

    @classmethod
    def setUpTestData(cls):
        cls.anfisa = User.objects.create(username='Анфиса')
        cls.anfisa_client = Client()
        cls.anfisa_client.force_login(cls.anfisa)

        cls.fedor = User.objects.create(username='Федор')
        cls.fedor_client = Client()
        cls.fedor_client.force_login(cls.fedor)

        cls.spam = User.objects.create(username='Спам')
        cls.spam_client = Client()
        cls.spam_client.force_login(cls.spam)

        cls.note_made_by_anfisa = Note.objects.create(
            title='Note by Anfisa',
            text='Text writed by Anfisa',
            author=cls.anfisa,
            slug=SLUG
        )

        Note.objects.bulk_create(
            Note(
                title=f'Сапм заметка {index}',
                text='Спам текст.',
                slug=f'Spam_zametka_{index}',
                author=cls.spam)
            for index in range(0, settings.NOTES_COUNT_ON_HOME_PAGE)
        )

        cls.note_made_by_fedor = Note.objects.create(
            title='Note by Fedor',
            text=NOTE_TEXT,
            author=cls.fedor,
            slug='note_by_fedor'
        )

        # Формируем данные для POST-запроса по обновлению комментария.
        cls.form_data = {
            'title': 'Заголовок_форма',
            'text': NOTE_TEXT,
            'slug': 'zagolovokforma'
        }

    def create_notes_dict(self):
        notes_dict = {
            'note_made_by_anfisa': {
                'title': 'Note by Anfisa',
                'text': 'Text written by Anfisa',
                'author': self.anfisa,
                'slug': SLUG
            },
            'spam_notes': [
                {
                    'title': f'Spam заметка {index}',
                    'text': 'Спам текст.',
                    'slug': f'Spam_zametka_{index}',
                    'author': self.spam
                }
                for index in range(0, settings.NOTES_COUNT_ON_HOME_PAGE)
            ],
            'note_made_by_fedor': {
                'title': 'Note by Fedor',
                'text': NOTE_TEXT,
                'author': self.fedor,
                'slug': 'note_by_fedor'
            },
            'additional_note': {
                'title': self.form_data['title'],
                'text': self.form_data['text'],
                'author': self.fedor,
                'slug': self.form_data['slug']
            }
        }
        return notes_dict
