from http import HTTPStatus

from django.contrib.auth import get_user_model
from django.test import Client, TestCase

from ..models import Group, Post

User = get_user_model()


class StaticURLTests(TestCase):
    def setUp(self):
        self.guest_client = Client()
        self.list_static_urls = [
            '/',
            '/about/author/',
            '/about/tech/',
        ]

    def test_staic_urls(self):
        for url_adress in self.list_static_urls:
            with self.subTest(adress=url_adress):
                response = self.guest_client.get(url_adress)
                self.assertEqual(response.status_code, HTTPStatus.OK)


class PostURLTest(TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.user_author = User.objects.create_user(username='auth')
        cls.group = Group.objects.create(
            title='Тестовая группа',
            slug='test-slug',
            description='Тестовое описание',
        )
        cls.post = Post.objects.create(
            author=cls.user_author,
            text='Тестовый текст для поста',
            group=cls.group
        )

    def setUp(self):
        self.guest_client = Client()
        self.user = User.objects.create_user(username='HasNoName')
        self.authorized_client = Client()
        self.authorized_client.force_login(self.user)
        self.author_client = Client()
        self.author_client.force_login(PostURLTest.user_author)
        self.post_id = PostURLTest.post.id
        self.slug = PostURLTest.group.slug
        self.list_urls_guests = {
            '/': 'posts/index.html',
            f'/group/{self.slug}/': 'posts/group_list.html',
            f'/profile/{self.user.username}/': 'posts/profile.html',
            f'/posts/{self.post_id}/': 'posts/post_detail.html',
        }
        self.list_urls_authorized = {
            '/': 'posts/index.html',
            f'/group/{self.slug}/': 'posts/group_list.html',
            f'/profile/{self.user.username}/': 'posts/profile.html',
            f'/posts/{self.post_id}/': 'posts/post_detail.html',
            '/create/': 'posts/create_post.html',
            '/follow/': 'posts/follow.html',
        }
        self.list_urls_author = {
            '/': 'posts/index.html',
            f'/group/{self.slug}/': 'posts/group_list.html',
            f'/profile/{self.user.username}/': 'posts/profile.html',
            f'/posts/{self.post_id}/': 'posts/post_detail.html',
            '/create/': 'posts/create_post.html',
            f'/posts/{self.post_id}/edit/': 'posts/create_post.html',
        }
        self.list_urls_redirect = {
            f'/posts/{self.post_id}/edit/': f'/posts/{self.post_id}/',
            f'/posts/{self.post_id}/comment/': f'/posts/{self.post_id}/',

            f'/profile/{PostURLTest.user_author.username}/follow/':
            f'/profile/{PostURLTest.user_author.username}/',

            f'/profile/{PostURLTest.user_author.username}/unfollow/':
            f'/profile/{PostURLTest.user_author.username}/',
        }

    def test_urls_gest_exists_at_desired_location(self):
        """Страницы доступны любому пользователю."""
        for url_adress, _ in self.list_urls_guests.items():
            with self.subTest(adress=url_adress):
                response = self.guest_client.get(url_adress)
                self.assertEqual(response.status_code, HTTPStatus.OK)

    def test_urls_authorized_exists_at_desired_location(self):
        """Страницы доступны авторизованному пользователю."""
        for url_adress, _ in self.list_urls_authorized.items():
            with self.subTest(adress=url_adress):
                response = self.authorized_client.get(url_adress)
                self.assertEqual(response.status_code, HTTPStatus.OK)

    def test_urls_author_exists_at_desired_location(self):
        """Страницы доступны автору."""
        for url_adress, _ in self.list_urls_author.items():
            with self.subTest(adress=url_adress):
                response = self.author_client.get(url_adress)
                self.assertEqual(response.status_code, HTTPStatus.OK)

    def test_urls_redirect(self):
        """URL-адреса страниц с редиректом работают правильно."""
        for url_adress, redirect in self.list_urls_redirect.items():
            with self.subTest(adress=url_adress):
                response = self.authorized_client.get(url_adress, follow=True)
                self.assertRedirects(response, redirect)

    def test_urls_guest_uses_correct_template(self):
        """URL-адрес для любого пользователя
        использует соответствующий шаблон.
        """
        for adress, template in self.list_urls_guests.items():
            with self.subTest(adress=adress):
                response = self.guest_client.get(adress)
                self.assertTemplateUsed(response, template)

    def test_urls_authorized_uses_correct_template(self):
        """URL-адрес авторизованного пользователя
        использует соответствующий шаблон.
        """
        for adress, template in self.list_urls_authorized.items():
            with self.subTest(adress=adress):
                response = self.authorized_client.get(adress)
                self.assertTemplateUsed(response, template)

    def test_urls_author_uses_correct_template(self):
        """URL-адрес автора использует соответствующий шаблон."""
        for adress, template in self.list_urls_author.items():
            with self.subTest(adress=adress):
                response = self.author_client.get(adress)
                self.assertTemplateUsed(response, template)

    def test_unexisting_page(self):
        """Запрос к несуществующей странице вернет 404."""
        response_guest = self.guest_client.get('/unexisting_page/')
        response_authorized = self.authorized_client.get('/unexisting_page/')
        response_author = self.author_client.get('/unexisting_page/')
        responsies = [response_guest, response_authorized, response_author]
        for response in responsies:
            with self.subTest(response=response):
                self.assertEqual(response.status_code, HTTPStatus.NOT_FOUND)
