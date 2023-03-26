import shutil
import tempfile

from django.core.files.uploadedfile import SimpleUploadedFile
from django.contrib.auth import get_user_model
from django.test import TestCase, Client
from django.conf import settings
from django.urls import reverse
from http import HTTPStatus

from ..models import Group, Post, Comment

User = get_user_model()

TEMP_MEDIA_ROOT = tempfile.mkdtemp(dir=settings.BASE_DIR)


class PostFormTests(TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.user = User.objects.create_user(username='auth')
        cls.group = Group.objects.create(
            title='Тестовая группа',
            slug='test_url',
            description='Тестовое описание',
        )
        cls.post = Post.objects.create(
            author=cls.user,
            text='Тестовое описание поста',
            group=cls.group,
        )

    def setUp(self):
        self.small_gif = (
            b'\x47\x49\x46\x38\x39\x61\x02\x00'
            b'\x01\x00\x80\x00\x00\x00\x00\x00'
            b'\xFF\xFF\xFF\x21\xF9\x04\x00\x00'
            b'\x00\x00\x00\x2C\x00\x00\x00\x00'
            b'\x02\x00\x01\x00\x00\x02\x02\x0C'
            b'\x0A\x00\x3B'
        )
        self.uploaded = SimpleUploadedFile(
            name='small.gif',
            content=self.small_gif,
            content_type='image/gif'
        )
        self.guest_client = Client()
        self.authorized_client = Client()
        self.authorized_client.force_login(PostFormTests.user)

    @classmethod
    def tearDownClass(cls):
        shutil.rmtree(settings.MEDIA_ROOT, ignore_errors=True)
        super().tearDownClass()

    def test_create_post_by_user(self):
        '''Проверка создания поста авторизованным пользователем'''
        posts_count = Post.objects.count()
        form_data = {'text': 'Текст записанный в форму',
                     'group': self.group.id,
                     'image': self.uploaded}
        response = self.authorized_client.post(reverse('posts:post_create'),
                                               data=form_data)
        redirect = reverse('posts:profile',
                           kwargs={'username': f'{self.user.username}'})
        self.assertRedirects(response, redirect)
        self.assertEqual(Post.objects.count(), posts_count + 1)
        self.assertTrue(
            Post.objects.filter(
                group=self.group.id,
                text='Текст записанный в форму',
                author=self.user,
                image=f'posts/{self.uploaded}'
            ).exists()
        )

    def test_create_post_by_guest(self):
        '''Проверка создания поста неавторизованным пользователем'''
        posts_count = Post.objects.count()
        form_data = {'text': 'Текст записанный в форму',
                     'group': self.group.id,
                     'image': self.uploaded
                     }
        response = self.guest_client.post(reverse('posts:post_create'),
                                          data=form_data)
        redirect = '/auth/login/?next=/create/'
        self.assertRedirects(response, redirect)
        self.assertEqual(Post.objects.count(), posts_count)

    def test_edit_post_by_user(self):
        '''Проверка изменения поста авторизованным пользователем'''
        self.post = Post.objects.create(text='Текст до изменения',
                                        author=self.user,
                                        group=self.group)
        form_data = {'text': 'Измененный текст, записанный в форму',
                     'group': self.group.id,
                     'image': self.uploaded}
        response = self.authorized_client.post(
            reverse('posts:post_edit', kwargs={'post_id': self.post.id}),
            data=form_data)
        post = Post.objects.get(id=self.post.id)
        self.assertRedirects(response, reverse(
            'posts:post_detail', kwargs={'post_id': self.post.id}
        ))
        self.assertTrue(Post.objects.filter(
                        group=self.group.id,
                        author=self.user,
                        pub_date=self.post.pub_date
                        ).exists())
        self.assertEqual(post.text, form_data['text'])

    def test_edit_post_by_guest(self):
        '''Проверка изменения поста неавторизованным пользователем'''
        self.post = Post.objects.create(text='Текст до изменения',
                                        author=self.user,
                                        group=self.group,
                                        image=self.uploaded
                                        )
        form_data = {'text': 'Измененный текст, записанный в форму',
                     'group': self.group.id
                     }
        response = self.guest_client.post(
            reverse('posts:post_edit', kwargs={'post_id': self.post.id}),
            data=form_data)
        post = Post.objects.get(id=self.post.id)
        self.assertRedirects(response,
                             f'/auth/login/?next=/posts/{self.post.id}/edit/')
        self.assertNotEqual(post.text, form_data['text'])

    def test_comment_by_user(self):
        '''Проверка комментирования поста авторизованным пользователем'''
        comments_count = Comment.objects.all().count()
        form_data = {
            'text': 'Текст комментария'
        }
        response = self.authorized_client.post(
            reverse('posts:add_comment', kwargs={'post_id': self.post.id}),
            data=form_data
        )
        comment = Comment.objects.get(post=self.post)
        self.assertEqual(response.status_code, HTTPStatus.FOUND.value)
        self.assertEqual(Comment.objects.count(), comments_count + 1)
        self.assertTrue(
            Comment.objects.filter(
                post=self.post.id,
                text='Текст комментария',
                author=self.user,
            ).exists()
        )
        self.assertEqual(comment.text, 'Текст комментария')

    def test_comment_by_guest(self):
        '''Проверка комментирования поста неавторизованным пользователем'''
        comments_count = Comment.objects.all().count()
        form_data = {
            'text': 'Текст комментария'
        }
        response = self.guest_client.post(
            reverse('posts:add_comment', kwargs={'post_id': self.post.id}),
            data=form_data
        )
        self.assertEqual(response.status_code, HTTPStatus.FOUND.value)
        self.assertEqual(Comment.objects.count(), comments_count)
        self.assertFalse(
            Comment.objects.filter(
                post=self.post.id,
                text='Текст комментария',
                author=self.user,
            ).exists()
        )
