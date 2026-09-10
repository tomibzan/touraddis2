from django.contrib import admin
from .models import ContactInquiry, NewsletterSubscription, SiteSettings, CarouselSlide, RateLimitRecord

# ---------------------------------------------------------
# Contact & Newsletter
# ---------------------------------------------------------
@admin.register(ContactInquiry)
class ContactInquiryAdmin(admin.ModelAdmin):
    list_display = ['name', 'email', 'subject', 'status', 'created_at']
    list_filter = ['status', 'created_at']
    search_fields = ['name', 'email', 'subject', 'reference_number']
    readonly_fields = ['reference_number', 'created_at', 'updated_at']

@admin.register(NewsletterSubscription)
class NewsletterSubscriptionAdmin(admin.ModelAdmin):
    list_display = ['email', 'source', 'is_active', 'created_at']
    list_filter = ['is_active', 'source']
    search_fields = ['email']

# ---------------------------------------------------------
# Site Settings (Singleton)
# ---------------------------------------------------------
@admin.register(SiteSettings)
class SiteSettingsAdmin(admin.ModelAdmin):
    list_display = ['site_name', 'contact_email', 'updated_at']
    
    def has_add_permission(self, request):
        # Ensure only one SiteSettings object can exist
        if SiteSettings.objects.exists():
            return False
        return super().has_add_permission(request)

# ---------------------------------------------------------
# Carousel Slides (NEW)
# ---------------------------------------------------------
@admin.register(CarouselSlide)
class CarouselSlideAdmin(admin.ModelAdmin):
    list_display = ['title', 'order', 'is_active', 'created_at']
    list_filter = ['is_active']
    list_editable = ['order', 'is_active']
    ordering = ['order']
    search_fields = ['title']

# ---------------------------------------------------------
# Rate Limit Records (For monitoring spam)
# ---------------------------------------------------------
@admin.register(RateLimitRecord)
class RateLimitRecordAdmin(admin.ModelAdmin):
    list_display = ['ip', 'action', 'timestamp']
    list_filter = ['action', 'timestamp']
    search_fields = ['ip']
    readonly_fields = ['ip', 'action', 'timestamp']