from django import forms
from .models import Booking


class BookingForm(forms.ModelForm):
    """Tour booking form."""
    
    class Meta:
        model = Booking
        fields = [
            'customer_name', 'customer_email', 'customer_phone',
            'customer_nationality', 'tour_date', 'number_of_guests',
            'special_requests', 'payment_method'
        ]
        widgets = {
            'tour_date': forms.DateInput(attrs={
                'type': 'date',
                'class': 'w-full px-4 py-2 border border-stone-300 rounded-lg',
                'min': forms.DateField().widget_attrs(forms.DateInput()).get('min')
            }),
            'number_of_guests': forms.NumberInput(attrs={
                'class': 'w-full px-4 py-2 border border-stone-300 rounded-lg',
                'min': 1
            }),
            'customer_name': forms.TextInput(attrs={
                'class': 'w-full px-4 py-2 border border-stone-300 rounded-lg'
            }),
            'customer_email': forms.EmailInput(attrs={
                'class': 'w-full px-4 py-2 border border-stone-300 rounded-lg'
            }),
            'customer_phone': forms.TextInput(attrs={
                'class': 'w-full px-4 py-2 border border-stone-300 rounded-lg'
            }),
            'customer_nationality': forms.TextInput(attrs={
                'class': 'w-full px-4 py-2 border border-stone-300 rounded-lg'
            }),
            'special_requests': forms.Textarea(attrs={
                'class': 'w-full px-4 py-2 border border-stone-300 rounded-lg',
                'rows': 3
            }),
            'payment_method': forms.Select(attrs={
                'class': 'w-full px-4 py-2 border border-stone-300 rounded-lg'
            }),
        }