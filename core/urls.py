from django.urls import path
from django.contrib.sitemaps.views import sitemap
from . import views
from .sitemaps import StaticViewSitemap, ProductSitemap, TourSitemap, ArticleSitemap

app_name = 'core'

sitemaps = {
    'static': StaticViewSitemap,
    'products': ProductSitemap,
    'tours': TourSitemap,
    'articles': ArticleSitemap,
}

urlpatterns = [
    path('', views.home, name='home'),
    path('about/', views.about, name='about'),
    path('contact/', views.contact, name='contact'),
    path('track-inquiry/', views.track_inquiry, name='track_inquiry'),
    path('newsletter/subscribe/', views.newsletter_subscribe, name='newsletter_subscribe'),
    path('robots.txt', views.robots_txt, name='robots_txt'),
    path('sitemap.xml', sitemap, {'sitemaps': sitemaps}, name='sitemap'),
]
