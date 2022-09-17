import shutil
import tempfile
from ..forms import PostForm
from ..models import Post, Group
from django.test import Client, TestCase, override_settings
from django.urls import reverse
from django.contrib.auth import get_user_model
from http import HTTPStatus
from django.core.files.uploadedfile import SimpleUploadedFile
from django.conf import settings

User = get_user_model()

# Создаем временную папку для медиа-файлов;
# на момент теста медиа папка будет переопределена
# Для сохранения media-файлов в тестах будет использоваться
# временная папка TEMP_MEDIA_ROOT, а потом мы ее удалим
TEMP_MEDIA_ROOT = tempfile.mkdtemp(dir=settings.BASE_DIR)


@override_settings(MEDIA_ROOT=TEMP_MEDIA_ROOT)
class TaskCreateFormTests(TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        # Создаем запись в базе данных для проверки сушествующего slug
        cls.user = User.objects.create_user(username='TestUser')
        cls.group = Group.objects.create(title='Тестовая группа',
                                         slug='test_slug',
                                         description='Тестовое описание')
        # в этом методе создаем только группу
        # cls.post = Post.objects.create(text='Первый пост', group=cls.group,
        #                                author=cls.user)

        # Создаем форму, если нужна проверка атрибутов
        cls.form = PostForm()

    def setUp(self):
        self.guest_client = Client()
        self.user = TaskCreateFormTests.user
        self.authorized_client = Client()
        self.authorized_client.force_login(self.user)
        small_gif = (
            b'\x47\x49\x46\x38\x39\x61\x02\x00'
            b'\x01\x00\x80\x00\x00\x00\x00\x00'
            b'\xFF\xFF\xFF\x21\xF9\x04\x00\x00'
            b'\x00\x00\x00\x2C\x00\x00\x00\x00'
            b'\x02\x00\x01\x00\x00\x02\x02\x0C'
            b'\x0A\x00\x3B'
        )
        self.uploaded = SimpleUploadedFile(
            name='small.gif',
            content=small_gif,
            content_type='image/gif'
        )

    @classmethod
    def tearDownClass(cls):
        super().tearDownClass()
        shutil.rmtree(TEMP_MEDIA_ROOT, ignore_errors=True)

    def test_create_task(self):
        """Валидная форма создает запись в Post."""
        # Создаем первый пост и проверяем статус запроса
        response = self.authorized_client.post(
            reverse('posts:profile',
                    kwargs={
                        'username': TaskCreateFormTests.user.username
                    }),
            data={
                'text': 'Test post',
                'group': TaskCreateFormTests.group.id
            },
            follow=True
        )

        self.assertEqual(response.status_code, HTTPStatus.OK)
        upload = self.uploaded

        form_data = {
            'text': 'Test post',
            'group': TaskCreateFormTests.group.id,
            'author': TaskCreateFormTests.user,
            'image': upload,
        }
        # Отправляем POST-запрос
        response = self.authorized_client.post(
            reverse('posts:post_create'),
            data=form_data,
            follow=True
        )
        # Проверяем, сработал ли редирект
        self.assertRedirects(
            response, reverse(
                'posts:profile',
                kwargs={
                    'username': TaskCreateFormTests.user.username
                }
            )
        )

        # Получаем пост и проверяем все его проперти
        post = Post.objects.first()
        self.assertEqual(post.text, 'Test post')
        self.assertEqual(post.author, self.user)
        self.assertEqual(post.group, TaskCreateFormTests.group)
        self.assertEqual(Post.objects.count(), 1)
        self.assertEqual(post.image, 'posts/small.gif')

    def test_authorized_user_edit_post(self):
        # проверка редактирования записи авторизованным пользователем
        post = Post.objects.create(
            text='post_text',
            author=self.user
        )
        form_data = {
            'text': 'post_text_edit',
            'group': self.group.id
        }
        response = self.authorized_client.post(
            reverse(
                'posts:post_edit',
                args=[post.id]),
            data=form_data,
            follow=True
        )
        self.assertRedirects(
            response,
            reverse('posts:post_detail', kwargs={'post_id': post.id})
        )
        post = Post.objects.first()
        self.assertEqual(response.status_code, HTTPStatus.OK)
        self.assertEqual(post.text, form_data['text'])
        self.assertEqual(post.author, self.user)
        self.assertEqual(post.group.id, form_data['group'])

    def test_nonauthorized_user_create_post(self):
        # проверка создания записи не авторизованным пользователем
        form_data = {
            'text': 'non_auth_edit_text',
            'group': self.group.id
        }
        response = self.guest_client.post(
            reverse('posts:post_create'),
            data=form_data,
            follow=True
        )
        self.assertEqual(response.status_code, HTTPStatus.OK)
        self.assertRedirects(
            response,
            ('/auth/login/?next=/create/')
        )
        self.assertEqual(Post.objects.count(), 0)
