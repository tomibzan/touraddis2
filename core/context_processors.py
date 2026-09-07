from .cart import Cart


def cart(request):
    """
    Context processor to make cart available in all templates.
    Lesson Learned: Eliminates need for custom template tags.
    """
    return {'cart': Cart(request)}