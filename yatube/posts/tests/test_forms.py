import shutil
import tempfile
from http import HTTPStatus

from django.conf import settings
from django.contrib.auth import get_user_model
from django.core.files.uploadedfile import SimpleUploadedFile
from django.test import Client, TestCase, override_settings
from django.urls import reverse

from ..models import Comment, Group, Post

TEMP_MEDIA_ROOT = tempfile.mkdtemp(dir=settings.BASE_DIR)

User = get_user_model()


@override_settings(MEDIA_ROOT=TEMP_MEDIA_ROOT)
class PostFormTests(TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.user = User.objects.create_user(username='auth')
        cls.group = Group.objects.create(
            title='Тестовая группа',
            slug='test-slug',
            description='Тестовое описание',
        )
        cls.post = Post.objects.create(
            author=PostFormTests.user,
            text='Пост для проверки форм',
            group=PostFormTests.group
        )

    @classmethod
    def tearDownClass(cls):
        super().tearDownClass()
        shutil.rmtree(TEMP_MEDIA_ROOT, ignore_errors=True)

    def setUp(self):
        # Создаем неавторизованный клиент
        self.guest_client = Client()
        # Создаем авторизованный клиент
        self.author_client = Client()
        self.author_client.force_login(PostFormTests.user)

    def test_create_post(self):
        """Валидная форма создает запись в Post."""
        posts_count = Post.objects.count()

        small_gif = (
            b'\x47\x49\x46\x38\x39\x61\x02\x00'
            b'\x01\x00\x80\x00\x00\x00\x00\x00'
            b'\xFF\xFF\xFF\x21\xF9\x04\x00\x00'
            b'\x00\x00\x00\x2C\x00\x00\x00\x00'
            b'\x02\x00\x01\x00\x00\x02\x02\x0C'
            b'\x0A\x00\x3B'
        )
        uploaded = SimpleUploadedFile(
            name='small.gif',
            content=small_gif,
            content_type='image/gif'
        )
        form_data = {
            'text': 'Здесь текст нового поста',
            'group': PostFormTests.group.id,
            'image': uploaded,
        }
        response = self.author_client.post(
            reverse('posts:post_create'),
            data=form_data,
            follow=True
        )
        latest_post = Post.objects.latest('created')
        form_fields = [
            (form_data['text'], latest_post.text),
            (form_data['group'], latest_post.group.id),
            (PostFormTests.user, latest_post.author),
            (f"posts/{form_data['image'].name}", latest_post.image.name),
        ]
        for form_field, post_data in form_fields:
            self.assertEqual(form_field, post_data)
        self.assertEqual(response.status_code, HTTPStatus.OK)

        self.assertRedirects(response, reverse(
            'posts:profile', args={PostFormTests.user.username})
        )
        self.assertEqual(Post.objects.count(), posts_count + 1)

    def test_post_edit(self):
        """Валидная форма редактирует запись в Post."""
        form_data = {
            'text': 'Здесь текст редактированного поста',
            'group': PostFormTests.group.id,
        }
        response = self.author_client.post(
            reverse('posts:post_edit', args={PostFormTests.post.id}),
            data=form_data,
            follow=True
        )
        latest_post = Post.objects.latest('created')
        form_fields = [
            (form_data['text'], latest_post.text),
            (form_data['group'], latest_post.group.id),
            (PostFormTests.user, latest_post.author),
        ]
        for form_field, post_data in form_fields:
            self.assertEqual(form_field, post_data)

        self.assertEqual(response.status_code, HTTPStatus.OK)
        self.assertRedirects(
            response, reverse(
                'posts:post_detail', args={PostFormTests.post.id})
        )

    def test_guest_not_create_post(self):
        """Не авторизованный пользователь не может создать пост."""
        posts_count = Post.objects.count()
        response_create = self.guest_client.post(
            reverse('posts:post_create'), follow=True)
        response_edit = self.guest_client.post(
            reverse('posts:post_edit',
                    args={PostFormTests.post.id}), follow=True,
        )
        self.assertRedirects(
            response_create,
                            (reverse('users:login')
                             + '?next=' + reverse('posts:post_create'))
        )
        self.assertRedirects(
            response_edit,
                            (reverse('users:login')
                             + '?next=' + reverse(
                                 'posts:post_edit',
                                 args={PostFormTests.post.id})))

        self.assertEqual(Post.objects.count(), posts_count)


class CommentFormTests(TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.user = User.objects.create_user(username='auth')
        cls.post = Post.objects.create(
            author=CommentFormTests.user,
            text='Пост для проверки комментариев',
        )

    def setUp(self):
        self.guest_client = Client()
        self.author_client = Client()
        self.author_client.force_login(CommentFormTests.user)

    def test_create_comment(self):
        """Валидная форма создает комментарий."""
        comment_count = Comment.objects.count()
        form_data = {
            'text': 'Тестовый комментарий',
        }
        response = self.author_client.post(
            reverse('posts:add_comment', args={CommentFormTests.post.id}),
            data=form_data,
            follow=True
        )
        latest_comment = Comment.objects.latest('created')
        self.assertEqual(response.status_code, HTTPStatus.OK)
        self.assertEqual(form_data['text'], latest_comment.text)
        self.assertRedirects(response, reverse(
            'posts:post_detail', args={CommentFormTests.post.id})
        )
        self.assertEqual(Comment.objects.count(), comment_count + 1)

    def test_guest_not_create_comment(self):
        """Не авторизованный пользователь не может комментировать."""
        comment_count = Comment.objects.count()
        response = self.guest_client.post(
            reverse('posts:add_comment',
                    args={CommentFormTests.post.id}), follow=True
        )
        self.assertRedirects(
            response,
                            (reverse('users:login')
                             + '?next=' + reverse(
                                 'posts:add_comment',
                                 args={CommentFormTests.post.id})))

        self.assertEqual(Comment.objects.count(), comment_count)
