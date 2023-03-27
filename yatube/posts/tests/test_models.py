from django.contrib.auth import get_user_model
from django.test import TestCase

from ..models import SYMBOLS_ON_POST, Group, Post

User = get_user_model()


class PostModelTest(TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.user = User.objects.create_user(username='auth')
        cls.group = Group.objects.create(
            title='Тестовая группа',
            slug='Тестовый слаг',
            description='Тестовое описание',
        )
        cls.post = Post.objects.create(
            author=cls.user,
            text='Тестовый текст поста',
        )

    def test_models_have_correct_object_names(self):
        """Проверяем, что у моделей корректно работает __str__."""
        post = PostModelTest.post
        group = PostModelTest.group
        post_test_title = str(post)
        group_test_title = str(group)
        self.assertEqual(post_test_title, post.text[:SYMBOLS_ON_POST])
        self.assertEqual(group_test_title, group.title)
