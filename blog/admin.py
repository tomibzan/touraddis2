from django.contrib import admin
from .models import BlogCategory, Tag, Article, Comment


@admin.register(BlogCategory)
class BlogCategoryAdmin(admin.ModelAdmin):
    list_display = ['name', 'slug', 'get_post_count']
    search_fields = ['name', 'description']
    prepopulated_fields = {'slug': ('name',)}
    
    def get_post_count(self, obj):
        # ✅ FIXED: Use status='published' instead of is_published=True
        return obj.posts.filter(status='published').count()
    get_post_count.short_description = 'Posts'


@admin.register(Tag)
class TagAdmin(admin.ModelAdmin):
    list_display = ['name', 'slug']
    search_fields = ['name']
    prepopulated_fields = {'slug': ('name',)}


@admin.register(Article)
class ArticleAdmin(admin.ModelAdmin):
    list_display = [
        'title', 'author', 'category',
        'status', 'published_at', 'views'
    ]
    list_filter = ['status', 'category', 'author', 'published_at']
    search_fields = ['title', 'excerpt', 'content']
    prepopulated_fields = {'slug': ('title',)}
    filter_horizontal = ['tags']
    readonly_fields = ['views', 'created_at', 'updated_at']
    
    fieldsets = (
        ('Basic Information', {
            'fields': ('title', 'slug', 'author', 'excerpt', 'content')
        }),
        ('Media', {
            'fields': ('featured_image',)
        }),
        ('Organization', {
            'fields': ('category', 'tags')
        }),
        ('Status', {
            'fields': ('status', 'published_at')
        }),
        ('SEO', {
            'fields': ('meta_title', 'meta_description', 'meta_keywords'),
            'classes': ('collapse',)
        }),
        ('Analytics', {
            'fields': ('views', 'created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )
    
    actions = ['publish_articles', 'unpublish_articles']
    
    def publish_articles(self, request, queryset):
        for article in queryset:
            article.status = 'published'
            if not article.published_at:
                from django.utils import timezone
                article.published_at = timezone.now()
            article.save()
        self.message_user(request, f"{queryset.count()} articles published")
    publish_articles.short_description = "Publish selected articles"
    
    def unpublish_articles(self, request, queryset):
        queryset.update(status='draft')
        self.message_user(request, f"{queryset.count()} articles unpublished")
    unpublish_articles.short_description = "Unpublish selected articles"


@admin.register(Comment)
class CommentAdmin(admin.ModelAdmin):
    list_display = ['name', 'article', 'status', 'created_at']
    list_filter = ['status', 'created_at']
    search_fields = ['name', 'email', 'content']
    readonly_fields = ['created_at', 'updated_at']
    
    actions = ['approve_comments', 'mark_as_spam']
    
    def approve_comments(self, request, queryset):
        queryset.update(status='approved')
        self.message_user(request, f"{queryset.count()} comments approved")
    approve_comments.short_description = "Approve selected comments"
    
    def mark_as_spam(self, request, queryset):
        queryset.update(status='spam')
        self.message_user(request, f"{queryset.count()} comments marked as spam")
    mark_as_spam.short_description = "Mark selected comments as spam"