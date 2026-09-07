import logging
from django.db import models
from django.urls import reverse
from django.utils.text import slugify
from django.utils import timezone
from django.core.validators import MinValueValidator
from core.models import BaseModel

logger = logging.getLogger(__name__)


class Tour(BaseModel):
    REGION_CHOICES = [
        ('addis_ababa', 'Addis Ababa City'),
        ('entoto', 'Entoto Mountains & Park'),
        ('bishoftu', 'Bishoftu (Debre Zeyit) & Lakes'),
        ('adama', 'Adama & Rift Valley'),
        ('custom_vicinity', 'Custom Addis Vicinity Tour'),
        # 🚀 FUTURE SCALE-UP: Simply add 'lalibela', 'omo_valley', etc. here later.
        # No database migrations will be needed!
    ]
    
    DIFFICULTY_CHOICES = [
        ('easy', 'Easy'),
        ('moderate', 'Moderate'),
        ('challenging', 'Challenging'),
        ('strenuous', 'Strenuous'),
    ]
    
    title = models.CharField(max_length=200)
    slug = models.SlugField(max_length=200, unique=True, blank=True)
    region = models.CharField(max_length=50, choices=REGION_CHOICES, db_index=True)
    
    short_description = models.CharField(max_length=250, help_text="Brief summary for list views and SEO")
    description = models.TextField(help_text="Full detailed itinerary")
    itinerary = models.TextField(blank=True, help_text="Day-by-day itinerary")
    
    # ✅ CHANGED TO LOCAL ImageField
    hero_image = models.ImageField(upload_to='tours/heroes/', blank=True, null=True)
    image_2 = models.ImageField(upload_to='tours/additional/', blank=True, null=True)
    image_3 = models.ImageField(upload_to='tours/additional/', blank=True, null=True)
    
    price_per_person = models.DecimalField(max_digits=10, decimal_places=2, validators=[MinValueValidator(0.01)], help_text="Price in ETB")
    duration_days = models.IntegerField(validators=[MinValueValidator(1)], help_text="Total duration in days")
    max_group_size = models.IntegerField(default=10, validators=[MinValueValidator(1)])
    difficulty_level = models.CharField(max_length=20, choices=DIFFICULTY_CHOICES, default='moderate')
    
    includes = models.TextField(blank=True, help_text="What's included (transport, meals, guide, etc.)")
    excludes = models.TextField(blank=True, help_text="What's not included")
    
    is_featured = models.BooleanField(default=False, db_index=True)
    is_active = models.BooleanField(default=True, db_index=True)
    
    meta_title = models.CharField(max_length=70, blank=True)
    meta_description = models.CharField(max_length=160, blank=True)
    
    views = models.PositiveIntegerField(default=0)
    
    class Meta:
        ordering = ['-created_at']
        verbose_name = "Tour Package"
        verbose_name_plural = "Tour Packages"
        indexes = [
            models.Index(fields=['slug', 'is_active']),
            models.Index(fields=['region', 'is_active']),
            models.Index(fields=['is_featured', 'is_active']),
        ]
    
    def __str__(self):
        return self.title
    
    def save(self, *args, **kwargs):
        if not self.slug:
            self.slug = slugify(self.title)
        super().save(*args, **kwargs)
    
    def get_absolute_url(self):
        return reverse('tours:tour_detail', kwargs={'slug': self.slug})
    
    @property
    def formatted_price(self):
        return f"{self.price_per_person} ETB"
    
    @property
    def total_bookings_count(self):
        return self.bookings.exclude(status='cancelled').count()
    
    @property
    def available_spots(self):
        confirmed_guests = sum(b.number_of_guests for b in self.bookings.filter(status='confirmed'))
        return max(0, self.max_group_size - confirmed_guests)


class TourImage(BaseModel):
    tour = models.ForeignKey(Tour, related_name='images', on_delete=models.CASCADE)
    # ✅ CHANGED TO LOCAL ImageField
    image = models.ImageField(upload_to='tours/gallery/', blank=True, null=True)
    alt_text = models.CharField(max_length=100, blank=True)
    caption = models.CharField(max_length=200, blank=True)
    order = models.PositiveIntegerField(default=0)
    
    class Meta:
        ordering = ['order']
    
    def __str__(self):
        return f"Image for {self.tour.title}"


class Booking(BaseModel):
    STATUS_CHOICES = [
        ('pending', 'Pending Inquiry'),
        ('confirmed', 'Confirmed'),
        ('paid', 'Paid'),
        ('completed', 'Completed'),
        ('cancelled', 'Cancelled'),
    ]
    
    PAYMENT_CHOICES = [
        ('bank_transfer', 'Bank Transfer'),
        ('telebirr', 'Telebirr'),
        ('chapa', 'Chapa (Card/Mobile)'),
        ('cash', 'Cash on Arrival'),
    ]
    
    tour = models.ForeignKey(Tour, related_name='bookings', on_delete=models.CASCADE)
    
    customer_name = models.CharField(max_length=150)
    customer_email = models.EmailField()
    customer_phone = models.CharField(max_length=20)
    customer_nationality = models.CharField(max_length=100, blank=True)
    
    tour_date = models.DateField()
    number_of_guests = models.IntegerField(default=1, validators=[MinValueValidator(1)])
    special_requests = models.TextField(blank=True)
    
    payment_method = models.CharField(max_length=20, choices=PAYMENT_CHOICES, default='bank_transfer')
    
    # ✅ CHANGED TO LOCAL ImageField
    payment_slip = models.ImageField(upload_to='bookings/payment_slips/', blank=True, null=True)
    
    payment_id = models.CharField(max_length=100, blank=True)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='pending', db_index=True)
    total_price = models.DecimalField(max_digits=10, decimal_places=2, default=0.00)
    reference_number = models.CharField(max_length=20, unique=True, blank=True)
    admin_notes = models.TextField(blank=True)
    
    class Meta:
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['customer_email']),
            models.Index(fields=['status', '-created_at']),
            models.Index(fields=['tour_date']),
        ]
    
    def __str__(self):
        return f"Booking {self.reference_number} - {self.customer_name}"
    
    def save(self, *args, **kwargs):
        if not self.reference_number:
            today = timezone.now().strftime('%Y%m%d')
            count = Booking.objects.filter(created_at__date=timezone.now().date()).count() + 1
            self.reference_number = f"BK-{today}-{count:03d}"
        
        if not self.total_price and self.tour:
            self.total_price = self.tour.price_per_person * self.number_of_guests
        
        super().save(*args, **kwargs)
    
    def confirm(self):
        self.status = 'confirmed'
        self.save(update_fields=['status', 'updated_at'])
        logger.info(f"Booking {self.reference_number} confirmed")
    
    def mark_as_paid(self, payment_id=None):
        self.status = 'paid'
        if payment_id:
            self.payment_id = payment_id
        self.save(update_fields=['status', 'payment_id', 'updated_at'])
        logger.info(f"Booking {self.reference_number} marked as paid")
    
    def mark_as_completed(self):
        self.status = 'completed'
        self.save(update_fields=['status', 'updated_at'])
        logger.info(f"Booking {self.reference_number} completed")
    
    def cancel(self, reason=None):
        self.status = 'cancelled'
        if reason:
            self.admin_notes = f"{self.admin_notes}\nCancelled: {reason}".strip()
        self.save(update_fields=['status', 'admin_notes', 'updated_at'])
        logger.info(f"Booking {self.reference_number} cancelled")