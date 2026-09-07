from django import forms
from .models import Order


class CheckoutForm(forms.ModelForm):
    """Checkout form with shipping and payment details."""

    class Meta:
        model = Order
        fields = [
            'full_name', 'email', 'phone',
            'shipping_address', 'order_notes', 'payment_method'
        ]
        widgets = {
            'full_name': forms.TextInput(attrs={
                'class': 'w-full px-4 py-2 border border-stone-300 rounded-lg focus:ring-2 focus:ring-ethiopian-green focus:border-transparent',
                'placeholder': 'Full Name'
            }),
            'email': forms.EmailInput(attrs={
                'class': 'w-full px-4 py-2 border border-stone-300 rounded-lg focus:ring-2 focus:ring-ethiopian-green focus:border-transparent',
                'placeholder': 'your@email.com'
            }),
            'phone': forms.TextInput(attrs={
                'class': 'w-full px-4 py-2 border border-stone-300 rounded-lg focus:ring-2 focus:ring-ethiopian-green focus:border-transparent',
                'placeholder': '+251 9XX XXX XXX'
            }),
            'shipping_address': forms.Textarea(attrs={
                'class': 'w-full px-4 py-2 border border-stone-300 rounded-lg focus:ring-2 focus:ring-ethiopian-green focus:border-transparent',
                'rows': 3,
                'placeholder': 'Full shipping address'
            }),
            'order_notes': forms.Textarea(attrs={
                'class': 'w-full px-4 py-2 border border-stone-300 rounded-lg focus:ring-2 focus:ring-ethiopian-green focus:border-transparent',
                'rows': 2,
                'placeholder': 'Special instructions (optional)'
            }),
            'payment_method': forms.Select(attrs={
                'class': 'w-full px-4 py-2 border border-stone-300 rounded-lg focus:ring-2 focus:ring-ethiopian-green focus:border-transparent'
            }),
        }