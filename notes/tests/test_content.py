#  Тесты на unittest для проекта YaNote.

'''
1.отдельная заметка передаётся на страницу со списком заметок в списке
 object_list в словаре context;
2.в список заметок одного пользователя не попадают заметки
 другого пользователя;
3.на страницы создания и редактирования заметки передаются формы.
'''

from datetime import datetime, timedelta
from django.utils import timezone

from django.conf import settings
from django.test import TestCase, Client
# Импортируем функцию reverse(), она понадобится для получения адреса страницы.
from django.urls import reverse

from django.contrib.auth import get_user_model

from notes.models import Note

User = get_user_model()


class TestContentList(TestCase):

    @classmethod
    def setUpTestData(cls):
        cls.author = User.objects.create(username='Автор Заметки')
        cls.admin = User.objects.create(username='Читатель простой')
        cls.note = Note.objects.create(
            title='Заголовок',
            text='Текст',
            author=cls.author,
        )

    def test_note_in_list_for_author(self):
        url = reverse('notes:list')
        # Создаем клиента
        #author_client = Client()
        # Авторизуем клиента
        #author_client.force_login(self.author)
        # Запрашиваем страницу со списком заметок:
        #response = author_client.get(url)
        # Получаем список объектов из контекста,
        # Проверяем, что заметка находится в этом списке:
        self.client.force_login(self.author)
        response = self.client.get(url)
        assert self.note in response.context['object_list']

    # В этом тесте тоже используем фикстуру заметки,
    # но в качестве клиента используем admin_client;
    # он не автор заметки, так что заметка не должна быть ему видна.
    def test_note_not_in_list_for_another_user(self):
        url = reverse('notes:list')
        #admin_client = Client()
        #admin_client.force_login(self.admin)
        self.client.force_login(self.admin)
        response = self.client.get(url)
        #if response.context is not None:
        assert self.note not in response.context['object_list']
        #self.assertIsNone(response.context)

    def test_authorized_client_has_form(self):
        urls = (
            ('notes:add', None),
            ('notes:edit', (self.note.slug,)),
        )
        for name, args in urls:
            with self.subTest(name=name):
                url = reverse(name, args=args)
                self.client.force_login(self.author)
                response = self.client.get(url)
                self.assertIn('form', response.context)
