from django.contrib import admin
from .models import Tour, TourImage, Booking


class TourImageInline(admin.TabularInline):
    model = TourImage
    extra = 1


@admin.register(Tour)
class TourAdmin(admin.ModelAdmin):
    list_display = [
        'title', 'region', 'price_per_person',
        'duration_days', 'is_featured', 'is_active'
    ]
    list_filter = ['region', 'is_featured', 'is_active', 'difficulty_level']
    search_fields = ['title', 'description', 'short_description']
    prepopulated_fields = {'slug': ('title',)}
    inlines = [TourImageInline]
    
    fieldsets = (
        ('Basic Information', {
            'fields': ('title', 'slug', 'region', 'short_description', 'description', 'itinerary')
        }),
        ('Media', {
            'fields': ('hero_image', 'image_2', 'image_3')
        }),
        ('Logistics', {
            'fields': ('price_per_person', 'duration_days', 'max_group_size', 'difficulty_level')
        }),
        ('Inclusions', {
            'fields': ('includes', 'excludes'),
            'classes': ('collapse',)
        }),
        ('Status', {
            'fields': ('is_featured', 'is_active')
        }),
        ('SEO', {
            'fields': ('meta_title', 'meta_description'),
            'classes': ('collapse',)
        }),
    )
    
    actions = ['mark_as_featured', 'activate_tours', 'deactivate_tours']
    
    def mark_as_featured(self, request, queryset):
        queryset.update(is_featured=True)
        self.message_user(request, f"{queryset.count()} tours marked as featured")
    mark_as_featured.short_description = "Mark selected tours as featured"
    
    def activate_tours(self, request, queryset):
        queryset.update(is_active=True)
        self.message_user(request, f"{queryset.count()} tours activated")
    activate_tours.short_description = "Activate selected tours"
    
    def deactivate_tours(self, request, queryset):
        queryset.update(is_active=False)
        self.message_user(request, f"{queryset.count()} tours deactivated")
    deactivate_tours.short_description = "Deactivate selected tours"


@admin.register(Booking)
class BookingAdmin(admin.ModelAdmin):
    list_display = [
        'reference_number', 'customer_name', 'tour',
        'tour_date', 'number_of_guests', 'total_price', 'status'
    ]
    list_filter = ['status', 'payment_method', 'tour', 'tour_date']
    search_fields = [
        'reference_number', 'customer_name',
        'customer_email', 'customer_phone'
    ]
    readonly_fields = ['reference_number', 'created_at', 'updated_at']
    
    fieldsets = (
        ('Customer Information', {
            'fields': (
                'customer_name', 'customer_email',
                'customer_phone', 'customer_nationality'
            )
        }),
        ('Booking Details', {
            'fields': ('tour', 'tour_date', 'number_of_guests', 'special_requests')
        }),
        ('Payment', {
            'fields': ('payment_method', 'payment_slip', 'payment_id', 'total_price')
        }),
        ('Status', {
            'fields': ('status', 'reference_number')
        }),
        ('Admin', {
            'fields': ('admin_notes', 'created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )
    
    actions = ['confirm_bookings', 'mark_as_paid', 'mark_as_completed', 'cancel_bookings']
    
    def confirm_bookings(self, request, queryset):
        for booking in queryset:
            booking.confirm()
        self.message_user(request, f"{queryset.count()} bookings confirmed")
    confirm_bookings.short_description = "Confirm selected bookings"
    
    def mark_as_paid(self, request, queryset):
        for booking in queryset:
            booking.mark_as_paid()
        self.message_user(request, f"{queryset.count()} bookings marked as paid")
    mark_as_paid.short_description = "Mark selected bookings as paid"
    
    def mark_as_completed(self, request, queryset):
        for booking in queryset:
            booking.mark_as_completed()
        self.message_user(request, f"{queryset.count()} bookings marked as completed")
    mark_as_completed.short_description = "Mark selected bookings as completed"
    
    def cancel_bookings(self, request, queryset):
        for booking in queryset:
            booking.cancel()
        self.message_user(request, f"{queryset.count()} bookings cancelled")
    cancel_bookings.short_description = "Cancel selected bookings"