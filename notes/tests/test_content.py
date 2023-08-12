#  Тесты на unittest для проекта YaNote.

from django.urls import reverse
from django.contrib.auth import get_user_model
from django.test import TestCase

from notes.models import Note
from notes.forms import NoteForm

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

    #  1. отдельная заметка передаётся на страницу со списком заметок.
    #  в списке object_list в словаре context.
    #  2.в список заметок одного пользователя не попадают заметки
    #  другого пользователя.
    def test_note_in_list_for_any_users(self):
        users = (
            (self.author, True),
            (self.admin, False),
        )
        for user, note_in_list_exp in users:  # 1-T, 2-F
            with self.subTest(user=user):
                url = reverse('notes:list')
                self.client.force_login(user)
                response = self.client.get(url)
                self.assertEqual(
                    note_in_list_exp,
                    self.note in response.context['object_list']
                )

    #  3. На страницы создания и редактирования заметки передаются формы.
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
                self.assertIsInstance(response.context['form'], NoteForm)
