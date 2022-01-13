from django.contrib.auth import get_user_model
from django.core.cache import cache
from django.test import Client, TestCase
from django.urls.base import reverse

from ..models import Post

User = get_user_model()


class PostCacheTest(TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.user = User.objects.create_user(username='auth')
        cls.post = Post.objects.create(
            author=PostCacheTest.user,
            text='Тестовый текст для проверки кэша',
        )

    def setUp(self):
        self.guest_client = Client()

    def test_cache_index_page(self):
        """Проверка кэша страницы index.html"""
        cache.clear()
        response_new_post = self.guest_client.get(reverse('posts:index'))
        self.assertContains(response_new_post, PostCacheTest.post.text)
        Post.objects.get(text=PostCacheTest.post.text).delete()
        response_post_in_cache = self.guest_client.get(reverse('posts:index'))
        self.assertContains(response_post_in_cache, PostCacheTest.post.text)
        cache.clear()
        response_clear_cache = self.guest_client.get(reverse('posts:index'))
        self.assertNotContains(response_clear_cache, PostCacheTest.post.text)
