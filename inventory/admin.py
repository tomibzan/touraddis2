from django.contrib import admin
from .models import Supplier, StockMovement, LowStockAlert


@admin.register(Supplier)
class SupplierAdmin(admin.ModelAdmin):
    list_display = ['name', 'contact_person', 'email', 'phone', 'is_active']
    list_filter = ['is_active']
    search_fields = ['name', 'contact_person', 'email']


@admin.register(StockMovement)
class StockMovementAdmin(admin.ModelAdmin):
    list_display = [
        'product', 'movement_type', 'quantity',
        'stock_before', 'stock_after', 'performed_by', 'created_at'
    ]
    list_filter = ['movement_type', 'created_at', 'supplier']
    search_fields = ['product__name', 'reference_number', 'reason']
    readonly_fields = [
        'stock_before', 'stock_after',
        'created_at', 'updated_at'
    ]
    
    fieldsets = (
        ('Movement Details', {
            'fields': ('product', 'movement_type', 'quantity')
        }),
        ('References', {
            'fields': ('supplier', 'order', 'reference_number')
        }),
        ('Metadata', {
            'fields': ('performed_by', 'reason')
        }),
        ('Stock Snapshot', {
            'fields': ('stock_before', 'stock_after', 'created_at'),
            'classes': ('collapse',)
        }),
    )


@admin.register(LowStockAlert)
class LowStockAlertAdmin(admin.ModelAdmin):
    list_display = [
        'product', 'is_acknowledged',
        'acknowledged_by', 'created_at'
    ]
    list_filter = ['is_acknowledged', 'created_at']
    search_fields = ['product__name']
    readonly_fields = ['created_at', 'updated_at']
    
    actions = ['acknowledge_alerts']
    
    def acknowledge_alerts(self, request, queryset):
        for alert in queryset:
            alert.acknowledge(user=request.user)
        self.message_user(request, f"{queryset.count()} alerts acknowledged")
    acknowledge_alerts.short_description = "Acknowledge selected alerts"