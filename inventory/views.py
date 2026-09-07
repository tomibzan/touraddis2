import logging
from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.db import transaction
from django.db.models import F  # ✅ Correctly imported F
from django.utils import timezone
from marketplace.models import Product
from .models import Supplier, StockMovement, LowStockAlert
from .forms import StockInForm, StockAdjustmentForm

logger = logging.getLogger(__name__)


@login_required
def inventory_dashboard(request):
    """Inventory overview dashboard."""
    # ✅ Uses F directly, no 'models.' prefix
    low_stock_products = Product.objects.filter(
        stock_quantity__lte=F('low_stock_threshold'),
        is_available=True
    )
    
    recent_movements = StockMovement.objects.select_related('product')[:20]
    
    stats = {
        'total_products': Product.objects.count(),
        'low_stock_count': low_stock_products.count(),
        'out_of_stock': Product.objects.filter(stock_quantity=0, is_available=True).count(),
        'total_movements_today': StockMovement.objects.filter(
            created_at__date=timezone.now().date()
        ).count(),
    }
    
    return render(request, 'inventory/dashboard.html', {
        'low_stock_products': low_stock_products,
        'recent_movements': recent_movements,
        'stats': stats,
    })


@login_required
def stock_in(request):
    """Add stock to products."""
    if request.method == 'POST':
        form = StockInForm(request.POST)
        if form.is_valid():
            with transaction.atomic():
                product = form.cleaned_data['product']
                quantity = form.cleaned_data['quantity']
                supplier = form.cleaned_data.get('supplier')
                reference = form.cleaned_data.get('reference_number')
                
                StockMovement.objects.create(
                    product=product,
                    movement_type='in',
                    quantity=quantity,
                    stock_before=product.stock_quantity,
                    supplier=supplier,
                    reference_number=reference,
                    performed_by=request.user,
                )
                
                product.increase_stock(quantity)
                
                messages.success(request, f"Added {quantity} units to {product.name}")
                logger.info(f"Stock in: {quantity}x {product.name} by {request.user}")
                return redirect('inventory:dashboard')
    else:
        form = StockInForm()
    
    return render(request, 'inventory/stock_in.html', {'form': form})


@login_required
def stock_adjustment(request):
    """Manual stock adjustment."""
    if request.method == 'POST':
        form = StockAdjustmentForm(request.POST)
        if form.is_valid():
            with transaction.atomic():
                product = form.cleaned_data['product']
                quantity = form.cleaned_data['quantity']
                reason = form.cleaned_data['reason']
                
                StockMovement.objects.create(
                    product=product,
                    movement_type='adjustment',
                    quantity=quantity,
                    stock_before=product.stock_quantity,
                    reason=reason,
                    performed_by=request.user,
                )
                
                if quantity > 0:
                    product.increase_stock(quantity)
                else:
                    product.reduce_stock(abs(quantity))
                
                messages.success(request, f"Stock adjusted for {product.name}")
                logger.info(f"Stock adjustment: {quantity}x {product.name} by {request.user}")
                return redirect('inventory:dashboard')
    else:
        form = StockAdjustmentForm()
    
    return render(request, 'inventory/stock_adjustment.html', {'form': form})


@login_required
def low_stock_alerts(request):
    """View and acknowledge low stock alerts."""
    alerts = LowStockAlert.objects.filter(
        is_acknowledged=False
    ).select_related('product')
    
    return render(request, 'inventory/low_stock_alerts.html', {
        'alerts': alerts,
    })


@login_required
def supplier_list(request):
    """List all suppliers."""
    suppliers = Supplier.objects.filter(is_active=True)
    return render(request, 'inventory/supplier_list.html', {
        'suppliers': suppliers,
    })


@login_required
def supplier_detail(request, pk):
    """Supplier detail with movement history."""
    supplier = get_object_or_404(Supplier, pk=pk)
    movements = supplier.movements.select_related('product')[:50]
    
    return render(request, 'inventory/supplier_detail.html', {
        'supplier': supplier,
        'movements': movements,
    })