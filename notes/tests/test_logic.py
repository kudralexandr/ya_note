#  Тесты на unittest для проекта YaNote.
from http import HTTPStatus
from random import randint

from pytils.translit import slugify

from django.urls import reverse
from django.contrib.auth import get_user_model

from django.test import Client, TestCase

from notes.forms import WARNING
from notes.models import Note


User = get_user_model()

UCODE_TITLE = {randint(10001, 99999)}
NOTE_TITLE = f'Заголовок заметки #code: {UCODE_TITLE}'
NEW_NOTE_TITLE = 'Обновлённый заголовок заметки'
NOTE_TEXT = 'Текст заметки'
NEW_NOTE_TEXT = 'Обновлённый текст заметки'
DEF_SLUG = 'myslugnote'
DEF_SLUG_ARG = (DEF_SLUG,)
NEW_SLUG = 'newslugnote'


class TestNoteCreation(TestCase):

    @classmethod
    def setUpTestData(cls):
        cls.url = reverse('notes:add', None)
        cls.author = User.objects.create(username='Автор Заметки')
        cls.author_client = Client()
        cls.author_client.force_login(cls.author)
        # Делаем всё то же самое для пользователя-читателя.
        cls.reader = User.objects.create(username='Читатель')
        cls.reader_client = Client()
        cls.reader_client.force_login(cls.reader)
        cls.form_data = {
            'title': NOTE_TITLE,
            'text': NOTE_TEXT,
            'slug': DEF_SLUG,
            'author': cls.author,
        }
        cls.form_data_upd = {
            'title': NEW_NOTE_TITLE,
            'text': NEW_NOTE_TEXT,
            'slug': NEW_SLUG,
        }

        cls.note_success = reverse('notes:success', None)
        cls.note_list = reverse('notes:list', None)
        cls.note_detail = reverse('notes:detail', args=DEF_SLUG_ARG)
        cls.edit_url = reverse('notes:edit', args=DEF_SLUG_ARG)
        cls.delete_url = reverse('notes:delete', args=DEF_SLUG_ARG)

    def is_note_in_db(self):
        return Note.objects.filter(title=self.form_data['title']).exists()

    #  1.1 Анонимный пользователь не может создать заметку.
    def test_anonymous_user_cant_create_note(self):
        self.client.post(self.url, data=self.form_data)
        self.assertFalse(self.is_note_in_db())

    #  1.2 Залогиненный пользователь может создать заметку.
    def test_user_can_create_note(self):
        # Совершаем запрос через авторизованный клиент.
        response = self.reader_client.post(self.url, data=self.form_data)
        self.assertRedirects(response, reverse('notes:success'))
        self.assertTrue(self.is_note_in_db())
        if self.is_note_in_db():
            note = Note.objects.get(title=self.form_data['title'])
            # Проверяем, что все атрибуты заметки совпадают с ожидаемыми.
            self.assertEqual(note.title, self.form_data['title'])
            self.assertEqual(note.text, self.form_data['text'])
            self.assertEqual(note.slug, self.form_data['slug'])
            self.assertEqual(note.author, self.reader)

    #  2.Невозможно создать две заметки с одинаковым slug.
    def test_double_slug(self):
        note = Note(**self.form_data)
        note.save()
        notes_count_after_first_add = Note.objects.count()
        response = self.author_client.post(self.url, data=self.form_data)
        self.assertFormError(
            response,
            form='form',
            field='slug',
            errors=self.form_data['slug'] + WARNING
        )
        # Дополнительно убедимся, что комментарий не был создан.
        notes_count_after_second_add = Note.objects.count()
        self.assertEqual(
            notes_count_after_first_add, notes_count_after_second_add
        )

    #  3. Если при создании заметки не заполнен slug, то он формируется
    # автоматически с помощью функции pytils.translit.slugify.
    def test_generate_slug(self):
        self.form_data['slug'] = ''
        response = self.author_client.post(self.url, data=self.form_data)
        self.assertRedirects(response, self.note_success)
        note = Note.objects.get(title=self.form_data['title'])
        self.assertEqual(note.slug, slugify(self.form_data['title']))

    #  4.1 Пользователь может удалять свои заметки.
    def test_author_can_delete_note(self):
        note = Note(**self.form_data)
        note.save()
        self.assertTrue(self.is_note_in_db())
        response = self.author_client.delete(self.delete_url)
        self.assertRedirects(response, self.note_success)
        self.assertFalse(self.is_note_in_db())

    #  4.2 Пользователь не может удалять чужие заметки.
    def test_user_cant_delete_note_of_another_user(self):
        note = Note(**self.form_data)
        note.save()
        self.assertTrue(self.is_note_in_db())
        response = self.reader_client.delete(self.delete_url)
        # Проверяем, что вернулась 404 ошибка.
        self.assertEqual(response.status_code, HTTPStatus.NOT_FOUND)
        # Убедимся, что комментарий по-прежнему на месте.
        self.assertTrue(self.is_note_in_db())

    #  4.3 Пользователь может редактировать свои заметки.
    def test_author_can_edit_note(self):
        note = Note(**self.form_data)
        note.save()
        self.assertTrue(self.is_note_in_db())
        response = self.author_client.post(
            self.edit_url, data=self.form_data_upd
        )
        # Проверяем, что сработал редирект.
        self.assertRedirects(response, self.note_success)
        note.refresh_from_db()
        # Проверяем, что текст комментария соответствует обновленному.
        self.assertEqual(note.title, NEW_NOTE_TITLE)
        self.assertEqual(note.text, NEW_NOTE_TEXT)
        self.assertEqual(note.slug, NEW_SLUG)

    #  4.4 Пользователь не может редактировать чужие заметки.
    def test_user_cant_edit_comment_of_another_user(self):
        # Создаем запись в БД.
        note = Note(**self.form_data)
        note.save()
        # Убеждаемся, что запись появилась в БД.
        self.assertTrue(self.is_note_in_db())
        # Выполняем запрос на редактирование от имени другого пользователя.
        response = self.reader_client.post(
            self.edit_url, data=self.form_data_upd
        )
        # Проверяем, что вернулась 404 ошибка.
        self.assertEqual(response.status_code, HTTPStatus.NOT_FOUND)
        # Обновляем объект комментария.
        note.refresh_from_db()
        # Проверяем, что текст остался тем же, что и был.
        self.assertEqual(note.title, NOTE_TITLE)
        self.assertEqual(note.text, NOTE_TEXT)
        self.assertEqual(note.slug, DEF_SLUG)
