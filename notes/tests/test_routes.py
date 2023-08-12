#  Тесты на unittest для проекта YaNote.

'''
1.Главная страница доступна анонимному пользователю.

2.Аутентифицированному пользователю доступна:
- страница со списком заметок notes/,
- страница успешного добавления заметки done/,
- страница добавления новой заметки add/.

3.Страницы
- отдельной заметки,
- удаления и
- редактирования заметки
доступны  только автору заметки.
Если на эти страницы попытается зайти другой пользователь — вернётся
ошибка 404.

4.При попытке перейти на страницу
- списка заметок,
- страницу успешного добавления записи,
- страницу добавления заметки,
- отдельной заметки,
- редактирования или
- удаления заметки
анонимный пользователь перенаправляется на страницу логина.

5.Страницы
- регистрации пользователей,
- входа в учётную запись и
- выхода из неё
доступны всем пользователям.
'''

from http import HTTPStatus

from django.contrib.auth import get_user_model
from django.test import TestCase, Client
from django.urls import reverse

from notes.models import Note

User = get_user_model()

LOGIN_URL = reverse('users:login')
LOGIN_REDIRECT = f'{LOGIN_URL}?next='


PAGE_LOGIN = 'users:login'
PAGE_SIGNUP = 'users:signup'
PAGE_LOGOUT = 'users:logout'
PAGE_HOME = 'notes:home'
PAGE_ADD_NOTE = 'notes:add'
PAGE_EDIT_NOTE = 'notes:edit'
PAGE_DETAIL_NOTE = 'notes:detail'
PAGE_DELETE_NOTE = 'notes:delete'
PAGE_LIST_NOTES = 'notes:list'
PAGE_DONE = 'notes:success'


class TestRoutes(TestCase):

    @classmethod
    def setUpTestData(cls):
        cls.author = User.objects.create(username='Автор Заметки')
        cls.author_client = Client()
        cls.author_client.force_login(cls.author)
        cls.reader = User.objects.create(username='Читатель простой')
        cls.reader_client = Client()
        cls.reader_client.force_login(cls.reader)
        cls.note = Note.objects.create(
            title='Заголовок',
            text='Текст',
            author=cls.author,
        )

    def test_availability_for_anyusers_to_view_edit_delete_note(self):
        page_user_statuses = (
            # Home, logins.
            (PAGE_HOME, None, self.client, HTTPStatus.OK,),
            (PAGE_LOGIN, None, self.client, HTTPStatus.OK,),
            (PAGE_SIGNUP, None, self.client, HTTPStatus.OK,),
            (PAGE_LOGOUT, None, self.client, HTTPStatus.OK,),
            # Detail.
            (
                PAGE_DETAIL_NOTE, (self.note.slug,),
                self.client, HTTPStatus.FOUND,
            ),
            (
                PAGE_DETAIL_NOTE, (self.note.slug,),
                self.reader_client, HTTPStatus.NOT_FOUND,
            ),
            (
                PAGE_DETAIL_NOTE, (self.note.slug,),
                self.author_client, HTTPStatus.OK,
            ),
            # Edit.
            (
                PAGE_EDIT_NOTE, (self.note.slug,),
                self.client, HTTPStatus.FOUND,
            ),
            (
                PAGE_EDIT_NOTE, (self.note.slug,),
                self.reader_client, HTTPStatus.NOT_FOUND,
            ),
            (
                PAGE_EDIT_NOTE, (self.note.slug,),
                self.author_client, HTTPStatus.OK,
            ),
            # Delete.
            (
                PAGE_DELETE_NOTE, (self.note.slug,),
                self.client, HTTPStatus.FOUND,
            ),
            (
                PAGE_DELETE_NOTE, (self.note.slug,),
                self.reader_client, HTTPStatus.NOT_FOUND
            ),
            (
                PAGE_DELETE_NOTE, (self.note.slug,),
                self.author_client, HTTPStatus.OK
            ),
        )
        for page, args, user, status in page_user_statuses:
            with self.subTest(page=page, args=args, user=user, status=status):
                url = reverse(page, args=args)
                response = user.get(url)
                self.assertEqual(response.status_code, status)

    def test_redirect_for_anonymous_client(self):
        urls = (
            (PAGE_LIST_NOTES, None),
            (PAGE_ADD_NOTE, None),
            (PAGE_DONE, None),
            (PAGE_DETAIL_NOTE, (self.note.slug,)),
            (PAGE_EDIT_NOTE, (self.note.slug,)),
            (PAGE_DELETE_NOTE, (self.note.slug,)),
        )
        for name, args in urls:
            with self.subTest(name=name):
                url = reverse(name, args=args)
                response = self.client.get(url)
                self.assertRedirects(response, LOGIN_REDIRECT + url)
