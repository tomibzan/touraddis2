import logging
import csv
from django.shortcuts import render
from django.contrib.auth.decorators import login_required
from django.http import HttpResponse
from django.db.models import Sum, Count
from django.utils import timezone
from datetime import timedelta
from marketplace.models import Order, Product
from tours.models import Booking

logger = logging.getLogger(__name__)


@login_required
def reports_dashboard(request):
    """Main reports dashboard."""
    today = timezone.now().date()
    last_30_days = today - timedelta(days=30)
    
    # Sales stats
    orders_last_30 = Order.objects.filter(
        created_at__date__gte=last_30_days,
        status__in=['payment_received', 'shipped', 'delivered']
    )
    
    total_revenue = orders_last_30.aggregate(
        total=Sum('total_amount')
    )['total'] or 0
    
    # Booking stats
    bookings_last_30 = Booking.objects.filter(
        created_at__date__gte=last_30_days,
        status__in=['confirmed', 'paid', 'completed']
    )
    
    booking_revenue = bookings_last_30.aggregate(
        total=Sum('total_price')
    )['total'] or 0
    
    stats = {
        'orders_count': orders_last_30.count(),
        'orders_revenue': total_revenue,
        'bookings_count': bookings_last_30.count(),
        'bookings_revenue': booking_revenue,
        'total_revenue': total_revenue + booking_revenue,
    }
    
    return render(request, 'reports/dashboard.html', {'stats': stats})


@login_required
def sales_report(request):
    """Detailed sales report."""
    orders = Order.objects.filter(
        status__in=['payment_received', 'shipped', 'delivered']
    ).select_related('items__product').order_by('-created_at')[:100]
    
    return render(request, 'reports/sales_report.html', {'orders': orders})


@login_required
def product_performance(request):
    """Product performance report."""
    from django.db.models import F
    from marketplace.models import OrderItem
    
    top_products = OrderItem.objects.values(
        'product__name', 'product__id'
    ).annotate(
        total_sold=Sum('quantity'),
        total_revenue=Sum('price_at_purchase') * Sum('quantity')
    ).order_by('-total_sold')[:20]
    
    return render(request, 'reports/product_performance.html', {
        'top_products': top_products,
    })


@login_required
def booking_report(request):
    """Tour booking report."""
    bookings = Booking.objects.filter(
        status__in=['confirmed', 'paid', 'completed']
    ).select_related('tour').order_by('-created_at')[:100]
    
    return render(request, 'reports/booking_report.html', {'bookings': bookings})


@login_required
def export_sales_csv(request):
    """Export sales data as CSV."""
    response = HttpResponse(content_type='text/csv')
    response['Content-Disposition'] = 'attachment; filename="sales_report.csv"'
    
    writer = csv.writer(response)
    writer.writerow(['Order ID', 'Date', 'Customer', 'Email', 'Total', 'Status'])
    
    orders = Order.objects.filter(
        status__in=['payment_received', 'shipped', 'delivered']
    ).order_by('-created_at')
    
    for order in orders:
        writer.writerow([
            order.id,
            order.created_at.strftime('%Y-%m-%d'),
            order.full_name,
            order.email,
            order.total_amount,
            order.get_status_display(),
        ])
    
    logger.info(f"Sales report exported by {request.user}")
    return response