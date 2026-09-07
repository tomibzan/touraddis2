from django.urls import path
from . import views

app_name = 'marketplace'

urlpatterns = [
    path('', views.product_list, name='product_list'),
    path('category/<slug:slug>/', views.category_detail, name='category_detail'),
    path('product/<slug:slug>/', views.product_detail, name='product_detail'),
    path('cart/', views.cart_detail, name='cart_detail'),
    path('cart/add/<int:product_id>/', views.cart_add, name='cart_add'),
    path('cart/remove/<int:product_id>/', views.cart_remove, name='cart_remove'),
    path('checkout/', views.checkout, name='checkout'),
    path('checkout/success/<int:order_id>/', views.checkout_success, name='checkout_success'),
    path('track-order/', views.track_order, name='track_order'),
]