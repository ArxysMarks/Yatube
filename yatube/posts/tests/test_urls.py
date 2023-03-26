from django.contrib.auth import get_user_model
from django.test import TestCase, Client
from http import HTTPStatus

from ..models import Group, Post

User = get_user_model()


class StaticURLTests(TestCase):
    def test_homepage(self):
        guest_client = Client()
        response = guest_client.get('/')
        self.assertEqual(response.status_code, 200)


class PostURLTest(TestCase):
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
        )

    def setUp(self):
        self.guest_client = Client()
        self.authorized_client = Client()
        self.authorized_client.force_login(PostURLTest.user)
        self.post = PostURLTest.post
        self.group = PostURLTest.group

    def test_availability_post_urls_for_guest(self):
        """Проверяем доступность адресов пользователям."""
        url_status = [
            ['/', self.guest_client, HTTPStatus.OK.value],
            [f'/group/{self.group.slug}/', self.guest_client,
             HTTPStatus.OK.value],
            [f'/profile/{self.user.username}/', self.guest_client,
             HTTPStatus.OK.value],
            [f'/posts/{self.post.id}/', self.guest_client,
             HTTPStatus.OK.value],
            ['/create/', self.authorized_client,
             HTTPStatus.OK.value],
            [f'/posts/{self.post.id}/edit/', self.authorized_client,
             HTTPStatus.OK.value],
            ['/unexisting_page/', self.guest_client,
             HTTPStatus.NOT_FOUND.value],
        ]
        for address, client, status in url_status:
            with self.subTest(address=address):
                response = client.get(address)
                error_name = (f'страница {address} работает неправильно, код -'
                              f' {response.status_code}, '
                              f'а должен быть {status}')
                self.assertEqual(response.status_code, status, error_name)

    def test_redirect_url(self):
        '''Проверяем доступность шаблонов по адресам'''
        templates_url_names = {
            '/': 'posts/index.html',
            (f'/group/{self.group.slug}/'): 'posts/group_list.html',
            (f'/profile/{self.user.username}/'): 'posts/profile.html',
            (f'/posts/{self.post.id}/'): 'posts/post_detail.html',
            '/create/': 'posts/create_post.html',
            (f'/posts/{self.post.id}/edit/'): 'posts/create_post.html',
        }
        for address, template in templates_url_names.items():
            with self.subTest(address=address):
                response = self.authorized_client.get(address)
                error_name = (f'страница {address} не переводит пользователя '
                              f'на шаблон {template}')
                self.assertTemplateUsed(response, template, error_name)

    def test_redirect_url_guest_client(self):
        '''Проверяем перенаправление неавторизованного пользователя'''
        url_create = '/auth/login/?next=/create/'
        url_edit = f'/auth/login/?next=/posts/{self.post.id}/edit/'
        url_redirect = {
            '/create/': url_create,
            f'/posts/{self.post.id}/edit/': url_edit,
        }
        for address, value in url_redirect.items():
            response = self.guest_client.get(address)
            self.assertRedirects(response, value)

    def test_redirect_url_authorized_client(self):
        '''Проверяем перенаправление авторизованного пользователя'''
        url_create = '/auth/login/?next=/create/'
        url_edit = f'/auth/login/?next=/posts/{self.post.id}/edit/'
        url_redirect = {
            '/create/': url_create,
            f'/posts/{self.post.id}/edit/': url_edit,
        }
        for address, value in url_redirect.items():
            response = self.guest_client.get(address)
            self.assertRedirects(response, value)
