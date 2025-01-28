from datetime import datetime

from django.views.generic import (CreateView, ListView, UpdateView)
from django.shortcuts import render, get_object_or_404, redirect
from django.core.paginator import Paginator
from django.contrib.auth import get_user_model
from django.urls import reverse, reverse_lazy
from django.contrib.auth.decorators import login_required
from django.http import Http404
from django.contrib.auth.mixins import LoginRequiredMixin, UserPassesTestMixin

from .models import Post, Category, Comment
from .forms import PostForm, CommentForm


User = get_user_model()


@login_required
def add_comment(request, pk):
    """
    Добавляет комментарий к посту по его идентефикатору (pk).
    Комментарии могут оставить только авторизированные пользователи.
    """
    post = get_object_or_404(Post, pk=pk)
    form = CommentForm(request.POST)
    if form.is_valid():
        comment = form.save(commit=False)
        comment.author = request.user
        comment.post = post
        comment.save()
    return redirect('blog:post_detail', pk=pk)


@login_required
def edit_comment(request, post_pk, comment_pk):
    """
    Позволяет редактировать комментарий. Если пользователь,
    который отправил запрос не является автором комментария,
    его перенаправляет на страницу публикации.
    """
    instance = get_object_or_404(Comment, pk=comment_pk)

    if request.user != instance.author:
        return redirect('blog:post_detail', pk=post_pk)

    form = CommentForm(request.POST or None, instance=instance)
    if form.is_valid():
        form.save()
        return redirect('blog:post_detail', pk=post_pk)

    context = {'form': form, 'comment': instance}
    return render(request, 'blog/comment.html', context)


@login_required
def delete_comment(request, post_pk, comment_pk):
    """
    Удаляет комментарий к посту.
    Если пользователь, который отправил запрос не является автором
    комментария, его перенаправляет на страницу публикации.
    """
    instance = get_object_or_404(Comment, pk=comment_pk)

    if request.user != instance.author:
        return redirect('blog:post_detail', pk=post_pk)

    if request.method == 'POST':
        instance.delete()
        return redirect('blog:post_detail', pk=post_pk)
    return render(request, 'blog/comment.html')


def get_posts_list():
    """Возвращает QuerySet для получения опубликованных постов."""
    return Post.objects.select_related(
        'author',
        'category',
        'location'
    ).filter(
        pub_date__lte=datetime.now(),
        is_published=True,
        category__is_published=True
    )


class OnlyAuthorMixin(UserPassesTestMixin):
    """
    Миксин, который проверяет, является ли пользователь, который
    отправил запрос автором поста. Вернет False, если не является.
    """

    def test_func(self):
        object = self.get_object()
        return object.author == self.request.user


class CheckValidFormMixin:
    """Миксин для проверки валидности формы."""

    def form_valid(self, form):
        form.instance.author = self.request.user
        return super().form_valid(form)


class PostsListView(ListView):
    """
    Выводит на главную страницу все опубликованные посты.
    В начале страницы показываются самые новые публикации.
    """

    model = Post
    template_name = 'blog/index.html'
    queryset = get_posts_list()

    paginate_by = 10


class PostCreateView(CheckValidFormMixin, LoginRequiredMixin, CreateView):
    """
    Создает пост. Создавать посты разрешается только админу
    и авторизованным пользователям.
    """

    model = Post
    form_class = PostForm
    template_name = 'blog/create.html'

    def get_success_url(self):
        return reverse_lazy(
            'blog:profile', kwargs={'username': self.object.author}
        )


class PostUpdateView(
    CheckValidFormMixin, OnlyAuthorMixin, LoginRequiredMixin, UpdateView
):
    """
    Класс позволяет изменить детали поста.
    Редактировать пост разрешается только его автору или администратору.
    Если происходит запрос на изменение не от автора поста,
    происходит перенаправление на страницу поста.
    """

    model = Post
    form_class = PostForm
    template_name = 'blog/create.html'

    def dispatch(self, request, *args, **kwargs):
        object = self.get_object()
        if request.user != object.author:
            return redirect('blog:post_detail', pk=object.pk)
        return super().dispatch(request, *args, **kwargs)

    def get_success_url(self):
        return reverse_lazy('blog:post_detail', kwargs={'pk': self.object.pk})


def post_detail(request, pk):
    """
    Позволяет получить детали поста по указанному идентификатору (pk).
    Если пост снят с публикации или "отложен",
    его может посмотреть только автор.
    """
    post = get_object_or_404(
        Post.objects.select_related(
            'author',
            'category',
            'location'
        ),
        pk=pk
    )

    if post.author != request.user:
        post = get_object_or_404(get_posts_list(), pk=pk)

    comments = post.comments.select_related('author')
    form = CommentForm()

    context = {
        'post': post,
        'form': form,
        'comments': comments,
    }
    return render(request, 'blog/detail.html', context)


@login_required
def delete_post(request, pk):
    """
    Удаляет пост по указанному идентификатору (pk), если текущий пользователь
    является автором этого поста. Если пользователь не является автором,
    происходит перенаправление на страницу деталей поста.
    """
    instance = get_object_or_404(Post, pk=pk)

    if request.user != instance.author:
        return redirect('blog:post_detail', pk=pk)

    form = PostForm(instance=instance)
    context = {'form': form}

    if request.method == 'POST':
        instance.delete()
        return redirect('blog:index')

    return render(request, 'blog/create.html', context)


class ProfileUpdateView(LoginRequiredMixin, UpdateView):
    """
    Этот класс позволяет пользователям, которые прошли аутентификацию,
    изменять данные своего профиля, такие как имя, фамилия, имя пользователя
    и адрес электронной почты.
    После изменения данных, пользователь будет перенаправлен на страницу
    профиля.
    """

    model = User
    template_name = 'blog/user.html'
    fields = ['first_name', 'last_name', 'username', 'email']

    def get_object(self, queryset=None):
        if self.request.user.is_authenticated:
            return self.request.user
        raise Http404()

    def get_success_url(self):
        user = self.get_object()
        return reverse('blog:profile', kwargs={'username': user.username})


def profile_details(request, username):
    """
    Функция для просмотра страницы пользователя, на которой есть информация
    о нем и опубликованные посты.
    """
    profile = get_object_or_404(
        User.objects.filter(
            username=username
        ))

    paginator = Paginator(Post.objects.all().filter(author=profile), 10)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)

    context = {
        'profile': profile,
        'page_obj': page_obj
    }

    return render(request, 'blog/profile.html', context)


def category_posts(request, category_slug):
    """Показывает информацию о категории и связанные с ней посты."""
    category = get_object_or_404(
        Category.objects.filter(
            slug=category_slug
        ),
        is_published=True,
    )

    paginator = Paginator(get_posts_list().filter(category=category), 10)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)

    context = {
        'category': category,
        'page_obj': page_obj
    }
    return render(request, 'blog/category.html', context)
