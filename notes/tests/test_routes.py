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
    DETAIL_NOTE_MADE_BY_ANFISA_URL,
    EDIT_NOTE_MADE_BY_ANFISA_URL,
    DELETE_NOTE_MADE_BY_ANFISA_URL

)


class TestRoutes(BaseClass):

    def test_pages_availability(self):
        """Доступность отдельных страниц"""
        cases = [
            [self.client, HOME_URL, HTTPStatus.OK],
            [self.client, LOGIN_URL, HTTPStatus.OK],
            [self.client, LOGOUT_URL, HTTPStatus.OK],
            [self.client, SIGNUP_URL, HTTPStatus.OK],
            [self.anfisa_client, LIST_URL, HTTPStatus.OK],
            [self.anfisa_client, ADD_URL, HTTPStatus.OK],
            [self.anfisa_client, SUCCESS_URL, HTTPStatus.OK],
            [self.anfisa_client,
             DETAIL_NOTE_MADE_BY_ANFISA_URL, HTTPStatus.OK],
            [self.anfisa_client,
             EDIT_NOTE_MADE_BY_ANFISA_URL, HTTPStatus.OK],
            [self.anfisa_client,
             DELETE_NOTE_MADE_BY_ANFISA_URL, HTTPStatus.OK],
            [self.fedor_client,
             DETAIL_NOTE_MADE_BY_ANFISA_URL, HTTPStatus.NOT_FOUND],
            [self.fedor_client,
             EDIT_NOTE_MADE_BY_ANFISA_URL, HTTPStatus.NOT_FOUND],
            [self.fedor_client,
             DELETE_NOTE_MADE_BY_ANFISA_URL, HTTPStatus.NOT_FOUND],

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
                    expected_answer
                )

    def test_redirect_for_anonymous_client(self):
        """Проверка редиректов"""
        cases = [
            [ADD_URL,
                f'{LOGIN_URL}?next={ADD_URL}'],
            [EDIT_NOTE_MADE_BY_ANFISA_URL,
                f'{LOGIN_URL}?next={EDIT_NOTE_MADE_BY_ANFISA_URL}'],
            [DELETE_NOTE_MADE_BY_ANFISA_URL,
                f'{LOGIN_URL}?next={DELETE_NOTE_MADE_BY_ANFISA_URL}'],
        ]
        for url, expected_redirect_url in cases:
            with self.subTest(
                url=url,
                expected_redirect_url=expected_redirect_url
            ):
                response = self.client.get(url)
                self.assertRedirects(response, expected_redirect_url)
