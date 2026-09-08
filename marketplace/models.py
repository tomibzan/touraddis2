# marketplace/models.py
import logging
from django.db import models
from django.urls import reverse
from django.utils.text import slugify
from django.core.validators import MinValueValidator

# ✅ Option 1: Import from core
# from core.models import BaseModel

# ✅ Option 2: Define locally (if core app doesn't exist)
class BaseModel(models.Model):
    """Abstract base model with common fields."""
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        abstract = True

logger = logging.getLogger(__name__)


class Category(BaseModel):
    CATEGORY_CHOICES = [
        ('outfits', 'Traditional Outfits'),
        ('food', 'Spices & Dry Foods'),
        ('souvenirs', 'Handcrafted Souvenirs'),
        ('jewelry', 'Ethiopian Jewelry'),
        ('art', 'Art & Paintings'),
        ('books', 'Books & Manuscripts'),
    ]
    
    name = models.CharField(max_length=50, choices=CATEGORY_CHOICES, unique=True)
    slug = models.SlugField(max_length=60, unique=True, blank=True)
    description = models.TextField(blank=True, help_text="SEO description")
    image = models.ImageField(upload_to='categories/', blank=True, null=True, help_text="Category thumbnail")
    order = models.PositiveIntegerField(default=0, help_text="Display order")
    is_active = models.BooleanField(default=True, db_index=True)
    meta_title = models.CharField(max_length=70, blank=True)
    meta_description = models.CharField(max_length=160, blank=True)
    
    class Meta:
        verbose_name_plural = "Categories"
        ordering = ['order', 'name']
        indexes = [models.Index(fields=['slug', 'is_active'])]
    
    def __str__(self):
        return self.get_name_display()
    
    def save(self, *args, **kwargs):
        if not self.slug:
            self.slug = slugify(self.get_name_display())
        super().save(*args, **kwargs)
    
    def get_absolute_url(self):
        return reverse('marketplace:category_detail', kwargs={'slug': self.slug})
    
    def get_product_count(self):
        return self.products.filter(is_available=True).count()


class Product(BaseModel):
    name = models.CharField(max_length=200)
    slug = models.SlugField(max_length=200, unique=True, blank=True)
    
    category = models.ForeignKey(Category, related_name='products', on_delete=models.CASCADE)
    
    short_description = models.CharField(max_length=250, help_text="Brief summary for list views")
    description = models.TextField(help_text="Full details, cultural significance, materials")
    
    main_image = models.ImageField(upload_to='products/main/', blank=True, null=True)
    image_2 = models.ImageField(upload_to='products/additional/', blank=True, null=True)
    image_3 = models.ImageField(upload_to='products/additional/', blank=True, null=True)
    
    price = models.DecimalField(max_digits=10, decimal_places=2, validators=[MinValueValidator(0.01)], help_text="Price in ETB")
    discounted_price = models.DecimalField(max_digits=10, decimal_places=2, blank=True, null=True, validators=[MinValueValidator(0.01)], help_text="Discounted price")
    
    stock_quantity = models.IntegerField(default=0, validators=[MinValueValidator(0)], help_text="Current stock level")
    low_stock_threshold = models.IntegerField(default=5, help_text="Alert when stock falls below this")
    
    weight = models.DecimalField(max_digits=6, decimal_places=2, blank=True, null=True, help_text="Weight in kg")
    dimensions = models.CharField(max_length=50, blank=True)
    materials = models.CharField(max_length=200, blank=True)
    origin = models.CharField(max_length=100, blank=True)
    
    is_available = models.BooleanField(default=True, db_index=True)
    is_featured = models.BooleanField(default=False, db_index=True)
    is_best_seller = models.BooleanField(default=False)
    
    meta_title = models.CharField(max_length=70, blank=True)
    meta_description = models.CharField(max_length=160, blank=True)
    meta_keywords = models.CharField(max_length=200, blank=True)
    
    views = models.PositiveIntegerField(default=0)
    average_rating = models.DecimalField(max_digits=3, decimal_places=2, default=0.00)
    total_reviews = models.PositiveIntegerField(default=0)
    
    class Meta:
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['slug', 'is_available']),
            models.Index(fields=['category', 'is_available']),
            models.Index(fields=['-created_at']),
            models.Index(fields=['stock_quantity']),
        ]
    
    def __str__(self):
        return self.name
    
    def save(self, *args, **kwargs):
        if not self.slug:
            self.slug = slugify(self.name)
        super().save(*args, **kwargs)
    
    def get_absolute_url(self):
        return reverse('marketplace:product_detail', kwargs={'slug': self.slug})
    
    @property
    def is_on_sale(self):
        return self.discounted_price is not None and self.discounted_price < self.price
    
    @property
    def final_price(self):
        return self.discounted_price if self.is_on_sale else self.price
    
    @property
    def discount_percentage(self):
        if self.is_on_sale:
            return int(((self.price - self.discounted_price) / self.price) * 100)
        return 0
    
    @property
    def is_in_stock(self):
        return self.stock_quantity > 0
    
    @property
    def is_low_stock(self):
        return 0 < self.stock_quantity <= self.low_stock_threshold
    
    @property
    def is_out_of_stock(self):
        return self.stock_quantity == 0
    
    def reduce_stock(self, quantity):
        from django.db import transaction
        with transaction.atomic():
            product = Product.objects.select_for_update().get(id=self.id)
            if product.stock_quantity < quantity:
                logger.warning(f"Cannot reduce stock for {self.name}: requested {quantity}, available {product.stock_quantity}")
                return False
            product.stock_quantity -= quantity
            product.save(update_fields=['stock_quantity', 'updated_at'])
            logger.info(f"Reduced stock for {self.name} by {quantity}")
            return True
    
    def increase_stock(self, quantity):
        from django.db import transaction
        with transaction.atomic():
            product = Product.objects.select_for_update().get(id=self.id)
            product.stock_quantity += quantity
            product.save(update_fields=['stock_quantity', 'updated_at'])
            logger.info(f"Increased stock for {self.name} by {quantity}")
            return True


class Order(BaseModel):
    PAYMENT_CHOICES = [
        ('bank_transfer', 'Bank Transfer'),
        ('telebirr', 'Telebirr'),
        ('chapa', 'Chapa (Card/Mobile)'),
        ('cash_on_delivery', 'Cash on Delivery'),
    ]
    
    STATUS_CHOICES = [
        ('pending_payment', 'Pending Payment'),
        ('payment_received', 'Payment Received'),
        ('processing', 'Processing'),
        ('shipped', 'Shipped'),
        ('delivered', 'Delivered'),
        ('cancelled', 'Cancelled'),
        ('refunded', 'Refunded'),
    ]
    
    full_name = models.CharField(max_length=150)
    email = models.EmailField()
    phone = models.CharField(max_length=20)
    shipping_address = models.TextField()
    order_notes = models.TextField(blank=True)
    
    payment_method = models.CharField(max_length=20, choices=PAYMENT_CHOICES, default='bank_transfer')
    payment_slip = models.ImageField(upload_to='orders/payment_slips/', blank=True, null=True, help_text="Proof of payment")
    
    payment_id = models.CharField(max_length=100, blank=True)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='pending_payment', db_index=True)
    total_amount = models.DecimalField(max_digits=10, decimal_places=2, default=0.00)
    tracking_number = models.CharField(max_length=100, blank=True, help_text="Shipment tracking number")
    shipped_at = models.DateTimeField(null=True, blank=True)
    delivered_at = models.DateTimeField(null=True, blank=True)
    admin_notes = models.TextField(blank=True)
    
    # ✅ Updated field with null=True to safely manage existing database records
    reference_number = models.CharField(
        max_length=20, 
        unique=True, 
        null=True, 
        blank=True, 
        help_text="Auto-generated professional order ID"
    )
    
    class Meta:
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['email']),
            models.Index(fields=['status', '-created_at']),
            models.Index(fields=['-created_at']),
        ]
    
    def __str__(self):
        # ✅ Fallback to ID if reference_number is missing on existing records
        ref = self.reference_number or f"#{self.id}"
        return f"Order {ref} - {self.full_name}"
    
    def save(self, *args, **kwargs):
        if not self.reference_number:
            from django.utils import timezone
            today = timezone.now().strftime('%Y%m%d')
            count = Order.objects.filter(created_at__date=timezone.now().date()).count() + 1
            self.reference_number = f"ORD-{today}-{count:04d}"
        super().save(*args, **kwargs)
    
    @property
    def total_items(self):
        return self.items.count()
    
    @property
    def status_display(self):
        return dict(self.STATUS_CHOICES).get(self.status, self.status)
    
    @property
    def is_pending(self):
        return self.status == 'pending_payment'
    
    @property
    def is_paid(self):
        return self.status in ['payment_received', 'processing', 'shipped', 'delivered']
    
    @property
    def is_shipped(self):
        return self.status in ['shipped', 'delivered']
    
    @property
    def is_completed(self):
        return self.status == 'delivered'
    
    def mark_as_paid(self, payment_id=None):
        self.status = 'payment_received'
        if payment_id:
            self.payment_id = payment_id
        self.save(update_fields=['status', 'payment_id', 'updated_at'])
        logger.info(f"Order #{self.id} marked as paid")
    
    def mark_as_shipped(self, tracking_number):
        from django.utils import timezone
        self.status = 'shipped'
        self.tracking_number = tracking_number
        self.shipped_at = timezone.now()
        self.save(update_fields=['status', 'tracking_number', 'shipped_at', 'updated_at'])
        logger.info(f"Order #{self.id} shipped with tracking: {tracking_number}")
    
    def mark_as_delivered(self):
        from django.utils import timezone
        self.status = 'delivered'
        self.delivered_at = timezone.now()
        self.save(update_fields=['status', 'delivered_at', 'updated_at'])
        logger.info(f"Order #{self.id} marked as delivered")


class OrderItem(BaseModel):
    """Individual items within an order."""
    
    order = models.ForeignKey(
        Order,
        related_name='items',
        on_delete=models.CASCADE
    )
    product = models.ForeignKey(
        Product,
        on_delete=models.CASCADE
    )
    quantity = models.PositiveIntegerField(default=1)
    price_at_purchase = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        null=True,
        blank=True
    )
    
    # Snapshot (in case product changes later)
    product_name = models.CharField(max_length=200, blank=True)
    
    class Meta:
        ordering = ['created_at']
    
    def __str__(self):
        return f"{self.quantity}x {self.product_name or self.product.name}"
    
    def save(self, *args, **kwargs):
        # Save product name as snapshot
        if not self.product_name and self.product:
            self.product_name = self.product.name
        super().save(*args, **kwargs)
    
    @property
    def subtotal(self):
        """FOOLPROOF CALCULATION: Handles None values gracefully."""
        try:
            price = self.price_at_purchase if self.price_at_purchase is not None else 0
            qty = self.quantity if self.quantity is not None else 0
            return qty * price
        except (TypeError, ValueError):
            return 0