import shutil
import tempfile

from django import forms
from django.conf import settings
from django.contrib.auth import get_user_model
from django.core.cache import cache
from django.core.files.uploadedfile import SimpleUploadedFile
from django.test import Client, TestCase, override_settings
from django.urls import reverse

from ..models import Follow, Group, Post

TEMP_MEDIA_ROOT = tempfile.mkdtemp(dir=settings.BASE_DIR)

User = get_user_model()


@override_settings(MEDIA_ROOT=TEMP_MEDIA_ROOT)
class PaginatorViewsTest(TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.user = User.objects.create_user(username='auth')
        cls.group = Group.objects.create(
            title='Тестовая группа',
            slug='test-slug',
            description='Тестовое описание',
        )
        cls.small_gif = (
            b'\x47\x49\x46\x38\x39\x61\x02\x00'
            b'\x01\x00\x80\x00\x00\x00\x00\x00'
            b'\xFF\xFF\xFF\x21\xF9\x04\x00\x00'
            b'\x00\x00\x00\x2C\x00\x00\x00\x00'
            b'\x02\x00\x01\x00\x00\x02\x02\x0C'
            b'\x0A\x00\x3B'
        )
        cls.post = Post.objects.create(
            author=PaginatorViewsTest.user,
            text='Тестовый текст для поста',
            group=PaginatorViewsTest.group,
            image=SimpleUploadedFile(
                name='small.gif',
                content=cls.small_gif,
                content_type='image/gif'
            )
        )
        cls.index_url = ('posts:index', 'posts/index.html', None)
        cls.group_url = (
            'posts:group_list', 'posts/group_list.html', (cls.group.slug,)
        )
        cls.profile_url = (
            'posts:profile', 'posts/profile.html', (cls.user.username,)
        )

        cls.post_detail_url = (
            'posts:post_detail',
            'posts/post_detail.html',
            (PaginatorViewsTest.post.id,)
        )
        cls.post_create_url = (
            'posts:post_create', 'posts/create_post.html', None
        )
        cls.post_edit_url = (
            'posts:post_edit',
            'posts/create_post.html',
            (PaginatorViewsTest.post.id,)
        )
        cls.paginator_urls = (
            cls.index_url,
            cls.group_url,
            cls.profile_url,
        )
        cls.not_paginator_urls = (
            cls.post_detail_url,
            cls.post_create_url,
            cls.post_edit_url,
        )

    @classmethod
    def tearDownClass(cls):
        super().tearDownClass()
        shutil.rmtree(TEMP_MEDIA_ROOT, ignore_errors=True)

    def setUp(self):
        self.author_client = Client()
        self.author_client.force_login(PaginatorViewsTest.user)

    def test_paginator_on_pages_with_post(self):
        """Проверка страниц с паджинатором"""
        paginator_amount = 10
        number_of_test_posts = 13
        pages_with_paginator_amount = (
            (number_of_test_posts - (number_of_test_posts % paginator_amount))
            / (paginator_amount))
        posts_in_last_page_amount = (number_of_test_posts
                                     - (pages_with_paginator_amount
                                        * (paginator_amount)))
        posts_amount = int(paginator_amount * pages_with_paginator_amount
                           + (posts_in_last_page_amount))
        posts = [
            Post(
                text=f'Post #{num}',
                author=PaginatorViewsTest.user,
                group=PaginatorViewsTest.group,
            ) for num in range(1, posts_amount)
        ]
        Post.objects.bulk_create(posts)

        filter_index = list(Post.objects.all())[:paginator_amount]
        filter_group = list(
            Post.objects.filter(
                group=PaginatorViewsTest.group.id))[:paginator_amount]
        filter_profile = list(
            Post.objects.filter(
                author=PaginatorViewsTest.user.id))[:paginator_amount]
        filters = (filter_index, filter_group, filter_profile)

        pages = [
            (1, paginator_amount),
            (2, posts_in_last_page_amount),
        ]
        """Проверка количества постов, передаваемых на страницу"""
        for name, _, args in PaginatorViewsTest.paginator_urls:
            for page, count in pages:
                with self.subTest(name=name, page=page):
                    response = self.author_client.get(
                        reverse(name, args=args), {'page': page}
                    )
                    self.assertEqual(
                        len(response.context.get
                            ('page_obj').object_list), count
                    )

        """Посты на страницах с пагинатором выводятся в правильном порядке."""
        for name, _, args in PaginatorViewsTest.paginator_urls:
            for filter in filters:
                cache.clear()
                with self.subTest(name=name):
                    response = self.author_client.get(
                        reverse(name, args=args))
                    self.assertListEqual(
                        response.context.get('page_obj').object_list, filter
                    )

    def test_paginator_pages_uses_correct_template(self):
        """URL-адреса страниц с паджинацией используют
        соответствующий шаблон.
        """
        for name, template, args in PaginatorViewsTest.paginator_urls:
            with self.subTest(name=name):
                response = self.author_client.get(
                    reverse(name, args=args)
                )
                self.assertTemplateUsed(response, template)

    def test_not_paginator_pages_uses_correct_template(self):
        """URL-адреса страниц без паджинации используют
        соответствующий шаблон.
        """
        for name, template, args in PaginatorViewsTest.not_paginator_urls:
            with self.subTest(name=name):
                response = self.author_client.get(
                    reverse(name, args=args)
                )
                self.assertTemplateUsed(response, template)

    def test_paginator_pages_show_correct_context(self):
        """Шаблоны страниц с пагинатором
        сформированы с правильным контекстом.
        """
        for name, _, args in PaginatorViewsTest.paginator_urls:
            response = self.author_client.get(reverse(name, args=args))
            first_object = response.context['page_obj'][0]
            post_author_0 = first_object.author.username
            post_text_0 = first_object.text
            post_group_0 = first_object.group.title
            post_image_0 = first_object.image.name
            self.assertEqual(post_author_0, PaginatorViewsTest.user.username)
            self.assertEqual(post_text_0, PaginatorViewsTest.post.text)
            self.assertEqual(post_group_0, PaginatorViewsTest.group.title)
            self.assertEqual(post_image_0, PaginatorViewsTest.post.image.name)

    def test_post_detail_page_show_correct_context(self):
        """Шаблон post_detail сформирован с правильным контекстом."""
        response = (self.author_client.get(
            reverse('posts:post_detail', args={self.post.id})))
        self.assertEqual(response.context.get
                         ('post').author.username,
                         (PaginatorViewsTest.user.username))
        self.assertEqual(response.context.get
                         ('post').text, PaginatorViewsTest.post.text)
        self.assertEqual(response.context.get
                         ('post').group.title, PaginatorViewsTest.group.title)
        self.assertEqual(response.context.get
                         ('post').image.name,
                         PaginatorViewsTest.post.image.name)

    def test_create_post_post_edit_show_correct_context(self):
        """Шаблоны create_post, post_edit
        сформирован с правильным контекстом.
        """
        response_create = self.author_client.get(reverse('posts:post_create'))
        response_edit = self.author_client.get(reverse(
            'posts:post_edit', args={PaginatorViewsTest.post.id}))
        responsies = [response_create, response_edit]
        form_fields = {
            'text': forms.fields.CharField,
            'group': forms.fields.ChoiceField,
        }
        for response in responsies:
            for value, expected in form_fields.items():
                with self.subTest(value=value):
                    form_field = response.context.get('form').fields.get(value)
                    self.assertIsInstance(form_field, expected)


class GroupViewsTest(TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.user = User.objects.create_user(username='auth')
        cls.group = Group.objects.create(
            title='Проверочная группа',
            slug='test-slug-slug',
            description='Группа для проверки поста',
        )
        cls.post = Post.objects.create(
            author=GroupViewsTest.user,
            text='Новый пост для проверки группы',
            group=GroupViewsTest.group
        )
        cls.index_url = ('posts:index', 'posts/index.html', None)

        cls.group_url = ('posts:group_list',
                         'posts/group_list.html',
                         (cls.group.slug,))

        cls.profile_url = ('posts:profile',
                           'posts/profile.html',
                           (cls.user.username,))

        cls.paginator_urls = (
            cls.index_url,
            cls.group_url,
            cls.profile_url,
        )

    def setUp(self):
        self.author_client = Client()
        self.author_client.force_login(GroupViewsTest.user)
        self.group_not = Group.objects.create(
            title='Группа без поста',
            slug='test-not-slug',
            description='Группа где нет поста',
        )

    def test_create_post_with_group(self):
        """При указании группы она появляется на страницах с пагинатором
        и пост не попадает на страницу с другой группой
        """
        for name, _, args in GroupViewsTest.paginator_urls:
            with self.subTest(name=name):
                response = self.author_client.get(
                    reverse(name, args=args)
                )
                first_object = response.context['page_obj'][0]
                post_group_0 = first_object.group.title
                self.assertEqual(post_group_0, GroupViewsTest.group.title)
                self.assertIsNot(post_group_0, self.group_not.title)


class FollowViewsTest(TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.user_follower = User.objects.create_user(username='follower')
        cls.user_unfollower = User.objects.create_user(username='unfollower')
        cls.author = User.objects.create_user(username='author')
        cls.post = Post.objects.create(
            author=FollowViewsTest.author,
            text='Новый пост для проверки подписки',
        )

    def setUp(self):
        self.user_follower = Client()
        self.user_follower.force_login(FollowViewsTest.user_follower)
        self.user_unfollower = Client()
        self.user_unfollower.force_login(FollowViewsTest.user_unfollower)
        self.author = Client()
        self.author.force_login(FollowViewsTest.author)

    def test_auth_can_follow_and_unfollow(self):
        """Авторизованный пользователь может
        подписываться и удалять пользователя из подписок
        """
        response_follow = self.user_follower.get(
            reverse('posts:profile_follow',
                    args={FollowViewsTest.post.author.username})
        )
        latest_post = Post.objects.filter(
            author__following__user=FollowViewsTest.user_follower).latest(
                'created')
        self.assertEqual(FollowViewsTest.post.text, latest_post.text)
        self.assertEqual(FollowViewsTest.post.author, latest_post.author)
        self.assertRedirects(response_follow, reverse(
            'posts:profile', args={FollowViewsTest.author.username})
        )
        response_unfollow = self.user_follower.get(
            reverse('posts:profile_unfollow',
                    args={FollowViewsTest.post.author.username})
        )
        self.assertFalse(Post.objects.filter(
            author__following__user=FollowViewsTest.user_follower).exists()
        )
        self.assertRedirects(response_unfollow, reverse(
            'posts:profile', args={FollowViewsTest.author.username})
        )

    def test_post_appears_in_followers(self):
        """Новая запись пользователя появляется в ленте тех,
        кто на него подписан и не появляется в ленте тех, кто не подписан.
        """
        Follow.objects.create(
            user=FollowViewsTest.user_follower,
            author=FollowViewsTest.author,
        )
        post = Post.objects.create(
            author=FollowViewsTest.author,
            text='Пост должен появиться в ленте подписчика',
        )
        response_follower = self.user_follower.get(
            reverse('posts:follow_index')
        )
        first_object = response_follower.context['page_obj'][0]
        post_author_0 = first_object.author.username
        post_text_0 = first_object.text
        self.assertEqual(post_author_0, post.author.username)
        self.assertEqual(post_text_0, post.text)

        self.assertFalse(Post.objects.filter(
            author__following__user=FollowViewsTest.user_unfollower).exists()
        )
