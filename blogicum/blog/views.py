from django.views.generic import (CreateView, ListView, UpdateView)
from django.shortcuts import render, get_object_or_404, redirect
from django.core.paginator import Paginator
from django.contrib.auth import get_user_model
from django.urls import reverse, reverse_lazy
from django.contrib.auth.decorators import login_required
from django.http import Http404
from django.contrib.auth.mixins import LoginRequiredMixin, UserPassesTestMixin
from django.conf import settings
from django.db.models import Count
from django.utils import timezone

from .models import Post, Category, Comment
from .forms import PostForm, CommentForm


User = get_user_model()

COUNT_POSTS = settings.COUNT_POSTS


@login_required
def add_comment(request, post_id):
    """
    Добавляет комментарий к посту по его идентефикатору (pk).
    Комментарии могут оставить только авторизированные пользователи.
    """
    post = get_object_or_404(Post, pk=post_id)
    form = CommentForm(request.POST)
    if form.is_valid():
        comment = form.save(commit=False)
        comment.author = request.user
        comment.post = post
        comment.save()
    return redirect('blog:post_detail', post_id=post_id)


def get_comment_post(post_id, comment_id):
    """
    Получает объект комментария по его идентификатору
    внутри заданного поста.
    """
    return get_object_or_404(
        Comment.objects.filter(pk=comment_id),
        post=post_id
    )


@login_required
def edit_comment(request, post_id, comment_id):
    """
    Позволяет редактировать комментарий. Если пользователь,
    который отправил запрос не является автором комментария,
    его перенаправляет на страницу публикации.
    """
    instance = get_comment_post(post_id, comment_id)

    if request.user != instance.author:
        return redirect('blog:post_detail', post_id=post_id)

    form = CommentForm(request.POST or None, instance=instance)
    if form.is_valid():
        form.save()
        return redirect('blog:post_detail', post_id=post_id)

    context = {'form': form, 'comment': instance}
    return render(request, 'blog/comment.html', context)


@login_required
def delete_comment(request, post_id, comment_id):
    """
    Удаляет комментарий к посту.
    Если пользователь, который отправил запрос не является автором
    комментария, его перенаправляет на страницу публикации.
    """
    instance = get_comment_post(post_id, comment_id)

    if request.user != instance.author:
        return redirect('blog:post_detail', post_id=post_id)

    if request.method == 'POST':
        instance.delete()
        return redirect('blog:post_detail', post_id=post_id)
    return render(request, 'blog/comment.html')


def get_posts(add_filter=False, add_comments=False):
    """
    Получает набор публикаций из базы данных с возможностью применения
    фильтров и предзагрузки комментариев.
    Публикации загружаются с использованием оптимизации запросов,
    чтобы уменьшить количество обращений к базе данных.
    """
    qwery = Post.objects.select_related(
        'author',
        'category',
        'location'
    )
    if add_filter:
        qwery = qwery.filter(
            pub_date__lte=timezone.now(),
            is_published=True,
            category__is_published=True
        )
    if add_comments:
        qwery = qwery.prefetch_related('comments')
    return qwery.annotate(
        comment_count=Count('comments')
    ).order_by('-pub_date', 'title')


class OnlyAuthorMixin(UserPassesTestMixin):
    """
    Миксин, который проверяет, является ли пользователь, который
    отправил запрос, автором поста. Вернет False, если не является.
    """

    def test_func(self):
        object = self.get_object()
        return object.author == self.request.user

    def handle_no_permission(self):
        return redirect('blog:post_detail', post_id=self.get_object().pk)


class PostsListView(ListView):
    """
    Выводит на главную страницу все опубликованные посты.
    В начале страницы показываются самые новые публикации.
    """

    model = Post
    template_name = 'blog/index.html'
    queryset = get_posts(add_filter=True)

    paginate_by = COUNT_POSTS


class PostCreateView(LoginRequiredMixin, CreateView):
    """
    Создает пост. Создавать посты разрешается только админу
    и авторизованным пользователям.
    """

    model = Post
    form_class = PostForm
    template_name = 'blog/create.html'

    def form_valid(self, form):
        form.instance.author = self.request.user
        return super().form_valid(form)

    def get_success_url(self):
        return reverse_lazy(
            'blog:profile', kwargs={'username': self.request.user}
        )


class PostUpdateView(LoginRequiredMixin, OnlyAuthorMixin, UpdateView):
    """
    Класс позволяет изменить детали поста.
    Редактировать пост разрешается только его автору или администратору.
    Если происходит запрос на изменение не от автора поста,
    происходит перенаправление на страницу поста.
    """

    model = Post
    form_class = PostForm
    template_name = 'blog/create.html'
    pk_url_kwarg = 'post_id'

    def get_success_url(self):
        return reverse_lazy(
            'blog:post_detail', kwargs={'post_id': self.kwargs['post_id']}
        )


def post_detail(request, post_id):
    """
    Позволяет получить детали поста по указанному идентификатору.
    Если пост снят с публикации или "отложен",
    его может посмотреть только автор.
    """
    post = get_object_or_404(
        get_posts(add_filter=False, add_comments=True),
        pk=post_id
    )

    if post.author != request.user:
        if (
            not post.is_published or not post.category.is_published or
            post.pub_date > timezone.now()
        ):
            raise Http404()

    comments = post.comments.select_related('author')
    form = CommentForm()

    context = {
        'post': post,
        'form': form,
        'comments': comments,
    }

    return render(request, 'blog/detail.html', context)


@login_required
def delete_post(request, post_id):
    """
    Удаляет пост по указанному идентификатору, если текущий пользователь
    является автором этого поста. Если пользователь не является автором,
    происходит перенаправление на страницу деталей поста.
    """
    instance = get_object_or_404(Post, pk=post_id)

    if request.user != instance.author:
        return redirect('blog:post_detail', post_id=post_id)

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
        return self.request.user

    def get_success_url(self):
        user = self.get_object()
        return reverse('blog:profile', kwargs={'username': user.username})


def get_page_obj(request, paginator):
    """
    Получает объект страницы из пагинатора на основе номера страницы,
    указанного в параметрах запроса.
    """
    page_number = request.GET.get('page')
    return paginator.get_page(page_number)


def profile_details(request, username):
    """
    Функция для просмотра страницы пользователя, на которой есть информация
    о нем и опубликованные посты.
    """
    profile = get_object_or_404(
        User.objects.all(),
        username=username
    )

    if request.user == profile:
        posts = get_posts()
    else:
        posts = get_posts(add_filter=True)

    paginator = Paginator(
        posts.filter(author=profile), COUNT_POSTS
    )

    context = {
        'profile': profile,
        'page_obj': get_page_obj(request, paginator)
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

    paginator = Paginator(
        get_posts(add_filter=True).filter(category=category),
        COUNT_POSTS
    )

    context = {
        'category': category,
        'page_obj': get_page_obj(request, paginator)
    }
    return render(request, 'blog/category.html', context)
