import shutil
import tempfile

from django.contrib.auth import get_user_model
from django.test import TestCase, Client, override_settings
from django.urls import reverse
from django.conf import settings
from django import forms
from django.core.files.uploadedfile import SimpleUploadedFile
from django.core.cache import cache
from yatube.constants import POST_ON_PAGE, POST_ON_LAS_PAGE_TEST

from ..models import Group, Post, Follow

User = get_user_model()

TEMP_MEDIA_ROOT = tempfile.mkdtemp(dir=settings.BASE_DIR)


@override_settings(MEDIA_ROOT=TEMP_MEDIA_ROOT)
class PostViewTest(TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.user = User.objects.create_user(username='auth')
        '''cls.group = Group.objects.create(
            title='Тестовая группа',
            slug='test_url',
            description='Тестовое описание',
        )
        cls.post = Post.objects.create(
            author=cls.user,
            text='Тестовое описание поста',
            group=cls.group
        )'''

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
        self.authorized_client.force_login(PostViewTest.user)
        # self.post = PostViewTest.post(image=self.uploaded)
        # self.group = PostViewTest.group
        self.group = Group.objects.create(title='Тестовая группа',
                                          slug='test_url',
                                          description='Тестовое описание')
        self.post = Post.objects.create(text='Тестовое описание поста',
                                        group=self.group,
                                        author=self.user,
                                        image=self.uploaded)

    @classmethod
    def tearDownClass(cls):
        shutil.rmtree(settings.MEDIA_ROOT, ignore_errors=True)
        super().tearDownClass()

    def test_pages_uses_correct_template(self):
        """URL-адрес использует соответствующий шаблон."""
        # Собираем в словарь пары "имя_html_шаблона: reverse(name)"
        templates_page_names = {
            reverse('posts:index'): 'posts/index.html',
            reverse('posts:group_list',
                    kwargs={'slug':
                            f'{self.group.slug}'}): 'posts/group_list.html',
            reverse('posts:profile',
                    kwargs={'username':
                            f'{self.user.username}'}): 'posts/profile.html',
            reverse('posts:post_detail',
                    kwargs={'post_id':
                            self.post.id}): 'posts/post_detail.html',
            reverse('posts:post_create'): 'posts/create_post.html',
            reverse('posts:post_edit',
                    kwargs={'post_id':
                            self.post.id}): 'posts/create_post.html'}
        for reverse_name, template in templates_page_names.items():
            with self.subTest(reverse_name=reverse_name):
                response = self.authorized_client.get(reverse_name)
                self.assertTemplateUsed(response, template)

    def test_index_show_correct_context(self):
        """Шаблон index сформирован с правильным контекстом."""
        response = self.authorized_client.get(reverse('posts:index'))
        page_context = response.context['page_obj'][0]
        self.assertEqual(page_context.text, self.post.text)
        self.assertEqual(page_context.author, self.user)
        self.assertEqual(page_context.group, self.post.group)
        self.assertEqual(page_context.image, self.post.image)

    def test_group_list_show_correct_context(self):
        """Шаблон group_list сформирован с правильным контекстом."""
        response = self.authorized_client.get(
            reverse('posts:group_list', kwargs={'slug': f'{self.group.slug}'}))
        group_on_page = response.context['group']
        self.assertEqual(group_on_page.title, self.group.title)
        self.assertEqual(group_on_page.description, self.group.description)
        page_context = response.context['page_obj'][0]
        self.assertEqual(page_context.text, self.post.text)
        self.assertEqual(page_context.author, self.user)
        self.assertEqual(page_context.group, self.post.group)
        self.assertEqual(page_context.image, self.post.image)

    def test_profile_show_correct_context(self):
        """Шаблон profile сформирован с правильным контекстом."""
        response = self.authorized_client.get(
            reverse('posts:profile',
                    kwargs={'username': f'{self.user.username}'}))
        profile = response.context['author']
        self.assertEqual(profile.username, self.user.username)
        page_context = response.context['page_obj'][0]
        self.assertEqual(page_context.text, self.post.text)
        self.assertEqual(page_context.author, self.user)
        self.assertEqual(page_context.group, self.post.group)
        self.assertEqual(page_context.image, self.post.image)

    def test_post_detail_show_correct_context(self):
        """Шаблон post_detail сформирован с правильным контекстом."""
        response = self.authorized_client.get(
            reverse('posts:post_detail', kwargs={'post_id': self.post.id}))
        page_context = response.context['post']
        self.assertEqual(page_context.text, self.post.text)
        self.assertEqual(page_context.author, self.user)
        self.assertEqual(page_context.group, self.post.group)
        self.assertEqual(page_context.image, self.post.image)

    def test_post_create_correct_context(self):
        """Шаблон post_create сформирован с правильным контекстом."""
        response = self.authorized_client.get(reverse('posts:post_create'))
        form_fields = {
            'text': forms.fields.CharField,
            'group': forms.fields.ChoiceField,
            'image': forms.ImageField
        }
        for value, expected in form_fields.items():
            with self.subTest(value=value):
                form_field = response.context.get('form').fields.get(value)
                # Проверяет, что поле формы является экземпляром
                # указанного класса
                self.assertIsInstance(form_field, expected)

    def test_post_edit_correct_context(self):
        """Шаблон post_edit сформирован с правильным контекстом."""
        response = self.authorized_client.get(
            reverse('posts:post_edit', kwargs={'post_id': self.post.id}))
        form_fields = {
            'text': forms.fields.CharField,
            'group': forms.fields.ChoiceField,
            'image': forms.ImageField
        }
        for value, expected in form_fields.items():
            with self.subTest(value=value):
                form_field = response.context.get('form').fields.get(value)
                # Проверяет, что поле формы является экземпляром
                # указанного класса
                self.assertIsInstance(form_field, expected)

    def test_post_with_groupadded_correctly(self):
        """Пост при создании с группой добавлен корректно"""
        templates_page_names = [
            reverse('posts:index'),
            reverse('posts:group_list', kwargs={'slug': f'{self.group.slug}'}),
            reverse('posts:profile',
                    kwargs={'username': f'{self.user.username}'}), ]
        for page in templates_page_names:
            response = self.authorized_client.get(page)
            self.assertIn(self.post, response.context['page_obj'])


class PaginatorViewsTest(TestCase):

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.user = User.objects.create_user(username='auth')
        cls.group = Group.objects.create(
            title='Тестовая группа',
            slug='test_url',
            description='Тестовое описание',
        )
        Post.objects.bulk_create(
            Post(
                author=cls.user,
                text=f'Тестовое описание {i}-го поста',
                group=cls.group
            )
            for i in range(POST_ON_LAS_PAGE_TEST + POST_ON_PAGE)
        )

    def setUp(self):
        self.guest_client = Client()
        self.authorized_client = Client()
        self.authorized_client.force_login(PaginatorViewsTest.user)

    def test_pages_contains_the_reqiered_number_of_posts(self):
        '''Проверяем паджинатор'''
        data = {
            'index': reverse('posts:index'),
            'group': reverse(
                'posts:group_list',
                kwargs={'slug': PaginatorViewsTest.group.slug}
            ),
            'profile': reverse(
                'posts:profile',
                kwargs={'username': PaginatorViewsTest.user.username}
            )
        }
        for position, page in data.items():
            with self.subTest(position=position):
                response_page_1 = self.guest_client.get(page)
                response_page_2 = self.guest_client.get(page + '?page=2')
                self.assertEqual(len(response_page_1.context['page_obj']),
                                 POST_ON_PAGE)
                self.assertEqual(len(response_page_2.context['page_obj']),
                                 POST_ON_LAS_PAGE_TEST)


class CacheTest(TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.user = User.objects.create_user(username='auth')

    def setUp(self):
        self.guest_client = Client()

    def test_cache_index(self):
        '''Проверка корректности работы кэширования'''
        self.post = Post.objects.create(text='Тестируем кэширование',
                                        author=self.user)
        response_before = self.guest_client.get(reverse('posts:index'))
        self.post = Post.objects.filter(
            text='Тестируем кэширование',
            author=self.user
        ).delete()
        response_after = self.guest_client.get(reverse('posts:index'))
        self.assertEqual(response_before.content, response_after.content)
        cache.clear()
        next_response = self.guest_client.get(reverse('posts:index'))
        self.assertNotEqual(response_before.content, next_response)


class FollowViewsTest(TestCase):

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.user = User.objects.create_user(username='user')
        cls.user2 = User.objects.create_user(username='user2')
        cls.author = User.objects.create_user(username='author')

    def setUp(self):
        self.guest_client = Client()
        self.authorized_client = Client()
        self.authorized_client.force_login(self.user)
        self.authorized_client2 = Client()
        self.authorized_client2.force_login(self.user2)

    def test_user_follower_authors(self):
        ''' Проверяем, что подписка и отписка работает '''
        count_foll_before = Follow.objects.filter(user=FollowViewsTest.user
                                                  ).count()
        self.authorized_client.get(
            reverse('posts:profile_follow', kwargs={
                'username': FollowViewsTest.author.username}), follow=True)
        count_foll_after = Follow.objects.filter(
            user=FollowViewsTest.user).count()
        self.assertTrue(Follow.objects.filter(
                        user=FollowViewsTest.user,
                        author=FollowViewsTest.author).exists())
        self.assertEqual(count_foll_before + 1, count_foll_after)
        self.authorized_client.get(
            reverse('posts:profile_unfollow', kwargs={
                'username': FollowViewsTest.author.username}))
        count_foll_after = Follow.objects.filter(
            user=FollowViewsTest.user).count()
        self.assertEqual(count_foll_before, count_foll_after)

    def test_post_in_follow_index(self):
        '''Проверяем что новый пост попадает в ленту'''
        post = Post.objects.create(
            author=FollowViewsTest.author,
            text='Текст')
        Follow.objects.create(user=FollowViewsTest.user,
                              author=FollowViewsTest.author)
        response_of_follower = self.authorized_client.get(reverse(
            'posts:follow_index'))
        response_of_not_follower = self.authorized_client2.get(reverse(
            'posts:follow_index'))
        last_post_foll = response_of_follower.context['page_obj']
        last_post_not_foll = response_of_not_follower.context['page_obj']
        self.assertIn(post, last_post_foll)
        self.assertNotIn(post, last_post_not_foll)
