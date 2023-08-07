#  Тесты на unittest для проекта YaNote.
from http import HTTPStatus

from django.contrib.auth import get_user_model
from django.test import Client, TestCase
from django.urls import reverse
from django.core.exceptions import ValidationError

from pytils.translit import slugify

from notes.forms import WARNING
from notes.models import Note

User = get_user_model()

'''
1.Залогиненный пользователь может создать заметку, а анонимный — не может.
2.Невозможно создать две заметки с одинаковым slug.
3.Если при создании заметки не заполнен slug, то он формируется автоматически,
 с помощью функции pytils.translit.slugify.
4.Пользователь может редактировать и удалять свои заметки,
 но не может редактировать или удалять чужие.
'''


class TestNoteCreation(TestCase):

    @classmethod
    def setUpTestData(cls):
        cls.url = reverse('notes:add', None)
        cls.user = User.objects.create(username='Автор Заметки')
        cls.auth_client = Client()
        cls.auth_client.force_login(cls.user)
        cls.form_data = {
            'title': 'Заголовок заметки',
            'text': 'Текст заметки',
            'slug': 'myslugnote',
        }
        
    def test_anonymous_user_cant_create_note(self):
        # Совершаем запрос от анонимного клиента, в POST-запросе отправляем
        # предварительно подготовленные данные формы с текстом комментария.
        self.client.post(self.url, data=self.form_data)
        # Считаем количество комментариев.
        notes_count = Note.objects.count()
        # Ожидаем, что комментариев в базе нет - сравниваем с нулём.
        self.assertEqual(notes_count, 0)

    def test_user_can_create_note(self):
        # Совершаем запрос через авторизованный клиент.
        response = self.auth_client.post(self.url, data=self.form_data)
        # Проверяем, что редирект привёл к разделу с комментами.
        self.assertRedirects(response, reverse('notes:success'))
        # Считаем количество комментариев.
        notes_count = Note.objects.count()
        # Убеждаемся, что есть один комментарий.
        self.assertEqual(notes_count, 1)
        # Получаем объект комментария из базы.
        note = Note.objects.get()
        # Проверяем, что все атрибуты комментария совпадают с ожидаемыми.
        self.assertEqual(note.title, self.form_data['title'])
        self.assertEqual(note.text, self.form_data['text'])
        self.assertEqual(note.slug, self.form_data['slug'])

    def test_double_slug(self):
        response = self.auth_client.post(self.url, data=self.form_data)
        self.assertRedirects(response, reverse('notes:success'))
        response = self.auth_client.post(self.url, data=self.form_data)
        #self.assertRaisesMessage(
        #    ValidationError,
        #    self.form_data['slug'] + WARNING
        #)
        self.assertFormError(
            response,
            form='form',
            field='slug',
            errors=self.form_data['slug'] + WARNING
        )
        # Дополнительно убедимся, что комментарий не был создан.
        notes_count = Note.objects.count()
        self.assertEqual(notes_count, 1)

    def test_generate_slug(self):
        self.form_data['slug'] = ''
        response = self.auth_client.post(self.url, data=self.form_data)
        self.assertRedirects(response, reverse('notes:success'))
        note = Note.objects.get()
        self.assertEqual(note.slug, slugify(self.form_data['title']))


class TestCommentEditDelete(TestCase):
    NOTE_TITLE = 'Заголовок заметки'
    NEW_NOTE_TITLE = 'Обновлённый заголовок заметки'
    NOTE_TEXT = 'Текст заметки'
    NEW_NOTE_TEXT = 'Обновлённый текст заметки'
    
    @classmethod
    def setUpTestData(cls):
        cls.author = User.objects.create(username='Автор комментария')
        cls.author_client = Client()
        cls.author_client.force_login(cls.author)
        # Делаем всё то же самое для пользователя-читателя.
        cls.reader = User.objects.create(username='Читатель')
        cls.reader_client = Client()
        cls.reader_client.force_login(cls.reader)
        #  Создаем заметку
        cls.note = Note.objects.create(
            title=cls.NOTE_TITLE,
            text=cls.NOTE_TEXT,
            author=cls.author,
            )
        cls.note_success = reverse('notes:success', None)
        cls.note_detail = reverse('notes:detail', args=(cls.note.slug,))
        cls.note_list = reverse('notes:list', None)
        # URL для редактирования.
        cls.edit_url = reverse('notes:edit', args=(cls.note.slug,))
        # URL для удаления комментария.
        cls.delete_url = reverse('notes:delete', args=(cls.note.slug,))
        # Формируем данные для POST-запроса по обновлению комментария.
        cls.form_data = {
            'title': cls.NEW_NOTE_TITLE,
            'text': cls.NEW_NOTE_TEXT,
            }

    def test_author_can_delete_note(self):
        response = self.author_client.delete(self.delete_url)
        self.assertRedirects(response, self.note_success)
        note_count = Note.objects.count()
        self.assertEqual(note_count, 0)

