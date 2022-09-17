from django.contrib.auth import get_user_model
from django.test import Client, TestCase
from django.urls import reverse
from posts.models import Group, Post, Follow
from ..forms import PostForm
from django.core.cache import cache

User = get_user_model()


class PostsViewsTest(TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()

        cls.user = User.objects.create_user(
            username="TestUser"
        )
        cls.random_user = User.objects.create_user(
            username="RandomUser"
        )
        cls.group = Group.objects.create(
            description="Тестовое описание",
            slug="Test-slug",
            title="Тестовое название"
        )
        cls.group_2 = Group.objects.create(
            description="Тестовое описание второй группы",
            slug="test-slug-group-2",
            title="Тестовое название второй группы"
        )
        cls.post = Post.objects.create(
            author=cls.user,
            text="test test",
            group=cls.group
        )

        # cls.client = Client()
        # cls.client.force_login(cls.user)

    def setUp(self):
        """Не забываем перед каждым тестом чистить кэш"""
        cache.clear()
        self.client = Client()
        self.auth_client = Client()
        self.user = PostsViewsTest.user
        self.auth_client.force_login(self.user)
        self.post = PostsViewsTest.post

    def check_context_contains_page_or_post(self, context, post=False):
        """Эта функция является частью простого контекстного тестирования.
        Она создана для того, что бы не создавать повторяющиеся конструкции"""
        if post:
            self.assertIn('post', context)
            post = context['post']
        else:
            self.assertIn('page_obj', context)
            post = context['page_obj'][0]
        self.assertEqual(post.author, PostsViewsTest.user)
        self.assertEqual(post.pub_date, PostsViewsTest.post.pub_date)
        self.assertEqual(post.text, PostsViewsTest.post.text)
        self.assertEqual(post.group, PostsViewsTest.post.group)

    def test_view_funcs_correct_templates(self):
        """Проверка на использование корректного шаблона"""

        names_templates = {
            reverse(
                "posts:index"
            ): "posts/index.html",
            reverse(
                "posts:post_create"
            ): "posts/create_post.html",
            reverse(
                "posts:group_list",
                kwargs={"slug": self.group.slug}
            ): "posts/group_list.html",
            reverse(
                "posts:post_detail",
                kwargs={"post_id": self.post.id}
            ): "posts/post_detail.html",
            reverse(
                "posts:post_edit",
                kwargs={"post_id": self.post.id}
            ): "posts/create_post.html",
            reverse(
                "posts:profile",
                kwargs={"username": self.user.username}
            ): "posts/profile.html",
        }
        for url, template in names_templates.items():
            with self.subTest(url=url):
                response = self.auth_client.get(url)
                self.assertTemplateUsed(response, template)

    def test_index_correct_context(self):
        response = self.auth_client.get(reverse("posts:index"))
        self.check_context_contains_page_or_post(response.context)
        self.assertContains(response, '<img')

    def test_group_posts_correct_context(self):
        response = self.auth_client.get(
            reverse(
                "posts:group_list",
                kwargs={"slug": self.group.slug}
            )
        )

        self.check_context_contains_page_or_post(response.context)
        self.assertIn('group', response.context)
        group = response.context['group']
        self.assertEqual(group.title, PostsViewsTest.group.title)
        self.assertEqual(group.description, PostsViewsTest.group.description)
        self.assertContains(response, '<img')

    def test_post_detail_correct_context(self):
        response = self.auth_client.get(
            reverse(
                "posts:post_detail",
                kwargs={"post_id": self.post.id}
            )
        )
        self.check_context_contains_page_or_post(response.context, post=True)
        self.assertIn('user', response.context)
        self.assertEqual(response.context['user'], PostsViewsTest.user)
        self.assertContains(response, '<img')

    def test_post_edit_correct_context(self):
        pages = {
            "create": reverse("posts:post_create"),
            "edit": reverse(
                "posts:post_edit",
                kwargs={"post_id": self.post.id}
            )
        }
        for name, url in pages.items():
            response = self.auth_client.get(url)

            self.assertIn('form', response.context)
            self.assertIsInstance(response.context['form'], PostForm)
            self.assertIn('is_edit', response.context)
            is_edit = response.context['is_edit']
            self.assertIsInstance(is_edit, bool)
            self.assertEqual(is_edit, name == "edit")

        # response = self.auth_client.get(reverse("posts:post_create"))
        # response_1 = self.auth_client.get(
        #     reverse(
        #         "posts:post_edit",
        #         kwargs={"post_id": self.post.id}
        #     )
        # )
        # form_obj = response.context.get("form")
        # # Поля формы проверять не нужно
        # # form_field_types = {
        #     "group": forms.fields.ChoiceField,
        #     "text": forms.fields.CharField,
        # }
        # for field, expected_type in form_field_types.items():
        #     with self.subTest(field=field):
        #         field_type = form_obj.fields.get(field)

        # self.assertIsInstance(field_type, expected_type)
        # self.assertIsInstance(form_obj, PostForm)
        # is_edit_flag = response.context.get("is_edit")
        # is_edit_flag_1 = response_1.context.get("is_edit")
        # self.assertEqual(is_edit_flag, False)
        # self.assertEqual(is_edit_flag_1, True)

    def test_profile_use_correct_context(self):
        response = self.auth_client.get(
            reverse(
                "posts:profile",
                kwargs={"username": self.user.username}
            )
        )
        self.check_context_contains_page_or_post(response.context)
        self.assertContains(response, '<img')

    def test_post_created_at_right_group_and_profile(self):
        """Тестовый пост создан не в той группе и профиле"""
        urls = (
            reverse(
                "posts:group_list",
                kwargs={"slug": self.group_2.slug}
            ),
            reverse(
                "posts:profile",
                kwargs={"username": self.random_user.username}
            )
        )
        for url in urls:
            with self.subTest(url=url):
                response = self.auth_client.get(url)
                page_obj = response.context.get("page_obj")

                self.assertEqual(len(page_obj), 0)

    def test_cache_index_page(self):
        """Проверка работы кеша"""
        post = Post.objects.create(
            text='Пост под кеш',
            author=self.user)
        content_add = self.auth_client.get(
            reverse('posts:index')).content
        post.delete()
        content_delete = self.auth_client.get(
            reverse('posts:index')).content
        self.assertEqual(content_add, content_delete)
        cache.clear()
        content_cache_clear = self.auth_client.get(
            reverse('posts:index')).content
        self.assertNotEqual(content_add, content_cache_clear)


class PaginatorViewsTest(TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.author = User.objects.create_user(username='test_user')
        cls.authorized_client = Client()
        cls.authorized_client.force_login(cls.author)
        cls.group = Group.objects.create(
            title='test_group',
            slug='test-slug',
            description='test_description'
        )
        cls.posts = [
            Post(
                author=cls.author,
                text='test_post',
                group=cls.group,
            ) for i in range(1, 14)
        ]
        Post.objects.bulk_create(cls.posts)
        cls.templates = {
            1: reverse('posts:index'),
            2: reverse('posts:group_list',
                       kwargs={'slug': f'{cls.group.slug}'}),
            3: reverse('posts:profile',
                       kwargs={'username': f'{cls.author.username}'})
        }
        cache.clear()

        cls.client = Client()

    def test_first_page_contains_ten_records(self):
        """Проверка пагинации на первой странице"""
        TEST_OF_PAGI_1: int = 10
        for i in PaginatorViewsTest.templates.keys():
            with self.subTest(i=i):
                response = self.client.get(self.templates[i])
                self.assertEqual(len(response.context.get(
                    'page_obj'
                ).object_list), TEST_OF_PAGI_1)

    def test_second_page_contains_three_records(self):
        """Проверка пагинации на второй странице"""
        TEST_OF_PAGI_2: int = 3
        for i in PaginatorViewsTest.templates.keys():
            with self.subTest(i=i):
                response = self.client.get(self.templates[i] + '?page=2')
                self.assertEqual(len(response.context.get(
                    'page_obj'
                ).object_list), TEST_OF_PAGI_2)


class FollowViewsTest(TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.post_autor = User.objects.create(
            username='post_autor'
        )
        cls.post_follower = User.objects.create(
            username='post_follower'
        )
        cls.post = Post.objects.create(
            text='follower text',
            author=cls.post_autor
        )

    def setUp(self):
        self.author_client = Client()
        self.author_client.force_login(self.post_follower)
        self.follower_client = Client()
        self.follower_client.force_login(self.post_autor)

    def test_follow_on_user(self):
        """Проверка подписывания"""
        count_follow = Follow.objects.count()
        self.follower_client.post(
            reverse(
                'posts:profile_follow',
                kwargs={'username': self.post_follower}))
        follow = Follow.objects.first()
        self.assertEqual(Follow.objects.count(), count_follow + 1)
        self.assertEqual(follow.author_id, self.post_follower.id)
        self.assertEqual(follow.user_id, self.post_autor.id)

    def test_unfollow_on_user(self):
        """Проверка отписывания"""
        Follow.objects.create(
            user=self.post_autor,
            author=self.post_follower
        )
        # count_follow = Follow.objects.count()
        self.follower_client.post(
            reverse(
                'posts:profile_unfollow',
                kwargs={'username': self.post_follower}))
        self.assertEqual(Follow.objects.count(), 0)

    def test_follow_on_authors(self):
        """Проверка записей у тех кто подписан."""
        post = Post.objects.create(
            author=self.post_autor,
            text="Подпишись на меня")
        Follow.objects.create(
            user=self.post_follower,
            author=self.post_autor)
        response = self.author_client.get(
            reverse('posts:follow_index'))
        self.assertIn(post, response.context['page_obj'].object_list)

    def test_notfollow_on_authors(self):
        """Проверка записей у тех кто не подписан."""
        post = Post.objects.create(
            author=self.post_autor,
            text="Подпишись на меня")
        response = self.author_client.get(
            reverse('posts:follow_index'))
        self.assertNotIn(post, response.context['page_obj'].object_list)
