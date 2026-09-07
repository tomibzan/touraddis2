from django import forms
from .models import ContactInquiry, NewsletterSubscription


class ContactForm(forms.ModelForm):
    """Contact form with validation."""
    
    class Meta:
        model = ContactInquiry
        fields = ['name', 'email', 'phone', 'subject', 'message']
        widgets = {
            'name': forms.TextInput(attrs={
                'class': 'w-full px-4 py-2 border border-stone-300 rounded-lg focus:ring-2 focus:ring-ethiopian-green focus:border-transparent',
                'placeholder': 'Your Name'
            }),
            'email': forms.EmailInput(attrs={
                'class': 'w-full px-4 py-2 border border-stone-300 rounded-lg focus:ring-2 focus:ring-ethiopian-green focus:border-transparent',
                'placeholder': 'your@email.com'
            }),
            'phone': forms.TextInput(attrs={
                'class': 'w-full px-4 py-2 border border-stone-300 rounded-lg focus:ring-2 focus:ring-ethiopian-green focus:border-transparent',
                'placeholder': '+251 9XX XXX XXX'
            }),
            'subject': forms.TextInput(attrs={
                'class': 'w-full px-4 py-2 border border-stone-300 rounded-lg focus:ring-2 focus:ring-ethiopian-green focus:border-transparent',
                'placeholder': 'Subject'
            }),
            'message': forms.Textarea(attrs={
                'class': 'w-full px-4 py-2 border border-stone-300 rounded-lg focus:ring-2 focus:ring-ethiopian-green focus:border-transparent',
                'rows': 5,
                'placeholder': 'Your message...'
            }),
        }


class NewsletterForm(forms.Form):
    """Newsletter subscription form."""
    email = forms.EmailField(widget=forms.EmailInput(attrs={
        'class': 'w-full px-4 py-2 border border-stone-300 rounded-lg',
        'placeholder': 'Enter your email'
    }))
    source = forms.CharField(widget=forms.HiddenInput(), required=False)