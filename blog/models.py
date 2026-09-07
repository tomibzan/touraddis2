import logging
from django.db import models
from django.urls import reverse
from django.utils.text import slugify
from django.conf import settings
from cloudinary.models import CloudinaryField # We will change this to ImageField next
from core.models import BaseModel

logger = logging.getLogger(__name__)

# Note: If you haven't changed CloudinaryField to ImageField in this file yet, 
# please do so as we did in marketplace and tours models.
# For now, here is the logic fix:

class BlogCategory(BaseModel):
    name = models.CharField(max_length=100, unique=True)
    slug = models.SlugField(max_length=100, unique=True, blank=True)
    description = models.TextField(blank=True)
    meta_title = models.CharField(max_length=70, blank=True)
    meta_description = models.CharField(max_length=160, blank=True)
    
    class Meta:
        verbose_name_plural = "Blog Categories"
        ordering = ['name']
    
    def __str__(self):
        return self.name
    
    def save(self, *args, **kwargs):
        if not self.slug:
            self.slug = slugify(self.name)
        super().save(*args, **kwargs)
    
    def get_absolute_url(self):
        return reverse('blog:category_detail', kwargs={'slug': self.slug})
    
    # ✅ FIXED: Use status='published'
    def get_post_count(self):
        return self.posts.filter(status='published').count()


class Tag(BaseModel):
    name = models.CharField(max_length=50, unique=True)
    slug = models.SlugField(max_length=50, unique=True, blank=True)
    
    class Meta:
        ordering = ['name']
    
    def __str__(self):
        return self.name
    
    def save(self, *args, **kwargs):
        if not self.slug:
            self.slug = slugify(self.name)
        super().save(*args, **kwargs)


class Article(BaseModel):
    STATUS_CHOICES = [
        ('draft', 'Draft'),
        ('published', 'Published'),
        ('archived', 'Archived'),
    ]
    
    title = models.CharField(max_length=200)
    slug = models.SlugField(max_length=200, unique=True, blank=True)
    author = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='articles')
    excerpt = models.TextField(max_length=300, help_text="Short summary for list views")
    content = models.TextField(help_text="Full article content")
    
    # ✅ If you are using local media, change this to: models.ImageField(upload_to='blog/featured/', blank=True, null=True)
    featured_image = models.ImageField(upload_to='blog/featured/', blank=True, null=True) 
    
    category = models.ForeignKey(BlogCategory, on_delete=models.SET_NULL, null=True, blank=True, related_name='posts')
    tags = models.ManyToManyField(Tag, blank=True, related_name='posts')
    
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='draft', db_index=True)
    published_at = models.DateTimeField(null=True, blank=True)
    
    meta_title = models.CharField(max_length=70, blank=True)
    meta_description = models.CharField(max_length=160, blank=True)
    meta_keywords = models.CharField(max_length=200, blank=True)
    views = models.PositiveIntegerField(default=0)
    
    class Meta:
        ordering = ['-published_at', '-created_at']
        indexes = [
            models.Index(fields=['slug', 'status']),
            models.Index(fields=['-published_at']),
            models.Index(fields=['category', 'status']),
        ]
    
    def __str__(self):
        return self.title
    
    def save(self, *args, **kwargs):
        if not self.slug:
            self.slug = slugify(self.title)
        if self.status == 'published' and not self.published_at:
            from django.utils import timezone
            self.published_at = timezone.now()
        super().save(*args, **kwargs)
    
    def get_absolute_url(self):
        return reverse('blog:article_detail', kwargs={'slug': self.slug})


class Comment(BaseModel):
    STATUS_CHOICES = [
        ('pending', 'Pending Approval'),
        ('approved', 'Approved'),
        ('spam', 'Spam'),
    ]
    
    article = models.ForeignKey(Article, on_delete=models.CASCADE, related_name='comments')
    name = models.CharField(max_length=100)
    email = models.EmailField()
    content = models.TextField()
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='pending', db_index=True)
    parent = models.ForeignKey('self', on_delete=models.CASCADE, null=True, blank=True, related_name='replies')
    
    class Meta:
        ordering = ['created_at']
    
    def __str__(self):
        return f"Comment by {self.name} on {self.article.title}"