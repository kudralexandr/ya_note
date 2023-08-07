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
from django.test import TestCase
from django.urls import reverse

from notes.models import Note

User = get_user_model()


class TestRoutes(TestCase):

    @classmethod
    def setUpTestData(cls):
        cls.author = User.objects.create(username='Автор Заметки')
        cls.reader = User.objects.create(username='Читатель простой')
        cls.note = Note.objects.create(
            title='Заголовок',
            text='Текст',
            author=cls.author,
        )

    def test_pages_availability(self):
        urls = (
            ('notes:home', None),
            ('users:login', None),
            ('users:logout', None),
            ('users:signup', None),
        )
        for name, args in urls:
            with self.subTest(name=name):
                url = reverse(name, args=args)
                response = self.client.get(url)
                self.assertEqual(response.status_code, HTTPStatus.OK)

    def test_availability_for_note_view_edit_delete(self):
        urls = [
            'notes:detail',
            'notes:edit',
            'notes:delete'
        ]
        users_statuses = (
            (self.author, HTTPStatus.OK),
            (self.reader, HTTPStatus.NOT_FOUND),
        )
        for user, status in users_statuses:
            self.client.force_login(user)
            for name in urls:
                with self.subTest(user=user, name=name):
                    url = reverse(name, args=(self.note.slug,))
                    response = self.client.get(url)
                    self.assertEqual(response.status_code, status)

    def test_redirect_for_anonymous_client(self):
        urls = (
            ('notes:list', None),
            ('notes:add', None),
            ('notes:success', None),
            ('notes:detail', (self.note.slug,)),
            ('notes:edit', (self.note.slug,)),
            ('notes:delete', (self.note.slug,)),
        )

        login_url = reverse('users:login')
        for name, args in urls:
            with self.subTest(name=name):
                url = reverse(name, args=args)
                redirect_url = f'{login_url}?next={url}'
                response = self.client.get(url)
                self.assertRedirects(response, redirect_url)
