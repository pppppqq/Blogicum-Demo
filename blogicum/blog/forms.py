from django import forms

from .models import Post, Comment


class PostForm(forms.ModelForm):
    """
    Форма для создания и редактирования публикации блога.
    Использует модель Post.
    """

    class Meta:
        model = Post
        exclude = ('author',)
        widgets = {
            'pub_date': forms.DateTimeInput(
                attrs={'type': 'datetime-local'}
            )
        }


class CommentForm(forms.ModelForm):
    """
    Форма для работы с комментариями к публикациям.
    Использует модель Comment.
    """

    class Meta:
        model = Comment
        fields = ('text',)
