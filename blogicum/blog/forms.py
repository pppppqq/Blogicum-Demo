from datetime import datetime

from django import forms

from .models import Post, Comment


class PostForm(forms.ModelForm):
    """
    Форма для создания и редактирования публикации блога.
    Использует модель Post.
    """

    class Meta:
        model = Post
        fields = (
            'title', 'text', 'pub_date', 'location', 'category', 'image'
        )

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['pub_date'].initial = datetime.now()


class CommentForm(forms.ModelForm):
    """
    Форма для работы с комментариями к публикациям.
    Использует модель Comment.
    """

    class Meta:
        model = Comment
        fields = ('text',)
