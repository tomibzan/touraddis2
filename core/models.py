import logging
from django.db import models
from django.conf import settings
from django.utils import timezone
from django.core.validators import MinValueValidator, EmailValidator

logger = logging.getLogger(__name__)


# =====================================================
# BASE MODEL (Common fields for all models)
# =====================================================
class BaseModel(models.Model):
    """Abstract base model with common timestamp fields."""
    created_at = models.DateTimeField(auto_now_add=True, db_index=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        abstract = True
        ordering = ['-created_at']


# =====================================================
# SITE SETTINGS (Global configuration)
# =====================================================
class SiteSettings(BaseModel):
    """Singleton model for global site configuration."""
    site_name = models.CharField(max_length=100, default='TourAddis')
    tagline = models.CharField(max_length=200, blank=True)
    
    # Contact Information
    contact_email = models.EmailField(default='info@touraddis.com')
    contact_phone = models.CharField(max_length=20, default='+251 912 612 046')
    whatsapp_number = models.CharField(max_length=20, blank=True)
    
    # Business Hours
    business_hours = models.TextField(
        help_text="e.g., Mon-Fri: 9AM-6PM, Sat: 10AM-4PM, Sun: Closed",
        blank=True
    )
    
    # Address
    address = models.TextField(blank=True)
    city = models.CharField(max_length=100, default='Addis Ababa')
    country = models.CharField(max_length=100, default='Ethiopia')
    
    # Social Media
    facebook_url = models.URLField(blank=True)
    instagram_url = models.URLField(blank=True)
    twitter_url = models.URLField(blank=True)
    tiktok_url = models.URLField(blank=True)
    telegram_url = models.URLField(blank=True)
    
    # Payment Details (for manual checkout)
    bank_name = models.CharField(max_length=100, blank=True)
    bank_account_number = models.CharField(max_length=50, blank=True)
    bank_account_name = models.CharField(max_length=150, blank=True)
    telebirr_number = models.CharField(max_length=20, blank=True)
    
    class Meta:
        verbose_name = 'Site Settings'
        verbose_name_plural = 'Site Settings'
    
    def __str__(self):
        return f"Site Settings: {self.site_name}"
    
    def save(self, *args, **kwargs):
        # Ensure only one instance exists (singleton pattern)
        self.pk = 1
        super().save(*args, **kwargs)
    
    @classmethod
    def load(cls):
        """Load the singleton instance or create default."""
        obj, created = cls.objects.get_or_create(pk=1)
        return obj


# =====================================================
# CONTACT INQUIRY (With Status Tracking)
# =====================================================
class ContactInquiry(BaseModel):
    """Customer contact form submissions with status tracking."""
    
    STATUS_CHOICES = [
        ('new', 'New'),
        ('in_progress', 'In Progress'),
        ('resolved', 'Resolved'),
        ('spam', 'Spam'),
    ]
    
    PRIORITY_CHOICES = [
        ('low', 'Low'),
        ('medium', 'Medium'),
        ('high', 'High'),
        ('urgent', 'Urgent'),
    ]
    
    # Contact Details
    name = models.CharField(max_length=150)
    email = models.EmailField(validators=[EmailValidator()])
    phone = models.CharField(max_length=20, blank=True)
    
    # Inquiry Details
    subject = models.CharField(max_length=200)
    message = models.TextField()
    
    # Status Tracking (Lesson Learned: Enhanced state management)
    status = models.CharField(
        max_length=20, 
        choices=STATUS_CHOICES, 
        default='new',
        db_index=True
    )
    priority = models.CharField(
        max_length=10,
        choices=PRIORITY_CHOICES,
        default='medium'
    )
    
    # Admin Notes
    admin_notes = models.TextField(blank=True, help_text="Internal notes for admin")
    resolved_at = models.DateTimeField(null=True, blank=True)
    resolved_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='resolved_inquiries'
    )
    
    # Reference (for tracking)
    reference_number = models.CharField(max_length=20, unique=True, blank=True)
    
    class Meta:
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['status', '-created_at']),
            models.Index(fields=['email']),
        ]
    
    def __str__(self):
        return f"Inquiry #{self.reference_number} - {self.subject}"
    
    def save(self, *args, **kwargs):
        # Generate reference number if not set
        if not self.reference_number:
            # Format: INQ-20260906-001
            today = timezone.now().strftime('%Y%m%d')
            count = ContactInquiry.objects.filter(
                created_at__date=timezone.now().date()
            ).count() + 1
            self.reference_number = f"INQ-{today}-{count:03d}"
        
        # Set resolved_at when status changes to resolved
        if self.status == 'resolved' and not self.resolved_at:
            self.resolved_at = timezone.now()
        
        super().save(*args, **kwargs)
    
    def mark_as_resolved(self, user=None):
        """Helper method to mark inquiry as resolved."""
        self.status = 'resolved'
        self.resolved_at = timezone.now()
        self.resolved_by = user
        self.save()
        logger.info(f"Inquiry {self.reference_number} marked as resolved by {user}")


# =====================================================
# NEWSLETTER SUBSCRIPTION (For Blog Integration)
# =====================================================
class NewsletterSubscription(BaseModel):
    """Email newsletter subscribers."""
    email = models.EmailField(unique=True, validators=[EmailValidator()])
    is_active = models.BooleanField(default=True)
    subscribed_at = models.DateTimeField(auto_now_add=True)
    unsubscribed_at = models.DateTimeField(null=True, blank=True)
    
    # Tracking
    source = models.CharField(
        max_length=50, 
        blank=True, 
        help_text="Where they subscribed from (e.g., 'blog', 'footer', 'popup')"
    )
    
    class Meta:
        ordering = ['-subscribed_at']
    
    def __str__(self):
        return self.email
    
    def unsubscribe(self):
        """Mark subscription as inactive."""
        self.is_active = False
        self.unsubscribed_at = timezone.now()
        self.save()
        logger.info(f"Newsletter subscription {self.email} unsubscribed")

class RateLimitRecord(models.Model):
    """Tracks form submissions to prevent spam."""
    ip = models.GenericIPAddressField()
    action = models.CharField(max_length=100) # e.g., 'contact_form', 'newsletter'
    timestamp = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        indexes = [
            models.Index(fields=['ip', 'action', 'timestamp']),
        ]
    
    def __str__(self):
        return f"{self.action} - {self.ip} at {self.timestamp}" 

class CarouselSlide(BaseModel):
    """Dedicated model for the homepage hero carousel."""
    title = models.CharField(max_length=200)
    subtitle = models.CharField(max_length=400, blank=True, help_text="Optional short description")
    image = models.ImageField(
        upload_to='carousel/', 
        help_text="Wide format image optimized for 3:1 ratio (e.g., 1200x400px)"
    )
    link_url = models.URLField(blank=True, null=True, help_text="Where to go when clicked (optional)")
    link_text = models.CharField(max_length=50, blank=True, default="Learn More", help_text="Button text")
    order = models.PositiveIntegerField(default=0, help_text="Lower numbers appear first")
    is_active = models.BooleanField(default=True)
    
    class Meta:
        ordering = ['order', 'created_at']
        verbose_name_plural = 'Carousel Slides'
    
    def __str__(self):
        return self.title           