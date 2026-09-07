import logging
from django.shortcuts import render, get_object_or_404, redirect
from django.contrib import messages
from django.core.mail import send_mail
from django.conf import settings
from django.db import transaction
from django.utils import timezone
from .models import Tour, Booking
from .forms import BookingForm

logger = logging.getLogger(__name__)


def tour_list(request):
    """List all active tours with filtering."""
    region = request.GET.get('region')
    
    tours = Tour.objects.filter(is_active=True)
    
    if region and region != 'all':
        tours = tours.filter(region=region)
    
    featured_tours = tours.filter(is_featured=True)[:3]
    
    return render(request, 'tours/tour_list.html', {
        'tours': tours,
        'featured_tours': featured_tours,
        'current_region': region,
        'regions': Tour.REGION_CHOICES,
    })


def tour_detail(request, slug):
    """Tour detail page with booking form."""
    tour = get_object_or_404(Tour, slug=slug, is_active=True)
    
    # Increment view counter
    tour.views += 1
    tour.save(update_fields=['views'])
    
    form = BookingForm()
    
    return render(request, 'tours/tour_detail.html', {
        'tour': tour,
        'form': form,
    })


def book_tour(request, slug):
    """Process tour booking."""
    tour = get_object_or_404(Tour, slug=slug, is_active=True)
    
    if request.method == 'POST':
        form = BookingForm(request.POST, request.FILES)
        if form.is_valid():
            with transaction.atomic():
                booking = form.save(commit=False)
                booking.tour = tour
                booking.total_price = tour.price_per_person * booking.number_of_guests
                booking.status = 'pending'
                booking.save()
                
                # Send email notification
                try:
                    send_mail(
                        subject=f"New Tour Booking: {booking.reference_number}",
                        message=(
                            f"New booking received!\n\n"
                            f"Reference: {booking.reference_number}\n"
                            f"Tour: {tour.title}\n"
                            f"Customer: {booking.customer_name}\n"
                            f"Email: {booking.customer_email}\n"
                            f"Phone: {booking.customer_phone}\n"
                            f"Date: {booking.tour_date}\n"
                            f"Guests: {booking.number_of_guests}\n"
                            f"Total: {booking.total_price} ETB\n\n"
                            f"Please contact the customer with payment details."
                        ),
                        from_email=settings.DEFAULT_FROM_EMAIL,
                        recipient_list=[settings.ADMIN_EMAIL, 'info@touraddis.com'],
                        fail_silently=True,
                    )
                    logger.info(f"Booking email sent for {booking.reference_number}")
                except Exception as e:
                    logger.error(f"Booking email failed for {booking.reference_number}: {e}")
                
                messages.success(
                    request,
                    f"Booking received! Reference: {booking.reference_number}. We'll contact you shortly."
                )
                return redirect('tours:tour_detail', slug=slug)
    else:
        form = BookingForm()
    
    return render(request, 'tours/book_tour.html', {
        'tour': tour,
        'form': form,
    })


def track_booking(request):
    """Track booking status."""
    booking = None
    error = None
    
    if request.method == 'POST':
        email = request.POST.get('email')
        reference = request.POST.get('reference')
        
        try:
            if reference:
                booking = Booking.objects.get(reference_number=reference, customer_email=email)
            else:
                booking = Booking.objects.filter(customer_email=email).first()
                
            if not booking:
                error = "No booking found. Please check your details."
        except Booking.DoesNotExist:
            error = "No booking found. Please check your details."
    
    return render(request, 'tours/track_booking.html', {
        'booking': booking,
        'error': error,
    })