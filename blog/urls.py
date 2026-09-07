from django.urls import path
from . import views

app_name = 'blog'

urlpatterns = [
    path('', views.article_list, name='article_list'),
    path('category/<slug:slug>/', views.category_detail, name='category_detail'),
    path('tag/<slug:slug>/', views.tag_detail, name='tag_detail'),
    path('<slug:slug>/', views.article_detail, name='article_detail'),
    path('<slug:slug>/comment/', views.add_comment, name='add_comment'),
]