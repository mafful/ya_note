# import pytest
from http import HTTPStatus

from .base_module import (
    BaseClass,
    HOME_URL,
    LIST_URL,
    ADD_URL,
    SUCCESS_URL,
    LOGIN_URL,
    LOGOUT_URL,
    SIGNUP_URL,
    DETAIL_AUTHOR_NOTE_URL,
    EDIT_AUTHOR_NOTE_URL,
    DELETE_AUTHOR_NOTE_URL

)


class TestRoutes(BaseClass):

    def test_pages_availability(self):
        """Доступность отдельных страниц"""
        cases = [
            [self.client, HOME_URL, HTTPStatus.OK],
            [self.client, LOGIN_URL, HTTPStatus.OK],
            [self.client, LOGOUT_URL, HTTPStatus.OK],
            [self.client, SIGNUP_URL, HTTPStatus.OK],
        ]
        for client_name, url, expected_answer in cases:
            with self.subTest(
                client=client_name,
                url=url,
                expected_answer=expected_answer
            ):
                response = client_name.get(url)
                self.assertEqual(
                    response.status_code,
                    expected_answer,
                    f'URL {url} expected {expected_answer}, but got {response}'
                )

    def test_pages_availability_for_auth_user(self):
        """
        Аутентифицированному пользователю доступна страница
        со списком заметок notes/,
        страница успешного добавления заметки done/,
        страница добавления новой заметки add/.
        """
        cases = [
            [self.author_client, LIST_URL, HTTPStatus.OK],
            [self.author_client, ADD_URL, HTTPStatus.OK],
            [self.author_client, SUCCESS_URL, HTTPStatus.OK],
        ]
        for client_name, url, expected_answer in cases:
            with self.subTest(
                client=client_name,
                url=url,
                expected_answer=expected_answer
            ):
                response = client_name.get(url)
                self.assertEqual(
                    response.status_code,
                    expected_answer,
                    f'URL {url} expected {expected_answer}, but got {response}'
                )

    def test_redirect_for_anonymous_client(self):
        """Проверка редиректов"""
        cases = [
            [ADD_URL,
                f'{LOGIN_URL}?next={ADD_URL}'],
            [EDIT_AUTHOR_NOTE_URL,
                f'{LOGIN_URL}?next={EDIT_AUTHOR_NOTE_URL}'],
            [DELETE_AUTHOR_NOTE_URL,
                f'{LOGIN_URL}?next={DELETE_AUTHOR_NOTE_URL}'],
        ]
        for url, expected_redirect_url in cases:
            with self.subTest(
                url=url,
                expected_redirect_url=expected_redirect_url
            ):
                response = self.client.get(url)
                self.assertRedirects(response, expected_redirect_url)

    def test_availability_for_note_edit_and_delete(self):
        """Проверка страниц редактирования и удаления заметки"""
        cases = [
            [self.author_client,
             DETAIL_AUTHOR_NOTE_URL, HTTPStatus.OK],
            [self.author_client,
             EDIT_AUTHOR_NOTE_URL, HTTPStatus.OK],
            [self.author_client,
             DELETE_AUTHOR_NOTE_URL, HTTPStatus.OK],
            [self.another_author_client,
             DETAIL_AUTHOR_NOTE_URL, HTTPStatus.NOT_FOUND],
            [self.another_author_client,
             EDIT_AUTHOR_NOTE_URL, HTTPStatus.NOT_FOUND],
            [self.another_author_client,
             DELETE_AUTHOR_NOTE_URL, HTTPStatus.NOT_FOUND],
        ]
        for client_name, url, expected_answer in cases:
            with self.subTest(
                client=client_name,
                url=url,
                expected_answer=expected_answer
            ):
                response = client_name.get(url)
                self.assertEqual(
                    response.status_code,
                    expected_answer,
                    f'URL {url} expected {expected_answer}, but got {response}'
                )
