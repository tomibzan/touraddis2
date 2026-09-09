import logging
from django.shortcuts import render, redirect
from django.contrib import messages
from django.core.mail import send_mail
from django.conf import settings
from django.db import transaction
from .models import ContactInquiry, NewsletterSubscription, SiteSettings
from .forms import ContactForm, NewsletterForm

logger = logging.getLogger(__name__)


def home(request):
    """Homepage with featured tours and products."""
    from tours.models import Tour
    from marketplace.models import Product
    from blog.models import Article
    
    featured_tours = Tour.objects.filter(is_featured=True, is_active=True)[:6]
    featured_products = Product.objects.filter(is_featured=True, is_available=True)[:8]
    latest_articles = Article.objects.filter(status='published')[:3]
    
    site_settings = SiteSettings.load()
    
    return render(request, 'core/home.html', {
        'featured_tours': featured_tours,
        'featured_products': featured_products,
        'latest_articles': latest_articles,
        'site_settings': site_settings,
    })


def about(request):
    """About page."""
    site_settings = SiteSettings.load()
    return render(request, 'core/about.html', {
        'site_settings': site_settings,
    })


def contact(request):
    """Contact form with status tracking."""
    if request.method == 'POST':
        form = ContactForm(request.POST)
        if form.is_valid():
            with transaction.atomic():
                inquiry = form.save()
                
                # Send email notification
                try:
                    send_mail(
                        subject=f"New Contact Inquiry: {inquiry.subject}",
                        message=f"From: {inquiry.name} ({inquiry.email})\n\n{inquiry.message}",
                        from_email=settings.DEFAULT_FROM_EMAIL,
                        recipient_list=[settings.ADMIN_EMAIL, 'info@touraddis.com'],
                        fail_silently=False,
                    )
                    logger.info(f"Contact inquiry email sent for {inquiry.reference_number}")
                except Exception as e:
                    logger.error(f"Contact email failed for {inquiry.reference_number}: {e}")
                
                messages.success(
                    request,
                    f"Thank you! Your inquiry has been received. Reference: {inquiry.reference_number}"
                )
                return redirect('core:contact')
    else:
        form = ContactForm()
    
    return render(request, 'core/contact.html', {'form': form})


def track_inquiry(request):
    """Track contact inquiry status."""
    inquiry = None
    error = None
    
    if request.method == 'POST':
        email = request.POST.get('email')
        reference = request.POST.get('reference')
        
        try:
            if reference:
                inquiry = ContactInquiry.objects.get(reference_number=reference, email=email)
            else:
                # Show latest inquiry for this email
                inquiry = ContactInquiry.objects.filter(email=email).first()
                
            if not inquiry:
                error = "No inquiry found. Please check your details."
        except ContactInquiry.DoesNotExist:
            error = "No inquiry found. Please check your details."
    
    return render(request, 'core/track_inquiry.html', {
        'inquiry': inquiry,
        'error': error,
    })


def newsletter_subscribe(request):
    """Newsletter subscription."""
    if request.method == 'POST':
        form = NewsletterForm(request.POST)
        if form.is_valid():
            email = form.cleaned_data['email']
            source = form.cleaned_data.get('source', 'website')
            
            subscription, created = NewsletterSubscription.objects.get_or_create(
                email=email,
                defaults={'source': source}
            )
            
            if created:
                messages.success(request, "Thank you for subscribing!")
                logger.info(f"New newsletter subscription: {email}")
            else:
                if not subscription.is_active:
                    subscription.is_active = True
                    subscription.save()
                    messages.success(request, "Welcome back! You're subscribed again.")
                else:
                    messages.info(request, "You're already subscribed!")
            
            return redirect(request.META.get('HTTP_REFERER', 'core:home'))
    
    return redirect('core:home')

def robots_txt(request):
    """Serve robots.txt to control search engine crawling."""
    lines = [
        "User-agent: *",
        "Allow: /",
        "Disallow: /admin/",
        "Disallow: /inventory/",
        "Disallow: /reports/",
        "",
        "Sitemap: https://touraddis.com/sitemap.xml",
    ]
    return HttpResponse("\n".join(lines), content_type="text/plain")
