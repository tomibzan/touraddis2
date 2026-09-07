import logging
from decimal import Decimal, InvalidOperation
from django.conf import settings
from django.db import transaction
from marketplace.models import Product

logger = logging.getLogger(__name__)


class Cart:
    """
    Production-ready shopping cart with atomic operations.
    Lesson Learned: Proper Decimal handling, stock validation, and error logging.
    """
    
    def __init__(self, request):
        self.session = request.session
        cart = self.session.get(settings.CART_SESSION_ID)
        if not cart:
            cart = self.session[settings.CART_SESSION_ID] = {}
        self.cart = cart

    def __iter__(self):
        """Iterate over cart items with product details."""
        product_ids = self.cart.keys()
        products = Product.objects.filter(id__in=product_ids, is_available=True)
        cart_copy = self.cart.copy()
        
        for product in products:
            cart_copy[str(product.id)]['product'] = product
            
        for item in cart_copy.values():
            try:
                # Ensure proper Decimal conversion
                item['price'] = Decimal(str(item['price']))
                item['total_price'] = item['price'] * item['quantity']
                yield item
            except (InvalidOperation, KeyError) as e:
                logger.error(f"Cart iteration error: {e}")
                continue

    def __len__(self):
        """Return total number of items in cart."""
        return sum(item['quantity'] for item in self.cart.values())

    def get_total_price(self):
        """Calculate total price of all items."""
        try:
            return sum(
                Decimal(str(item['price'])) * item['quantity'] 
                for item in self.cart.values()
            )
        except (InvalidOperation, KeyError) as e:
            logger.error(f"Cart total calculation error: {e}")
            return Decimal('0.00')

    @transaction.atomic
    def add(self, product, quantity=1, override_quantity=False):
        """
        Add product to cart with atomic operation.
        Lesson Learned: Stock validation and proper error handling.
        """
        try:
            product_id = str(product.id)
            
            # Validate stock
            if quantity > product.stock_quantity:
                logger.warning(
                    f"Attempted to add {quantity} of {product.name}, "
                    f"but only {product.stock_quantity} in stock"
                )
                quantity = product.stock_quantity
            
            if quantity <= 0:
                logger.warning(f"Invalid quantity {quantity} for product {product.id}")
                return False
            
            # Initialize product in cart if not exists
            if product_id not in self.cart:
                self.cart[product_id] = {
                    'quantity': 0,
                    'price': str(product.price)
                }
            
            # Update quantity
            if override_quantity:
                self.cart[product_id]['quantity'] = quantity
            else:
                self.cart[product_id]['quantity'] += quantity
            
            # Update price if it changed
            self.cart[product_id]['price'] = str(product.price)
            
            self.save()
            logger.info(f"Added {quantity}x {product.name} to cart")
            return True
            
        except Exception as e:
            logger.error(f"Error adding product {product.id} to cart: {e}")
            return False

    def save(self):
        """Mark session as modified to trigger save."""
        self.session.modified = True

    def remove(self, product):
        """Remove product from cart."""
        product_id = str(product.id)
        if product_id in self.cart:
            del self.cart[product_id]
            self.save()
            logger.info(f"Removed product {product.name} from cart")

    def clear(self):
        """Clear entire cart."""
        if settings.CART_SESSION_ID in self.session:
            del self.session[settings.CART_SESSION_ID]
            self.save()
            logger.info("Cart cleared")

    def get_items(self):
        """Return list of cart items as dictionaries."""
        items = []
        for item in self:
            items.append({
                'product_id': item['product'].id,
                'product': item['product'],
                'quantity': item['quantity'],
                'price': item['price'],
                'total_price': item['total_price'],
            })
        return items