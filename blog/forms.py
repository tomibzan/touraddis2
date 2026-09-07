from django import forms
from .models import Comment


class CommentForm(forms.ModelForm):
    """Comment form for blog articles."""
    
    class Meta:
        model = Comment
        fields = ['name', 'email', 'content']
        widgets = {
            'name': forms.TextInput(attrs={
                'class': 'w-full px-4 py-2 border border-stone-300 rounded-lg',
                'placeholder': 'Your Name'
            }),
            'email': forms.EmailInput(attrs={
                'class': 'w-full px-4 py-2 border border-stone-300 rounded-lg',
                'placeholder': 'your@email.com'
            }),
            'content': forms.Textarea(attrs={
                'class': 'w-full px-4 py-2 border border-stone-300 rounded-lg',
                'rows': 4,
                'placeholder': 'Your comment...'
            }),
        }