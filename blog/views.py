import logging
from django.shortcuts import render, get_object_or_404, redirect
from django.contrib import messages
from django.core.paginator import Paginator
from django.db import transaction
from .models import Article, BlogCategory, Tag, Comment
from .forms import CommentForm

logger = logging.getLogger(__name__)


def article_list(request):
    """List all published articles."""
    # ✅ FIXED: Use status='published'
    articles = Article.objects.filter(status='published').select_related('author', 'category')
    
    paginator = Paginator(articles, 12)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    
    categories = BlogCategory.objects.all()
    
    return render(request, 'blog/article_list.html', {
        'page_obj': page_obj,
        'categories': categories,
    })


def article_detail(request, slug):
    """Article detail page with comments."""
    # ✅ FIXED: Use status='published'
    article = get_object_or_404(
        Article.objects.select_related('author', 'category'),
        slug=slug,
        status='published'
    )
    
    article.views += 1
    article.save(update_fields=['views'])
    
    # ✅ FIXED: Use status='approved'
    comments = article.comments.filter(status='approved').select_related('parent')
    form = CommentForm()
    
    return render(request, 'blog/article_detail.html', {
        'article': article,
        'comments': comments,
        'form': form,
    })


def category_detail(request, slug):
    """Articles filtered by category."""
    category = get_object_or_404(BlogCategory, slug=slug)
    # ✅ FIXED: Use status='published'
    articles = Article.objects.filter(category=category, status='published')
    
    paginator = Paginator(articles, 12)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    
    return render(request, 'blog/category_detail.html', {
        'category': category,
        'page_obj': page_obj,
    })


def tag_detail(request, slug):
    """Articles filtered by tag."""
    tag = get_object_or_404(Tag, slug=slug)
    # ✅ FIXED: Use status='published'
    articles = tag.posts.filter(status='published')
    
    paginator = Paginator(articles, 12)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    
    return render(request, 'blog/tag_detail.html', {
        'tag': tag,
        'page_obj': page_obj,
    })


def add_comment(request, slug):
    """Add comment to article."""
    article = get_object_or_404(Article, slug=slug, status='published')
    
    if request.method == 'POST':
        form = CommentForm(request.POST)
        if form.is_valid():
            with transaction.atomic():
                comment = form.save(commit=False)
                comment.article = article
                comment.status = 'pending'
                comment.save()
                
                messages.success(request, "Thank you! Your comment is pending moderation.")
                logger.info(f"New comment on '{article.title}' by {comment.name}")
                
                return redirect('blog:article_detail', slug=slug)
    
    return redirect('blog:article_detail', slug=slug)