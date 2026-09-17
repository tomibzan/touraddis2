import logging
from django.db import transaction
from django.db.models import F
from django.http import HttpResponse, HttpResponseBadRequest
from django.shortcuts import render, get_object_or_404, redirect
from django.views.decorators.http import require_POST
from django.contrib import messages
from django.core.mail import send_mail
from django.conf import settings
from django.utils import timezone

from .models import Category, Product, Order, OrderItem
from .forms import CheckoutForm
from core.cart import Cart

logger = logging.getLogger(__name__)


# =====================================================
# PRODUCT LISTING
# =====================================================
def product_list(request, slug=None):
    """List products with optional category filtering and HTMX support."""
    categories = Category.objects.filter(is_active=True)
    current_category = None
    products = Product.objects.filter(is_available=True)

    if slug:
        current_category = get_object_or_404(Category, slug=slug, is_active=True)
        products = products.filter(category=current_category)

    # HTMX partial response for dynamic filtering
    if request.headers.get('HX-Request'):
        return render(request, 'marketplace/partials/product_grid.html', {
            'products': products,
            'current_category': current_category,
        })

    return render(request, 'marketplace/product_list.html', {
        'categories': categories,
        'current_category': current_category,
        'products': products,
    })


def category_detail(request, slug):
    """Alias for product_list filtered by category."""
    return product_list(request, slug=slug)


# =====================================================
# PRODUCT DETAIL
# =====================================================
def product_detail(request, slug):
    """Product detail page with thread-safe view counter."""
    product = get_object_or_404(Product, slug=slug, is_available=True)

    # Thread-safe view counter increment
    Product.objects.filter(id=product.id).update(views=F('views') + 1)
    
    # Refresh the object to get the updated view count (optional, but good for context)
    product.refresh_from_db(fields=['views'])

    # Related products from same category
    related_products = Product.objects.filter(
        category=product.category,
        is_available=True
    ).exclude(id=product.id)[:4]

    return render(request, 'marketplace/product_detail.html', {
        'product': product,
        'related_products': related_products,
    })


# =====================================================
# CART OPERATIONS
# =====================================================
def cart_detail(request):
    """Display shopping cart contents."""
    cart = Cart(request)
    return render(request, 'marketplace/cart_detail.html', {'cart': cart})


@require_POST
def cart_add(request, product_id):
    """Add product to cart with HTMX support and safe quantity parsing."""
    cart = Cart(request)
    product = get_object_or_404(Product, id=product_id, is_available=True)

    # Safe quantity parsing
    quantity_str = request.POST.get('quantity', '1')
    try:
        quantity = int(quantity_str) if quantity_str else 1
    except (ValueError, TypeError):
        quantity = 1

    # Validate stock
    if quantity > product.stock_quantity:
        error_msg = f"Only {product.stock_quantity} available in stock."
        if request.headers.get('HX-Request'):
            # Return 400 Bad Request for HTMX to handle gracefully
            return HttpResponseBadRequest(error_msg)
        
        messages.warning(request, error_msg)
        return redirect('marketplace:product_detail', slug=product.slug)

    if quantity <= 0:
        quantity = 1

    success = cart.add(product=product, quantity=quantity, override_quantity=False)

    if success:
        logger.info(f"Added {quantity}x {product.name} to cart")
    else:
        logger.warning(f"Failed to add {product.name} to cart")

    # HTMX response: return updated cart count badge
    if request.headers.get('HX-Request'):
        return render(request, 'core/partials/cart_count.html', {'cart': cart})

    messages.success(request, f"{product.name} added to cart!")
    return redirect('marketplace:cart_detail')


@require_POST
def cart_remove(request, product_id):
    """Remove product from cart with HTMX support."""
    cart = Cart(request)
    product = get_object_or_404(Product, id=product_id)
    
    # Check if product is actually in cart before removing
    if str(product.id) in cart.cart: 
        cart.remove(product)
        logger.info(f"Removed {product.name} from cart")

    # HTMX response
    if request.headers.get('HX-Request'):
        return render(request, 'core/partials/cart_count.html', {'cart': cart})

    messages.info(request, f"{product.name} removed from cart")
    return redirect('marketplace:cart_detail')


# =====================================================
# CHECKOUT
# =====================================================
def checkout(request):
    """Checkout view with atomic order creation and 'Buy Now' support."""
    cart = Cart(request)

    # Handle "Buy Now" directly from product page
    if request.method == 'GET' and 'buy_now' in request.GET:
        product_id = request.GET.get('buy_now')
        quantity_str = request.GET.get('quantity', '1')

        try:
            quantity = int(quantity_str) if quantity_str else 1
        except (ValueError, TypeError):
            quantity = 1

        product = get_object_or_404(Product, id=product_id, is_available=True)

        # Clear cart and add only this item for "Buy Now"
        cart.clear()
        cart.add(product=product, quantity=quantity, override_quantity=True)
        
        # Refresh cart object for the rest of the view
        cart = Cart(request)

    # Redirect if cart is empty
    if not cart or len(cart) == 0:
        messages.info(request, "Your cart is empty. Add some products first!")
        return redirect('marketplace:product_list')

    if request.method == 'POST':
        form = CheckoutForm(request.POST)
        if form.is_valid():
            try:
                with transaction.atomic():
                    # Create the order
                    order = form.save(commit=False)
                    order.total_amount = cart.get_total_price()
                    order.status = 'pending_payment'
                    
                    # Generate a professional reference number (e.g., ORD-20260910-001)
                    today = timezone.now().strftime('%Y%m%d')
                    daily_count = Order.objects.filter(created_at__date=timezone.now().date()).count() + 1
                    order.reference_number = f"ORD-{today}-{daily_count:03d}"
                    
                    order.save()

                    # Create order items and reduce stock
                    for item in cart:
                        OrderItem.objects.create(
                            order=order,
                            product=item['product'],
                            quantity=item['quantity'],
                            price_at_purchase=item['price'],
                        )
                        # Atomically reduce product stock
                        item['product'].reduce_stock(item['quantity'])

                    # ✅ ONLY clear the cart AFTER everything is successfully saved
                    cart.clear()

                # Send email notification (outside transaction to avoid blocking the user)
                try:
                    send_mail(
                        subject=f"New Order #{order.reference_number} - {order.full_name}",
                        message=(
                            f"New order placed on TourAddis Marketplace.\n\n"
                            f"Reference: {order.reference_number}\n"
                            f"Customer: {order.full_name}\n"
                            f"Email: {order.email}\n"
                            f"Phone: {order.phone}\n"
                            f"Total Amount: {order.total_amount} ETB\n"
                            f"Payment Method: {order.get_payment_method_display()}\n\n"
                            f"Shipping Address:\n{order.shipping_address}\n\n"
                            f"Order Notes: {order.order_notes or 'None'}\n\n"
                            f"Admin URL: {request.build_absolute_uri(f'/admin/marketplace/order/{order.id}/change/')}"
                        ),
                        from_email=settings.DEFAULT_FROM_EMAIL,
                        recipient_list=[settings.ADMIN_EMAIL, 'info@touraddis.com'],
                        fail_silently=True,
                    )
                    logger.info(f"Order #{order.reference_number} email sent successfully")
                except Exception as e:
                    logger.error(f"Order #{order.reference_number} email failed: {e}")

                logger.info(f"Order #{order.reference_number} created for {order.full_name}")
                return redirect('marketplace:checkout_success', order_id=order.id)

            except Exception as e:
                logger.error(f"Checkout failed: {e}")
                messages.error(request, "Something went wrong while processing your order. Please try again.")
    else:
        form = CheckoutForm()

    return render(request, 'marketplace/checkout.html', {
        'form': form,
        'cart': cart,
    })


def checkout_success(request, order_id):
    """Order confirmation page."""
    order = get_object_or_404(Order, id=order_id)
    return render(request, 'marketplace/checkout_success.html', {'order': order})


# =====================================================
# ORDER TRACKING
# =====================================================
def track_order(request):
    """Track order status by Reference Number and email."""
    order = None
    error = None

    if request.method == 'POST':
        # Strip # symbol, spaces, and convert to uppercase for robust matching
        ref_number = request.POST.get('order_id', '').strip().lstrip('#').strip().upper()
        email = request.POST.get('email', '').strip().lower()

        if not ref_number or not email:
            error = "Please enter both Reference Number and Email."
        else:
            try:
                order = Order.objects.get(reference_number=ref_number, email=email)
            except Order.DoesNotExist:
                error = "Order not found. Please check your Reference Number and Email."
            except Exception as e:
                logger.error(f"Order tracking error: {e}")
                error = "An error occurred. Please try again."

    return render(request, 'marketplace/track_order.html', {
        'order': order,
        'error': error,
    })