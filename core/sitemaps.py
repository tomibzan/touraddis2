from django.contrib.sitemaps import Sitemap
from django.urls import reverse
from marketplace.models import Product
from tours.models import Tour
from blog.models import Article


class StaticViewSitemap(Sitemap):
    """Sitemap for static pages."""
    priority = 0.8
    changefreq = 'weekly'
    
    def items(self):
        return ['core:home', 'core:about', 'core:contact', 'tours:tour_list', 'marketplace:product_list', 'blog:article_list']
    
    def location(self, item):
        return reverse(item)


class ProductSitemap(Sitemap):
    """Sitemap for marketplace products."""
    changefreq = 'weekly'
    priority = 0.7
    
    def items(self):
        return Product.objects.filter(is_available=True, stock_quantity__gt=0)
    
    def location(self, item):
        return item.get_absolute_url()
    
    def lastmod(self, obj):
        return obj.updated_at


class TourSitemap(Sitemap):
    """Sitemap for tour packages."""
    changefreq = 'weekly'
    priority = 0.8
    
    def items(self):
        return Tour.objects.filter(is_active=True)
    
    def location(self, item):
        return item.get_absolute_url()
    
    def lastmod(self, obj):
        return obj.updated_at


class ArticleSitemap(Sitemap):
    """Sitemap for blog articles."""
    changefreq = 'weekly'
    priority = 0.6
    
    def items(self):
        return Article.objects.filter(status='published')
    
    def location(self, item):
        return item.get_absolute_url()
    
    def lastmod(self, obj):
        return obj.published_at or obj.updated_at
