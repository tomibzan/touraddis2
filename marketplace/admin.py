from django.contrib import admin
from .models import Category, Product, Order, OrderItem
from django.core.mail import EmailMultiAlternatives
from django.template.loader import render_to_string
from django.utils.html import strip_tags


@admin.register(Category)
class CategoryAdmin(admin.ModelAdmin):
    list_display = ['name', 'slug', 'order', 'is_active', 'get_product_count']
    list_filter = ['is_active']
    search_fields = ['name', 'description']
    prepopulated_fields = {'slug': ('name',)}
    
    def get_product_count(self, obj):
        return obj.get_product_count()
    get_product_count.short_description = 'Products'


class OrderItemInline(admin.TabularInline):
    model = OrderItem
    extra = 0
    readonly_fields = ['product', 'quantity', 'price_at_purchase', 'subtotal']
    
    def subtotal(self, obj):
        return obj.subtotal


@admin.register(Order)
class OrderAdmin(admin.ModelAdmin):
    list_display = [
        'id', 'full_name', 'email', 'status',
        'total_amount', 'payment_method', 'created_at'
    ]
    list_filter = ['status', 'payment_method', 'created_at']
    search_fields = ['full_name', 'email', 'phone', 'tracking_number']
    readonly_fields = ['created_at', 'updated_at', 'shipped_at', 'delivered_at']
    inlines = [OrderItemInline]
    
    fieldsets = (
        ('Customer Information', {
            'fields': ('full_name', 'email', 'phone', 'shipping_address', 'order_notes')
        }),
        ('Order Details', {
            'fields': ('status', 'total_amount', 'payment_method', 'payment_slip', 'payment_id')
        }),
        ('Shipping', {
            'fields': ('tracking_number', 'shipped_at', 'delivered_at')
        }),
        ('Admin', {
            'fields': ('admin_notes', 'created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )
    
    actions = ['mark_as_paid', 'mark_as_shipped', 'mark_as_delivered']
    
    def mark_as_paid(self, request, queryset):
        for order in queryset:
            order.mark_as_paid()
        self.message_user(request, f"{queryset.count()} orders marked as paid")
    mark_as_paid.short_description = "Mark selected orders as paid"
    
    def mark_as_shipped(self, request, queryset):
        # This would normally prompt for tracking number
        self.message_user(request, "Please update tracking numbers individually")
    mark_as_shipped.short_description = "Mark selected orders as shipped"
    
    def mark_as_delivered(self, request, queryset):
        for order in queryset:
            order.mark_as_delivered()
        self.message_user(request, f"{queryset.count()} orders marked as delivered")
    mark_as_delivered.short_description = "Mark selected orders as delivered"

    def save_model(self, request, obj, form, change):
        # Get the old object to check if status changed
        old_obj = self.model.objects.get(pk=obj.pk) if change else None
        super().save_model(request, obj, form, change)
        
        # If status changed TO 'shipped', send email
        if change and old_obj.status != 'shipped' and obj.status == 'shipped' and obj.tracking_number:
            subject = f"Your TourAddis Order #{obj.reference_number} has been Shipped!"
            html_content = render_to_string('emails/order_shipped.html', {'order': obj})
            text_content = strip_tags(html_content)
            
            email = EmailMultiAlternatives(subject, text_content, 'info@touraddis.com', [obj.email])
            email.attach_alternative(html_content, "text/html")
            email.send(fail_silently=True) # fail_silently=True prevents admin crashes if email config is slightly off


@admin.register(Product)
class ProductAdmin(admin.ModelAdmin):
    list_display = [
        'name', 'category', 'price', 'final_price',
        'stock_quantity', 'is_available', 'is_featured'
    ]
    list_filter = ['category', 'is_available', 'is_featured', 'is_best_seller']
    search_fields = ['name', 'description', 'materials', 'origin']
    prepopulated_fields = {'slug': ('name',)}
    
    fieldsets = (
        ('Basic Information', {
            'fields': ('name', 'slug', 'category', 'short_description', 'description')
        }),
        ('Media', {
            'fields': ('main_image', 'image_2', 'image_3')
        }),
        ('Pricing', {
            'fields': ('price', 'discounted_price')
        }),
        ('Inventory', {
            'fields': ('stock_quantity', 'low_stock_threshold')
        }),
        ('Product Details', {
            'fields': ('weight', 'dimensions', 'materials', 'origin'),
            'classes': ('collapse',)
        }),
        ('Status', {
            'fields': ('is_available', 'is_featured', 'is_best_seller')
        }),
        ('SEO', {
            'fields': ('meta_title', 'meta_description', 'meta_keywords'),
            'classes': ('collapse',)
        }),
    )
    
    actions = ['mark_as_featured', 'mark_as_best_seller', 'reduce_stock']
    
    def mark_as_featured(self, request, queryset):
        queryset.update(is_featured=True)
        self.message_user(request, f"{queryset.count()} products marked as featured")
    mark_as_featured.short_description = "Mark selected products as featured"
    
    def mark_as_best_seller(self, request, queryset):
        queryset.update(is_best_seller=True)
        self.message_user(request, f"{queryset.count()} products marked as best sellers")
    mark_as_best_seller.short_description = "Mark selected products as best sellers"
    
    def reduce_stock(self, request, queryset):
        self.message_user(request, "Stock reduction should be done through orders")
    reduce_stock.short_description = "Reduce stock (use orders instead)"