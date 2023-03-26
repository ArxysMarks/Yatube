from django import forms

from .models import Post, Comment


class PostForm(forms.ModelForm):
    class Meta:
        model = Post
        fields = ('text', 'group', 'image')
        group = forms.ModelChoiceField(queryset=Post.objects.all(),
                                       required=False, to_field_name="group")
        labels = {
            "group": "Группа",
            "text": "Текст"
        }
        help_texts = {
            "group": "Группа, к которой будет относиться пост",
            "text": "Текст нового поста"
        }

    def clean_field(self):
        data = self.cleaned_data["text"]
        if data == '':
            raise forms.ValidationError('Это поле необходимо заполнить')
        return data


class CommentForm(forms.ModelForm):
    class Meta:
        model = Comment
        fields = ('text',)
