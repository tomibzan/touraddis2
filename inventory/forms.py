from django import forms
from marketplace.models import Product
from .models import Supplier


class StockInForm(forms.Form):
    """Form for adding stock."""
    product = forms.ModelChoiceField(
        queryset=Product.objects.filter(is_available=True),
        widget=forms.Select(attrs={
            'class': 'w-full px-4 py-2 border border-stone-300 rounded-lg'
        })
    )
    quantity = forms.IntegerField(
        min_value=1,
        widget=forms.NumberInput(attrs={
            'class': 'w-full px-4 py-2 border border-stone-300 rounded-lg'
        })
    )
    supplier = forms.ModelChoiceField(
        queryset=Supplier.objects.filter(is_active=True),
        required=False,
        widget=forms.Select(attrs={
            'class': 'w-full px-4 py-2 border border-stone-300 rounded-lg'
        })
    )
    reference_number = forms.CharField(
        required=False,
        widget=forms.TextInput(attrs={
            'class': 'w-full px-4 py-2 border border-stone-300 rounded-lg',
            'placeholder': 'PO/Invoice number'
        })
    )


class StockAdjustmentForm(forms.Form):
    """Form for manual stock adjustments."""
    product = forms.ModelChoiceField(
        queryset=Product.objects.all(),
        widget=forms.Select(attrs={
            'class': 'w-full px-4 py-2 border border-stone-300 rounded-lg'
        })
    )
    quantity = forms.IntegerField(
        widget=forms.NumberInput(attrs={
            'class': 'w-full px-4 py-2 border border-stone-300 rounded-lg',
            'placeholder': 'Use negative for reduction'
        }),
        help_text="Positive to add, negative to reduce"
    )
    reason = forms.CharField(
        widget=forms.Textarea(attrs={
            'class': 'w-full px-4 py-2 border border-stone-300 rounded-lg',
            'rows': 3,
            'placeholder': 'Reason for adjustment'
        })
    )