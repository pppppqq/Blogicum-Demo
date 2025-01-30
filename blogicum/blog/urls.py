from django.urls import path, include

from . import views

app_name = 'blog'


post_urls = [
    path('<int:post_id>/', views.post_detail,
         name='post_detail'),
    path('create/', views.PostCreateView.as_view(), name='create_post'),
    path('<int:post_id>/edit/', views.PostUpdateView.as_view(),
         name='edit_post'),
    path('<int:post_id>/delete/', views.delete_post, name='delete_post'),
]

comment_urls = [
    path('comment/', views.add_comment,
         name='add_comment'),
    path('edit_comment/<int:comment_id>/',
         views.edit_comment, name='edit_comment'),
    path('delete_comment/<int:comment_id>/',
         views.delete_comment, name='delete_comment'),
]

urlpatterns = [
    path('', views.PostsListView.as_view(), name='index'),
    path('posts/', include(post_urls)),
    path('posts/<int:post_id>/', include(comment_urls)),
    path('category/<slug:category_slug>/', views.category_posts,
         name='category_posts'),
    path('profile_edit/', views.ProfileUpdateView.as_view(),
         name="edit_profile"),
    path('profile/<str:username>/', views.profile_details, name='profile'),
]
