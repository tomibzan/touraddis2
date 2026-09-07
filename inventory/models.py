import logging
from django.db import models
from django.conf import settings
from core.models import BaseModel

logger = logging.getLogger(__name__)


# =====================================================
# SUPPLIER
# =====================================================
class Supplier(BaseModel):
    """Product suppliers."""
    name = models.CharField(max_length=200)
    contact_person = models.CharField(max_length=150, blank=True)
    email = models.EmailField(blank=True)
    phone = models.CharField(max_length=20, blank=True)
    address = models.TextField(blank=True)
    
    # Status
    is_active = models.BooleanField(default=True, db_index=True)
    
    # Notes
    notes = models.TextField(blank=True)
    
    class Meta:
        ordering = ['name']
    
    def __str__(self):
        return self.name


# =====================================================
# STOCK MOVEMENT
# =====================================================
class StockMovement(BaseModel):
    """Track all stock movements (in/out/adjustments)."""
    
    MOVEMENT_TYPE_CHOICES = [
        ('in', 'Stock In (Restock)'),
        ('out', 'Stock Out (Sale)'),
        ('adjustment', 'Manual Adjustment'),
        ('return', 'Customer Return'),
        ('damage', 'Damaged/Lost'),
    ]
    
    # Product Reference
    product = models.ForeignKey(
        'marketplace.Product',
        on_delete=models.CASCADE,
        related_name='stock_movements'
    )
    
    # Movement Details
    movement_type = models.CharField(
        max_length=20,
        choices=MOVEMENT_TYPE_CHOICES,
        db_index=True
    )
    quantity = models.IntegerField(
        help_text="Positive for stock in, negative for stock out"
    )
    
    # Before/After Snapshot
    stock_before = models.IntegerField()
    stock_after = models.IntegerField()
    
    # References
    supplier = models.ForeignKey(
        Supplier,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='movements'
    )
    order = models.ForeignKey(
        'marketplace.Order',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='stock_movements'
    )
    
    # Metadata
    performed_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True
    )
    reason = models.TextField(
        blank=True,
        help_text="Reason for adjustment or notes"
    )
    reference_number = models.CharField(
        max_length=50,
        blank=True,
        help_text="PO number, invoice number, etc."
    )
    
    class Meta:
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['product', '-created_at']),
            models.Index(fields=['movement_type', '-created_at']),
        ]
    
    def __str__(self):
        return f"{self.get_movement_type_display()} - {self.product.name} ({self.quantity})"
    
    def save(self, *args, **kwargs):
        # Calculate stock_after
        self.stock_after = self.stock_before + self.quantity
        super().save(*args, **kwargs)
        
        # Log the movement
        logger.info(
            f"Stock movement: {self.product.name} - "
            f"{self.get_movement_type_display()} - "
            f"Qty: {self.quantity} - "
            f"Before: {self.stock_before}, After: {self.stock_after}"
        )


# =====================================================
# LOW STOCK ALERT
# =====================================================
class LowStockAlert(BaseModel):
    """Track low stock alerts."""
    product = models.OneToOneField(
        'marketplace.Product',
        on_delete=models.CASCADE,
        related_name='low_stock_alert'
    )
    is_acknowledged = models.BooleanField(default=False)
    acknowledged_at = models.DateTimeField(null=True, blank=True)
    acknowledged_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True
    )
    
    class Meta:
        ordering = ['-created_at']
    
    def __str__(self):
        return f"Low Stock Alert: {self.product.name}"
    
    def acknowledge(self, user=None):
        """Mark alert as acknowledged."""
        from django.utils import timezone
        self.is_acknowledged = True
        self.acknowledged_at = timezone.now()
        self.acknowledged_by = user
        self.save()
        logger.info(f"Low stock alert for {self.product.name} acknowledged")